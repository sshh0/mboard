from email.utils import parsedate_to_datetime
from random import randint
from django.conf import settings
from captcha.models import CaptchaStore
from django.db.models import Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage
from django.views.decorators.http import last_modified, require_POST
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import timedelta
from mboard.models import Post, Board, Rating, CalcTime
from libs.meritrank.trust import BL_PHT
from .forms import PostForm, ThreadPostForm
from django.views.decorators.cache import cache_page, never_cache
import networkx as nx
from django.contrib.sessions.models import Session
from django.db.models import Q

# The amount of vote a post gives to the edge into its creator.
# If there is only a single outgoing edge (which is the case), the actual amount
# doesn't matter. However, setting it to a specific value is useful for debugging
POST_TO_USER_VOTE = 77777

# The minimal amount of vote the author gives to its post when creating it.
# Authors can change the vote for their post to promote it at the price of higher
# risk of backlash and spending their popularity. This is one of the important tuning
# parameters for the algorithm which is up to discussion.
MINIMAL_AUTHOR_VOTE = 1

# This is how much more important negative votes are than positive ones
# e.g. if it is 10, this means 1 negative vote is balanced out by 10 positive ones.
NEGATIVE_VOTE_AMPLIFICATION_COEFFICIENT = 10

# Posts from users with less than this rank will be hidden from view.
# Setting this to 0.0 or higher will effectively hide all posts by stranded (new) users
SHADOWBAN_THRESHOLD = -0.01

# Only this number of stranded posts will be shown at the end of a thread. The rest
# will be hidden from the user.
STRANDED_POSTS_IN_THREAD_LIMIT = 10


def refresh_rank(request, board):
    try:
        Session.objects.get(session_key=request.session.session_key)
    except Session.DoesNotExist:  # new session or user has key not present in db
        request.session.create()
    user = Session.objects.get(session_key=request.session.session_key)
    obj, created = CalcTime.objects.get_or_create(user=user, board=board, defaults={'user': user, 'board': board})
    cache_expired = obj.rank_calc_time + timedelta(hours=1) > timezone.now()
    if not cache_expired and not created and not settings.RANK_DEBUG:
        return user

    G = nx.DiGraph()

    # Add Post -> Author edges
    # Every post gets a single outgoing edge: the edge into its creator.
    # This means the post transitively sends all the votes/merit/credit to its creator.
    for node in board.post_set.all():
        G.add_edge(node, node.session, weight=POST_TO_USER_VOTE)
        # Add Author -> Post edge of a minimum/default size.
        G.add_edge(node.session, node, weight=MINIMAL_AUTHOR_VOTE)

    # Add User -> Post edges (just read from Rating table)
    # Note this can overwrite default author vote if the author voted for his post.
    for node in board.rating_set.all():
        # Do not overwrite edges added by the "add default author edges" procedure above,
        # in case the corresponding DB rank row was added automatically by recalculation procedure earlier.
        # If we do overwrite it with data from the DB, which could be vote=0.0,
        # the result will be zero OPpost ratings.
        # This is an ugly workaround that stems from the "user-target" Rating table keys design.
        if G.get_edge_data(node.user, node.target, default={}).get(
                'weight') == MINIMAL_AUTHOR_VOTE and node.vote == 0.0:
            continue

        G.add_edge(node.user, node.target,
                   weight=node.vote if node.vote >= 0.0 else node.vote * NEGATIVE_VOTE_AMPLIFICATION_COEFFICIENT)

    rep = calc_rep(G, user)
    for target, rank in rep.items():
        # print(user, target, rank)
        if not (isinstance(user, Session) and isinstance(target, Post)):
            # We only save User->Post edges in DB
            continue
        Rating.objects.update_or_create(board=board,
                                        user=user,
                                        target=target,
                                        defaults={'rank': rank})
    CalcTime.objects.filter(user=user, board=board).update(rank_calc_time=timezone.now())
    return user


def calc_rep(graph, seed_node):
    ppr = BL_PHT(graph, seed_node)
    reputation = {}
    # print(graph.edges)
    for n in graph.nodes():
        if n != seed_node:
            reputation[n] = ppr.compute(seed_node, n)
    return reputation


def single_annotate(user, thread):  # add rank/vote fields to a single thread (for OP post on a thread page)
    if user != thread.session:
        try:
            obj = Rating.objects.get(user=user, target=thread)
            thread.rank = obj.rank
            thread.vote = obj.vote
            thread.vote_time = obj.vote_time
        except Rating.DoesNotExist:
            pass
    return thread


