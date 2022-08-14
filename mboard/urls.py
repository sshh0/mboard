from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from mboard.views import *

app_name = 'mboard'

urlpatterns = [
    path('', main_page, name='main_page'),
    path('<str:board>/', list_threads, name='list_threads'),
    path('<str:board>/<int:pagenum>/', list_threads, name='list_threads'),
    path('<str:board>/thread/<int:thread_id>/', get_thread, name='get_thread'),
    path('<str:board>/thread/<int:thread_id>/<int:post_id>.json', ajax_tooltips_onhover),
    path('<str:board>/thread/<int:thread_id>.json', ajax_load_new_posts),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
