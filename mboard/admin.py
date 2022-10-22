from django.contrib import admin
from .models import Post, Board, Rating, CalcTime
from django.contrib.sessions.models import Session


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'bump', 'date', 'poster', 'thread', 'board', 'post_shortened', 'video', 'session']

    def post_shortened(self, obj):
        return obj.text[:20]


class BoardAdmin(admin.ModelAdmin):
    list_display = ['board_link', 'id']


class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'target', 'vote', 'rank']


class CalcTimeAdmin(admin.ModelAdmin):
    list_display = ['user', 'rank_calc_time']


admin.site.register(Post, PostAdmin)
admin.site.register(Board, BoardAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(CalcTime, CalcTimeAdmin)
admin.site.register(Session)
