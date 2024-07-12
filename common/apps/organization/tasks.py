import logging

from celery import shared_task
from common.apps.organization.models import Domain, Organization
from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


def get_new_organization_handler():
    handler_path = getattr(settings, "NEW_ORGANIZATION_HANDLER", None)
    if handler_path is not None:
        return import_string(handler_path)
    return None


@shared_task(name="spacedf.tasks.new_organization")
@transaction.atomic()
def create_organization(id, name, slug_name, is_active, owner):
    logger.info(f"create_organization({id}, {name}, {slug_name}, {is_active}, {owner})")

    organization = Organization(
        schema_name=slug_name,
        id=id,
        name=name,
        slug_name=slug_name,
        is_active=is_active,
    )
    organization.save()
    Domain(
        domain=f"{slug_name}.{settings.DEFAULT_TENANT_HOST}",
        tenant=organization,
        is_primary=True,
    ).save()

    NewOrganizationHandler = get_new_organization_handler()

    if NewOrganizationHandler is not None:
        NewOrganizationHandler(organization, owner).handle()
