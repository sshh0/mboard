from django.contrib import admin
from .models import Post, Board, Rating


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'bump', 'date', 'poster', 'thread', 'board', 'post_shortened', 'video']

    def post_shortened(self, obj):
        return obj.text[:20]


class BoardAdmin(admin.ModelAdmin):
    list_display = ['board_link', 'id']


class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'target', 'vote', 'rank']


admin.site.register(Post, PostAdmin)
admin.site.register(Board, BoardAdmin)
admin.site.register(Rating, RatingAdmin)
