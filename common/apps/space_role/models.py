from common.apps.organization_user.models import OrganizationUser
from common.apps.space.models import Space
from common.apps.space_role.constants import SpacePermission
from common.models.base_model import BaseModel
from django.contrib.postgres.fields import ArrayField
from django.db import models


class SpacePolicy(BaseModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    tags = ArrayField(models.CharField(max_length=256))
    permissions = ArrayField(
        models.CharField(max_length=256, choices=SpacePermission.choices)
    )


class SpaceRole(BaseModel):
    name = models.CharField(max_length=256)
    space = models.ForeignKey(
        Space, related_name="space_role", on_delete=models.CASCADE
    )
    policies = models.ManyToManyField(SpacePolicy)


class SpaceRoleUser(BaseModel):
    space_role = models.ForeignKey(
        SpaceRole,
        related_name="space_role_user",
        on_delete=models.CASCADE,
    )
    organization_user = models.ForeignKey(
        OrganizationUser, related_name="space_role_user", on_delete=models.CASCADE
    )
