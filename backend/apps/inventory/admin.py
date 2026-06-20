"""Django admin registrations for the inventory module."""
from django.contrib import admin

from .models import InventoryCategory, InventoryItem, StockMovement


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    fields = ["kind", "quantity_delta", "quantity_after", "counterparty", "actor", "created_at"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False  # movements are created via the API move action


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "category", "quantity", "min_stock", "unit", "location"]
    list_filter = ["category"]
    search_fields = ["sku", "name", "location"]
    readonly_fields = ["id", "quantity", "created_at", "updated_at"]
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["item", "kind", "quantity_delta", "quantity_after", "actor", "created_at"]
    list_filter = ["kind"]
    search_fields = ["item__sku", "counterparty"]
    readonly_fields = ["id", "item", "kind", "quantity_delta", "quantity_after", "note", "counterparty", "actor", "created_at"]

    def has_add_permission(self, request):
        return False
