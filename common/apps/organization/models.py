from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from common.apps.organization.constants import OrganizationTemplate
from common.models.base_model import BaseModel


class Organization(TenantMixin, BaseModel):
    name = models.CharField(max_length=100)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(max_length=64, unique=True)
    is_multi_tenant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    template = models.CharField(
        max_length=256, choices=OrganizationTemplate.choices, blank=True, null=True
    )


class Domain(DomainMixin, BaseModel):
    pass
