"""IT Asset Management models (cloude.md module 3).

Tracks the lifecycle of an asset (procured -> in use -> in repair -> scrapped),
who currently holds it, its maintenance history, and warranty expiry. Each
asset carries a human-friendly ``asset_tag`` used for QR/barcode lookup.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class AssetCategory(BaseModel):
    """Type of asset (Laptop, Desktop, Monitor, Printer, ...)."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Asset category"
        verbose_name_plural = "Asset categories"

    def __str__(self):
        return f"{self.code} — {self.name}"


class Asset(BaseModel):
    """A tracked IT asset with a lifecycle status and current holder."""

    class Status(models.TextChoices):
        PROCURED = "procured", _("Procured")
        IN_USE = "in_use", _("In use")
        IN_STORE = "in_store", _("In store")
        IN_REPAIR = "in_repair", _("In repair")
        SCRAPPED = "scrapped", _("Scrapped")

    # Final states an asset cannot be assigned out of.
    RETIRED_STATUSES = {Status.SCRAPPED}

    # Printed on the physical tag and scanned via QR/barcode.
    asset_tag = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCURED, db_index=True
    )

    serial_number = models.CharField(max_length=120, blank=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    model = models.CharField(max_length=120, blank=True)
    specs = models.TextField(blank=True)

    # Whoever physically holds the asset right now (mirrors the latest active
    # AssetAssignment). Null when the asset is in store / unassigned.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets_held",
    )

    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    warranty_expiry = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["asset_tag"]
        indexes = [
            models.Index(fields=["status", "category"]),
        ]

    def __str__(self):
        return f"{self.asset_tag} — {self.name}"

    @property
    def is_retired(self) -> bool:
        return self.status in self.RETIRED_STATUSES

    @property
    def warranty_active(self) -> bool:
        return bool(self.warranty_expiry and self.warranty_expiry >= timezone.localdate())


class AssetAssignment(BaseModel):
    """A record of an asset being handed to (and later returned from) a holder.

    The currently-open assignment (``returned_at`` is null) reflects who holds
    the asset; ``Asset.assigned_to`` mirrors it for quick lookups.
    """

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="assignments"
    )
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="asset_assignments",
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.asset.asset_tag} -> {self.holder.email}"

    @property
    def is_open(self) -> bool:
        return self.returned_at is None


class MaintenanceRecord(BaseModel):
    """A repair / maintenance entry in an asset's history."""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="maintenance_records"
    )
    reported_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    summary = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vendor = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-reported_at"]

    def __str__(self):
        return f"{self.asset.asset_tag}: {self.summary}"

    @property
    def is_open(self) -> bool:
        return self.resolved_at is None
