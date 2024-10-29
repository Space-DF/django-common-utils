from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.apps.organization_role.constants import OrganizationPermission
from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel

User = get_user_model()


class OrganizationPolicy(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    tags = ArrayField(models.CharField(max_length=256))
    permissions = ArrayField(
        models.CharField(max_length=256, choices=OrganizationPermission.choices)
    )


class OrganizationRole(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    policies = models.ManyToManyField(OrganizationPolicy)


class OrganizationRoleUser(BaseModel, SynchronousTenantModel):
    organization_role = models.ForeignKey(
        OrganizationRole,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
    organization_user = models.ForeignKey(
        User,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
