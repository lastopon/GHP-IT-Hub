"""Helpdesk & Ticketing models (cloude.md module 2).

A General User opens a Ticket (Hardware / Software / Network), IT Staff triage
and assign it, track it against an SLA due date, and the requester rates the
service after the ticket is closed. Frequently used fixes are stored as
Knowledge Base articles.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class TicketCategory(BaseModel):
    """Top-level problem category (Hardware, Software, Network, ...).

    ``default_sla_hours`` seeds the SLA due date when a ticket is created under
    this category; leave null to skip SLA tracking.
    """

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    default_sla_hours = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ticket category"
        verbose_name_plural = "Ticket categories"

    def __str__(self):
        return f"{self.code} — {self.name}"


class Ticket(BaseModel):
    """A support request raised by a user and worked by IT staff."""

    class Status(models.TextChoices):
        NEW = "new", _("New")
        ASSIGNED = "assigned", _("Assigned")
        IN_PROGRESS = "in_progress", _("In progress")
        ON_HOLD = "on_hold", _("On hold")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")
        CANCELLED = "cancelled", _("Cancelled")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    # Open + working states; used to recompute SLA / queue dashboards.
    OPEN_STATUSES = {Status.NEW, Status.ASSIGNED, Status.IN_PROGRESS, Status.ON_HOLD}
    # States a requester may set once their issue is solved.
    CLOSED_STATUSES = {Status.RESOLVED, Status.CLOSED, Status.CANCELLED}

    # Human-friendly running number, assigned on first save (e.g. TKT-000123).
    reference = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.PROTECT,
        related_name="tickets",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, db_index=True
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets_requested",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_assigned",
    )

    sla_due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # 1–5 satisfaction rating, set by the requester after closure.
    satisfaction_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    satisfaction_comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.title}"

    @property
    def is_open(self) -> bool:
        return self.status in self.OPEN_STATUSES

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.sla_due_at and self.is_open and timezone.now() > self.sla_due_at
        )

    def save(self, *args, **kwargs):
        creating = self._state.adding
        if creating:
            if not self.reference:
                self.reference = self._next_reference()
            if self.sla_due_at is None and self.category_id:
                hours = self.category.default_sla_hours
                if hours:
                    self.sla_due_at = timezone.now() + timezone.timedelta(hours=hours)
        super().save(*args, **kwargs)

    @staticmethod
    def _next_reference() -> str:
        last = (
            Ticket.all_objects.exclude(reference="")
            .order_by("-reference")
            .values_list("reference", flat=True)
            .first()
        )
        seq = int(last.split("-")[1]) + 1 if last else 1
        return f"TKT-{seq:06d}"


class TicketComment(BaseModel):
    """A note or reply on a ticket. Internal notes are hidden from requesters."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ticket_comments",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.ticket.reference}"


class TicketAttachment(BaseModel):
    """A file/image attached to a ticket (cloude.md: 'แนบรูปภาพประกอบ')."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="helpdesk/attachments/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or self.file.name


class KnowledgeBaseArticle(BaseModel):
    """Reusable fix / how-to for common problems (cloude.md Knowledge Base)."""

    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kb_articles",
    )
    body = models.TextField()
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Knowledge base article"

    def __str__(self):
        return self.title
