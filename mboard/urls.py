from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.shortcuts import redirect
from mboard.views import list_threads, get_thread, ajax_tooltips_onhover, ajax_load_new_posts, \
    captcha_ajax_validation, ajax_posting, info_page, post_vote

app_name = 'mboard'

urlpatterns = [
    path('postvote/', post_vote),
    path('info/', info_page, name='info_page'),
    path('captcha_val/', captcha_ajax_validation),
    path('posting/', ajax_posting),
    path('', lambda request: redirect('mboard:list_threads', board='b')),
    path('<str:board>/', list_threads, name='list_threads'),
    path('<str:board>/<int:pagenum>/', list_threads, name='threads_paginator'),
    path('<str:board>/thread/<int:thread_id>/', get_thread, name='get_thread'),
    path('<str:board>/thread/<int:thread_id>/<int:post_id>.json', ajax_tooltips_onhover),
    path('<str:board>/thread/<int:thread_id>.json', ajax_load_new_posts),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
