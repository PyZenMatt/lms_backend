from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework import serializers

from users.models import User
from courses.models import Course, TeacherDiscountDecision
from rewards.models import PaymentDiscountSnapshot, Tier
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationSerializerDiscountTests(TestCase):
    @override_settings(TEOCOIN_EUR_RATE=1)
    def test_discount_pending_includes_offered_and_decision_id(self):
        teacher = User.objects.create_user(
            username="t1", email="t1@example.com", password="pass", role="teacher"
        )
        student = User.objects.create_user(
            username="s1", email="s1@example.com", password="pass", role="student"
        )

        # Ensure an active Bronze-like tier exists
        Tier.objects.update_or_create(
            name="Bronzo",
            defaults={
                "teacher_split_percent": Decimal("50.00"),
                "platform_split_percent": Decimal("50.00"),
                "max_accept_discount_ratio": Decimal("1.00"),
                "teo_bonus_multiplier": Decimal("1.25"),
                "is_active": True,
            },
        )

        course = Course.objects.create(
            title="C1", description="d", teacher=teacher, price_eur=Decimal("100.00")
        )

        # Create a snapshot with tier details copied so serializers can compute offered values
        snap = PaymentDiscountSnapshot.objects.create(
            order_id="ord-123",
            course=course,
            student=student,
            teacher=teacher,
            price_eur=Decimal("100.00"),
            discount_percent=10,
            student_pay_eur=Decimal("90.00"),
            teacher_eur=Decimal("50.00"),
            platform_eur=Decimal("40.00"),
            teacher_teo=Decimal("0"),
            platform_teo=Decimal("10"),
            tier_name="Bronzo",
            tier_teacher_split_percent=Decimal("50.00"),
            tier_platform_split_percent=Decimal("50.00"),
            tier_max_accept_discount_ratio=Decimal("1.00"),
            tier_teo_bonus_multiplier=Decimal("1.25"),
        )

        # Pending decision for the same trio
        from django.utils import timezone
        decision = TeacherDiscountDecision.objects.create(
            teacher=teacher,
            student=student,
            course=course,
            course_price=snap.price_eur,
            discount_percentage=snap.discount_percent,
            teo_cost=0,
            teacher_bonus=0,
            teacher_commission_rate=Decimal("50.00"),
            teacher_staking_tier="Bronzo",
            decision="pending",
            expires_at=timezone.now(),
        )

        notif = Notification.objects.create(
            user=teacher,
            message="pending",
            notification_type="teocoin_discount_pending",
            related_object_id=snap.id,
        )

        data = NotificationSerializer(notif).data
        # Offered teacher TEO for 100 EUR, 10% discount, Bronze 1.25x bonus => 12.5 TEO
        assert data.get("offered_teacher_teo") == "12.50000000"
        # decision_id is resolved
        assert data.get("decision_id") == decision.id
