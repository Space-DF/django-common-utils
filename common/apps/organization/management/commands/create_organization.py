from django.conf import settings
from django.core.management.base import BaseCommand

from common.apps.organization.models import Domain, Organization


class Command(BaseCommand):
    help = "Create a new space"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, help="Organization name")
        parser.add_argument("--slug_name", type=str, help="Organization slug name")
        parser.add_argument(
            "--is_multi_tenant", type=bool, help="True if organization is multi-tenant"
        )

    def handle(self, *args, **kwargs):
        name = kwargs.get("name") or input("Name [test]: ") or "test"
        slug_name = kwargs.get("slug_name") or input("Slug name [test]: ") or "test"
        is_multi_tenant = (
            kwargs.get("is_multi_tenant") or input("Is multi-tenant [False]: ") or False
        )

        organization = Organization(
            schema_name=slug_name,
            name=name,
            slug_name=slug_name,
            is_active=True,
            is_multi_tenant=is_multi_tenant,
        )
        organization.save()
        Domain(
            domain=f"{slug_name}.{settings.DEFAULT_TENANT_HOST}",
            tenant=organization,
            is_primary=True,
        ).save()

        self.stdout.write(
            self.style.SUCCESS(f"Organization {organization.name} created successfully")
        )
