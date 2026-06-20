"""Django admin registrations for the daily report module."""
from django.contrib import admin

from .models import (
    ChecklistItem,
    ChecklistItemResult,
    ChecklistRun,
    ChecklistTemplate,
)


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ["order", "text", "response_type", "unit", "is_active"]


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]
    inlines = [ChecklistItemInline]


class ChecklistItemResultInline(admin.TabularInline):
    model = ChecklistItemResult
    extra = 0
    fields = ["item", "passed", "reading", "note"]
    readonly_fields = ["item"]


@admin.register(ChecklistRun)
class ChecklistRunAdmin(admin.ModelAdmin):
    list_display = ["template", "performed_on", "status", "performed_by", "completed_at"]
    list_filter = ["status", "performed_on", "template"]
    search_fields = ["template__code", "performed_by__email"]
    readonly_fields = ["id", "started_at", "completed_at", "created_at", "updated_at"]
    inlines = [ChecklistItemResultInline]


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ["template", "order", "text", "response_type"]
    list_filter = ["template", "response_type"]
    search_fields = ["text"]
