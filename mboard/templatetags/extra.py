import re
import os
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from mboard.models import Post
from precise_bbcode.bbcode import get_parser
from faker import Faker
register = template.Library()


@register.filter()
def gen_name_from_cookie(cookie_id):
    """
    as we keep updating datasets, results are not guaranteed to be consistent across patch versions
    (from faker README)
    """
    name = Faker('ru_RU')  # can take a locale argument to return localised data
    name.seed_instance(cookie_id)
    return name.name()


@register.simple_tag()
def get_proper_elided_page_range(paginator, pagenum, on_each_side, on_ends):
    return paginator.get_elided_page_range(number=pagenum, on_each_side=on_each_side, on_ends=on_ends)


@register.simple_tag()
def customize_post_string(post_string, thread_id, posts_ids, post_id):
    post_string = escape(post_string)
    post_string = insert_links(post_string, thread_id, posts_ids)
    post_string = color_quoted_text(post_string)
    parser = get_parser()
    post_string = parser.render(post_string)
    post_string = roll_game(post_string, post_id)
    return mark_safe(post_string.replace("\n", "<br>"))


@register.filter(name='strippath')  # gets '/filepath/file.extension', returns 'file.extension'
def into_basename(file):
    return os.path.basename(file)


def color_quoted_text(post_string):
    quoted_text = re.findall(r'^\s*&gt;.+', post_string, flags=re.MULTILINE)  # '^\s*&gt;[^&gt;].+'
    if quoted_text:
        span = "<span style='color:#789922'>{index}</span>"
        for count, index in enumerate(quoted_text):
            post_string = post_string.replace(index, span.format(index=index.strip()))
    return post_string


def insert_links(post_string, thread_id, posts_ids):
    found_quote = re.findall(pattern='&gt;&gt;[0-9]+', string=post_string)
    if found_quote:
        for quote in found_quote:
            html = "<a class='quote' data-quote='{}' href='{}'>>>{}</a>"
            quote_num = quote.strip('&gt;&gt;')
            post = Post.objects.filter(pk=quote_num).first()  # no error is raised if Null unlike get()
            if post:  # if the post exists, and not some random number
                if post.pk not in posts_ids[thread_id]:  # post exists but in another thread
                    html = html.format(quote_num, post.get_absolute_url(), quote_num + ' →')
                else:
                    if post.thread is None:
                        html = html.format(quote_num, post.get_absolute_url()+f'#id{quote_num}', quote_num + ' (OP)')
                    html = html.format(quote_num, post.get_absolute_url(), quote_num)
                post_string = post_string.replace(quote, html)
    return post_string


def roll_game(s, post_id):
    roll_found = re.findall('\[roll\]', s)
    if roll_found:
        msec = Post.objects.get(pk=post_id).date.microsecond
        roll = str(msec * post_id + msec)[-5:]
        colored = f"<span class='roll'>{roll}</span>"
        s = s.replace(roll_found[0], colored, 1)
    return s
