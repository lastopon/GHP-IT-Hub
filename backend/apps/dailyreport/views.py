"""Daily Report & Checklist API views (cloude.md module 5)."""
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.permissions import IsITStaff, ReadOnlyOrAdmin
from apps.helpdesk.models import Ticket

from .models import (
    ChecklistItem,
    ChecklistItemResult,
    ChecklistRun,
    ChecklistTemplate,
)
from .serializers import (
    ChecklistItemResultSerializer,
    ChecklistItemSerializer,
    ChecklistRunDetailSerializer,
    ChecklistRunSerializer,
    ChecklistTemplateSerializer,
    SubmitRunSerializer,
)


class StaffWriteReadAuthenticated(IsAuthenticated):
    """Anyone authenticated may read; only IT staff/admin may write."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user.is_it_staff)


class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """Templates + their items. Anyone authenticated reads, admin writes."""

    queryset = ChecklistTemplate.objects.prefetch_related("items").all()
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "code"]


class ChecklistItemViewSet(viewsets.ModelViewSet):
    """Template items. Read for all authenticated, write for admin."""

    queryset = ChecklistItem.objects.select_related("template")
    serializer_class = ChecklistItemSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["template"]


class ChecklistRunViewSet(viewsets.ModelViewSet):
    """Checklist runs. Authenticated users read; IT staff perform them."""

    queryset = ChecklistRun.objects.select_related(
        "template", "performed_by"
    ).prefetch_related("results")
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["template", "status", "performed_by", "performed_on"]
    ordering_fields = ["performed_on", "started_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChecklistRunDetailSerializer
        return ChecklistRunSerializer

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsITStaff])
    def submit(self, request, pk=None):
        """Record all item results for the run and mark it completed.

        Every result's item must belong to the run's template, and an item may
        appear at most once. Re-submitting replaces the run's results.
        """
        run = self.get_object()
        serializer = SubmitRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rows = serializer.validated_data["results"]

        valid_item_ids = set(
            run.template.items.values_list("id", flat=True)
        )
        seen = set()
        for row in rows:
            item_id = row["item"]
            if item_id not in valid_item_ids:
                raise ValidationError(
                    {"results": f"Item {item_id} is not part of this checklist."}
                )
            if item_id in seen:
                raise ValidationError(
                    {"results": f"Item {item_id} appears more than once."}
                )
            seen.add(item_id)

        with transaction.atomic():
            # Replace any prior results so a re-submit is idempotent.
            run.results.all().delete()
            ChecklistItemResult.objects.bulk_create(
                [
                    ChecklistItemResult(
                        run=run,
                        item_id=row["item"],
                        passed=row.get("passed"),
                        reading=row.get("reading", ""),
                        note=row.get("note", ""),
                    )
                    for row in rows
                ]
            )
            run.status = ChecklistRun.Status.COMPLETED
            run.completed_at = timezone.now()
            if serializer.validated_data.get("note"):
                run.note = serializer.validated_data["note"]
            run.save(update_fields=["status", "completed_at", "note", "updated_at"])

        return Response(ChecklistRunDetailSerializer(run).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def daily_summary(self, request):
        """Roll up the day's checklist runs and Helpdesk tickets.

        ?date=YYYY-MM-DD (defaults to today, server timezone).
        """
        date_str = request.query_params.get("date")
        if date_str:
            from datetime import date

            try:
                day = date.fromisoformat(date_str)
            except ValueError:
                raise ValidationError({"date": "Use YYYY-MM-DD."})
        else:
            day = timezone.localdate()

        runs = ChecklistRun.objects.filter(performed_on=day)
        run_agg = runs.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=ChecklistRun.Status.COMPLETED)),
        )
        runs_with_failures = (
            runs.filter(results__passed=False).distinct().count()
        )

        # Tickets opened on the same calendar day.
        tickets = Ticket.objects.filter(created_at__date=day)
        ticket_agg = tickets.aggregate(
            opened=Count("id"),
            open_now=Count("id", filter=Q(status__in=Ticket.OPEN_STATUSES)),
        )

        return Response(
            {
                "date": day,
                "checklists": {
                    "runs": run_agg["total"],
                    "completed": run_agg["completed"],
                    "with_failures": runs_with_failures,
                },
                "tickets": {
                    "opened": ticket_agg["opened"],
                    "still_open": ticket_agg["open_now"],
                },
            }
        )


class ChecklistItemResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only item results (written via the run submit action)."""

    queryset = ChecklistItemResult.objects.select_related("run", "item")
    serializer_class = ChecklistItemResultSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["run", "item", "passed"]