def multi_annotate(user, threads):
    return threads.annotate(
        # Coalesce is required to force NULLs -> 0.0
        rank=Coalesce(Subquery(
            Rating.objects.filter(
                user=user,
                target=OuterRef('pk')
            ).values('rank')
        ), 0.0),
        vote=Subquery(
            Rating.objects.filter(
                user=user,
                target=OuterRef('pk')
            ).values_list('vote')
        ),
        vote_time=Subquery(
            Rating.objects.filter(
                user=user,
                target=OuterRef('pk')
            ).values('vote_time')
        )
    )


def create_new_thread(request, board, ):
    form = ThreadPostForm(data=request.POST, files=request.FILES)
    if not form.is_valid():
        return render(request, 'post_error.html', {'form': form, 'board': board})
    new_thread = form.save(commit=False)
    new_thread.board = board
    new_thread.session_id = request.session.session_key
    new_thread.save()
    return redirect(reverse('mboard:get_thread', kwargs={'thread_id': new_thread.id, 'board': board}))


@never_cache  # adds headers to response to disable browser cache
# @cache_page(3600)  # cache also resets (signals.py) after saving a new post, so it's only useful under a small load
def list_threads(request, board, pagenum=1):
    board = get_object_or_404(Board, board_link=board)
    if request.method == 'POST':
        return create_new_thread(request, board)
    form = ThreadPostForm()
    user = refresh_rank(request, board)

    threads = board.post_set.all().filter(thread__isnull=True)
    threads = multi_annotate(user, threads)
    threads = threads.filter(Q(session=request.session.session_key) | Q(rank__gt=0)).order_by('-rank')

    threads_dict, posts_ids = {}, {}
    paginator = Paginator(threads, 10)
    try:
        threads = paginator.page(number=pagenum)
    except InvalidPage:
        return redirect(reverse('mboard:list_threads', kwargs={'board': board}))

    for thread in threads:
        threads_dict[thread] = multi_annotate(user=user, threads=thread.post_set.all()).exclude(
            rank__lt=SHADOWBAN_THRESHOLD)[:4]
        posts_ids[thread.pk] = thread.posts_ids()
        # threads_rank_dict[thread.pk] = Rating.objects.get(user=user, target=thread.session)

    context = {'threads': threads_dict,
               'form': form,
               'paginator': paginator,
               'rank_debug': settings.RANK_DEBUG,
               'page_obj': threads,
               'board': board,
               'posts_ids': posts_ids}
    return render(request, 'list_threads.html', context)


def create_new_post(request, thread_id, board):
    form = PostForm(data=request.POST, files=request.FILES)
    if not form.is_valid():
        return render(request, 'post_error.html', {'form': form, 'board': board})
    new_post = form.save(commit=False)
    new_post.thread_id = thread_id
    new_post.session_id = request.session.session_key
    new_post.thread.bump = new_post.bump
    new_post.thread.save()
    new_post.board = new_post.thread.board
    new_post.save()
    return redirect(
        reverse('mboard:get_thread', kwargs={'thread_id': thread_id, 'board': board}) + f'#id{new_post.id}')


@never_cache
# @cache_page(3600)
def get_thread(request, thread_id, board):
    if request.method == 'POST':
        return create_new_post(request, thread_id, board)
    board = get_object_or_404(Board, board_link=board)
    thread = get_object_or_404(Post, pk=thread_id)
    user = refresh_rank(request, board)
    thread = single_annotate(user=user, thread=thread)
    posts = multi_annotate(user, thread.post_set.all()).exclude(rank__lt=SHADOWBAN_THRESHOLD)

    posts_filtered = []
    stranded_count = 0
    # Allow only STRANDED_POSTS_IN_THREAD_LIMIT number of stranded posts in a thread
    for p in reversed(posts):
        if p.rank == 0.0 and p.session != user:
            stranded_count += 1
            if stranded_count >= STRANDED_POSTS_IN_THREAD_LIMIT:
                continue
        posts_filtered.append(p)
    posts_filtered.reverse()

    form = PostForm(initial={'thread_id': thread_id})
    context = {'thread': thread,
               'posts_ids': {thread.pk: thread.posts_ids()},
               'form': form,
               'board': board,
               'rank_debug': settings.RANK_DEBUG,
               'posts': posts_filtered}
    return render(request, 'thread.html', context)


