from django.apps import AppConfig


class MboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mboard'

    def ready(self):
        import mboard.signals  # signals aren't imported automatically # noqa




