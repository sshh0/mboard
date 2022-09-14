from django.db.models.signals import post_delete
from mboard.models import Post


def delete_media(instance, **kwargs):  # Signal receivers must accept keyword arguments (**kwargs).
    if instance.image or instance.video:
        instance.image.delete(save=False)
        instance.thumbnail.delete(save=False)
        instance.video.delete(save=False)
        instance.video_thumb.delete(save=False)



post_delete.connect(delete_media, Post)
