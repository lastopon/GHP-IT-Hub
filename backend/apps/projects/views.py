"""Project Management / Kanban API views (cloude.md module 6)."""
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import AuditLog

from .models import BoardColumn, Card, Project
from .serializers import (
    BoardColumnSerializer,
    CardSerializer,
    MoveCardSerializer,
    ProjectBoardSerializer,
    ProjectSerializer,
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


def _resequence(column):
    """Normalise card order in a column to 0..n-1 by current order."""
    for index, card in enumerate(column.cards.order_by("order", "created_at")):
        if card.order != index:
            card.order = index
            card.save(update_fields=["order", "updated_at"])


class ProjectViewSet(viewsets.ModelViewSet):
    """Projects. Authenticated users read; IT staff manage."""

    queryset = Project.objects.select_related("manager").prefetch_related(
        "columns__cards"
    )
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["status", "manager", "is_active"]
    search_fields = ["code", "name", "description"]
    ordering_fields = ["created_at", "due_date", "code"]

    def get_serializer_class(self):
        if self.action in ("retrieve", "board"):
            return ProjectBoardSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        project = serializer.save()
        AuditLog.objects.create(
            actor=self.request.user,
            action=AuditLog.Action.CREATE,
            target=f"project:{project.code}",
            ip_address=_client_ip(self.request),
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def board(self, request, pk=None):
        """The project's full board (columns -> cards), ordered."""
        return Response(ProjectBoardSerializer(self.get_object()).data)


class BoardColumnViewSet(viewsets.ModelViewSet):
    """Board columns. Authenticated users read; IT staff manage."""

    queryset = BoardColumn.objects.select_related("project").prefetch_related("cards")
    serializer_class = BoardColumnSerializer
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["project"]
    ordering_fields = ["order"]


class CardViewSet(viewsets.ModelViewSet):
    """Cards. Authenticated users read; IT staff manage and move them."""

    queryset = Card.objects.select_related("column", "column__project", "assignee")
    serializer_class = CardSerializer
    permission_classes = [StaffWriteReadAuthenticated]
    filterset_fields = ["column", "assignee", "priority", "is_milestone"]
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        # New cards go to the bottom of their column.
        column = serializer.validated_data["column"]
        last = column.cards.order_by("-order").first()
        serializer.save(order=(last.order + 1) if last else 0)

    @action(detail=True, methods=["post"], permission_classes=[StaffWriteReadAuthenticated])
    def move(self, request, pk=None):
        """Move a card to a column at a position, re-sequencing both lanes."""
        card = self.get_object()
        serializer = MoveCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        position = serializer.validated_data["position"]
        target_column_id = serializer.validated_data.get("column")

        source_column = card.column
        if target_column_id:
            target_column = BoardColumn.objects.filter(pk=target_column_id).first()
            if target_column is None:
                raise ValidationError({"column": "Unknown column."})
            if target_column.project_id != source_column.project_id:
                raise ValidationError(
                    {"column": "Target column belongs to a different project."}
                )
        else:
            target_column = source_column

        with transaction.atomic():
            # Lock the affected lane(s) so concurrent moves can't read the same
            # snapshot and write colliding order values. Lock columns in a
            # stable id order to avoid deadlock between two cross-column moves.
            lock_column_ids = sorted(
                {str(source_column.pk), str(target_column.pk)}
            )
            list(
                Card.objects.select_for_update()
                .filter(column_id__in=lock_column_ids)
                .order_by("pk")
            )

            # Build the target lane's ordered card list excluding the moved card,
            # insert it at the requested position, then write 0..n-1.
            siblings = list(
                target_column.cards.exclude(pk=card.pk).order_by("order", "created_at")
            )
            position = min(position, len(siblings))
            siblings.insert(position, card)

            card.column = target_column
            for index, c in enumerate(siblings):
                if c.pk == card.pk:
                    c.order = index
                    c.save(update_fields=["column", "order", "updated_at"])
                elif c.order != index:
                    c.order = index
                    c.save(update_fields=["order", "updated_at"])

            # If the card changed columns, close the gap it left behind.
            if target_column.pk != source_column.pk:
                _resequence(source_column)

        return Response(CardSerializer(card).data)
