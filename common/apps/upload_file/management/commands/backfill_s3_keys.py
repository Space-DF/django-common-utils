import logging
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from common.apps.upload_file.service import _find_s3_key, _get_s3_client

logger = logging.getLogger(__name__)

BUCKET = settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME")
s3 = _get_s3_client()


def is_old_key(value):
    return value and not value.startswith(("public/", "private/"))


def copy_s3_object(old_key, new_key):
    found = _find_s3_key(BUCKET, old_key)
    if not found:
        logger.warning(f"Source not found, skipping: {old_key}")
        return None

    ext = os.path.splitext(found)[1]
    if ext:
        new_key = f"{new_key}{ext}"

    s3.copy_object(
        Bucket=BUCKET,
        Key=new_key,
        CopySource={"Bucket": BUCKET, "Key": found},
    )
    logger.info(f"Copied: {found} → {new_key}")
    return new_key


def backfill_tenant_models(org_slug):
    schema = org_slug

    if apps.is_installed("common.apps.organization_user"):
        model = apps.get_model("organization_user", "OrganizationUser")
        for obj in model.objects.exclude(avatar="").exclude(avatar__isnull=True):
            if not is_old_key(obj.avatar):
                continue
            old_key = f"uploads/{obj.avatar}"
            new_key = f"private/organizations/{schema}/users/{obj.id}/{obj.avatar}"
            result = copy_s3_object(old_key, new_key)
            if result:
                model.objects.filter(pk=obj.pk).update(avatar=result)

    if apps.is_installed("common.apps.space"):
        model = apps.get_model("space", "Space")
        for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
            if not is_old_key(obj.logo):
                continue
            old_key = f"uploads/{obj.logo}"
            new_key = f"public/organizations/{schema}/{obj.logo}"
            result = copy_s3_object(old_key, new_key)
            if result:
                model.objects.filter(pk=obj.pk).update(logo=result)

    if apps.is_installed("apps.building"):
        for model_name in ["Building", "Floor", "Area"]:
            model = apps.get_model("building", model_name)
            for obj in model.objects.exclude(scene_asset="").exclude(
                scene_asset__isnull=True
            ):
                if not is_old_key(obj.scene_asset):
                    continue
                old_key = f"uploads/{obj.scene_asset}"
                new_key = f"private/organizations/{schema}/{obj.scene_asset}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(scene_asset=result)

    if apps.is_installed("apps.facility"):
        model = apps.get_model("facility", "Facility")
        for obj in model.objects.exclude(scene_asset="").exclude(
            scene_asset__isnull=True
        ):
            if not is_old_key(obj.scene_asset):
                continue
            old_key = f"uploads/{obj.scene_asset}"
            new_key = f"private/organizations/{schema}/{obj.scene_asset}"
            result = copy_s3_object(old_key, new_key)
            if result:
                model.objects.filter(pk=obj.pk).update(scene_asset=result)


