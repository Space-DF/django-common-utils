import logging

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

logger = logging.getLogger(__name__)


def is_new_key(value):
    return value and value.startswith(("public/", "private/"))


def extract_old_value(new_key):
    return new_key.split("/")[-1]


def revert_tenant_models():
    if apps.is_installed("common.apps.organization_user"):
        model = apps.get_model("organization_user", "OrganizationUser")
        for obj in model.objects.exclude(avatar="").exclude(avatar__isnull=True):
            if not is_new_key(obj.avatar):
                continue
            old_value = extract_old_value(obj.avatar)
            model.objects.filter(pk=obj.pk).update(avatar=old_value)
            logger.info(f"Reverted OrganizationUser avatar: {obj.avatar} → {old_value}")

    if apps.is_installed("common.apps.space"):
        model = apps.get_model("space", "Space")
        for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
            if not is_new_key(obj.logo):
                continue
            old_value = extract_old_value(obj.logo)
            model.objects.filter(pk=obj.pk).update(logo=old_value)
            logger.info(f"Reverted Space logo: {obj.logo} → {old_value}")

    if apps.is_installed("apps.building"):
        for model_name in ["Building", "Floor", "Area"]:
            model = apps.get_model("building", model_name)
            for obj in model.objects.exclude(scene_asset="").exclude(
                scene_asset__isnull=True
            ):
                if not is_new_key(obj.scene_asset):
                    continue
                old_value = extract_old_value(obj.scene_asset)
                model.objects.filter(pk=obj.pk).update(scene_asset=old_value)
                logger.info(
                    f"Reverted {model_name} scene_asset: {obj.scene_asset} → {old_value}"
                )

    if apps.is_installed("apps.facility"):
        model = apps.get_model("facility", "Facility")
        for obj in model.objects.exclude(scene_asset="").exclude(
            scene_asset__isnull=True
        ):
            if not is_new_key(obj.scene_asset):
                continue
            old_value = extract_old_value(obj.scene_asset)
            model.objects.filter(pk=obj.pk).update(scene_asset=old_value)
            logger.info(
                f"Reverted Facility scene_asset: {obj.scene_asset} → {old_value}"
            )


def revert_console_models():
    if apps.is_installed("apps.authentication"):
        try:
            model = apps.get_model("authentication", "RootUser")
            for obj in model.objects.exclude(avatar="").exclude(avatar__isnull=True):
                if not is_new_key(obj.avatar):
                    continue
                old_value = extract_old_value(obj.avatar)
                model.objects.filter(pk=obj.pk).update(avatar=old_value)
                logger.info(f"Reverted RootUser avatar: {obj.avatar} → {old_value}")
        except LookupError:
            pass

    if apps.is_installed("apps.organization"):
        try:
            model = apps.get_model("organization", "Organization")
            for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
                if not is_new_key(obj.logo):
                    continue
                old_value = extract_old_value(obj.logo)
                model.objects.filter(pk=obj.pk).update(logo=old_value)
                logger.info(f"Reverted Organization logo: {obj.logo} → {old_value}")
        except LookupError:
            pass

    if apps.is_installed("apps.organization_setting"):
        try:
            model = apps.get_model("organization_setting", "OrganizationTheme")
            for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
                if not is_new_key(obj.logo):
                    continue
                old_value = extract_old_value(obj.logo)
                model.objects.filter(pk=obj.pk).update(logo=old_value)
                logger.info(
                    f"Reverted OrganizationTheme logo: {obj.logo} → {old_value}"
                )

            for obj in model.objects.exclude(favicon="").exclude(favicon__isnull=True):
                if not is_new_key(obj.favicon):
                    continue
                old_value = extract_old_value(obj.favicon)
                model.objects.filter(pk=obj.pk).update(favicon=old_value)
                logger.info(
                    f"Reverted OrganizationTheme favicon: {obj.favicon} → {old_value}"
                )
        except LookupError:
            pass

    if apps.is_installed("apps.custom_page"):
        try:
            model = apps.get_model("custom_page", "CustomPage")
            for obj in model.objects.exclude(background_image="").exclude(
                background_image__isnull=True
            ):
                if not is_new_key(obj.background_image):
                    continue
                old_value = extract_old_value(obj.background_image)
                model.objects.filter(pk=obj.pk).update(background_image=old_value)
                logger.info(
                    f"Reverted CustomPage background_image: {obj.background_image} → {old_value}"
                )
        except LookupError:
            pass

    if apps.is_installed("apps.custom_email"):
        try:
            model = apps.get_model("custom_email", "OrganizationEmail")
            for obj in model.objects.exclude(header_image="").exclude(
                header_image__isnull=True
            ):
                if not is_new_key(obj.header_image):
                    continue
                old_value = extract_old_value(obj.header_image)
                model.objects.filter(pk=obj.pk).update(header_image=old_value)
                logger.info(
                    f"Reverted OrganizationEmail header_image: {obj.header_image} → {old_value}"
                )
        except LookupError:
            pass


