from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.apps.space.models import Space
from common.apps.space_role.constants import SpacePermission
from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SpacePolicy(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    tags = ArrayField(models.CharField(max_length=256))
    permissions = ArrayField(
        models.CharField(max_length=256, choices=SpacePermission.choices)
    )


class SpaceRole(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    space = models.ForeignKey(
        Space, related_name="space_role", on_delete=models.CASCADE
    )
    policies = models.ManyToManyField(SpacePolicy)


class SpaceRoleUser(BaseModel, SynchronousTenantModel):
    space_role = models.ForeignKey(
        SpaceRole,
        related_name="space_role_user",
        on_delete=models.CASCADE,
    )
    organization_user = models.ForeignKey(
        User, related_name="space_role_user", on_delete=models.CASCADE, null=True, blank=True
    )
    is_default = models.BooleanField(default=False)


class SpaceInvitation(BaseModel, SynchronousTenantModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
    ]

    space_role_user = models.OneToOneField(SpaceRoleUser, on_delete=models.CASCADE)
    email = models.EmailField()
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='space_invitations'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=255, unique=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def is_token_expired(self):
        return timezone.now() > self.created_at + timedelta(days=7)
