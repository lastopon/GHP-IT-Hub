"""Smoke tests for the inventory module (stock moves, low-stock, RBAC)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import InventoryCategory, InventoryItem, StockMovement

User = get_user_model()


class InventoryTests(APITestCase):
    def setUp(self):
        self.category = InventoryCategory.objects.create(name="Memory", code="MEM")
        self.staff = User.objects.create_user(
            email="staff@ghp.local", password="Staff@1234", role=User.Role.STAFF
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234"
        )

    def _item(self, **kwargs):
        defaults = dict(sku="RAM-8GB", name="8GB DDR4", category=self.category, min_stock=5)
        defaults.update(kwargs)
        return InventoryItem.objects.create(**defaults)

    # ---- RBAC ----
    def test_general_user_can_read_items(self):
        self._item()
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("inventoryitem-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_general_user_cannot_create_item(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("inventoryitem-list"),
            {"sku": "X", "name": "x", "category": str(self.category.id)},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_quantity_is_read_only_on_create(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-list"),
            {"sku": "SSD-1TB", "name": "1TB SSD", "category": str(self.category.id), "quantity": 99},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data["quantity"], 0)  # ignored; moves set quantity

    # ---- Stock movements ----
    def test_receive_increases_quantity_and_logs(self):
        item = self._item()
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "receive", "quantity": 10, "counterparty": "Acme Co"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["quantity"], 10)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 10)
        mv = StockMovement.objects.get(item=item)
        self.assertEqual(mv.quantity_delta, 10)
        self.assertEqual(mv.quantity_after, 10)
        self.assertEqual(mv.actor, self.staff)

    def test_issue_decreases_quantity(self):
        item = self._item(quantity=10)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "issue", "quantity": 4},
        )
        self.assertEqual(res.data["quantity"], 6)
        mv = StockMovement.objects.filter(item=item).first()
        self.assertEqual(mv.quantity_delta, -4)

    def test_cannot_issue_more_than_in_stock(self):
        item = self._item(quantity=3)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "issue", "quantity": 5},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)  # unchanged
        self.assertFalse(StockMovement.objects.filter(item=item).exists())

    def test_move_quantity_must_be_positive(self):
        item = self._item(quantity=5)
        self.client.force_authenticate(self.staff)
        for kind in ("receive", "issue"):
            res = self.client.post(
                reverse("inventoryitem-move", args=[item.id]),
                {"kind": kind, "quantity": 0},
            )
            self.assertEqual(
                res.status_code, status.HTTP_400_BAD_REQUEST, f"{kind} qty=0"
            )

    # ---- Signed adjust (stock-take corrections) ----
    def test_adjust_up_increases_quantity(self):
        item = self._item(quantity=10)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "adjust", "quantity": 3},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["quantity"], 13)
        mv = StockMovement.objects.filter(item=item).first()
        self.assertEqual(mv.quantity_delta, 3)

    def test_adjust_down_decreases_quantity(self):
        item = self._item(quantity=10)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "adjust", "quantity": -4},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["quantity"], 6)
        mv = StockMovement.objects.filter(item=item).first()
        self.assertEqual(mv.quantity_delta, -4)

    def test_adjust_zero_is_rejected(self):
        item = self._item(quantity=10)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "adjust", "quantity": 0},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjust_down_cannot_go_negative(self):
        item = self._item(quantity=3)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "adjust", "quantity": -5},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)  # unchanged
        self.assertFalse(StockMovement.objects.filter(item=item).exists())

    def test_move_unknown_item_404(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("inventoryitem-move", args=["00000000-0000-0000-0000-000000000000"]),
            {"kind": "receive", "quantity": 1},
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_general_user_cannot_move(self):
        item = self._item(quantity=5)
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("inventoryitem-move", args=[item.id]),
            {"kind": "issue", "quantity": 1},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Low stock ----
    def test_low_stock_lists_items_at_or_below_threshold(self):
        self._item(sku="LOW-1", quantity=2, min_stock=5)   # low
        self._item(sku="OK-1", quantity=20, min_stock=5)   # ok
        self.client.force_authenticate(self.staff)
        res = self.client.get(reverse("inventoryitem-low-stock"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        skus = {row["sku"] for row in res.data["results"]}
        self.assertEqual(skus, {"LOW-1"})

    def test_is_low_stock_flag(self):
        item = self._item(quantity=5, min_stock=5)
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("inventoryitem-detail", args=[item.id]))
        self.assertTrue(res.data["is_low_stock"])  # quantity == min_stock is low
