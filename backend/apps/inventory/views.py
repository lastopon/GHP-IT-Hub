"""Inventory Management API views (cloude.md module 4)."""
from django.db import transaction
from django.db.models import F
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import AuditLog
from apps.authentication.permissions import IsITStaff, ReadOnlyOrAdmin

from .models import InventoryCategory, InventoryItem, StockMovement
from .serializers import (
    InventoryCategorySerializer,
    InventoryItemDetailSerializer,
    InventoryItemSerializer,
    StockMovementSerializer,
    StockMoveSerializer,
)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class StaffWriteReadAuthenticated(IsAuthenticated):
    """Anyone authenticated may read; only IT staff/admin may write."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user.is_it_staff)


class InventoryCategoryViewSet(viewsets.ModelViewSet):
    """Categories: anyone authenticated reads, admin writes."""

    queryset = InventoryCategory.objects.all().order_by("name")
    serializer_class = InventoryCategorySerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "code"]


class InventoryItemViewSet(viewsets.ModelViewSet):
    """Spare-part items. Authenticated users read; IT staff manage and move stock."""

    queryset = InventoryItem.objects.select_related("category").prefetch_related(
        "movements"
    )
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["category", "is_active"]
    search_fields = ["sku", "name", "location"]
    ordering_fields = ["sku", "name", "quantity", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return InventoryItemDetailSerializer
        return InventoryItemSerializer

    def _audit(self, action_type, item):
        AuditLog.objects.create(
            actor=self.request.user,
            action=action_type,
            target=f"inventory:{item.sku}",
            ip_address=_client_ip(self.request),
        )

    def perform_create(self, serializer):
        item = serializer.save()
        self._audit(AuditLog.Action.CREATE, item)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def low_stock(self, request):
        """Items at or below their reorder point (quantity <= min_stock)."""
        qs = self.filter_queryset(self.get_queryset()).filter(
            quantity__lte=F("min_stock")
        )
        page = self.paginate_queryset(qs)
        serializer = InventoryItemSerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsITStaff])
    def move(self, request, pk=None):
        """Receive / issue / adjust stock, updating quantity + writing a ledger row."""
        serializer = StockMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kind = serializer.validated_data["kind"]
        magnitude = serializer.validated_data["quantity"]
        delta = -magnitude if kind == StockMovement.Kind.ISSUE else magnitude

        # Resolve via the viewset (404 + permission/queryset scoping) first,
        # then re-fetch under a row lock inside the transaction.
        self.get_object()
        with transaction.atomic():
            # Lock the row so concurrent moves can't oversell or race the count.
            item = InventoryItem.objects.select_for_update().get(pk=pk)
            new_qty = item.quantity + delta
            if new_qty < 0:
                raise ValidationError(
                    {"quantity": f"Only {item.quantity} in stock; cannot issue {magnitude}."}
                )
            item.quantity = new_qty
            item.save(update_fields=["quantity", "updated_at"])
            StockMovement.objects.create(
                item=item,
                kind=kind,
                quantity_delta=delta,
                quantity_after=new_qty,
                note=serializer.validated_data.get("note", ""),
                counterparty=serializer.validated_data.get("counterparty", ""),
                actor=request.user,
            )
        self._audit(AuditLog.Action.UPDATE, item)
        return Response(InventoryItemDetailSerializer(item).data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only stock movement ledger (created via the item move action)."""

    queryset = StockMovement.objects.select_related("item", "actor")
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["item", "kind"]
