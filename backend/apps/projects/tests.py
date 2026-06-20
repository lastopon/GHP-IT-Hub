"""Smoke tests for the projects / Kanban module (board, card move, RBAC)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import BoardColumn, Card, Project

User = get_user_model()


class ProjectTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@ghp.local", password="Staff@1234", role=User.Role.STAFF
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234"
        )
        self.project = Project.objects.create(code="P1", name="Project 1")
        self.todo = BoardColumn.objects.create(project=self.project, name="To Do", order=0)
        self.doing = BoardColumn.objects.create(
            project=self.project, name="Doing", order=1
        )

    def _card(self, column, title, order):
        return Card.objects.create(column=column, title=title, order=order)

    # ---- RBAC ----
    def test_general_user_can_read_board(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("project-board", args=[self.project.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["columns"]), 2)

    def test_general_user_cannot_create_project(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(reverse("project-list"), {"code": "X", "name": "x"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_card_appends_to_bottom(self):
        self._card(self.todo, "a", 0)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("card-list"), {"column": str(self.todo.id), "title": "b"}
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["order"], 1)  # after the existing card

    # ---- Move within a column ----
    def test_move_reorders_within_column(self):
        a = self._card(self.todo, "a", 0)
        b = self._card(self.todo, "b", 1)
        c = self._card(self.todo, "c", 2)
        self.client.force_authenticate(self.staff)
        # Move c to the top.
        res = self.client.post(
            reverse("card-move", args=[c.id]), {"position": 0}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        order = list(
            self.todo.cards.order_by("order").values_list("title", flat=True)
        )
        self.assertEqual(order, ["c", "a", "b"])

    # ---- Move across columns ----
    def test_move_to_other_column_resequences_both(self):
        a = self._card(self.todo, "a", 0)
        b = self._card(self.todo, "b", 1)
        d = self._card(self.doing, "d", 0)
        self.client.force_authenticate(self.staff)
        # Move a into Doing at position 0.
        res = self.client.post(
            reverse("card-move", args=[a.id]),
            {"column": str(self.doing.id), "position": 0},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        a.refresh_from_db()
        self.assertEqual(a.column, self.doing)
        # Source column closed its gap: b is now 0.
        b.refresh_from_db()
        self.assertEqual(b.order, 0)
        # Target column: a before d.
        doing_order = list(
            self.doing.cards.order_by("order").values_list("title", flat=True)
        )
        self.assertEqual(doing_order, ["a", "d"])

    def test_move_position_beyond_end_clamps(self):
        a = self._card(self.doing, "a", 0)
        b = self._card(self.todo, "b", 0)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("card-move", args=[b.id]),
            {"column": str(self.doing.id), "position": 999},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        doing_order = list(
            self.doing.cards.order_by("order").values_list("title", flat=True)
        )
        self.assertEqual(doing_order, ["a", "b"])  # appended at the end

    def test_move_rejects_column_from_other_project(self):
        other = Project.objects.create(code="P2", name="Project 2")
        other_col = BoardColumn.objects.create(project=other, name="X", order=0)
        a = self._card(self.todo, "a", 0)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("card-move", args=[a.id]),
            {"column": str(other_col.id), "position": 0},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_rejects_unknown_column(self):
        a = self._card(self.todo, "a", 0)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("card-move", args=[a.id]),
            {"column": "00000000-0000-0000-0000-000000000000", "position": 0},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_user_cannot_move(self):
        a = self._card(self.todo, "a", 0)
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("card-move", args=[a.id]), {"position": 0}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
