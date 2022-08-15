from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render, redirect, reverse, get_object_or_404
from mboard.models import Post, Board
from .forms import PostForm, ThreadPostForm
from PIL import Image
from io import BytesIO
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.views.decorators.http import last_modified
from email.utils import parsedate_to_datetime


def list_threads(request, board, pagenum=1):
    board = get_object_or_404(Board, board_name=board)
    if request.method == 'POST':
        if 'threadnum' in request.POST:  # reply to the thread from outside the thread (JS)
            return get_thread(request, request.POST.get('threadnum'), board, x=True)
        form = ThreadPostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_thread = form.save(commit=False)
            if form.cleaned_data['image']:
                new_thread.thumbnail = make_thumbnail(
                    form.cleaned_data['image'])
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


def get_thread(request, thread_id, board, x=False):
    if request.method == 'POST':
        form = PostForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            if form.cleaned_data['image']:
                new_post.thumbnail = make_thumbnail(form.files['image'])
            new_post.thread_id = thread_id
            new_post.thread.bump = new_post.bump
            new_post.thread.save()
            new_post.board = new_post.thread.board
            new_post.save()
            return redirect(
                reverse('mboard:get_thread', kwargs={'thread_id': thread_id, 'board': board}) + f'#id{new_post.id}')
        if x:  # failed reply from outside the thread
            return render(request, 'post_error.html', {'form': form, 'board': board})
    else:
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


def make_thumbnail(inmemory_image):
    image = Image.open(inmemory_image)
    image.thumbnail(size=(200, 220))
    output = BytesIO()
    image.save(output, quality=85, format=image.format)
    thumb = InMemoryUploadedFile(
        output, 'ImageField', 'thumb_' + inmemory_image.name, 'image/jpeg', None, None)
    return thumb


def main_page(request):
    return render(request, 'main_page.html', context={'board': 'mboard'})
