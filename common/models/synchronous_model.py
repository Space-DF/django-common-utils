from django.conf import settings
from django.db import connection, models
from django.forms import model_to_dict
from django.utils.module_loading import import_string


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

        celery_app = import_string(settings.CELERY_APP)

        celery_app.send_task(
            name=f"spacedf.tasks.update_{self._meta.model_name}",
            exchange=f"update_{self._meta.model_name}",
            routing_key=f"spacedf.tasks.update_{self._meta.model_name}",
            kwargs={
                "organization_slug_name": connection.get_tenant().slug_name,
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
        celery_app = import_string(settings.CELERY_APP)

        celery_app.send_task(
            name=f"spacedf.tasks.delete_{self._meta.model_name}",
            exchange=f"delete_{self._meta.model_name}",
            routing_key=f"spacedf.tasks.delete_{self._meta.model_name}",
            kwargs={
                "organization_slug_name": connection.get_tenant().slug_name,
                "pk": pk,
            },
        )
