from django.conf import settings
from django.db import connection, models

from common.celery.task_senders import send_task
from common.utils.model_to_dict import model_to_dict


class SynchronousTenantModel(models.Model):
    """
    The abstract model is able to synchronous with another service via Celery
    """

    pass

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)

        if (
            hasattr(settings, "SYNCHRONOUS_MODEL")
            and self._meta.model_name in settings.SYNCHRONOUS_MODEL
        ):
            self.send_synchronous_updating_message()

        return result

    def send_synchronous_updating_message(self):
        if hasattr(self, "synchronous_fields"):
            synchronous_fields = self.synchronous_fields
        else:
            synchronous_fields = [field.name for field in self._meta.get_fields()]
        
        tenant_slug = connection.get_tenant().slug_name
        send_task(
            name=f"update_{self._meta.model_name}",
            message={
                "organization_slug_name": tenant_slug,
                "tenant_slug": tenant_slug,  # Add tenant_slug for topic-based routing
                "data": {
                    key: value
                    for (key, value) in model_to_dict(self).items()
                    if key in synchronous_fields
                },
            },
        )

    def delete(self, *args, **kwargs):
        pk = self.pk
        result = super().delete(*args, **kwargs)

        if (
            hasattr(settings, "SYNCHRONOUS_MODEL")
            and self._meta.model_name in settings.SYNCHRONOUS_MODEL
        ):
            self.send_synchronous_delete_message(pk)

        return result

    def send_synchronous_delete_message(self, pk):
        tenant_slug = connection.get_tenant().slug_name
        send_task(
            name=f"delete_{self._meta.model_name}",
            message={
                "organization_slug_name": tenant_slug,
                "tenant_slug": tenant_slug,  # Add tenant_slug for topic-based routing
                "pk": pk,
            },
        )
