"""Django admin registrations for the asset module."""
from django.contrib import admin

from .models import Asset, AssetAssignment, AssetCategory, MaintenanceRecord


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]


class AssetAssignmentInline(admin.TabularInline):
    model = AssetAssignment
    extra = 0
    fields = ["holder", "assigned_at", "returned_at", "note"]


class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0
    fields = ["reported_at", "resolved_at", "summary", "cost", "vendor"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        "asset_tag",
        "name",
        "category",
        "status",
        "assigned_to",
        "warranty_expiry",
    ]
    list_filter = ["status", "category"]
    search_fields = ["asset_tag", "name", "serial_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [AssetAssignmentInline, MaintenanceRecordInline]


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ["asset", "summary", "reported_at", "resolved_at", "vendor"]
    list_filter = ["resolved_at"]
    search_fields = ["asset__asset_tag", "summary", "vendor"]
