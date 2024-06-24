from common.models.base_model import BaseModel
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Organization(TenantMixin, BaseModel):
    name = models.CharField(max_length=100)


class Domain(DomainMixin, BaseModel):
    pass
