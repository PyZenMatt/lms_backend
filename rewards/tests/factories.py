from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from rewards.models import PaymentDiscountSnapshot
from courses.models import Course, TeacherDiscountDecision

User = get_user_model()

TWOPLACES = Decimal("0.01")
TEOEIGHT = Decimal("0.00000001")


def q2(v: Decimal) -> Decimal:
    if isinstance(v, Decimal):
        return v.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return Decimal(str(v)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def q8(v: Decimal) -> Decimal:
    if isinstance(v, Decimal):
        return v.quantize(TEOEIGHT, rounding=ROUND_HALF_UP)
    return Decimal(str(v)).quantize(TEOEIGHT, rounding=ROUND_HALF_UP)


def make_user(username: str, role: str = "teacher", is_superuser=False, is_staff=False, email: str | None = None):
    email = email or f"{username}@example.com"
    # The project's User.create_user requires 'role' in this repo
    if is_superuser:
        return User.objects.create_superuser(username=username, email=email, password="p", role=role, is_staff=is_staff)
    return User.objects.create_user(username=username, email=email, password="p", role=role)


def make_course(title: str = "Test Course", price_eur: Decimal = Decimal("100.00"), teacher: User | None = None):
    # create a minimal Course; teacher must be provided for relation consistency
    if teacher is None:
        teacher = make_user("teacher_for_course", role="teacher")
    return Course.objects.create(title=title, description="auto-created course", teacher=teacher, price_eur=q2(price_eur))


def make_snapshot(
    teacher: User,
    student: User,
    course: Course,
    price_eur: Decimal = Decimal("100.00"),
    discount_percent: Decimal = Decimal("10.0"),
    split_teacher_ratio: Decimal = Decimal("0.50"),
    teacher_teo: Decimal = Decimal("0"),
    status: str = "pending",
):
    """
    Create a valid PaymentDiscountSnapshot with required non-null fields.
    student_pay = price * (1 - discount_percent/100)
    teacher_eur = student_pay * split_teacher_ratio
    platform_eur = student_pay - teacher_eur
    """
    price = q2(price_eur)
    disc_pct = int(discount_percent) if isinstance(discount_percent, Decimal) and discount_percent == discount_percent.to_integral_value() else int(discount_percent)
    # compute student_pay
    student_pay = q2(price * (Decimal("1") - Decimal(disc_pct) / Decimal("100")))
    teacher_eur_amt = q2(student_pay * Decimal(str(split_teacher_ratio)))
    platform_eur_amt = q2(student_pay - teacher_eur_amt)

    snap = PaymentDiscountSnapshot.objects.create(
        course=course,
        teacher=teacher,
        student=student,
        status=status,
        price_eur=price,
        discount_percent=disc_pct,
        student_pay_eur=student_pay,
        teacher_eur=teacher_eur_amt,
        platform_eur=platform_eur_amt,
        teacher_teo=q8(teacher_teo),
        platform_teo=q8(Decimal("0")),
        absorption_policy="teo",
        teacher_accepted_teo=q8(Decimal("0")),
    )
    return snap


def make_decision(snapshot: PaymentDiscountSnapshot, teacher: User, offered_teacher_teo: Decimal = Decimal("1.50"), minutes_valid: int = 30):
    """
    Create a TeacherDiscountDecision compatible with the project's model in courses.models.
    Convert offered_teacher_teo to wei (18 decimals) for teo_cost and teacher_bonus.
    """
    # convert TEO to wei as integer
    wei_multiplier = 10 ** 18
    teo_decimal = Decimal(offered_teacher_teo)
    teo_wei = int((teo_decimal * Decimal(wei_multiplier)).to_integral_value())

    decision = TeacherDiscountDecision.objects.create(
        teacher=teacher,
        student=snapshot.student,
        course=snapshot.course,
        course_price=snapshot.price_eur if snapshot and snapshot.price_eur is not None else Decimal("0.01"),
        discount_percentage=int(snapshot.discount_percent if snapshot else 0),
        teo_cost=teo_wei,
        teacher_bonus=0,
        teacher_commission_rate=Decimal("50.00"),
        teacher_staking_tier="Bronze",
        decision="pending",
        expires_at=timezone.now() + timedelta(minutes=minutes_valid),
    )
    return decision
