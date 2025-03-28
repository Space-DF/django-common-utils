from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

from common.apps.space.models import Space


class Command(BaseCommand):
    help = "Create a new space"

    def add_arguments(self, parser):
        parser.add_argument("--organization", type=str, help="Organization slug")
        parser.add_argument("--name", type=str, help="Space name")
        parser.add_argument("--slug_name", type=str, help="Space slug name")
        parser.add_argument("--created_by", type=str, help="Space creator UUID")

    def handle(self, *args, **kwargs):
        organization = (
            kwargs.get("organization") or input("Organization slug [test]: ") or "test"
        )
        name = kwargs.get("name") or input("Name [test]: ") or "test"
        slug_name = kwargs.get("slug_name") or input("Slug name [test]: ") or "test"
        created_by = (
            kwargs.get("created_by")
            or input("Creator UUID [05931ac6-d2c4-4fed-818f-13a0ee506e7e]: ")
            or "05931ac6-d2c4-4fed-818f-13a0ee506e7e"
        )

        with schema_context(organization):
            space = Space.objects.create(
                name=name, logo="", slug_name=slug_name, created_by=created_by
            )

        self.stdout.write(
            self.style.SUCCESS(f"Space {space.name} created successfully")
        )
