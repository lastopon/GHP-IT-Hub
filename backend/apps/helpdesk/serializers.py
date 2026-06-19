"""Serializers for the helpdesk module."""
from rest_framework import serializers

from .models import (
    KnowledgeBaseArticle,
    Ticket,
    TicketAttachment,
    TicketCategory,
    TicketComment,
)


class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = [
            "id",
            "name",
            "code",
            "description",
            "default_sla_hours",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "original_name", "created_at"]
        read_only_fields = ["id", "original_name", "created_at"]

    def create(self, validated_data):
        upload = validated_data.get("file")
        if upload is not None and not validated_data.get("original_name"):
            validated_data["original_name"] = getattr(upload, "name", "")
        return super().create(validated_data)


class TicketCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "ticket",
            "author",
            "author_email",
            "body",
            "is_internal",
            "created_at",
        ]
        read_only_fields = ["id", "author", "author_email", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    requester_email = serializers.CharField(source="requester.email", read_only=True)
    assignee_email = serializers.CharField(source="assignee.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "reference",
            "title",
            "description",
            "category",
            "category_name",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "requester",
            "requester_email",
            "assignee",
            "assignee_email",
            "sla_due_at",
            "resolved_at",
            "closed_at",
            "satisfaction_rating",
            "satisfaction_comment",
            "is_overdue",
            "comments",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference",
            "requester",
            "resolved_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """A requester opens a ticket; status/assignee are staff-controlled."""

    class Meta:
        model = Ticket
        fields = ["id", "reference", "title", "description", "category", "priority"]
        read_only_fields = ["id", "reference"]


class KnowledgeBaseArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = KnowledgeBaseArticle
        fields = [
            "id",
            "title",
            "category",
            "category_name",
            "body",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
