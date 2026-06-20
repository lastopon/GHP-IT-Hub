"""Seed default asset categories (idempotent)."""
from django.core.management.base import BaseCommand

from apps.assets.models import AssetCategory

CATEGORIES = [
    {"code": "LT", "name": "Laptop"},
    {"code": "DT", "name": "Desktop"},
    {"code": "MON", "name": "Monitor"},
    {"code": "PRN", "name": "Printer"},
    {"code": "NET", "name": "Network Device"},
    {"code": "SRV", "name": "Server"},
]


class Command(BaseCommand):
    help = "Create default asset categories."

    def handle(self, *args, **options):
        for c in CATEGORIES:
            obj, created = AssetCategory.objects.get_or_create(
                code=c["code"], defaults={"name": c["name"]}
            )
            self.stdout.write(("+ " if created else "= ") + f"category {obj.code}")
        self.stdout.write(self.style.SUCCESS("Asset seed complete."))
