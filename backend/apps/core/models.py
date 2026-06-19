"""Core abstract models shared by every domain app."""
import uuid

from django.conf import settings
from django.db import models

from .managers import ActiveManager


class BaseModel(models.Model):
    """Abstract base for all domain models.

    Provides a UUID primary key, audit timestamps, a created_by FK and an
    ``is_active`` soft-delete flag. ``objects`` hides soft-deleted rows;
    ``all_objects`` returns everything.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def delete(self, using=None, keep_parents=False):
        """Soft-delete by default. Pass ``hard=True`` to remove the row."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
