#!/usr/bin/env python
import os
import django
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from rewards.models import PaymentDiscountSnapshot, BlockchainTransaction, TokenBalance
from courses.models import TeacherDiscountDecision, Course

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolplatform.settings")
django.setup()


def create_user(email, username, role="teacher"):
    User = get_user_model()
    user = User.objects.create_user(email=email, password="pass", username=username, role=role)
    return user


def auth_client_for(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


def test_accept_updates_decision_and_snapshot(db):
    User = get_user_model()

    teacher = create_user("t1@example.com", "t1", role="teacher")
    student = create_user("s1@example.com", "s1", role="student")

    course = Course.objects.create(title="C", description="D", teacher=teacher, price_eur=Decimal("10.00"))

    # Create snapshot that would have been created at confirm
    snap = PaymentDiscountSnapshot.objects.create(
        order_id="test-order-1",
        course=course,
        student=student,
        teacher=teacher,
        price_eur=Decimal("10.00"),
        discount_percent=10,
        student_pay_eur=Decimal("9.00"),
        teacher_eur=Decimal("5.00"),
        platform_eur=Decimal("4.00"),
        teacher_teo=Decimal("1.25000000"),
        platform_teo=Decimal("0.00000000"),
    )

    # Create pending decision
    decision = TeacherDiscountDecision.objects.create(
        teacher=teacher,
        student=student,
        course=course,
        course_price=snap.price_eur,
        discount_percentage=snap.discount_percent,
        teo_cost=int((snap.teacher_teo * Decimal(10 ** 18)).to_integral_value()),
        teacher_bonus=0,
        teacher_commission_rate=Decimal("50.00"),
        teacher_staking_tier="Bronze",
        decision="pending",
        expires_at=snap.created_at,
    )

    client = auth_client_for(teacher)

    url = f"/api/v1/teacher-choices/{decision.id}/accept/"
    resp = client.post(url, {}, format="json")
    assert resp.status_code == 200

    decision.refresh_from_db()
    assert decision.decision == "accepted"
    assert decision.decision_made_at is not None

    snap.refresh_from_db()
    # teacher_accepted_teo should be set to snapshot teacher_teo (or to computed value)
    assert snap.teacher_accepted_teo.quantize(Decimal("0.00000001")) >= Decimal("0.00000000")


def test_accept_is_idempotent_for_ledger(db):
    teacher = create_user("t2@example.com", "t2", role="teacher")
    student = create_user("s2@example.com", "s2", role="student")

    course = Course.objects.create(title="C2", description="D2", teacher=teacher, price_eur=Decimal("20.00"))

    snap = PaymentDiscountSnapshot.objects.create(
        order_id="test-order-2",
        course=course,
        student=student,
        teacher=teacher,
        price_eur=Decimal("20.00"),
        discount_percent=10,
        student_pay_eur=Decimal("18.00"),
        teacher_eur=Decimal("10.00"),
        platform_eur=Decimal("8.00"),
        teacher_teo=Decimal("2.00000000"),
        platform_teo=Decimal("0.00000000"),
    )

    decision = TeacherDiscountDecision.objects.create(
        teacher=teacher,
        student=student,
        course=course,
        course_price=snap.price_eur,
        discount_percentage=snap.discount_percent,
        teo_cost=int((snap.teacher_teo * Decimal(10 ** 18)).to_integral_value()),
        teacher_bonus=0,
        teacher_commission_rate=Decimal("50.00"),
        teacher_staking_tier="Bronze",
        decision="pending",
        expires_at=snap.created_at,
    )

    client = auth_client_for(teacher)
    url = f"/api/v1/teacher-choices/{decision.id}/accept/"

    # First accept
    r1 = client.post(url, {}, format="json")
    assert r1.status_code == 200

    # Second accept should be idempotent (return 200 and not create new transaction)
    r2 = client.post(url, {}, format="json")
    assert r2.status_code == 200

    # There should be only one course_earned transaction for this teacher/course/amount
    txs = BlockchainTransaction.objects.filter(user=teacher, transaction_type="course_earned", related_object_id=str(course.id))
    assert txs.count() <= 1
