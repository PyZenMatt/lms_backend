import threading
import time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from rewards.models import PaymentDiscountSnapshot, Tier
from courses.models import Course


User = get_user_model()


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