@require_POST
def ajax_posting(request):
    if request.POST.get('thread_id'):  # it's a post to an existing thread
        form = PostForm(data=request.POST, files=request.FILES)
    else:  # new thread
        form = ThreadPostForm(data=request.POST, files=request.FILES)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors})

    new_post = form.save(commit=False)
    new_post.session_id = request.session.session_key
    if form.data.get('thread_id'):
        new_post.thread_id = form.data['thread_id']
    new_post.board = Board.objects.get(board_link=request.POST['board'])
    new_post.save()  # '.id' doesn't exist before saving
    thread_id = new_post.thread_id if new_post.thread_id else new_post.id
    return JsonResponse({"postok": 'ok', 'thread_id': thread_id})


def ajax_tooltips_onhover(request, thread_id, **kwargs):
    if not (request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'post_id' in kwargs):
        return None
    post = Post.objects.get(pk=kwargs['post_id'])
    thread = Post.objects.get(pk=thread_id)
    post_ids = {thread.pk: thread.posts_ids()}
    jsn = render_to_string('post.html',
                           {'post': post,
                            'thread': thread,
                            'posts_ids': post_ids},
                           request)
    return JsonResponse(jsn, safe=False)


@last_modified(lambda request, thread_id, **kwargs: Post.objects.get(pk=thread_id).bump)
def ajax_load_new_posts(request, thread_id, **kwargs):  # don't proceed if no new posts, return 304 response
    thread = Post.objects.get(pk=thread_id)
    return get_new_posts(request, thread)


def ajax_discover_new_threads(request, board, **kwargs):
    board = get_object_or_404(Board, board_link=board)
    user = refresh_rank(request, board)
    stranded_threads = multi_annotate(user, board.post_set.all().filter(  # also exclude user's own threads
        thread__isnull=True)).filter(~Q(session=request.session.session_key) & Q(rank=0.0))
    if not stranded_threads:
        return HttpResponse(status=204)
    jsn = ''.join(
        render_to_string(
            'thread_disc.html',
            {'thread': thread, 'posts_ids': {thread.pk: thread.posts_ids()}},
            request)
        for thread in stranded_threads)  # could be a lot of threads, a limit should be imposed somehow

    return JsonResponse(jsn, safe=False)


def get_new_posts(request, thread):
    last_post_date = parsedate_to_datetime(request.headers['If-Modified-Since'])
    posts = thread.post_set.all().filter(date__gt=last_post_date)
    posts_ids = {thread.pk: thread.posts_ids()}
    if not posts:
        return None
    html_rendered_string = ''.join(
        render_to_string(
            request=request, template_name='post.html',
            context={
                'post': post,
                'thread': thread,
                'show_unvoted_rank': settings.RANK_DEBUG,
                'posts_ids': posts_ids})
        for post in posts)
    return JsonResponse(html_rendered_string, safe=False)


def random_digit_challenge():
    code = ''.join(str(randint(0, 9)) for _ in range(0, 4))
    return code, code


def captcha_ajax_validation(request):
    cs = CaptchaStore.objects.filter(response=request.GET['captcha'], hashkey=request.GET['hash'])
    if cs or settings.CAPTCHA_TEST_MODE:
        json_data = {'status': 1}
    else:
        json_data = {'status': 0, 'err': _('Invalid captcha')}
    return JsonResponse(json_data)


@cache_page(3600)
def info_page(request):
    context = {'board': ' '}
    try:
        context.update(
            {'plast24h': Post.objects.all().filter(date__gte=timezone.now() - timedelta(hours=24)).count(),
             'firstp_date': Post.objects.first().date,
             'lastp_date': Post.objects.last().date,
             'tcount': Post.objects.filter(thread=None).count(),
             'pcount': Post.objects.count(),
             'bcount': Board.objects.count()}
        )
    except Exception:  # noqa
        pass
    finally:
        return render(request, 'info_page.html', context)


def post_vote(request):
    vote = request.GET['vote']
    target = Post.objects.get(pk=int(request.GET['post']))
    user = Session.objects.get(session_key=request.session.session_key)
    rating, _ = Rating.objects.get_or_create(user=user, target=target, board=target.board)
    if vote and target and rating:
        if rating.vote_time and rating.vote_time > timezone.now() - timedelta(minutes=10):
            return JsonResponse({'vote': 'Expired'})
        rating.vote_time = timezone.now()
        rating.vote += 1 if int(vote) == 1 else -1
        rating.save()
        return JsonResponse({'vote': rating.vote})
    return JsonResponse({'vote': 'Not allowed'})
