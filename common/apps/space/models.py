from django.core.validators import MinValueValidator
from django.db import models

from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel


class Space(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    total_devices = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    description = models.TextField(null=True, blank=True)
    created_by = models.UUIDField()

    class Meta:
        indexes = [
            models.Index(fields=["slug_name"], name="slug_name_idx"),
        ]
