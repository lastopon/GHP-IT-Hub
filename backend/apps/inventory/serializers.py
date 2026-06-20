"""Serializers for the inventory module."""
from rest_framework import serializers

from .models import InventoryCategory, InventoryItem, StockMovement


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ["id", "name", "code", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "item",
            "kind",
            "kind_display",
            "quantity_delta",
            "quantity_after",
            "note",
            "counterparty",
            "actor",
            "actor_email",
            "created_at",
        ]
        read_only_fields = fields  # movements are created via the item move action


class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "sku",
            "name",
            "category",
            "category_name",
            "quantity",
            "min_stock",
            "unit",
            "location",
            "is_low_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        # quantity is changed only through the move action, never a direct write.
        read_only_fields = ["id", "quantity", "is_low_stock", "created_at", "updated_at"]


class InventoryItemDetailSerializer(InventoryItemSerializer):
    movements = StockMovementSerializer(many=True, read_only=True)

    class Meta(InventoryItemSerializer.Meta):
        fields = InventoryItemSerializer.Meta.fields + ["movements"]


class StockMoveSerializer(serializers.Serializer):
    """Input for the item ``move`` action (received / issued / adjusted)."""

    kind = serializers.ChoiceField(choices=StockMovement.Kind.choices)
    # For receive/issue this is a positive magnitude (sign derived from kind).
    # For adjust it is a signed delta: positive raises stock, negative lowers
    # it (stock-take correction). Validated per-kind in validate().
    quantity = serializers.IntegerField()
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)
    counterparty = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )

    def validate(self, attrs):
        kind = attrs["kind"]
        qty = attrs["quantity"]
        if kind == StockMovement.Kind.ADJUST:
            if qty == 0:
                raise serializers.ValidationError(
                    {"quantity": "Adjustment cannot be zero."}
                )
        elif qty < 1:
            # receive / issue take a positive magnitude; the sign comes from kind.
            raise serializers.ValidationError(
                {"quantity": "Quantity must be at least 1."}
            )
        return attrs
