"""Shared model managers."""
from django.db import models


class ActiveQuerySet(models.QuerySet):
    """QuerySet helpers for soft-deletable models."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class ActiveManager(models.Manager):
    """Default manager that hides soft-deleted (is_active=False) rows.

    Use ``all_objects = models.Manager()`` on a model for unrestricted access.
    """

    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).filter(is_active=True)
