"""Project Management / Kanban models (cloude.md module 6).

An IT Project (e.g. a network upgrade) owns an ordered set of BoardColumns
(To Do / In Progress / Done) and Cards. A card lives in one column and carries
an assignee, due date, priority and a position within its column; cards are
moved between columns and reordered via the card ``move`` action.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Project(BaseModel):
    """An IT project tracked on a Kanban board."""

    class Status(models.TextChoices):
        PLANNING = "planning", _("Planning")
        ACTIVE = "active", _("Active")
        ON_HOLD = "on_hold", _("On hold")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING, db_index=True
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_managed",
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class BoardColumn(BaseModel):
    """A column (lane) on a project's Kanban board."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="columns"
    )
    name = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)
    # Optional work-in-progress limit (0 = no limit).
    wip_limit = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.project.code}:{self.name}"


class Card(BaseModel):
    """A task card living in one board column."""

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    column = models.ForeignKey(
        BoardColumn, on_delete=models.CASCADE, related_name="cards"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cards_assigned",
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    due_date = models.DateField(null=True, blank=True)
    is_milestone = models.BooleanField(default=False)
    # Position within the column (lower = higher in the lane).
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title
