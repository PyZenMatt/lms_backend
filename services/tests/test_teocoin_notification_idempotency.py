from django.test import TestCase
from django.contrib.auth import get_user_model
from notifications.services import TeoCoinDiscountNotificationService
from notifications.models import Notification
from courses.models import TeacherDiscountDecision
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class TeoCoinNotificationIdempotencyTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", email="t1@test.com", password="t", role="teacher")
        self.student = User.objects.create_user(username="s1", email="s1@test.com", password="t", role="student")
        # create a course for FK
        from courses.models import Course
        self.course = Course.objects.create(title="C1", description="d", teacher=self.teacher, price_eur=Decimal("100.00"))

    def test_pending_idempotent_by_decision(self):
        svc = TeoCoinDiscountNotificationService()
        # create a decision record
        dec = TeacherDiscountDecision.objects.create(
            teacher=self.teacher,
            student=self.student,
            course=self.course,
            course_price=Decimal("100.00"),
            discount_percentage=10,
            teo_cost=1000000000000000000, # 1 TEO in wei
            teacher_bonus=0,
            teacher_commission_rate=Decimal("10.00"),
            teacher_staking_tier="basic",
            expires_at=timezone.now() + timezone.timedelta(minutes=60),
        )

        # call notify twice with same decision_id
        ok1 = svc.notify_teacher_discount_pending(
            teacher=self.teacher,
            student=self.student,
            course_title="C1",
            discount_percent=10,
            teo_cost=1.0,
            teacher_bonus=0.0,
            request_id=999,
            expires_at=dec.expires_at,
            decision_id=dec.id,
            offered_teacher_teo=None,
        )
        ok2 = svc.notify_teacher_discount_pending(
            teacher=self.teacher,
            student=self.student,
            course_title="C1",
            discount_percent=10,
            teo_cost=1.0,
            teacher_bonus=0.0,
            request_id=999,
            expires_at=dec.expires_at,
            decision_id=dec.id,
            offered_teacher_teo=None,
        )

        self.assertTrue(ok1)
        self.assertTrue(ok2)
        # There should be exactly one pending notification for this decision and teacher
        notifications = Notification.objects.filter(user=self.teacher, notification_type="teocoin_discount_pending", related_object_id=dec.id)
        self.assertEqual(notifications.count(), 1)
