from email.utils import parsedate_to_datetime
from random import randint
from django.conf import settings
from captcha.models import CaptchaStore
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage
from django.views.decorators.http import last_modified
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import timedelta
from mboard.models import Post, Board, Rating, CalcTime
from .forms import PostForm, ThreadPostForm
from django.views.decorators.cache import cache_page, never_cache
from trust.pagerank import PersonalizedPageRank
import networkx as nx
from django.contrib.sessions.models import Session
# import matplotlib.pyplot as plt


def testfunc(request):
    if not request.session.session_key:
        request.session.create()
    user = Session.objects.get(session_key=request.session.session_key)
    obj, created = CalcTime.objects.get_or_create(user=user, defaults={'user': user})
    if created is True or obj.rank_calc_time < timezone.now():  # session was just created or expired
        G = nx.DiGraph()
        for node in Rating.objects.all():
            G.add_edge(node.user, node.target, weight=node.vote)
        rep = calc_rep(G, user)
        for target, rank in rep.items():
            print(user, target, rank)
            Rating.objects.update_or_create(user=user,
                                            target=target,
                                            defaults={'rank': rank})
    else:
        for i in Rating.objects.filter(user=user).order_by('-rank'):  # up to date session, sort results by rank
            print(i, i.rank)


def calc_rep(graph, seed_node):
    ppr = PersonalizedPageRank(graph, seed_node, reset_probability=0.0)
    reputation = {}
    for n in graph.nodes():
        if n != seed_node:
            reputation[n] = ppr.compute(seed_node, n)
    return reputation


# def vote(voter, author, amount=1):
#     weight = G.get_edge_data(voter, author, default={'weight': 0})['weight'] + amount
#     G.add_edge(voter, author, weight=weight)


# def vis_graph(g):
#     # Visualize the graph, for clarity
#     pos = nx.spring_layout(g)
#     nx.draw_networkx(g, pos, font_size=7)
#     labels = nx.get_edge_attributes(g, 'weight')
#     nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)
#
#     plt.savefig("filename.png")


@never_cache  # adds headers to response to disable browser cache
# @cache_page(3600)  # cache also resets (signals.py) after saving a new post, so it's only useful under a small load
def list_threads(request, board, pagenum=1):
    board = get_object_or_404(Board, board_link=board)
    if request.method == 'POST':
        form = ThreadPostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_thread = form.save(commit=False)
            new_thread.board = board
            new_thread.session_id = request.session.session_key
            new_thread.save()
            return redirect(reverse('mboard:get_thread', kwargs={'thread_id': new_thread.id, 'board': board}))
        return render(request, 'post_error.html', {'form': form, 'board': board})
    testfunc(request)
    form = ThreadPostForm()
    threads = board.post_set.all().filter(thread__isnull=True).order_by('-bump')
    threads_dict, posts_ids = {}, {}
    paginator = Paginator(threads, 10)
    try:
        threads = paginator.page(number=pagenum)
    except InvalidPage:
        return redirect(reverse('mboard:list_threads', kwargs={'board': board}))
    for thread in threads:
        posts_to_display = thread.post_set.all().order_by('-date')[:4]
        threads_dict[thread] = reversed(posts_to_display)
        posts_ids[thread.pk] = thread.posts_ids()
    context = {'threads': threads_dict, 'form': form, 'paginator': paginator, 'page_obj': threads, 'board': board,
               'posts_ids': posts_ids}
    return render(request, 'list_threads.html', context)


@never_cache
# @cache_page(3600)
def get_thread(request, thread_id, board):
    if request.method == 'POST':
        form = PostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.thread_id = thread_id
            new_post.session_id = request.session.session_key
            new_post.thread.bump = new_post.bump
            new_post.thread.save()
            new_post.board = new_post.thread.board
            new_post.save()
            return redirect(
                reverse('mboard:get_thread', kwargs={'thread_id': thread_id, 'board': board}) + f'#id{new_post.id}')
        return render(request, 'post_error.html', {'form': form, 'board': board})
    board = get_object_or_404(Board, board_link=board)
    thread = get_object_or_404(Post, pk=thread_id)
    if not request.session.session_key:
        request.session.create()
    form = PostForm(initial={'thread_id': thread_id})
    context = {'thread': thread, 'posts_ids': {thread.pk: thread.posts_ids()}, 'form': form, 'board': board}
    return render(request, 'thread.html', context)


def ajax_posting(request):
    if request.method == 'POST':
        if request.POST.get('thread_id'):  # it's a post to an existing thread
            form = PostForm(data=request.POST, files=request.FILES)
        else:  # new thread
            form = ThreadPostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.session_id = request.session.session_key
            if form.data.get('thread_id'):
                new_post.thread_id = form.data['thread_id']
            new_post.board = Board.objects.get(board_link=request.POST['board'])
            new_post.save()  # '.id' doesn't exist before saving
            thread_id = new_post.thread_id if new_post.thread_id else new_post.id
            return JsonResponse({"postok": 'ok', 'thread_id': thread_id})
        return JsonResponse({'errors': form.errors})
    return JsonResponse({'errors': _('Posting error')})


def ajax_tooltips_onhover(request, thread_id, **kwargs):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'post_id' in kwargs:
        post = Post.objects.get(pk=kwargs['post_id'])
        thread = Post.objects.get(pk=thread_id)
        post_ids = {thread.pk: thread.posts_ids()}
        jsn = render_to_string('post.html',
                               {'post': post, 'thread': thread, 'posts_ids': post_ids}, request)
        return JsonResponse(jsn, safe=False)


@last_modified(lambda request, thread_id, **kwargs: Post.objects.get(pk=thread_id).bump)
def ajax_load_new_posts(request, thread_id, **kwargs):  # don't proceed if no new posts, return 304 response
    thread = Post.objects.get(pk=thread_id)
    return get_new_posts(request, thread)


def get_new_posts(request, thread):
    last_post_date = parsedate_to_datetime(request.headers['If-Modified-Since'])
    posts = thread.post_set.all().filter(date__gt=last_post_date)
    posts_ids = {thread.pk: thread.posts_ids()}
    html_rendered_string = ''
    if posts:
        for post in posts:
            html_rendered_string += render_to_string(request=request, template_name='post.html',
                                                     context={'post': post, 'thread': thread, 'posts_ids': posts_ids})
        return JsonResponse(html_rendered_string, safe=False)


def random_digit_challenge():
    code = ''
    for _ in range(4):
        code += str(randint(0, 9))
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
        context['plast24h'] = Post.objects.all().filter(date__gte=timezone.now() - timedelta(hours=24)).count()
        context['firstp_date'] = Post.objects.first().date
        context['lastp_date'] = Post.objects.last().date
        context['tcount'] = Post.objects.filter(thread=None).count()
        context['pcount'] = Post.objects.count()
        context['bcount'] = Board.objects.count()
        return render(request, 'info_page.html', context)
    except Exception:  # noqa
        return render(request, 'info_page.html', context)


def post_vote(request):
    vote = request.GET['vote']
    post = Post.objects.get(pk=int(request.GET['post']))
    if vote and post:
        post.vote += 1 if int(vote) == 1 else -1
        post.save()
        return JsonResponse({'vote': post.vote})
    return HttpResponse(status=400)
