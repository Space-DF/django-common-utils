from django.db import models

from common.apps.organization_user.models import OrganizationUser
from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel


class Space(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        OrganizationUser,
        related_name="created_space",
        on_delete=models.SET_NULL,
        default=None,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["slug_name"], name="slug_name_idx"),
        ]
