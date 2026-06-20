"""Smoke tests for the daily report module (runs, submit, daily summary)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.helpdesk.models import Ticket, TicketCategory

from .models import (
    ChecklistItem,
    ChecklistItemResult,
    ChecklistRun,
    ChecklistTemplate,
)

User = get_user_model()


class DailyReportTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@ghp.local", password="Staff@1234", role=User.Role.STAFF
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234"
        )
        self.template = ChecklistTemplate.objects.create(
            code="SRV", name="Server Room"
        )
        self.i1 = ChecklistItem.objects.create(
            template=self.template, text="AC temp", response_type="reading", unit="°C", order=1
        )
        self.i2 = ChecklistItem.objects.create(
            template=self.template, text="UPS light", order=2
        )

    def _new_run(self, performer=None):
        self.client.force_authenticate(performer or self.staff)
        return self.client.post(
            reverse("checklistrun-list"), {"template": str(self.template.id)}
        )

    # ---- RBAC ----
    def test_general_user_can_read_templates(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("checklisttemplate-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["items"][0]["text"], "AC temp")

    def test_general_user_cannot_create_run(self):
        res = self._new_run(self.user)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_create_run_sets_performer_and_status(self):
        res = self._new_run()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["status"], ChecklistRun.Status.IN_PROGRESS)
        run = ChecklistRun.objects.get(id=res.data["id"])
        self.assertEqual(run.performed_by, self.staff)

    # ---- Submit ----
    def test_submit_records_results_and_completes(self):
        run_id = self._new_run().data["id"]
        res = self.client.post(
            reverse("checklistrun-submit", args=[run_id]),
            {
                "results": [
                    {"item": str(self.i1.id), "reading": "22", "passed": True},
                    {"item": str(self.i2.id), "passed": False, "note": "UPS beeping"},
                ],
                "note": "all walked",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["status"], ChecklistRun.Status.COMPLETED)
        self.assertTrue(res.data["has_failures"])
        self.assertEqual(len(res.data["results"]), 2)
        self.assertIsNotNone(res.data["completed_at"])

    def test_submit_rejects_item_from_other_template(self):
        other = ChecklistTemplate.objects.create(code="X", name="Other")
        foreign = ChecklistItem.objects.create(template=other, text="foreign")
        run_id = self._new_run().data["id"]
        res = self.client.post(
            reverse("checklistrun-submit", args=[run_id]),
            {"results": [{"item": str(foreign.id), "passed": True}]},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_rejects_duplicate_item(self):
        run_id = self._new_run().data["id"]
        res = self.client.post(
            reverse("checklistrun-submit", args=[run_id]),
            {
                "results": [
                    {"item": str(self.i1.id), "passed": True},
                    {"item": str(self.i1.id), "passed": False},
                ]
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resubmit_replaces_results(self):
        run_id = self._new_run().data["id"]
        url = reverse("checklistrun-submit", args=[run_id])
        self.client.post(
            url,
            {"results": [{"item": str(self.i1.id), "passed": True}]},
            format="json",
        )
        self.client.post(
            url,
            {"results": [{"item": str(self.i2.id), "passed": False}]},
            format="json",
        )
        self.assertEqual(ChecklistItemResult.objects.filter(run_id=run_id).count(), 1)

    def test_general_user_cannot_submit(self):
        run_id = self._new_run().data["id"]
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("checklistrun-submit", args=[run_id]),
            {"results": [{"item": str(self.i1.id), "passed": True}]},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Daily summary ----
    def test_daily_summary_rolls_up_runs_and_tickets(self):
        # A completed run with a failure.
        run_id = self._new_run().data["id"]
        self.client.post(
            reverse("checklistrun-submit", args=[run_id]),
            {"results": [{"item": str(self.i2.id), "passed": False}]},
            format="json",
        )
        # A ticket opened today.
        cat = TicketCategory.objects.create(code="HW", name="Hardware")
        Ticket.objects.create(
            title="t", description="d", category=cat, requester=self.user
        )
        res = self.client.get(reverse("checklistrun-daily-summary"))
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["checklists"]["runs"], 1)
        self.assertEqual(res.data["checklists"]["completed"], 1)
        self.assertEqual(res.data["checklists"]["with_failures"], 1)
        self.assertEqual(res.data["tickets"]["opened"], 1)
        self.assertEqual(res.data["tickets"]["still_open"], 1)

    def test_daily_summary_invalid_date(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get(reverse("checklistrun-daily-summary"), {"date": "nope"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
