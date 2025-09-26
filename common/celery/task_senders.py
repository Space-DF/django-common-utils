from django.conf import settings
from django.utils.module_loading import import_string


def send_task(name, message, **kwargs):
    celery_app = import_string(settings.CELERY_APP)
    
    # Extract tenant information from message if available
    tenant_slug = None
    if isinstance(message, dict):
        tenant_slug = message.get('tenant_slug') or message.get('slug_name')
        # Ensure organization_slug_name is set for tenant tasks
        if tenant_slug and 'organization_slug_name' not in message:
            message['organization_slug_name'] = tenant_slug
    
    # Determine routing key based on task name and tenant
    if tenant_slug:
        # Topic-based routing with tenant
        if name in ['new_organization', 'delete_organization']:
            action = 'created' if 'new' in name else 'deleted'
            routing_key = f"{tenant_slug}.org.{action}"
        elif 'space' in name:
            action = 'updated' if 'update' in name else 'deleted'
            routing_key = f"{tenant_slug}.space.{action}"
        else:
            # Generic tenant-based routing
            routing_key = f"{tenant_slug}.{name}"
        
        exchange = "app.events"
    
    # For topic-based routing, use the app.events exchange directly
    if tenant_slug and exchange == "app.events":
        return celery_app.send_task(
            name=f"spacedf.tasks.{name}",
            exchange="app.events",
            routing_key=routing_key,
            retry=True,
            retry_policy=dict(
                max_retries=3, interval_start=3, interval_step=1, interval_max=6
            ),
            kwargs=message,
            **kwargs,
        )
