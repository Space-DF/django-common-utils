from django.conf import settings
from django.utils.module_loading import import_string

from common.celery.constants import SUBSCRIPTION_LIFECYCLE_EXCHANGES


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


def send_subscription_task(service, lifecycle, task_name, message, **kwargs):
    celery_app = import_string(settings.CELERY_APP)
    exchange = SUBSCRIPTION_LIFECYCLE_EXCHANGES.get(lifecycle)
    if exchange is None:
        raise ValueError(f"unsupported subscription lifecycle: {lifecycle}")

    routing_key = f"{service}.{lifecycle}"
    return celery_app.send_task(
        name=f"spacedf.tasks.{task_name}",
        exchange=exchange,
        routing_key=routing_key,
        retry=True,
        retry_policy=dict(
            max_retries=3, interval_start=3, interval_step=1, interval_max=6
        ),
        kwargs=message,
        **kwargs,
    )
