from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel
from django.db import models


class Space(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(max_length=64, unique=True)
    is_multi_tenant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug_name"], name="slug_name_idx"),
        ]
