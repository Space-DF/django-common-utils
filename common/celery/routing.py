from django.conf import settings
from django.utils.module_loading import import_string
from kombu import Exchange, Queue


def setup_synchronous_model_task_routing():
    celery_app = import_string(settings.CELERY_APP)

    if celery_app.conf.task_queues is None:
        celery_app.conf.task_queues = ()
    if celery_app.conf.task_routes is None:
        celery_app.conf.task_routes = {}

    for model_name in settings.CLONE_MODELS:
        celery_app.conf.task_queues = celery_app.conf.task_queues + (
            Queue(
                f"{settings.SERVICE_NAME}_update_{model_name}",
                exchange=Exchange(f"update_{model_name}", type="fanout"),
                routing_key=f"update_{model_name}",
                queue_arguments={
                    "x-single-active-consumer": True,
                },
            ),
            Queue(
                f"{settings.SERVICE_NAME}_delete_{model_name}",
                exchange=Exchange(f"delete_{model_name}", type="fanout"),
                routing_key=f"delete_{model_name}",
                queue_arguments={
                    "x-single-active-consumer": True,
                },
            ),
        )
        update_task_name = f"spacedf.tasks.update_{model_name}"
        celery_app.conf.task_routes[update_task_name] = {
            "queue": f"{settings.SERVICE_NAME}_update_{model_name}",
            "routing_key": f"update_{model_name}",
        }
        delete_task_name = f"spacedf.tasks.delete_{model_name}"
        celery_app.conf.task_routes[delete_task_name] = {
            "queue": f"{settings.SERVICE_NAME}_delete_{model_name}",
            "routing_key": f"delete_{model_name}",
        }


def setup_organization_task_routing():
    celery_app = import_string(settings.CELERY_APP)

    if celery_app.conf.task_queues is None:
        celery_app.conf.task_queues = ()
    if celery_app.conf.task_routes is None:
        celery_app.conf.task_routes = {}

    celery_app.conf.task_queues = celery_app.conf.task_queues + (
        Queue(
            f"{settings.SERVICE_NAME}_new_organization",
            exchange=Exchange("new_organization", type="fanout"),
            routing_key="new_organization",
            queue_arguments={
                "x-single-active-consumer": True,
            },
        ),
    )
    celery_app.conf.task_routes["spacedf.tasks.new_organization"] = {
        "queue": f"{settings.SERVICE_NAME}_new_organization",
        "routing_key": "new_organization",
    }
