import logging

from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string

from common.apps.organization.models import Domain, Organization
from common.celery.tasks import task

logger = logging.getLogger(__name__)


def get_new_organization_handler():
    handler_path = getattr(settings, "NEW_ORGANIZATION_HANDLER", None)
    if handler_path is not None:
        return import_string(handler_path)
    return None


@task(name="spacedf.tasks.new_organization", max_retries=3)
@transaction.atomic
def create_organization(id, name, slug_name, is_active, owner, created_at, updated_at):
    logger.info(f"create_organization: owner_email={owner.get('email')}, org-slug={slug_name}")

    organization = Organization(
        schema_name=slug_name,
        id=id,
        name=name,
        slug_name=slug_name,
        is_active=is_active,
        created_at=created_at,
        updated_at=updated_at,
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


@task(name="spacedf.tasks.delete_organization", max_retries=3)
@transaction.atomic
def delete_organization(slug_name):
    logger.info(f"delete_organization({slug_name})")
    organization = Organization.objects.get(schema_name=slug_name)
    organization.delete(force_drop=True)
