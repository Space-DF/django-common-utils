from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel

User = get_user_model()


class Space(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    total_devices = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_by = models.ForeignKey(
        User,
        related_name="created_space",
        on_delete=models.SET_NULL,
        default=None,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["slug_name"], name="slug_name_idx"),
        ]
