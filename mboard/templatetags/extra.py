import re
import os
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from mboard.models import Post
from precise_bbcode.bbcode import get_parser

register = template.Library()


@register.simple_tag()
def get_proper_elided_page_range(paginator, pagenum, on_each_side, on_ends):
    return paginator.get_elided_page_range(number=pagenum, on_each_side=on_each_side, on_ends=on_ends)


@register.simple_tag()
def customize_post_string(post_string, thread, posts_ids):
    post_string = escape(post_string)
    post_string = insert_links(post_string, thread, posts_ids)
    post_string = color_quoted_text(post_string)
    parser = get_parser()
    post_string = parser.render(post_string)
    return mark_safe(post_string.replace("\n", "<br>"))


@register.filter(name='strippath')  # gets '/filepath/file.extension', returns 'file.extension'
def into_basename(file):
    return os.path.basename(file)


def color_quoted_text(post_string):
    quoted_text = re.findall(r'^\s*&gt;.+', post_string, flags=re.MULTILINE)  # '^\s*&gt;[^&gt;].+'
    if quoted_text:
        span = "<span style='color:peru'>{index}</span>"
        for count, index in enumerate(quoted_text):
            post_string = post_string.replace(index, span.format(index=index.strip()))
    return post_string


def insert_links(post_string, thread, posts_ids):
    found_quote = re.findall(pattern='&gt;&gt;[0-9]+', string=post_string)
    if found_quote:
        for quote in found_quote:
            quote_num = quote.strip('&gt;&gt;')
            post = Post.objects.filter(pk=quote_num).first()  # no error is raised if Null unlike get()
            if post:  # if the post exists, and not some random number
                html = "<a class='quote' data-quote='{data_id}' href='{link}'>>>{post_id}</a>"
                if post.pk not in posts_ids[thread]:  # post exists but in another thread
                    html = html.format(data_id=quote_num, link=post.get_absolute_url(), post_id=quote_num + ' →')
                else:
                    html = html.format(data_id=quote_num, link=post.get_absolute_url(), post_id=quote_num)
                post_string = post_string.replace(quote, html)
    return post_string
