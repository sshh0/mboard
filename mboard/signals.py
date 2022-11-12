from django.db.models.signals import post_delete, post_save
from mboard.models import Post
# from django.core.cache import cache


def delete_media(instance, **kwargs):  # "Signal receivers must accept keyword arguments (**kwargs)"
    if instance.image:
        instance.image.delete(save=False)
        instance.thumbnail.delete(save=False)

    if instance.video:
        instance.video.delete(save=False)
        instance.video_thumb.delete(save=False)


def bump_thread(instance, **kwards):
    if instance.thread is not None:
        instance.thread.bump = instance.bump
        instance.thread.save()


# def clear_cache(**kwards):
#     cache.clear()


post_delete.connect(delete_media, Post)
# post_delete.connect(clear_cache, Post)

post_save.connect(bump_thread, Post)
# post_save.connect(clear_cache, Post)
