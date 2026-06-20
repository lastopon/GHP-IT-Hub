"""Daily Report & Checklist models (cloude.md module 5).

IT staff walk a routine (server-room check, office equipment, ...) defined by a
ChecklistTemplate of ChecklistItems. Each walk is a ChecklistRun whose
ChecklistItemResults record pass/fail/NA plus an optional reading and note. The
daily summary view rolls these up alongside the day's Helpdesk ticket counts.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class ChecklistTemplate(BaseModel):
    """A reusable routine, e.g. "Server room daily check"."""

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ChecklistItem(BaseModel):
    """One thing to check within a template (e.g. "AC temperature")."""

    class ResponseType(models.TextChoices):
        BOOL = "bool", _("Pass / Fail")
        READING = "reading", _("Numeric reading")
        TEXT = "text", _("Free text")

    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="items"
    )
    text = models.CharField(max_length=255)
    response_type = models.CharField(
        max_length=20, choices=ResponseType.choices, default=ResponseType.BOOL
    )
    unit = models.CharField(max_length=30, blank=True)  # e.g. "°C" for readings
    # Ordering within the template (lower = earlier).
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.template.code}: {self.text}"


class ChecklistRun(BaseModel):
    """One walk-through of a template by a staff member at a point in time."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", _("In progress")
        COMPLETED = "completed", _("Completed")

    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.PROTECT, related_name="runs"
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="checklist_runs",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True
    )
    # Business day the run belongs to (defaults to creation date).
    performed_on = models.DateField(default=timezone.localdate, db_index=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-performed_on", "-started_at"]
        indexes = [
            models.Index(fields=["performed_on", "status"]),
        ]

    def __str__(self):
        return f"{self.template.code} @ {self.performed_on}"

    @property
    def has_failures(self) -> bool:
        return self.results.filter(passed=False).exists()


class ChecklistItemResult(BaseModel):
    """The recorded answer for one item within a run."""

    run = models.ForeignKey(
        ChecklistRun, on_delete=models.CASCADE, related_name="results"
    )
    item = models.ForeignKey(
        ChecklistItem, on_delete=models.PROTECT, related_name="results"
    )
    # True = OK, False = problem, null = not applicable / skipped.
    passed = models.BooleanField(null=True, blank=True)
    reading = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["item__order"]
        # One result per item per run.
        constraints = [
            models.UniqueConstraint(
                fields=["run", "item"], name="unique_result_per_run_item"
            )
        ]

    def __str__(self):
        return f"{self.run_id}:{self.item_id} -> {self.passed}"
