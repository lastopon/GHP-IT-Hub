"""Serializers for the projects / Kanban module."""
from rest_framework import serializers

from .models import BoardColumn, Card, Project


class CardSerializer(serializers.ModelSerializer):
    assignee_email = serializers.CharField(source="assignee.email", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = Card
        fields = [
            "id",
            "column",
            "title",
            "description",
            "assignee",
            "assignee_email",
            "priority",
            "priority_display",
            "due_date",
            "is_milestone",
            "order",
            "created_at",
            "updated_at",
        ]
        # order/column are changed via the move action, not a direct write.
        read_only_fields = ["id", "order", "created_at", "updated_at"]


class BoardColumnSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = BoardColumn
        fields = ["id", "project", "name", "order", "wip_limit", "cards", "created_at"]
        read_only_fields = ["id", "cards", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    manager_email = serializers.CharField(source="manager.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "code",
            "description",
            "status",
            "status_display",
            "manager",
            "manager_email",
            "start_date",
            "due_date",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectBoardSerializer(ProjectSerializer):
    """Project with its full board: columns (ordered) -> cards (ordered)."""

    columns = BoardColumnSerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["columns"]


class MoveCardSerializer(serializers.Serializer):
    """Input for the card ``move`` action."""

    # Target column; defaults to the card's current column when omitted.
    column = serializers.UUIDField(required=False)
    # Zero-based insert position within the target column.
    position = serializers.IntegerField(min_value=0)
