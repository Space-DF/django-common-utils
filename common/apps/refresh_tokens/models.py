from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models.base_model import BaseModel


class RefreshTokenFamilyStatus(models.TextChoices):
    Active = "Active", _("Active")
    Inactive = "Inactive", _("Inactive")


class RefreshTokenStatus(models.TextChoices):
    New = "New", _("New")
    Used = "Used", _("Used")


class RefreshTokenFamily(BaseModel):
    status = models.CharField(
        max_length=10,
        choices=RefreshTokenFamilyStatus.choices,
        default=RefreshTokenFamilyStatus.Active,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class RefreshToken(BaseModel):
    jti = models.CharField(max_length=32, choices=RefreshTokenStatus.choices)
    status = models.CharField(
        max_length=10,
        choices=RefreshTokenStatus.choices,
        default=RefreshTokenStatus.New,
    )
    family = models.ForeignKey(RefreshTokenFamily, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, default=None
    )
