"""User, Department, and AuditLog models for GHP IT Hub.

RBAC roles follow cloude.md module 1:
- Super Admin / IT Manager  -> ADMIN
- IT Staff / Engineer       -> STAFF
- General User              -> USER
"""
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """Organizational unit a user belongs to (mirrors AD OU when LDAP is on)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class UserManager(BaseUserManager):
    """Manager for the email-based custom user."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user keyed by UUID and authenticated by email.

    The default ``username`` field is removed; ``email`` is the login id.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", _("Super Admin / IT Manager")
        STAFF = "staff", _("IT Staff / Engineer")
        USER = "user", _("General User")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # replaced by email
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.USER, db_index=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    phone = models.CharField(max_length=30, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    # True when the account was provisioned/authenticated through LDAP/AD.
    is_ldap_user = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password only

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email

    # ---- RBAC convenience helpers ----
    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_it_staff(self) -> bool:
        return self.role in {self.Role.ADMIN, self.Role.STAFF}


class AuditLog(models.Model):
    """Immutable audit trail entry.

    Records are write-once: attempting to update an existing row raises
    ValueError (matches the AERO-IT audit pattern).
    """

    class Action(models.TextChoices):
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
        LOGIN = "login", _("Login")
        LOGOUT = "logout", _("Logout")
        LOGIN_FAILED = "login_failed", _("Login failed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    # Free-form target reference, e.g. "asset:1234" or "user:foo@bar".
    target = models.CharField(max_length=255, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log"
        verbose_name_plural = "Audit logs"

    def __str__(self):
        who = self.actor.email if self.actor else "system"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} {self.action} {self.target}"

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("AuditLog entries are immutable and cannot be modified.")
        return super().save(*args, **kwargs)
