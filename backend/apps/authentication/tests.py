"""Smoke tests for the auth module (JWT login + RBAC + immutable audit log)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AuditLog, Department

User = get_user_model()


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.dept = Department.objects.create(code="IT", name="Information Technology")
        self.admin = User.objects.create_superuser(
            email="admin@ghp.local", password="Admin@1234", department=self.dept
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234", department=self.dept
        )

    def test_login_returns_tokens_and_user(self):
        url = reverse("login")
        res = self.client.post(url, {"email": "admin@ghp.local", "password": "Admin@1234"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["role"], User.Role.ADMIN)

    def test_login_failure_is_audited(self):
        url = reverse("login")
        res = self.client.post(url, {"email": "admin@ghp.local", "password": "wrong"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED).exists()
        )

    def test_general_user_cannot_list_users(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("user-list"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(reverse("user-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me_endpoint_returns_own_profile(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("user-me"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "user@ghp.local")


class AuditLogImmutabilityTests(APITestCase):
    def test_audit_log_cannot_be_updated(self):
        log = AuditLog.objects.create(action=AuditLog.Action.LOGIN, target="user:x")
        log.target = "user:y"
        with self.assertRaises(ValueError):
            log.save()
