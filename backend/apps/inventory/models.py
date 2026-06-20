"""Inventory Management models (cloude.md module 4).

Tracks spare parts (RAM, SSD, cables, ...) on hand, warns when a part drops to
its minimum stock level, and records every stock movement (received / issued /
adjusted). Quantities are only ever changed through StockMovement so the
``quantity`` field and the movement ledger stay in sync.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class InventoryCategory(BaseModel):
    """Grouping for spare parts (Memory, Storage, Peripherals, Cables, ...)."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Inventory category"
        verbose_name_plural = "Inventory categories"

    def __str__(self):
        return f"{self.code} — {self.name}"


class InventoryItem(BaseModel):
    """A stocked spare part with an on-hand quantity and a reorder threshold."""

    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.PROTECT,
        related_name="items",
    )
    # Current stock on hand. Never written directly by the API — only adjusted
    # through StockMovement so the ledger reconciles.
    quantity = models.PositiveIntegerField(default=0)
    # Reorder point: when quantity <= min_stock the item is "low".
    min_stock = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=30, default="pcs")
    location = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.sku} — {self.name}"

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.min_stock


class StockMovement(BaseModel):
    """An immutable ledger entry recording a change to an item's quantity.

    ``quantity_delta`` is signed: positive for received/adjust-up, negative for
    issued/adjust-down. ``quantity_after`` snapshots the resulting on-hand level.
    """

    class Kind(models.TextChoices):
        RECEIVE = "receive", _("Received")
        ISSUE = "issue", _("Issued")
        ADJUST = "adjust", _("Adjusted")

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="movements"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    quantity_delta = models.IntegerField()
    quantity_after = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    # Who the parts were issued to / received from (free-form).
    counterparty = models.CharField(max_length=200, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stock_movements",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item.sku} {self.kind} {self.quantity_delta:+d}"