def backfill_console_models():
    if apps.is_installed("apps.authentication"):
        try:
            model = apps.get_model("authentication", "RootUser")
            for obj in model.objects.exclude(avatar="").exclude(avatar__isnull=True):
                if not is_old_key(obj.avatar):
                    continue
                old_key = f"uploads/{obj.avatar}"
                new_key = f"private/root_users/{obj.id}/{obj.avatar}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(avatar=result)
        except LookupError:
            pass

    if apps.is_installed("apps.organization"):
        try:
            model = apps.get_model("organization", "Organization")
            for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
                if not is_old_key(obj.logo):
                    continue
                old_key = f"uploads/{obj.logo}"
                new_key = f"public/organizations/{obj.slug_name}/{obj.logo}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(logo=result)
        except LookupError:
            pass

    if apps.is_installed("apps.organization_setting"):
        try:
            model = apps.get_model("organization_setting", "OrganizationTheme")
            for obj in model.objects.exclude(logo="").exclude(logo__isnull=True):
                if not is_old_key(obj.logo):
                    continue
                org_slug = obj.setting.organization.slug_name
                old_key = f"uploads/{obj.logo}"
                new_key = f"public/organizations/{org_slug}/{obj.logo}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(logo=result)

            for obj in model.objects.exclude(favicon="").exclude(favicon__isnull=True):
                if not is_old_key(obj.favicon):
                    continue
                org_slug = obj.setting.organization.slug_name
                old_key = f"uploads/{obj.favicon}"
                new_key = f"public/organizations/{org_slug}/{obj.favicon}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(favicon=result)
        except LookupError:
            pass

    if apps.is_installed("apps.custom_page"):
        try:
            model = apps.get_model("custom_page", "CustomPage")
            for obj in model.objects.exclude(background_image="").exclude(
                background_image__isnull=True
            ):
                if not is_old_key(obj.background_image):
                    continue
                org_slug = obj.organization.slug_name
                old_key = f"uploads/{obj.background_image}"
                new_key = f"public/organizations/{org_slug}/{obj.background_image}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(background_image=result)
        except LookupError:
            pass

    if apps.is_installed("apps.custom_email"):
        try:
            model = apps.get_model("custom_email", "OrganizationEmail")
            for obj in model.objects.exclude(header_image="").exclude(
                header_image__isnull=True
            ):
                if not is_old_key(obj.header_image):
                    continue
                org_slug = obj.organization.slug_name
                old_key = f"uploads/{obj.header_image}"
                new_key = f"public/organizations/{org_slug}/{obj.header_image}"
                result = copy_s3_object(old_key, new_key)
                if result:
                    model.objects.filter(pk=obj.pk).update(header_image=result)
        except LookupError:
            pass


class Command(BaseCommand):
    help = "Backfill S3 keys from old uploads/{uuid} format to new structured keys"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without moving files or updating DB",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write("DRY RUN — no changes will be made")

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
                        self._dry_run_tenant(tenant.slug_name)
                    else:
                        backfill_tenant_models(tenant.slug_name)

            connection.set_schema_to_public()

        self.stdout.write("Processing console (public) schema...")
        if dry_run:
            self._dry_run_console()
        else:
            backfill_console_models()

        self.stdout.write(self.style.SUCCESS("Backfill complete."))

    def _dry_run_tenant(self, schema):
        if apps.is_installed("common.apps.organization_user"):
            model = apps.get_model("organization_user", "OrganizationUser")
            count = (
                model.objects.filter(avatar__isnull=False)
                .exclude(avatar="")
                .exclude(avatar__startswith="private/")
                .exclude(avatar__startswith="public/")
                .count()
            )
            if count:
                self.stdout.write(f"    OrganizationUser.avatar: {count} records")

        if apps.is_installed("common.apps.space"):
            model = apps.get_model("space", "Space")
            count = (
                model.objects.filter(logo__isnull=False)
                .exclude(logo="")
                .exclude(logo__startswith="public/")
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
                    .exclude(scene_asset__startswith="private/")
                    .exclude(scene_asset__startswith="public/")
                    .count()
                )
                if count:
                    self.stdout.write(f"    {model_name}.scene_asset: {count} records")

        if apps.is_installed("apps.facility"):
            model = apps.get_model("facility", "Facility")
            count = (
                model.objects.filter(scene_asset__isnull=False)
                .exclude(scene_asset="")
                .exclude(scene_asset__startswith="private/")
                .exclude(scene_asset__startswith="public/")
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
                    .exclude(avatar__startswith="private/")
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
                    .exclude(logo__startswith="public/")
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
                    .exclude(logo__startswith="public/")
                    .count()
                )
                if count:
                    self.stdout.write(f"    OrganizationTheme.logo: {count} records")

                count = (
                    model.objects.filter(favicon__isnull=False)
                    .exclude(favicon="")
                    .exclude(favicon__startswith="public/")
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
                    .exclude(background_image__startswith="public/")
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
                    .exclude(header_image__startswith="public/")
                    .count()
                )
                if count:
                    self.stdout.write(
                        f"    OrganizationEmail.header_image: {count} records"
                    )
            except LookupError:
                pass
