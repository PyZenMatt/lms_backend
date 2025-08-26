import threading
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from courses.models import Course
from rewards.models import PaymentDiscountSnapshot, Tier

User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_confirm_idempotent():
    teacher = User.objects.create_user(username='t2', email='t2@example.com', password='pass', role='teacher')
    student = User.objects.create_user(username='s2', email='s2@example.com', password='pass', role='student')
    course = Course.objects.create(title='C2', price_eur=Decimal('100.00'), teacher=teacher)

    Tier.objects.update_or_create(name='Bronzo', defaults={
        'teacher_split_percent': Decimal('50.00'),
        'platform_split_percent': Decimal('50.00'),
        'max_accept_discount_ratio': Decimal('1.00'),
        'teo_bonus_multiplier': Decimal('1.25'),
        'is_active': True,
    })

    client = APIClient()
    client.force_authenticate(user=student)

    confirm_url = '/api/v1/rewards/discounts/confirm/'

    payload = {
        'order_id': 'pi_test_1',
        'course_id': course.id,
        'teacher_id': teacher.id,
        'student_id': student.id,
        'price_eur': '100.00',
        'discount_percent': '10',
        'accept_teo': True,
        'accept_ratio': '1.0',
    }

    resp1 = client.post(confirm_url, payload, format='json')
    assert resp1.status_code in (201,)
    body1 = resp1.json()
    assert body1.get('snapshot') is not None

    resp2 = client.post(confirm_url, payload, format='json')
    assert resp2.status_code in (200,)
    body2 = resp2.json()

    # Ensure only one snapshot exists and idempotence preserved
    assert PaymentDiscountSnapshot.objects.filter(order_id='pi_test_1').count() == 1


@pytest.mark.django_db(transaction=True)
def test_confirm_race_condition():
    teacher = User.objects.create_user(username='t3', email='t3@example.com', password='pass', role='teacher')
    student = User.objects.create_user(username='s3', email='s3@example.com', password='pass', role='student')
    course = Course.objects.create(title='C3', price_eur=Decimal('100.00'), teacher=teacher)

    Tier.objects.update_or_create(name='Bronzo', defaults={
        'teacher_split_percent': Decimal('50.00'),
        'platform_split_percent': Decimal('50.00'),
        'max_accept_discount_ratio': Decimal('1.00'),
        'teo_bonus_multiplier': Decimal('1.25'),
        'is_active': True,
    })

    client = APIClient()
    client.force_authenticate(user=student)
    confirm_url = '/api/v1/rewards/discounts/confirm/'

    payload = {
        'order_id': 'pi_test_race',
        'course_id': course.id,
        'teacher_id': teacher.id,
        'student_id': student.id,
        'price_eur': '100.00',
        'discount_percent': '10',
        'accept_teo': True,
        'accept_ratio': '1.0',
    }

    responses = []

    def do_post():
        resp = client.post(confirm_url, payload, format='json')
        responses.append(resp.status_code)

    t1 = threading.Thread(target=do_post)
    t2 = threading.Thread(target=do_post)
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Expect one 201 and one 200, no 500
    assert 500 not in responses
    assert responses.count(201) == 1
    assert responses.count(200) == 1
    assert PaymentDiscountSnapshot.objects.filter(order_id='pi_test_race').count() == 1
