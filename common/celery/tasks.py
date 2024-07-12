import logging

from celery import shared_task
from django.db import transaction
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)


def tenant_shared_task(**option):
    """
    Use as a decorator for the Celery shared_task to handle the model of tenant
    """

    def create_tenant_shared_task(handler):
        @shared_task(**option)
        @transaction.atomic()
        def tenant_handle(organization_slug_name, **kwargs):
            logger.info(
                f"{handler.__name__}(organization_slug_name={organization_slug_name}, kwargs={kwargs})"
            )

            organization = get_tenant_model().objects.get(
                schema_name=organization_slug_name
            )
            with tenant_context(organization):
                return handler(**kwargs)

        return tenant_handle

    return create_tenant_shared_task


def create_tenant_model_shared_tasks(Model):
    """
    This function create the Celery shared_task to listen the update and delete event
    """

    @tenant_shared_task(name=f"spacedf.tasks.update_{Model._meta.model_name}")
    def update(data):
        try:
            obj = Model.objects.get(id=data["id"])
            for attr, value in data.items():
                setattr(obj, attr, value)
        except Model.DoesNotExist:
            obj = Model(**data)

        obj.save()

    @tenant_shared_task(name=f"spacedf.tasks.delete_{Model._meta.model_name}")
    def delete(pk):
        obj = Model.objects.get(pk=pk)
        obj.delete()

    return update, delete
