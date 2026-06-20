"""IT Asset Management API views (cloude.md module 3)."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import AuditLog
from apps.authentication.permissions import IsITStaff, ReadOnlyOrAdmin

from .models import Asset, AssetAssignment, AssetCategory, MaintenanceRecord
from .serializers import (
    AssetAssignmentSerializer,
    AssetCategorySerializer,
    AssetDetailSerializer,
    AssetSerializer,
    MaintenanceRecordSerializer,
)

User = get_user_model()


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


class AssetCategoryViewSet(viewsets.ModelViewSet):
    """Categories: anyone authenticated reads, admin writes."""

    queryset = AssetCategory.objects.all().order_by("name")
    serializer_class = AssetCategorySerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "code"]


class AssetViewSet(viewsets.ModelViewSet):
    """Assets. Authenticated users read; IT staff manage and run lifecycle actions."""

    queryset = Asset.objects.select_related("category", "assigned_to").prefetch_related(
        "assignments", "maintenance_records"
    )
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["status", "category", "assigned_to", "is_active"]
    search_fields = ["asset_tag", "name", "serial_number", "manufacturer", "model"]
    ordering_fields = ["asset_tag", "created_at", "warranty_expiry", "purchase_date"]

    def get_serializer_class(self):
        if self.action in ("retrieve", "lookup"):
            return AssetDetailSerializer
        return AssetSerializer

    def perform_create(self, serializer):
        asset = serializer.save()
        self._audit(AuditLog.Action.CREATE, asset)

    def _audit(self, action_type, asset):
        AuditLog.objects.create(
            actor=self.request.user,
            action=action_type,
            target=f"asset:{asset.asset_tag}",
            ip_address=_client_ip(self.request),
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def lookup(self, request):
        """Resolve an asset by its tag (QR/barcode scan). ?tag=GHP-LT-0001"""
        tag = request.query_params.get("tag")
        if not tag:
            raise ValidationError({"tag": "This query parameter is required."})
        asset = self.get_queryset().filter(asset_tag=tag).first()
        if asset is None:
            raise NotFound("No asset with that tag.")
        return Response(AssetDetailSerializer(asset).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsITStaff])
    def assign(self, request, pk=None):
        """Hand the asset to a holder, opening a new assignment record."""
        asset = self.get_object()
        if asset.is_retired:
            raise ValidationError("A scrapped asset cannot be assigned.")
        holder_id = request.data.get("holder")
        if not holder_id:
            raise ValidationError({"holder": "This field is required."})
        try:
            holder = User.objects.filter(pk=holder_id, is_active=True).first()
        except (DjangoValidationError, ValueError, TypeError):
            holder = None
        if holder is None:
            raise ValidationError({"holder": "Must be an active user."})

        note = request.data.get("note", "")
        with transaction.atomic():
            # Close any currently-open assignment before opening a new one.
            asset.assignments.filter(returned_at__isnull=True).update(
                returned_at=timezone.now()
            )
            AssetAssignment.objects.create(asset=asset, holder=holder, note=note)
            asset.assigned_to = holder
            if asset.status in (Asset.Status.PROCURED, Asset.Status.IN_STORE):
                asset.status = Asset.Status.IN_USE
            asset.save(update_fields=["assigned_to", "status", "updated_at"])
        self._audit(AuditLog.Action.UPDATE, asset)
        return Response(AssetDetailSerializer(asset).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="return",
        url_name="return",
        permission_classes=[IsAuthenticated, IsITStaff],
    )
    def return_asset(self, request, pk=None):
        """Return the asset: close the open assignment and clear the holder."""
        asset = self.get_object()
        with transaction.atomic():
            open_qs = asset.assignments.filter(returned_at__isnull=True)
            if not open_qs.exists():
                raise ValidationError("This asset is not currently assigned.")
            open_qs.update(returned_at=timezone.now())
            asset.assigned_to = None
            if asset.status == Asset.Status.IN_USE:
                asset.status = Asset.Status.IN_STORE
            asset.save(update_fields=["assigned_to", "status", "updated_at"])
        self._audit(AuditLog.Action.UPDATE, asset)
        return Response(AssetDetailSerializer(asset).data)


class AssetAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only assignment history (created via Asset.assign / return_asset)."""

    queryset = AssetAssignment.objects.select_related("asset", "holder")
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["asset", "holder", "returned_at"]


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    """Maintenance history. Authenticated users read; IT staff manage."""

    queryset = MaintenanceRecord.objects.select_related("asset")
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["asset", "resolved_at"]
    search_fields = ["summary", "detail", "vendor"]
