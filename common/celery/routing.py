from django.conf import settings
from django.utils.module_loading import import_string
from kombu import Exchange, Queue


def setup_synchronous_model_task_routing():
    celery_app = import_string(settings.CELERY_APP)

    # Topic-based routing for model events (spaces, etc.)
    app_events_exchange = Exchange("app.events", type="topic")
    
    if hasattr(settings, "CLONE_MODELS"):
        for model_name in settings.CLONE_MODELS:
            # Configure task routes with topic-based routing keys
            update_task_name = f"spacedf.tasks.update_{model_name}"
            celery_app.conf.task_routes[update_task_name] = {
                "queue": f"{settings.SERVICE_NAME}-service",
                "exchange": "app.events",
                "routing_key": f"*.{model_name}.updated",
            }
            delete_task_name = f"spacedf.tasks.delete_{model_name}"
            celery_app.conf.task_routes[delete_task_name] = {
                "queue": f"{settings.SERVICE_NAME}-service",
                "exchange": "app.events",
                "routing_key": f"*.{model_name}.deleted",
            }


def setup_organization_task_routing():
    celery_app = import_string(settings.CELERY_APP)
    
    # print(f"Setting up topic-based routing for {settings.SERVICE_NAME}")

    # Topic-based routing for organization events
    app_events_exchange = Exchange("app.events", type="topic")
    
    # Create service queue with topic-based bindings
    service_queue = Queue(
        f"{settings.SERVICE_NAME}-service",
        exchange=app_events_exchange,
        routing_key="*.*.*",  # Bind to all tenant events
        queue_arguments={"x-single-active-consumer": True},
    )
    
    # Set default queue and exchange to use topic-based approach
    celery_app.conf.task_default_queue = f"{settings.SERVICE_NAME}-service"
    celery_app.conf.task_default_exchange = "app.events"
    celery_app.conf.task_default_routing_key = "*.*.*"
    
    # Completely replace task queues with topic-based queue
    celery_app.conf.task_queues = (service_queue,)
    
    # Completely replace task routes with topic-based routing
    celery_app.conf.task_routes = {
        "spacedf.tasks.new_organization": {
            "queue": f"{settings.SERVICE_NAME}-service",
            "exchange": "app.events",
            "routing_key": "*.org.created",
        },
        "spacedf.tasks.delete_organization": {
            "queue": f"{settings.SERVICE_NAME}-service", 
            "exchange": "app.events",
            "routing_key": "*.org.deleted",
        },
        "spacedf.tasks.update_space": {
            "queue": f"{settings.SERVICE_NAME}-service",
            "exchange": "app.events",
            "routing_key": "*.space.updated",
        },
        "spacedf.tasks.delete_space": {
            "queue": f"{settings.SERVICE_NAME}-service",
            "exchange": "app.events",
            "routing_key": "*.space.deleted",
        }
    }
    
    # print(f"Topic-based routing setup complete for {settings.SERVICE_NAME}")
    # print(f"Default queue: {celery_app.conf.task_default_queue}")
    # print(f"Task queues: {len(celery_app.conf.task_queues)}")
