from email.utils import parsedate_to_datetime
from random import randint
from captcha.models import CaptchaStore
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.views.decorators.http import last_modified
from mboard.models import Post, Board
from .forms import PostForm, ThreadPostForm


def list_threads(request, board, pagenum=1):
    board = get_object_or_404(Board, board_name=board)
    if request.method == 'POST':
        if 'threadnum' in request.POST:  # reply to the thread from outside the thread (JS)
            return get_thread(request, request.POST.get('threadnum'), board)
        form = ThreadPostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_thread = form.save(commit=False)
            new_thread.board = board
            new_thread.save()
            return redirect(reverse('mboard:get_thread', kwargs={'thread_id': new_thread.id, 'board': board}))
    else:
        form = ThreadPostForm()
    threads = board.post_set.all().filter(thread__isnull=True).order_by('-bump')[:20]
    threads_dict = {}
    posts_ids = {}
    paginator = Paginator(threads, 10)
    threads = paginator.page(number=pagenum)
    for thread in threads:
        posts_to_display = thread.post_set.all().order_by('-date')[:4]
        threads_dict[thread] = reversed(posts_to_display)
        posts_ids[thread] = thread.all_posts_ids_in_thread()
    context = {'threads': threads_dict, 'form': form, 'paginator': paginator, 'page_obj': threads, 'board': board,
               'posts_ids': posts_ids}
    return render(request, 'list_threads.html', context)


def get_thread(request, thread_id, board):
    if request.method == 'POST':
        form = PostForm(data=request.POST, files=request.FILES, use_required_attribute=False)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.thread_id = thread_id
            new_post.thread.bump = new_post.bump
            new_post.thread.save()
            new_post.board = new_post.thread.board
            new_post.save()
            return redirect(
                reverse('mboard:get_thread', kwargs={'thread_id': thread_id, 'board': board}) + f'#id{new_post.id}')
        return render(request, 'post_error.html', {'form': form, 'board': board})
    form = PostForm
    board = Board.objects.get(board_name=board)
    thread = board.post_set.get(pk=thread_id)
    context = {'thread': thread, 'posts_ids': {thread: thread.all_posts_ids_in_thread()}, 'form': form, 'board': board}
    return render(request, 'thread.html', context)


def ajax_tooltips_onhover(request, thread_id, **kwargs):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'post_id' in kwargs:
            post = Post.objects.get(pk=kwargs['post_id'])
            thread = Post.objects.get(pk=thread_id)
            posts_ids = {thread: thread.all_posts_ids_in_thread()}
            jsn = render_to_string(request=request, template_name='post.html',
                                   context={'post': post, 'thread': thread, 'posts_ids': posts_ids})
            return JsonResponse(jsn, safe=False)


@last_modified(lambda request, thread_id, **kwargs: Post.objects.get(pk=thread_id).bump)
def ajax_load_new_posts(request, thread_id, **kwargs):  # don't proceed if no new posts, return 304 response
    thread = Post.objects.get(pk=thread_id)
    return get_new_posts(request, thread)


def get_new_posts(request, thread):
    last_post_date = parsedate_to_datetime(request.headers['If-Modified-Since'])
    posts = thread.post_set.all().filter(date__gt=last_post_date)
    posts_ids = {thread: thread.all_posts_ids_in_thread()}
    html_rendered_string = ''
    if posts:
        for post in posts:
            html_rendered_string += render_to_string(request=request, template_name='post.html',
                                                     context={'post': post, 'thread': thread, 'posts_ids': posts_ids})
        return JsonResponse(html_rendered_string, safe=False)


def random_digit_challenge():
    ret = ''
    for _ in range(4):
        ret += str(randint(0, 9))
    return ret, ret


def captcha_ajax_validation(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cs = CaptchaStore.objects.filter(response=request.GET['captcha'], hashkey=request.GET['hash'])
        if cs:
            json_data = {'status': 1}
        else:
            json_data = {'status': 0}
        return JsonResponse(json_data)
    else:
        json_data = {'status': 0}
        return JsonResponse(json_data)