class Command(BaseCommand):
    help = "Revert S3 keys from new structured format back to old bare UUID format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be reverted without changing DB",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write("DRY RUN — no changes will be made")

        from django.conf import settings

        if hasattr(settings, "TENANT_MODEL"):
            from django_tenants.utils import get_tenant_model

            TenantModel = get_tenant_model()
            tenants = TenantModel.objects.exclude(schema_name="public")

            if tenants.exists():
                self.stdout.write("Processing tenant schemas...")
                for tenant in tenants:
                    connection.set_tenant(tenant)
                    self.stdout.write(f"  Schema: {tenant.slug_name}")
                    if dry_run:
                        self._dry_run_tenant()
                    else:
                        revert_tenant_models()

            connection.set_schema_to_public()

        self.stdout.write("Processing console (public) schema...")
        if dry_run:
            self._dry_run_console()
        else:
            revert_console_models()

        self.stdout.write(self.style.SUCCESS("Revert complete."))

    def _dry_run_tenant(self):
        if apps.is_installed("common.apps.organization_user"):
            model = apps.get_model("organization_user", "OrganizationUser")
            count = (
                model.objects.filter(avatar__isnull=False)
                .exclude(avatar="")
                .filter(
                    Q(avatar__startswith="private/") | Q(avatar__startswith="public/")
                )
                .count()
            )
            if count:
                self.stdout.write(f"    OrganizationUser.avatar: {count} records")

        if apps.is_installed("common.apps.space"):
            model = apps.get_model("space", "Space")
            count = (
                model.objects.filter(logo__isnull=False)
                .exclude(logo="")
                .filter(Q(logo__startswith="private/") | Q(logo__startswith="public/"))
                .count()
            )
            if count:
                self.stdout.write(f"    Space.logo: {count} records")

        if apps.is_installed("apps.building"):
            for model_name in ["Building", "Floor", "Area"]:
                model = apps.get_model("building", model_name)
                count = (
                    model.objects.filter(scene_asset__isnull=False)
                    .exclude(scene_asset="")
                    .filter(
                        Q(scene_asset__startswith="private/")
                        | Q(scene_asset__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(f"    {model_name}.scene_asset: {count} records")

        if apps.is_installed("apps.facility"):
            model = apps.get_model("facility", "Facility")
            count = (
                model.objects.filter(scene_asset__isnull=False)
                .exclude(scene_asset="")
                .filter(
                    Q(scene_asset__startswith="private/")
                    | Q(scene_asset__startswith="public/")
                )
                .count()
            )
            if count:
                self.stdout.write(f"    Facility.scene_asset: {count} records")

    def _dry_run_console(self):
        if apps.is_installed("apps.authentication"):
            try:
                model = apps.get_model("authentication", "RootUser")
                count = (
                    model.objects.filter(avatar__isnull=False)
                    .exclude(avatar="")
                    .filter(
                        Q(avatar__startswith="private/")
                        | Q(avatar__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(f"    RootUser.avatar: {count} records")
            except LookupError:
                pass

        if apps.is_installed("apps.organization"):
            try:
                model = apps.get_model("organization", "Organization")
                count = (
                    model.objects.filter(logo__isnull=False)
                    .exclude(logo="")
                    .filter(
                        Q(logo__startswith="private/") | Q(logo__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(f"    Organization.logo: {count} records")
            except LookupError:
                pass

        if apps.is_installed("apps.organization_setting"):
            try:
                model = apps.get_model("organization_setting", "OrganizationTheme")
                count = (
                    model.objects.filter(logo__isnull=False)
                    .exclude(logo="")
                    .filter(
                        Q(logo__startswith="private/") | Q(logo__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(f"    OrganizationTheme.logo: {count} records")

                count = (
                    model.objects.filter(favicon__isnull=False)
                    .exclude(favicon="")
                    .filter(
                        Q(favicon__startswith="private/")
                        | Q(favicon__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(f"    OrganizationTheme.favicon: {count} records")
            except LookupError:
                pass

        if apps.is_installed("apps.custom_page"):
            try:
                model = apps.get_model("custom_page", "CustomPage")
                count = (
                    model.objects.filter(background_image__isnull=False)
                    .exclude(background_image="")
                    .filter(
                        Q(background_image__startswith="private/")
                        | Q(background_image__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(
                        f"    CustomPage.background_image: {count} records"
                    )
            except LookupError:
                pass

        if apps.is_installed("apps.custom_email"):
            try:
                model = apps.get_model("custom_email", "OrganizationEmail")
                count = (
                    model.objects.filter(header_image__isnull=False)
                    .exclude(header_image="")
                    .filter(
                        Q(header_image__startswith="private/")
                        | Q(header_image__startswith="public/")
                    )
                    .count()
                )
                if count:
                    self.stdout.write(
                        f"    OrganizationEmail.header_image: {count} records"
                    )
            except LookupError:
                pass
