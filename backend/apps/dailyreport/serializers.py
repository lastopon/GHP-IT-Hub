"""Serializers for the daily report / checklist module."""
from rest_framework import serializers

from .models import (
    ChecklistItem,
    ChecklistItemResult,
    ChecklistRun,
    ChecklistTemplate,
)


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = [
            "id",
            "template",
            "text",
            "response_type",
            "unit",
            "order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistTemplate
        fields = [
            "id",
            "name",
            "code",
            "description",
            "items",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "items", "created_at"]


class ChecklistItemResultSerializer(serializers.ModelSerializer):
    item_text = serializers.CharField(source="item.text", read_only=True)

    class Meta:
        model = ChecklistItemResult
        fields = [
            "id",
            "run",
            "item",
            "item_text",
            "passed",
            "reading",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "run", "item_text", "created_at"]


class ChecklistRunSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    performed_by_email = serializers.CharField(
        source="performed_by.email", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    has_failures = serializers.BooleanField(read_only=True)

    class Meta:
        model = ChecklistRun
        fields = [
            "id",
            "template",
            "template_name",
            "performed_by",
            "performed_by_email",
            "status",
            "status_display",
            "performed_on",
            "started_at",
            "completed_at",
            "note",
            "has_failures",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "performed_by",
            "status",
            "started_at",
            "completed_at",
            "has_failures",
            "created_at",
        ]


class ChecklistRunDetailSerializer(ChecklistRunSerializer):
    results = ChecklistItemResultSerializer(many=True, read_only=True)

    class Meta(ChecklistRunSerializer.Meta):
        fields = ChecklistRunSerializer.Meta.fields + ["results"]


class _SubmitResultSerializer(serializers.Serializer):
    """One item's answer inside the run ``submit`` payload."""

    item = serializers.UUIDField()
    passed = serializers.BooleanField(required=False, allow_null=True)
    reading = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)


class SubmitRunSerializer(serializers.Serializer):
    """Bulk-submit results for a run and mark it completed."""

    results = _SubmitResultSerializer(many=True)
    note = serializers.CharField(required=False, allow_blank=True)
