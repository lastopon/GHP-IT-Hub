"""Serializers for the asset management module."""
from rest_framework import serializers

from .models import Asset, AssetAssignment, AssetCategory, MaintenanceRecord


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ["id", "name", "code", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class AssetAssignmentSerializer(serializers.ModelSerializer):
    holder_email = serializers.CharField(source="holder.email", read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = AssetAssignment
        fields = [
            "id",
            "asset",
            "holder",
            "holder_email",
            "assigned_at",
            "returned_at",
            "note",
            "is_open",
            "created_at",
        ]
        read_only_fields = ["id", "holder_email", "is_open", "created_at"]


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = [
            "id",
            "asset",
            "reported_at",
            "resolved_at",
            "summary",
            "detail",
            "cost",
            "vendor",
            "is_open",
            "created_at",
        ]
        read_only_fields = ["id", "is_open", "created_at"]


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    assigned_to_email = serializers.CharField(
        source="assigned_to.email", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    warranty_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "asset_tag",
            "name",
            "category",
            "category_name",
            "status",
            "status_display",
            "serial_number",
            "manufacturer",
            "model",
            "specs",
            "assigned_to",
            "assigned_to_email",
            "purchase_date",
            "purchase_cost",
            "warranty_expiry",
            "warranty_active",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            # assigned_to is changed via the assign/return actions, not by PATCH.
            "assigned_to",
            "created_at",
            "updated_at",
        ]


class AssetDetailSerializer(AssetSerializer):
    """Asset with its assignment + maintenance history (read-only nested)."""

    assignments = AssetAssignmentSerializer(many=True, read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)

    class Meta(AssetSerializer.Meta):
        fields = AssetSerializer.Meta.fields + ["assignments", "maintenance_records"]
