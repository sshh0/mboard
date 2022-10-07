from django.contrib import admin
from django.urls import path, include
# from django.http import HttpResponse


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mboard.urls')),
    path('captcha/', include('captcha.urls')),
    # path('robots.txt', lambda x: HttpResponse("User-Agent: *\nDisallow: /", content_type="text/plain")),
    # path('__debug__/', include('debug_toolbar.urls')),
]
