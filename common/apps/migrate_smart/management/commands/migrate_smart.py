import hashlib
import os

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

FINGERPRINT_TABLE = "_migration_fingerprint"


def compute_migration_fingerprint():
    hasher = hashlib.sha256()
    for app_config in apps.get_app_configs():
        migration_dir = os.path.join(app_config.path, "migrations")
        if not os.path.isdir(migration_dir):
            continue
        for filename in sorted(os.listdir(migration_dir)):
            if not filename.endswith(".py") or filename == "__init__.py":
                continue
            filepath = os.path.join(migration_dir, filename)
            if not os.path.isfile(filepath):
                continue
            with open(filepath, "rb") as f:
                hasher.update(f"{app_config.label}/{filename}:".encode())
                hasher.update(f.read())
    return hasher.hexdigest()


def ensure_fingerprint_table():
    connection.set_schema_to_public()
    with connection.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {FINGERPRINT_TABLE} (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def get_stored_fingerprint():
    connection.set_schema_to_public()
    with connection.cursor() as cur:
        cur.execute(f"SELECT value FROM {FINGERPRINT_TABLE} WHERE id = 1")
        row = cur.fetchone()
        return row[0] if row else None


def store_fingerprint(value):
    connection.set_schema_to_public()
    with connection.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {FINGERPRINT_TABLE} (id, value)
            VALUES (1, %s)
            ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value, updated_at = now()
            """,
            [value],
        )


class Command(BaseCommand):
    help = "Run migrations with fingerprint-based skip for unchanged migration files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-tenant",
            action="store_true",
            help="Skip tenant schema migrations entirely",
        )

    def handle(self, *args, **options):
        current = compute_migration_fingerprint()
        ensure_fingerprint_table()
        stored = get_stored_fingerprint()

        self.stdout.write("Running shared schema migrations...")
        call_command("migrate_schemas", interactive=False, verbosity=1, shared=True)

        if options.get("skip_tenant"):
            self.stdout.write("Skipping tenant migrations (--skip-tenant)")
            return

        if stored == current:
            self.stdout.write(
                self.style.SUCCESS(
                    "No migration files changed since last run — skipping tenant migrations"
                )
            )
            return

        self.stdout.write(
            "Migration files changed - running tenant schema migrations..."
        )
        call_command("migrate_schemas", interactive=False, verbosity=1, tenant=True)
        store_fingerprint(current)
        self.stdout.write(
            self.style.SUCCESS("Tenant migrations complete — fingerprint stored")
        )
