"""RBAC permission classes (cloude.md module 1)."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Super Admin / IT Manager only."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsITStaff(BasePermission):
    """IT Staff/Engineer or Admin."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_it_staff
        )


class IsSelfOrAdmin(BasePermission):
    """Owners can act on their own object; admins on anyone's."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_admin:
            return True
        return obj == request.user


class ReadOnlyOrAdmin(BasePermission):
    """Anyone authenticated can read; only admins can write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin
