from decimal import Decimal
from rest_framework.test import APIClient
import pytest
from django.test import TestCase, override_settings

from users.models import User
from courses.models import Course
from rewards.models import PaymentDiscountSnapshot
from services.db_teocoin_service import db_teocoin_service


class ConfirmHoldTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher = User.objects.create_user(username="t_hold", email="t_hold@example.com", password="pass", role="teacher")
        self.student = User.objects.create_user(username="s_hold", email="s_hold@example.com", password="pass", role="student")
        self.course = Course.objects.create(title="C_hold", price_eur=Decimal("50.00"), teacher=self.teacher)
        # credit student with some TEO
        db_teocoin_service.add_balance(self.student, Decimal("20.00"), transaction_type="test_credit", description="credit")

    @override_settings(TEOCOIN_EUR_RATE=1)
    def test_hold_on_click(self):
        self.client.force_authenticate(self.student)
        pre_balance = db_teocoin_service.get_available_balance(self.student)

        payload = {
            "order_id": "hold_test_1",
            "course_id": self.course.id,
            "price_eur": "50.00",
            "discount_percent": "10",
            "accept_teo": False,
            "teacher_id": self.teacher.id,
        }

        res = self.client.post("/api/v1/rewards/discounts/confirm/", payload, format="json")
        assert res.status_code in (200, 201)
        data = res.json()
        assert data.get("status") == "pending"
        # Balance should not be decremented at hold time
        post_balance = db_teocoin_service.get_available_balance(self.student)
        assert post_balance == pre_balance

    @override_settings(TEOCOIN_EUR_RATE=1)
    def test_confirm_idempotent(self):
        self.client.force_authenticate(self.student)
        payload = {
            "order_id": "idemp_test_1",
            "course_id": self.course.id,
            "price_eur": "50.00",
            "discount_percent": "10",
            "accept_teo": False,
            "teacher_id": self.teacher.id,
            "checkout_session_id": "sess-123",
        }

        res1 = self.client.post("/api/v1/rewards/discounts/confirm/", payload, format="json")
        assert res1.status_code in (200, 201)
        data1 = res1.json()
        self.assertIsNotNone = lambda x: x is not None
        snapshot1 = data1.get("snapshot")
        assert snapshot1 is not None

        # Send same request again - should return existing snapshot and created=False
        res2 = self.client.post("/api/v1/rewards/discounts/confirm/", payload, format="json")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2.get("created") is False
        snap2 = data2.get("snapshot")
        assert snap2.get("id") == snapshot1.get("id")
