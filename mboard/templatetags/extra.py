import os
from django import template


register = template.Library()


@register.simple_tag()
def get_proper_elided_page_range(paginator, pagenum, on_each_side, on_ends):
    return paginator.get_elided_page_range(number=pagenum, on_each_side=on_each_side, on_ends=on_ends)


@register.filter(name='strippath')  # gets '/filepath/file.extension', returns 'file.extension'
def into_basename(file):
    return os.path.basename(file)
