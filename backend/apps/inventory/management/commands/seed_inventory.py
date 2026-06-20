"""Seed default inventory categories (idempotent)."""
from django.core.management.base import BaseCommand

from apps.inventory.models import InventoryCategory

CATEGORIES = [
    {"code": "MEM", "name": "Memory"},
    {"code": "STO", "name": "Storage"},
    {"code": "PER", "name": "Peripherals"},
    {"code": "CBL", "name": "Cables"},
    {"code": "PWR", "name": "Power"},
]


class Command(BaseCommand):
    help = "Create default inventory categories."

    def handle(self, *args, **options):
        for c in CATEGORIES:
            obj, created = InventoryCategory.objects.get_or_create(
                code=c["code"], defaults={"name": c["name"]}
            )
            self.stdout.write(("+ " if created else "= ") + f"category {obj.code}")
        self.stdout.write(self.style.SUCCESS("Inventory seed complete."))
