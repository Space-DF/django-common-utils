import logging

from celery import shared_task
from common.apps.organization.models import Domain, Organization
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(name="spacedf.tasks.new_organization")
@transaction.atomic()
def create_organization_service(id, name, slug_name, is_multi_tenant, is_active):
    organization = Organization(
        schema_name=slug_name,
        id=id,
        name=name,
        slug_name=slug_name,
        is_multi_tenant=is_multi_tenant,
        is_active=is_active,
    )
    organization.save()
    Domain(
        domain=f"{slug_name}.{settings.DEFAULT_TENANT_HOST}",
        tenant=organization,
        is_primary=True,
    ).save()
