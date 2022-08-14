from django.apps import AppConfig


class MboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mboard'

    def ready(self):
        from .signals import post_delete
