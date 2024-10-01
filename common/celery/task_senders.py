from django.conf import settings
from django.utils.module_loading import import_string


def send_task(name, message, **kwargs):
    celery_app = import_string(settings.CELERY_APP)
    return celery_app.send_task(
        name=f"spacedf.tasks.{name}",
        exchange=name,
        routing_key=f"spacedf.tasks.{name}",
        retry=True,
        retry_policy=dict(
            max_retries=3, interval_start=3, interval_step=1, interval_max=6
        ),
        kwargs=message,
        **kwargs,
    )
