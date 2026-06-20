"""Smoke tests for the asset module (lifecycle, RBAC, QR lookup)."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Asset, AssetCategory

User = get_user_model()


class AssetTests(APITestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(name="Laptop", code="LT")
        self.staff = User.objects.create_user(
            email="staff@ghp.local", password="Staff@1234", role=User.Role.STAFF
        )
        self.user = User.objects.create_user(
            email="user@ghp.local", password="User@1234"
        )

    def _make_asset(self, **kwargs):
        defaults = dict(
            asset_tag="GHP-LT-0001",
            name="Dell Latitude",
            category=self.category,
        )
        defaults.update(kwargs)
        return Asset.objects.create(**defaults)

    # ---- RBAC ----
    def test_general_user_can_read_assets(self):
        self._make_asset()
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("asset-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_general_user_cannot_create_asset(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("asset-list"),
            {"asset_tag": "GHP-LT-0002", "name": "x", "category": str(self.category.id)},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_asset(self):
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("asset-list"),
            {"asset_tag": "GHP-LT-0002", "name": "x", "category": str(self.category.id)},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

    # ---- Lifecycle: assign / return ----
    def test_assign_sets_holder_and_status_and_history(self):
        asset = self._make_asset()  # status=procured
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("asset-assign", args=[asset.id]), {"holder": str(self.user.id)}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["status"], Asset.Status.IN_USE)
        self.assertEqual(str(res.data["assigned_to"]), str(self.user.id))
        # One open assignment exists.
        asset.refresh_from_db()
        self.assertEqual(asset.assignments.filter(returned_at__isnull=True).count(), 1)

    def test_reassign_closes_previous_assignment(self):
        asset = self._make_asset()
        other = User.objects.create_user(email="o@ghp.local", password="Pass@1234")
        self.client.force_authenticate(self.staff)
        self.client.post(reverse("asset-assign", args=[asset.id]), {"holder": str(self.user.id)})
        self.client.post(reverse("asset-assign", args=[asset.id]), {"holder": str(other.id)})
        asset.refresh_from_db()
        self.assertEqual(asset.assigned_to_id, other.id)
        # Exactly one open assignment; the first was closed.
        self.assertEqual(asset.assignments.filter(returned_at__isnull=True).count(), 1)
        self.assertEqual(asset.assignments.count(), 2)

    def test_return_clears_holder_and_status(self):
        asset = self._make_asset()
        self.client.force_authenticate(self.staff)
        self.client.post(reverse("asset-assign", args=[asset.id]), {"holder": str(self.user.id)})
        res = self.client.post(reverse("asset-return", args=[asset.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertIsNone(res.data["assigned_to"])
        self.assertEqual(res.data["status"], Asset.Status.IN_STORE)

    def test_return_when_not_assigned_is_rejected(self):
        asset = self._make_asset()
        self.client.force_authenticate(self.staff)
        res = self.client.post(reverse("asset-return", args=[asset.id]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_rejects_unknown_holder(self):
        asset = self._make_asset()
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("asset-assign", args=[asset.id]),
            {"holder": "00000000-0000-0000-0000-000000000000"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_rejects_malformed_holder(self):
        asset = self._make_asset()
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("asset-assign", args=[asset.id]), {"holder": "not-a-uuid"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_assign_scrapped_asset(self):
        asset = self._make_asset(status=Asset.Status.SCRAPPED)
        self.client.force_authenticate(self.staff)
        res = self.client.post(
            reverse("asset-assign", args=[asset.id]), {"holder": str(self.user.id)}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_user_cannot_assign(self):
        asset = self._make_asset()
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("asset-assign", args=[asset.id]), {"holder": str(self.user.id)}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ---- QR / barcode lookup ----
    def test_lookup_by_tag_returns_asset(self):
        self._make_asset(asset_tag="GHP-LT-9999")
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("asset-lookup"), {"tag": "GHP-LT-9999"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["asset_tag"], "GHP-LT-9999")
        self.assertIn("maintenance_records", res.data)

    def test_lookup_unknown_tag_404(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("asset-lookup"), {"tag": "NOPE"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_lookup_requires_tag(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("asset-lookup"))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Holder picker ----
    def test_staff_can_list_holders(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get(reverse("asset-holders"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        emails = {row["email"] for row in res.data}
        self.assertIn("user@ghp.local", emails)  # any active user can hold

    def test_general_user_cannot_list_holders(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("asset-holders"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
