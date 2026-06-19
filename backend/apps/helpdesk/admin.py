"""Django admin registrations for the helpdesk module."""
from django.contrib import admin

from .models import (
    KnowledgeBaseArticle,
    Ticket,
    TicketAttachment,
    TicketCategory,
    TicketComment,
)


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "default_sla_hours", "is_active"]
    search_fields = ["code", "name"]


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    fields = ["author", "body", "is_internal", "created_at"]
    readonly_fields = ["created_at"]


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    fields = ["file", "original_name", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "title",
        "category",
        "status",
        "priority",
        "requester",
        "assignee",
        "sla_due_at",
    ]
    list_filter = ["status", "priority", "category"]
    search_fields = ["reference", "title", "description", "requester__email"]
    readonly_fields = ["id", "reference", "created_at", "updated_at"]
    inlines = [TicketCommentInline, TicketAttachmentInline]


@admin.register(KnowledgeBaseArticle)
class KnowledgeBaseArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "is_published", "created_at"]
    list_filter = ["is_published", "category"]
    search_fields = ["title", "body"]
