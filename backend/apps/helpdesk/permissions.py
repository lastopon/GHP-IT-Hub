"""Helpdesk RBAC (builds on apps.authentication roles).

- General Users open tickets and see/act on their own.
- IT Staff/Admin triage, assign, and work every ticket.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsTicketParticipantOrStaff(BasePermission):
    """Object-level access for tickets.

    IT Staff/Admin can act on any ticket. A General User can read their own
    ticket but only patch a narrow set of fields (handled in the view).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_it_staff:
            return True
        # Owners may read; writes are filtered down to allowed fields in the view.
        return obj.requester_id == user.id
