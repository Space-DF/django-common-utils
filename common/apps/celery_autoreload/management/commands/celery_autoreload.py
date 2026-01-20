import shlex
import subprocess  # nosec B404

from django.core.management.base import BaseCommand
from django.utils import autoreload


def create_celery_task(app, concurrency):
    def restart_celery():
        cmd = "pkill celery"
        subprocess.call(shlex.split(cmd))  # nosec B603
        cmd = (
            f'celery {f"-A {app}" if app is not None else ""}'
            f' worker -l info {f"-c {concurrency}" if concurrency is not None else ""} '
        )
        subprocess.call(shlex.split(cmd))  # nosec B603

    return restart_celery


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            help="The service name",
            type=str,
        )
        parser.add_argument(
            "--concurrency",
            help="The concurrency",
            type=int,
        )

    def handle(self, *args, **options):
        autoreload.run_with_reloader(
            create_celery_task(
                options.get("app", None), options.get("concurrency", None)
            )
        )
