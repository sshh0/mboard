from email.utils import parsedate_to_datetime
from django.conf import settings
from captcha.models import CaptchaStore
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator, InvalidPage
from django.views.decorators.http import last_modified, require_POST
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import timedelta
from mboard.models import Post, Board
from .forms import PostForm, ThreadPostForm
from django.views.decorators.cache import cache_page
from mboard.utils import process_post
from django.contrib import messages


def list_threads(request, board, pagenum=1):
    board = get_object_or_404(Board, board_link=board)
    if request.method == 'POST':
        return create_new_post(request, board, new_thread=True)
    form = ThreadPostForm()
    threads = board.post_set.filter(thread__isnull=True).order_by('-bump')
    paginator = Paginator(threads, 10)
    try:
        threads = paginator.page(number=pagenum)
    except InvalidPage:
        return redirect(reverse('mboard:list_threads', kwargs={'board': board}))
    threads_dict = {thread: thread.post_set.order_by('-date')[:4][::-1] for thread in threads}
    context = {'threads': threads_dict, 'form': form, 'paginator': paginator, 'page_obj': threads, 'board': board}
    return render(request, 'list_threads.html', context)


def get_thread(request, thread_id, board):
    board = get_object_or_404(Board, board_link=board)
    if request.method == 'POST':
        return create_new_post(request, board, new_thread=False, thread_id=thread_id)
    thread = get_object_or_404(Post, pk=thread_id)
    form = PostForm(initial={'thread_id': thread_id})
    context = {'thread': thread, 'form': form, 'board': board}
    return render(request, 'thread.html', context)


def create_new_post(request, board: Board, new_thread: bool, thread_id: int = None):  # pure html posting
    if new_thread:
        form = ThreadPostForm(data=request.POST, files=request.FILES)
    else:
        form = PostForm(data=request.POST, files=request.FILES)
    if not form.is_valid():
        return render(request, 'post_error.html', {'form': form, 'board': board})
    new_post = form.save(commit=False)
    try:
        process_post(request, new_post, board, new_thread, thread_id)
    except Exception:
        form.add_error(field=None, error='Posting error')  # TODO translate
        return render(request, 'post_error.html', {'form': form, 'board': board})
    thread_id = thread_id if thread_id else new_post.id
    append_id = '' if new_thread else f'#id{new_post.id}'
    return redirect(
        reverse('mboard:get_thread', kwargs={'thread_id': thread_id, 'board': board}) + append_id)


@require_POST
def ajax_posting(request):
    if request.POST.get('thread_id'):  # it's a post to an existing thread
        form = PostForm(data=request.POST, files=request.FILES)
        new_thread = False
    else:  # new thread
        form = ThreadPostForm(data=request.POST, files=request.FILES)
        new_thread = True
    if not form.is_valid():
        return JsonResponse({'errors': form.errors})

    board = get_object_or_404(Board, board_link=request.POST['board'])
    new_post = form.save(commit=False)
    thread_id = form.data.get('thread_id', default=None)
    try:
        process_post(request, new_post, board, new_thread, thread_id)
    except Exception:
        return JsonResponse({'errors': ['Posting error']})  # todo translate
    new_post_id = new_post.thread_id if new_post.thread_id else new_post.id
    return JsonResponse({"postok": 'ok', 'new_post_id': new_post_id})


@require_POST
def delete_post(request):
    try:
        post = Post.objects.get(pk=request.POST.get('post-id'))  # TODO many posts???
        if request.POST.get('del-pass', None) == settings.MOD_PASS:
            messages.success(request, f'Deleted {post.pk}')
            post.delete()
        else:
            try:
                assert post.cookie == request.session.session_key, _('Incorrect password')
                assert timezone.now() <= post.date + timedelta(minutes=15), _('You cannot delete a post this old')
                assert post.thread is not None, _('You cannot delete a thread')
                post.delete()
            except (AssertionError, Exception) as e:
                messages.error(request, e)
    except Post.DoesNotExist:
        messages.error(request, _("The post doesn't exist"))
    finally:
        return redirect(request.META['HTTP_REFERER'])


def ajax_tooltips_onhover(request, **kwargs):
    post = get_object_or_404(Post, pk=kwargs['post_id'])
    json_html = render_to_string('post.html', {'post': post}, request)
    return JsonResponse(json_html, safe=False)


@last_modified(lambda request, thread_id, **kwargs: Post.objects.get(pk=thread_id).bump)
def ajax_load_new_posts(request, thread_id, **kwargs):  # don't proceed if no new posts, return 304 response
    thread = get_object_or_404(Post, pk=thread_id)
    return get_new_posts(request, thread)


def get_new_posts(request, thread):
    last_post_date = parsedate_to_datetime(request.headers['If-Modified-Since'])
    posts = thread.post_set.filter(date__gt=last_post_date)
    html_rendered_string = ''
    if posts:
        for post in posts:
            html_rendered_string += render_to_string('post.html', {'post': post}, request)
        return JsonResponse(html_rendered_string, safe=False)
    return HttpResponse(status=304)


def random_digit_challenge():
    code = str(timezone.now().microsecond)[:4]  # random digits to be used in captcha
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
             'bcount': Board.objects.count(),
             'posts': Post.objects.order_by('-date')[:20]}
        )
    except Exception:
        pass
    finally:
        return render(request, 'info_page.html', context)


def catalog(request, board):
    board = get_object_or_404(Board, board_link=board)
    threads = board.post_set.filter(thread__isnull=True).order_by('-bump')[:50]
    return render(request, 'threads_catalog.html', context={'board': board, 'threads': threads})
