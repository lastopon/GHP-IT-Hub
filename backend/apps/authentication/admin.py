"""Django admin registrations for the auth module."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, Department, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "role", "department", "is_active"]
    list_filter = ["role", "is_active", "department", "is_ldap_user"]
    search_fields = ["email", "first_name", "last_name", "employee_id"]
    readonly_fields = ["id", "created_at", "updated_at", "is_ldap_user"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "employee_id")}),
        ("Role & org", {"fields": ("role", "department")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("LDAP", {"fields": ("is_ldap_user",)}),
        ("Timestamps", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "department"),
            },
        ),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "created_at"]
    search_fields = ["code", "name"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "target", "ip_address"]
    list_filter = ["action", "created_at"]
    search_fields = ["target", "actor__email"]
    readonly_fields = ["id", "actor", "action", "target", "detail", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # audit logs are immutable
