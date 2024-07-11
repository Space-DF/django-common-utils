from common.apps.organization_role.constants import OrganizationPermission
from common.apps.organization_user.models import OrganizationUser
from common.models.base_model import BaseModel
from django.contrib.postgres.fields import ArrayField
from django.db import models


class OrganizationPolicy(BaseModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    tags = ArrayField(models.CharField(max_length=256))
    permissions = ArrayField(
        models.CharField(max_length=256, choices=OrganizationPermission.choices)
    )


class OrganizationRole(BaseModel):
    name = models.CharField(max_length=256)
    policies = models.ManyToManyField(OrganizationPolicy)


class OrganizationRoleUser(BaseModel):
    organization_role = models.ForeignKey(
        OrganizationRole,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
    organization_user = models.ForeignKey(
        OrganizationUser,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
