from django.apps import AppConfig


class CeleryAutoreloadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common.apps.celery_autoreload"
