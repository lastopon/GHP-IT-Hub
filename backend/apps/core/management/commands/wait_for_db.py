"""Block until the database accepts connections (used by docker entrypoint)."""
import time

from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Wait for the default database to become available."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=60)
        parser.add_argument("--interval", type=float, default=1.0)

    def handle(self, *args, **options):
        timeout = options["timeout"]
        interval = options["interval"]
        deadline = time.monotonic() + timeout

        self.stdout.write("Waiting for database...")
        while True:
            try:
                connections["default"].cursor()
            except OperationalError:
                if time.monotonic() >= deadline:
                    self.stderr.write(
                        self.style.ERROR(f"Database not available after {timeout}s")
                    )
                    raise SystemExit(1)
                time.sleep(interval)
            else:
                self.stdout.write(self.style.SUCCESS("Database is available."))
                break
