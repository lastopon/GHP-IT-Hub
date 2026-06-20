"""Seed a sample project with a default 3-column board (idempotent)."""
from django.core.management.base import BaseCommand

from apps.projects.models import BoardColumn, Project

PROJECT = {"code": "NET-UPGRADE", "name": "Network Upgrade 2026"}
COLUMNS = [
    {"order": 0, "name": "To Do"},
    {"order": 1, "name": "In Progress"},
    {"order": 2, "name": "Done"},
]


class Command(BaseCommand):
    help = "Create a sample project with a To Do / In Progress / Done board."

    def handle(self, *args, **options):
        project, created = Project.objects.get_or_create(
            code=PROJECT["code"], defaults={"name": PROJECT["name"]}
        )
        self.stdout.write(("+ " if created else "= ") + f"project {project.code}")
        for col in COLUMNS:
            obj, made = BoardColumn.objects.get_or_create(
                project=project,
                name=col["name"],
                defaults={"order": col["order"]},
            )
            self.stdout.write(("  + " if made else "  = ") + f"column {obj.name}")
        self.stdout.write(self.style.SUCCESS("Projects seed complete."))
