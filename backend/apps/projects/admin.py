"""Django admin registrations for the projects module."""
from django.contrib import admin

from .models import BoardColumn, Card, Project


class BoardColumnInline(admin.TabularInline):
    model = BoardColumn
    extra = 0
    fields = ["order", "name", "wip_limit"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "status", "manager", "start_date", "due_date"]
    list_filter = ["status"]
    search_fields = ["code", "name"]
    inlines = [BoardColumnInline]


class CardInline(admin.TabularInline):
    model = Card
    extra = 0
    fields = ["order", "title", "assignee", "priority", "due_date", "is_milestone"]


@admin.register(BoardColumn)
class BoardColumnAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "wip_limit"]
    list_filter = ["project"]
    inlines = [CardInline]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ["title", "column", "assignee", "priority", "order", "is_milestone"]
    list_filter = ["priority", "is_milestone"]
    search_fields = ["title", "description"]
