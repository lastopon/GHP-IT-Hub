"""Seed demo departments and one user per RBAC role (idempotent)."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.authentication.models import Department

User = get_user_model()

DEPARTMENTS = [
    {"code": "IT", "name": "Information Technology"},
    {"code": "HR", "name": "Human Resources"},
    {"code": "FIN", "name": "Finance"},
]

USERS = [
    {
        "email": "admin@ghp.local",
        "password": "Admin@1234",
        "first_name": "Super",
        "last_name": "Admin",
        "role": User.Role.ADMIN,
        "dept": "IT",
        "superuser": True,
    },
    {
        "email": "staff@ghp.local",
        "password": "Staff@1234",
        "first_name": "IT",
        "last_name": "Engineer",
        "role": User.Role.STAFF,
        "dept": "IT",
    },
    {
        "email": "user@ghp.local",
        "password": "User@1234",
        "first_name": "General",
        "last_name": "User",
        "role": User.Role.USER,
        "dept": "HR",
    },
]


class Command(BaseCommand):
    help = "Create demo departments and one user per RBAC role."

    def handle(self, *args, **options):
        dept_by_code = {}
        for d in DEPARTMENTS:
            obj, created = Department.objects.get_or_create(
                code=d["code"], defaults={"name": d["name"]}
            )
            dept_by_code[d["code"]] = obj
            self.stdout.write(("+ " if created else "= ") + f"department {obj.code}")

        for u in USERS:
            if User.objects.filter(email=u["email"]).exists():
                self.stdout.write(f"= user {u['email']} (exists)")
                continue
            kwargs = dict(
                email=u["email"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                department=dept_by_code.get(u["dept"]),
            )
            if u.get("superuser"):
                user = User.objects.create_superuser(password=u["password"], **kwargs)
            else:
                user = User.objects.create_user(password=u["password"], **kwargs)
            self.stdout.write(self.style.SUCCESS(f"+ user {user.email} ({user.role})"))

        self.stdout.write(self.style.SUCCESS("Seed complete."))
