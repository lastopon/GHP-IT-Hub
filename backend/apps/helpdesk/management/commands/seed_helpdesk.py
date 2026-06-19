"""Seed default ticket categories (idempotent)."""
from django.core.management.base import BaseCommand

from apps.helpdesk.models import TicketCategory

# Categories from cloude.md module 2, with a starter SLA (hours).
CATEGORIES = [
    {"code": "HW", "name": "Hardware", "default_sla_hours": 8},
    {"code": "SW", "name": "Software", "default_sla_hours": 8},
    {"code": "NET", "name": "Network", "default_sla_hours": 4},
    {"code": "OTHER", "name": "Other", "default_sla_hours": 24},
]


class Command(BaseCommand):
    help = "Create default helpdesk ticket categories."

    def handle(self, *args, **options):
        for c in CATEGORIES:
            obj, created = TicketCategory.objects.get_or_create(
                code=c["code"],
                defaults={
                    "name": c["name"],
                    "default_sla_hours": c["default_sla_hours"],
                },
            )
            self.stdout.write(("+ " if created else "= ") + f"category {obj.code}")
        self.stdout.write(self.style.SUCCESS("Helpdesk seed complete."))
