"""Helpdesk API views (cloude.md module 2)."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.models import AuditLog
from apps.authentication.permissions import IsITStaff, ReadOnlyOrAdmin

User = get_user_model()

from .models import (
    KnowledgeBaseArticle,
    Ticket,
    TicketCategory,
    TicketComment,
)
from .permissions import IsTicketParticipantOrStaff
from .serializers import (
    KnowledgeBaseArticleSerializer,
    TicketCategorySerializer,
    TicketCommentSerializer,
    TicketCreateSerializer,
    TicketSerializer,
)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class TicketCategoryViewSet(viewsets.ModelViewSet):
    """Categories: anyone authenticated reads, admin writes."""

    queryset = TicketCategory.objects.all().order_by("name")
    serializer_class = TicketCategorySerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "code"]


class TicketViewSet(viewsets.ModelViewSet):
    """Tickets. Requesters see their own; IT staff see and work all."""

    queryset = Ticket.objects.select_related(
        "category", "requester", "assignee"
    ).prefetch_related("comments", "attachments")
    permission_classes = [IsAuthenticated, IsTicketParticipantOrStaff]
    filterset_fields = ["status", "priority", "category", "assignee"]
    search_fields = ["reference", "title", "description"]
    ordering_fields = ["created_at", "priority", "status", "sla_due_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        return TicketSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # General users are scoped to their own tickets; staff see everything.
        if not user.is_it_staff:
            qs = qs.filter(requester=user)
        return qs

    def perform_create(self, serializer):
        ticket = serializer.save(requester=self.request.user)
        AuditLog.objects.create(
            actor=self.request.user,
            action=AuditLog.Action.CREATE,
            target=f"ticket:{ticket.reference}",
            ip_address=_client_ip(self.request),
        )

    def update(self, request, *args, **kwargs):
        # General users may only patch satisfaction fields on their own ticket.
        if not request.user.is_it_staff:
            allowed = {"satisfaction_rating", "satisfaction_comment"}
            extra = set(request.data) - allowed
            if extra:
                raise PermissionDenied(
                    "You may only set satisfaction_rating / satisfaction_comment."
                )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsITStaff])
    def assign(self, request, pk=None):
        """Assign (or reassign) a ticket to a staff member."""
        ticket = self.get_object()
        assignee_id = request.data.get("assignee")
        if not assignee_id:
            raise ValidationError({"assignee": "This field is required."})
        ticket.assignee_id = assignee_id
        if ticket.status == Ticket.Status.NEW:
            ticket.status = Ticket.Status.ASSIGNED
        ticket.save(update_fields=["assignee", "status", "updated_at"])
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsITStaff])
    def resolve(self, request, pk=None):
        """Mark a ticket resolved and stamp resolved_at."""
        ticket = self.get_object()
        ticket.status = Ticket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.save(update_fields=["status", "resolved_at", "updated_at"])
        return Response(TicketSerializer(ticket).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsITStaff])
    def assignees(self, request):
        """Staff/admin users a ticket can be assigned to.

        Scoped to the helpdesk so IT Staff can populate the assignee picker
        without the admin-only user-management endpoint.
        """
        qs = User.objects.filter(
            Q(role=User.Role.STAFF) | Q(role=User.Role.ADMIN), is_active=True
        ).order_by("email")
        data = [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
            }
            for u in qs
        ]
        return Response(data)


class TicketCommentViewSet(viewsets.ModelViewSet):
    """Comments on tickets. Internal notes are hidden from non-staff."""

    queryset = TicketComment.objects.select_related("author", "ticket")
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["ticket", "is_internal"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_it_staff:
            # Only the requester's own tickets, and never internal notes.
            qs = qs.filter(ticket__requester=user, is_internal=False)
        return qs

    def perform_create(self, serializer):
        ticket = serializer.validated_data["ticket"]
        user = self.request.user
        # A general user can only comment on their own ticket, never internally.
        if not user.is_it_staff:
            if ticket.requester_id != user.id:
                raise PermissionDenied("You cannot comment on this ticket.")
            if serializer.validated_data.get("is_internal"):
                raise PermissionDenied("Only staff can add internal notes.")
        serializer.save(author=user)


class KnowledgeBaseArticleViewSet(viewsets.ModelViewSet):
    """Knowledge base. Staff manage; everyone reads published articles."""

    queryset = KnowledgeBaseArticle.objects.select_related("category")
    serializer_class = KnowledgeBaseArticleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "is_published"]
    search_fields = ["title", "body"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_it_staff:
            qs = qs.filter(is_published=True)
        return qs

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated(), IsITStaff()]
        return [IsAuthenticated()]
