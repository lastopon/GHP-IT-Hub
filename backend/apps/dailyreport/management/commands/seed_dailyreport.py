"""Seed a default server-room checklist template (idempotent)."""
from django.core.management.base import BaseCommand

from apps.dailyreport.models import ChecklistItem, ChecklistTemplate

TEMPLATE = {"code": "SRV-DAILY", "name": "Server Room Daily Check"}
ITEMS = [
    {"order": 1, "text": "AC temperature", "response_type": "reading", "unit": "°C"},
    {"order": 2, "text": "UPS status light", "response_type": "bool"},
    {"order": 3, "text": "Internet link OK", "response_type": "bool"},
    {"order": 4, "text": "Server rack tidy / no alarms", "response_type": "bool"},
    {"order": 5, "text": "Notes", "response_type": "text"},
]


class Command(BaseCommand):
    help = "Create a default server-room checklist template with items."

    def handle(self, *args, **options):
        tpl, created = ChecklistTemplate.objects.get_or_create(
            code=TEMPLATE["code"], defaults={"name": TEMPLATE["name"]}
        )
        self.stdout.write(("+ " if created else "= ") + f"template {tpl.code}")
        for it in ITEMS:
            obj, made = ChecklistItem.objects.get_or_create(
                template=tpl,
                text=it["text"],
                defaults={
                    "order": it["order"],
                    "response_type": it["response_type"],
                    "unit": it.get("unit", ""),
                },
            )
            self.stdout.write(("  + " if made else "  = ") + f"item {obj.text}")
        self.stdout.write(self.style.SUCCESS("Daily report seed complete."))
