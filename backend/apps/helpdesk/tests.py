"""Smoke tests for the helpdesk module (ticket flow + RBAC scoping)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import AuditLog

from .models import Ticket, TicketCategory

User = get_user_model()


class TicketFlowTests(APITestCase):
    def setUp(self):
        self.category = TicketCategory.objects.create(
            name="Hardware", code="HW", default_sla_hours=8
        )
        self.staff = User.objects.create_user(
            email="staff@ghp.local", password="Staff@1234", role=User.Role.STAFF
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234"
        )
        self.other = User.objects.create_user(
            email="other@ghp.local", password="Other@1234"
        )

    def _create_ticket(self, requester):
        self.client.force_authenticate(requester)
        return self.client.post(
            reverse("ticket-list"),
            {
                "title": "Laptop won't boot",
                "description": "Black screen on power-on.",
                "category": str(self.category.id),
                "priority": Ticket.Priority.HIGH,
            },
        )

    def test_create_assigns_reference_and_sla(self):
        res = self._create_ticket(self.user)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        ticket = Ticket.objects.get(id=res.data["id"])
        self.assertTrue(ticket.reference.startswith("TKT-"))
        self.assertEqual(ticket.requester, self.user)
        self.assertIsNotNone(ticket.sla_due_at)  # seeded from category SLA

    def test_create_is_audited(self):
        self._create_ticket(self.user)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CREATE).exists()
        )

    def test_reference_increments(self):
        r1 = self._create_ticket(self.user)
        r2 = self._create_ticket(self.user)
        self.assertNotEqual(r1.data["reference"], r2.data["reference"])

    def test_reference_uses_numeric_max_not_lexicographic(self):
        # TKT-1000000 must rank above TKT-999999; a string sort would not.
        Ticket.objects.create(
            reference="TKT-1000000",
            title="big",
            description="d",
            category=self.category,
            requester=self.user,
        )
        res = self._create_ticket(self.user)
        self.assertEqual(res.data["reference"], "TKT-1000001")

    def test_general_user_sees_only_own_tickets(self):
        self._create_ticket(self.user)
        self.client.force_authenticate(self.other)
        res = self.client.get(reverse("ticket-list"))
        self.assertEqual(res.data["count"], 0)

    def test_staff_sees_all_tickets(self):
        self._create_ticket(self.user)
        self.client.force_authenticate(self.staff)
        res = self.client.get(reverse("ticket-list"))
        self.assertEqual(res.data["count"], 1)

    def test_general_user_cannot_change_status(self):
        res = self._create_ticket(self.user)
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.user)
        patch = self.client.patch(url, {"status": Ticket.Status.CLOSED})
        self.assertEqual(patch.status_code, status.HTTP_403_FORBIDDEN)

    def _resolve(self, ticket_id):
        self.client.force_authenticate(self.staff)
        self.client.post(reverse("ticket-resolve", args=[ticket_id]))

    def test_requester_can_rate_resolved_ticket(self):
        res = self._create_ticket(self.user)
        self._resolve(res.data["id"])
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.user)
        patch = self.client.patch(url, {"satisfaction_rating": 5})
        self.assertEqual(patch.status_code, status.HTTP_200_OK)

    def test_requester_cannot_rate_unresolved_ticket(self):
        res = self._create_ticket(self.user)  # status=new
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.user)
        patch = self.client.patch(url, {"satisfaction_rating": 5})
        self.assertEqual(patch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_must_be_within_1_to_5(self):
        res = self._create_ticket(self.user)
        self._resolve(res.data["id"])
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.user)
        patch = self.client.patch(url, {"satisfaction_rating": 99})
        self.assertEqual(patch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requester_cannot_delete_ticket(self):
        res = self._create_ticket(self.user)
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.user)
        delete = self.client.delete(url)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_delete_ticket(self):
        res = self._create_ticket(self.user)
        url = reverse("ticket-detail", args=[res.data["id"]])
        self.client.force_authenticate(self.staff)
        delete = self.client.delete(url)
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_staff_can_assign_and_resolve(self):
        res = self._create_ticket(self.user)
        ticket_id = res.data["id"]
        self.client.force_authenticate(self.staff)
        assign = self.client.post(
            reverse("ticket-assign", args=[ticket_id]),
            {"assignee": str(self.staff.id)},
        )
        self.assertEqual(assign.status_code, status.HTTP_200_OK)
        self.assertEqual(assign.data["status"], Ticket.Status.ASSIGNED)

        resolve = self.client.post(reverse("ticket-resolve", args=[ticket_id]))
        self.assertEqual(resolve.data["status"], Ticket.Status.RESOLVED)
        self.assertIsNotNone(resolve.data["resolved_at"])

    def test_general_user_cannot_assign(self):
        res = self._create_ticket(self.user)
        self.client.force_authenticate(self.user)
        assign = self.client.post(
            reverse("ticket-assign", args=[res.data["id"]]),
            {"assignee": str(self.user.id)},
        )
        self.assertEqual(assign.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_rejects_general_user_as_assignee(self):
        res = self._create_ticket(self.user)
        self.client.force_authenticate(self.staff)
        assign = self.client.post(
            reverse("ticket-assign", args=[res.data["id"]]),
            {"assignee": str(self.user.id)},  # role=user, not assignable
        )
        self.assertEqual(assign.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_rejects_unknown_assignee(self):
        res = self._create_ticket(self.user)
        self.client.force_authenticate(self.staff)
        assign = self.client.post(
            reverse("ticket-assign", args=[res.data["id"]]),
            {"assignee": "00000000-0000-0000-0000-000000000000"},
        )
        self.assertEqual(assign.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_rejects_malformed_assignee_id(self):
        res = self._create_ticket(self.user)
        self.client.force_authenticate(self.staff)
        assign = self.client.post(
            reverse("ticket-assign", args=[res.data["id"]]),
            {"assignee": "not-a-uuid"},
        )
        self.assertEqual(assign.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_can_list_assignees(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get(reverse("ticket-assignees"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        roles = {row["role"] for row in res.data}
        # Only staff/admin are assignable; general users are excluded.
        self.assertTrue(roles <= {User.Role.STAFF, User.Role.ADMIN})
        emails = {row["email"] for row in res.data}
        self.assertIn("staff@ghp.local", emails)
        self.assertNotIn("user@ghp.local", emails)

    def test_general_user_cannot_list_assignees(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("ticket-assignees"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
