import logging

from celery import shared_task
from django.conf import settings
from django.db import models, transaction
from django.utils.module_loading import import_string
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger(__name__)


def task(max_retries=3, bind=False, task_acks_late=True, prefetch_count=1, **option):
    def create_shared_task(handler):
        @shared_task(
            max_retries=max_retries,
            bind=True,
            task_acks_late=task_acks_late,
            prefetch_count=prefetch_count,
            **option,
        )
        def inner(self, **kwargs):
            logger.info(f"{option['name']}(kwargs={kwargs})")

            try:
                if bind:
                    handler(self=self, **kwargs)
                else:
                    handler(**kwargs)
            except Exception as ex:
                logger.exception(ex)
                self.retry(countdown=3**self.request.retries)

        return inner

    return create_shared_task


def tenant_shared_task(**option):
    """
    Use as a decorator for the Celery shared_task to handle the model of tenant
    """

    def create_tenant_shared_task(handler):
        @task(**option)
        @transaction.atomic
        def tenant_handle(organization_slug_name, **kwargs):
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
        many_to_many_fields = {}
        for field in Model._meta.get_fields():
            if isinstance(field, models.ForeignKey) and field.name in data:
                key = f"{field.name}_id"
                value = data.pop(field.name, None)
                data[key] = value
            if isinstance(field, models.ManyToManyField) and field.name in data:
                value = data.pop(field.name, None)
                many_to_many_fields[field.name] = value
        try:
            obj = Model.objects.get(id=data["id"])
            for attr, value in data.items():
                setattr(obj, attr, value)
        except Model.DoesNotExist:
            obj = Model(**data)

        for field, value in many_to_many_fields.items():
            getattr(obj, field).set(value)

        obj.save()

    @tenant_shared_task(name=f"spacedf.tasks.delete_{Model._meta.model_name}")
    def delete(pk):
        obj = Model.objects.get(pk=pk)
        obj.delete()

    return update, delete


def send_task(name, message):
    celery_app = import_string(settings.CELERY_APP)
    celery_app.send_task(
        name=f"spacedf.tasks.{name}",
        exchange=name,
        routing_key=f"spacedf.tasks.{name}",
        retry=True,
        retry_policy=dict(
            max_retries=3, interval_start=3, interval_step=1, interval_max=6
        ),
        kwargs=message,
    )
