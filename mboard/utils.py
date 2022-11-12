import re
from django.utils.html import escape
from mboard.models import Post, Board
from precise_bbcode.bbcode import get_parser
import random
from urllib.request import urlopen
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.contrib.sessions.models import Session


def process_post(new_post: Post, board: Board, new_thread: bool, thread_id, request):
    if new_thread:  # new thread
        new_post.board = board
    else:  # new post
        new_post.thread_id = int(thread_id)
        new_post.thread.bump = new_post.bump
        new_post.board = new_post.thread.board

    new_post.text = escape(new_post.text)
    new_post.text = insert_links(new_post.text, new_post)
    new_post.text = color_quoted_text(new_post.text)
    parser = get_parser()
    new_post.text = parser.render(new_post.text)
    new_post.text = roll_game(new_post.text)
    link_cookie_to_post(new_post, request)
    new_post.save()


def link_cookie_to_post(new_post, request):
    try:
        Session.objects.get(session_key=request.session.session_key)
    except Session.DoesNotExist:  # new session or user has key not present in db
        request.session.create()
    new_post.cookie = request.session.session_key


def color_quoted_text(post_string):
    quoted_text = re.findall(r'^\s*&gt;.+', post_string, flags=re.MULTILINE)  # '^\s*&gt;[^&gt;].+'
    if quoted_text:
        span = "<span class='quoted-text'>{index}</span>"
        for count, index in enumerate(quoted_text):
            post_string = post_string.replace(index, span.format(index=index.strip()))
    return post_string


def insert_links(post_string, new_post):
    found_quotes = re.findall(pattern='&gt;&gt;[0-9]+', string=post_string)
    if found_quotes:
        for quote in found_quotes:
            html = "<a class='quote' data-quote='{}' href='{}'>>>{}</a>"
            quote_num = quote.strip('&gt;&gt;')
            post = Post.objects.filter(pk=quote_num).first()  # no error is raised if Null unlike get()
            if post:  # if the post exists and isn't some random number
                posts_ids = new_post.thread.posts_ids() if new_post.thread else []
                if post.pk in posts_ids:
                    if post.thread is None:
                        html = html.format(quote_num, post.get_absolute_url()+f'#id{quote_num}', quote_num + ' (OP)')
                    html = html.format(quote_num, post.get_absolute_url(), quote_num)
                else:
                    html = html.format(quote_num, post.get_absolute_url(), quote_num + ' →')
                post_string = post_string.replace(quote, html)
    return post_string


def roll_game(s):
    roll_found = re.findall('\[roll\]', s)  # todo
    if roll_found:
        roll = random.randint(0, 81527)
        colored = f"<span class='roll'>{roll}</span>"
        s = s.replace(roll_found[0], colored, 1)
    return s


def test_if_ip_is_bad(request):
    ip = request.META.get("REMOTE_ADDR")
    bad_ip = False
    url = 'https://check.getipintel.net/check.php?flag={flag}&ip={ip}&contact={email}'
    full_url = url.format(flag='m', ip=ip, email=settings.EMAIL)
    try:
        ip_check_response = urlopen(full_url)
        ip_is_bad_chance = ip_check_response.read().decode()
        if float(ip_is_bad_chance) >= 0.99:
            bad_ip = True
    except Exception as e:  # noqa
        pass
    finally:
        return bad_ip


def spam_protection(make_new_post):
    def wrapper(request, *args, **kwargs):
        if settings.PREVENT_SPAM:
            bad_ip = test_if_ip_is_bad(request)
            if bad_ip:
                return decline_posting(request)
        return make_new_post(request, *args, **kwargs)
    return wrapper


def decline_posting(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'errors': {'error': 'Proxy/VPN'}})
    return HttpResponse('Proxy/VPN')
