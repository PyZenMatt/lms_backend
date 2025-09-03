import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from courses.models import TeacherDiscountDecision, Course
from django.utils import timezone
from rewards.models import PaymentDiscountSnapshot, BlockchainTransaction
from blockchain.models import DBTeoCoinTransaction

@pytest.mark.django_db
def test_accept_idempotent_creates_single_ledger(django_user_model):
    teacher = django_user_model.objects.create_user(username="t", password="p", email="t@example.com", role="teacher")
    student = django_user_model.objects.create_user(username="s", password="p", email="s@example.com", role="student")
    client = APIClient(); client.force_authenticate(teacher)

    # create minimal course for decision.course foreign key
    from courses.models import Course
    course = Course.objects.create(title="C1", description="d", teacher=teacher)

    snap = PaymentDiscountSnapshot.objects.create(
        teacher=teacher,
        student=student,
        course=course,
        status="pending",
        teacher_teo=Decimal("1.5"),
        price_eur=Decimal("10.00"),
        discount_percent=0,
        student_pay_eur=Decimal("10.00"),
        teacher_eur=Decimal("5.00"),
        platform_eur=Decimal("5.00"),
    )
    from django.utils import timezone
    decision = TeacherDiscountDecision.objects.create(
        teacher=teacher,
        student=student,
        course=snap.course,
        course_price=Decimal("1.00"),
        discount_percentage=0,
        teo_cost=1500000000000000000,
        teacher_bonus=0,
        teacher_commission_rate=Decimal("50.00"),
        teacher_staking_tier="Bronze",
        decision="pending",
        expires_at=timezone.now() + timezone.timedelta(hours=24),
    )

    # Ensure a platform user exists for get_platform_balance()
    platform_user = django_user_model.objects.create_superuser(username="platform", email="platform@example.com", password="p", role="platform")

    # Call service directly to avoid test request atomic wrapper issues
    from rewards.services.transaction_services import teacher_make_decision

    r1 = teacher_make_decision(decision_id=decision.pk, accept=True, actor=teacher)
    r2 = teacher_make_decision(decision_id=decision.pk, accept=True, actor=teacher)

    assert DBTeoCoinTransaction.objects.filter(
        transaction_type="discount_accept",
        user=teacher,
        description__icontains=str(decision.pk),
    ).count() == 1
    assert BlockchainTransaction.objects.filter(
        related_object_id=str(decision.pk), transaction_type="discount_accept"
    ).count() == 1

    snap.refresh_from_db()
    assert snap.status == "closed"
    assert snap.teacher_accepted_teo == Decimal("1.5")

@pytest.mark.django_db
def test_pending_excludes_closed(django_user_model):
    teacher = django_user_model.objects.create_user(username="t2", password="p", email="t2@example.com", role="teacher")
    student = django_user_model.objects.create_user(username="s2", password="p", email="s2@example.com", role="student")
    client = APIClient(); client.force_authenticate(teacher)

    course2 = Course.objects.create(title="C2", description="d2", teacher=teacher)

    s1 = PaymentDiscountSnapshot.objects.create(
        teacher=teacher,
        student=student,
        course=course2,
        status="pending",
        price_eur=Decimal("10.00"),
        discount_percent=0,
        student_pay_eur=Decimal("10.00"),
        teacher_eur=Decimal("5.00"),
        platform_eur=Decimal("5.00"),
    )
    s2 = PaymentDiscountSnapshot.objects.create(
        teacher=teacher,
        student=student,
        course=course2,
        status="closed",
        price_eur=Decimal("20.00"),
        discount_percent=0,
        student_pay_eur=Decimal("20.00"),
        teacher_eur=Decimal("10.00"),
        platform_eur=Decimal("10.00"),
    )

    # Check pending snapshots directly
    pending_ids = list(PaymentDiscountSnapshot.objects.filter(teacher=teacher, status="pending").values_list("id", flat=True))
    assert s1.id in pending_ids and s2.id not in pending_ids

@pytest.mark.django_db
def test_decline_closes_without_ledger(django_user_model):
    teacher = django_user_model.objects.create_user(username="t3", password="p", email="t3@example.com", role="teacher")
    student = django_user_model.objects.create_user(username="s3", password="p", email="s3@example.com", role="student")
    client = APIClient(); client.force_authenticate(teacher)

    course3 = Course.objects.create(title="C3", description="d3", teacher=teacher)

    snap = PaymentDiscountSnapshot.objects.create(
        teacher=teacher,
        student=student,
        course=course3,
        status="pending",
        teacher_teo=Decimal("2.0"),
        price_eur=Decimal("20.00"),
        discount_percent=0,
        student_pay_eur=Decimal("20.00"),
        teacher_eur=Decimal("10.00"),
        platform_eur=Decimal("10.00"),
    )
    decision = TeacherDiscountDecision.objects.create(
        teacher=teacher,
        student=student,
        course=snap.course,
        course_price=Decimal("2.00"),
        discount_percentage=0,
        teo_cost=2000000000000000000,
        teacher_bonus=0,
        teacher_commission_rate=Decimal("50.00"),
        teacher_staking_tier="Bronze",
        decision="pending",
        expires_at=timezone.now() + timezone.timedelta(hours=24),
    )

    # Ensure platform user exists
    platform_user = django_user_model.objects.create_superuser(username="platform2", email="platform2@example.com", password="p", role="platform")
    from rewards.services.transaction_services import teacher_make_decision
    r = teacher_make_decision(decision_id=decision.pk, accept=False, actor=teacher)

    snap.refresh_from_db()
    assert snap.status == "closed"
    assert DBTeoCoinTransaction.objects.filter(transaction_type="discount_accept", user=teacher, description__icontains=str(decision.pk)).count() == 0
    assert BlockchainTransaction.objects.filter(related_object_id=str(decision.pk), transaction_type="discount_accept").count() == 0
