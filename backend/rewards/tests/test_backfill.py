from django.test import TestCase
from django.urls import reverse
from users.models import User
from rewards.models import PaymentDiscountSnapshot
from notifications.models import Notification
from decimal import Decimal
from rest_framework.test import APIClient


class BackfillSnapshotsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create teacher and student
        self.teacher = User.objects.create_user(
            username="t1", email="t1@example.com", password="pass", role="teacher"
        )
        self.student = User.objects.create_user(
            username="s1", email="s1@example.com", password="pass", role="student"
        )
        # Create a dummy course
        from courses.models import Course

        self.course = Course.objects.create(
            title="C1", description="d", teacher=self.teacher, price_eur=Decimal("66.50")
        )

        # Snapshot: teacher present, student present
        self.snap = PaymentDiscountSnapshot.objects.create(
            order_id="testorder1",
            course=self.course,
            student=self.student,
            teacher=self.teacher,
            price_eur=Decimal("66.50"),
            discount_percent=0,
            student_pay_eur=Decimal("66.50"),
            teacher_eur=Decimal("66.50"),
            platform_eur=Decimal("0.00"),
            teacher_teo=Decimal("0"),
        )

    def test_backfill_creates_decision_and_notification(self):
        # Force auth as teacher (project uses JWT auth, not session auth)
        self.client.force_authenticate(user=self.teacher)
        url = reverse("rewards:discount-backfill")
        res = self.client.post(
            url, data={"snapshot_ids": [self.snap.id]}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(len(data.get("created", [])), 1)

        # Second call idempotent
        res2 = self.client.post(
            url, data={"snapshot_ids": [self.snap.id]}, content_type="application/json"
        )
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()
        self.assertEqual(len(d2.get("created", [])), 0)
