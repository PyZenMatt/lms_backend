from decimal import Decimal
from rest_framework.test import APIClient
from django.test import TestCase, override_settings

from users.models import User
from courses.models import Course
from rewards.models import PaymentDiscountSnapshot, Tier


class DiscountViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create teacher and student with roles required by custom User model
        self.teacher = User.objects.create_user(
            username="t1", email="t1@example.com", password="pass", role="teacher"
        )
        self.student = User.objects.create_user(
            username="s1", email="s1@example.com", password="pass", role="student"
        )
        # ensure Bronze tier exists
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
        # create course
        self.course = Course.objects.create(
            title="C1", description="d", teacher=self.teacher, price_eur=Decimal("100.00")
        )

    @override_settings(TEOCOIN_EUR_RATE=1)
    def test_confirm_returns_offered_teacher_teo(self):
        # authenticate as student
        self.client.force_authenticate(self.student)

        payload = {
            "order_id": "test_order_1",
            "course_id": self.course.id,
            "price_eur": "100.00",
            "discount_percent": "10",
            "accept_teo": False,
            "teacher_id": self.teacher.id,
        }

        res = self.client.post("/api/v1/rewards/discounts/confirm/", payload, format="json")
        self.assertIn(res.status_code, (200, 201))
        data = res.data
        snapshot = data.get("snapshot")
        self.assertIsNotNone(snapshot)
        offered = snapshot.get("offered_teacher_teo")
        # Expect 12.50000000 for Bronze 100€ 10%
        self.assertEqual(str(offered), "12.50000000")

    @override_settings(TEOCOIN_EUR_RATE=1)
    def test_pending_list_contains_offered(self):
        # create snapshot directly
        PaymentDiscountSnapshot.objects.create(
            order_id="pi_test_pending",
            course=self.course,
            student=self.student,
            teacher=self.teacher,
            price_eur=Decimal("100.00"),
            discount_percent=10,
            student_pay_eur=Decimal("90.00"),
            teacher_eur=Decimal("50.00"),
            platform_eur=Decimal("50.00"),
            teacher_teo=Decimal("0"),
            platform_teo=Decimal("0"),
        )

        self.client.force_authenticate(self.teacher)
        res = self.client.get("/api/v1/rewards/discounts/pending/")
        self.assertEqual(res.status_code, 200)
        items = res.data
        # find our snapshot
        found = [i for i in items if i.get("order_id") == "pi_test_pending"]
        self.assertTrue(found)
        item = found[0]
        self.assertIn("offered_teacher_teo", item)
        self.assertEqual(item.get("offered_teacher_teo"), "12.50000000")
import threading
import time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from rewards.models import PaymentDiscountSnapshot, Tier
from courses.models import Course


User = get_user_model()


@override_settings(TEOCOIN_EUR_RATE=1)
@pytest.mark.django_db(transaction=True)
def test_preview_happy_path(db):
    # setup
    teacher = User.objects.create_user(username='t1', email='t1@example.com', password='pass', role='teacher')
    student = User.objects.create_user(username='s1', email='s1@example.com', password='pass', role='student')
    course = Course.objects.create(title='C1', price_eur=Decimal('100.00'), teacher=teacher)

    # ensure Bronze tier
    Tier.objects.update_or_create(name='Bronzo', defaults={
        'teacher_split_percent': Decimal('50.00'),
        'platform_split_percent': Decimal('50.00'),
        'max_accept_discount_ratio': Decimal('1.00'),
        'teo_bonus_multiplier': Decimal('1.25'),
        'is_active': True,
    })

    client = APIClient()
    client.force_authenticate(user=student)

    url = '/api/v1/rewards/discounts/preview/'
    payload = {
        'course_id': course.id,
        'teacher_id': teacher.id,
        'student_id': student.id,
        'price_eur': '100.00',
        'discount_percent': '10',
        'accept_teo': False,
    }

    resp = client.post(url, payload, format='json')
    assert resp.status_code == 200
    data = resp.json().get('data')
    assert data is not None
    assert data['student_pay_eur'] == '90.00'
    assert data['teacher_eur'] == '50.00'
    assert data['platform_eur'] == '40.00'
    assert data['teacher_teo'] == '0.00000000'
    assert data['platform_teo'] == '10.00000000'


@pytest.mark.django_db
def test_preview_invalid():
    user = User.objects.create_user(username='u2', email='u2@example.com', password='pass', role='student')
    client = APIClient()
    client.force_authenticate(user=user)
    url = '/api/v1/rewards/discounts/preview/'
    payload = {
        'price_eur': '100.00',
        'discount_percent': '200',
    }
    resp = client.post(url, payload, format='json')
    assert resp.status_code == 422
    body = resp.json()
    assert 'errors' in body or 'detail' in body

