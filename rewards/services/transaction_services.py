from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_DOWN
from django.core.exceptions import ValidationError

# Adapt to existing models in this project
from rewards.models import PaymentDiscountSnapshot
from courses.models import TeacherDiscountDecision, Course
from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from users.models import User
from django.conf import settings
from django.db import IntegrityError


def get_or_create_payment_snapshot(*, order_id: str | None = None, external_txn_id: str | None = None,
                                   defaults: dict, source: str = "local") -> tuple:
    """Idempotent creation of PaymentDiscountSnapshot.

    Prioritizes external_txn_id for uniqueness; falls back to order_id. Raises
    ValueError if neither key is provided. Returns (snapshot, created).
    """
    if external_txn_id:
        key = {"external_txn_id": external_txn_id}
    elif order_id:
        key = {"order_id": order_id}
    else:
        raise ValueError("external_txn_id or order_id required for idempotent snapshot creation")

    try:
        # Use select_for_update pattern if inside a transaction to avoid races
        snap, created = PaymentDiscountSnapshot.objects.get_or_create(
            **key,
            defaults={**defaults, "source": source, **key},
        )
    except IntegrityError:
        # Concurrent insert created it first - fetch the existing
        snap = PaymentDiscountSnapshot.objects.filter(**key).first()
        created = False if snap else True
    return snap, created


def get_platform_balance():
    """Return DBTeoCoinBalance instance used as platform treasury.

    Strategy: try to find a superuser/platform user via settings.PLATFORM_USER_EMAIL;
    fallback to the first superuser. Raises ValidationError if none found.
    """
    platform_email = getattr(settings, "PLATFORM_USER_EMAIL", None)
    user = None
    if platform_email:
        user = User.objects.filter(email=platform_email).first()
    if not user:
        user = User.objects.filter(is_superuser=True).first()
    if not user:
        raise ValidationError("Platform user not configured")

    bal, _ = DBTeoCoinBalance.objects.get_or_create(user=user)
    return bal


@transaction.atomic
def apply_discount_and_snapshot(*, student_user_id: int, teacher_id: int,
                                course_id: int, teo_cost: Decimal,
                                offered_teacher_teo: Decimal) -> dict:
    """
    1) Debit TEO from student's DB balance
    2) Create PaymentDiscountSnapshot (status=pending) and TeacherDiscountDecision (pending)
    Returns {snapshot_id, pending_decision_id}
    """
    if teo_cost <= 0:
        raise ValidationError("teo_cost must be > 0")
    if offered_teacher_teo < 0:
        raise ValidationError("offered_teacher_teo invalid")

    # Lock student balance for update (create if missing)
    student = User.objects.get(id=student_user_id)
    # Ensure a DBTeoCoinBalance exists for the student
    student_balance, _ = DBTeoCoinBalance.objects.get_or_create(user=student, defaults={"available_balance": Decimal("0"), "staked_balance": Decimal("0")})
    # Now lock the existing row for update
    student_balance = DBTeoCoinBalance.objects.select_for_update().get(user=student)
    if student_balance.available_balance < teo_cost:
        raise ValidationError("Insufficient TEO balance")

    # 1) Debit student
    student_balance.available_balance -= teo_cost
    student_balance.save(update_fields=["available_balance"])
    # Record DB transaction (course relation if available)
    txn_kwargs = dict(
        user=student,
        transaction_type="spent_discount",
        amount=teo_cost,
        description=f"Discount apply course_id={course_id}",
    )
    if course_id:
        txn_kwargs["course_id"] = course_id
    DBTeoCoinTransaction.objects.create(**txn_kwargs)

    # 2) Snapshot + decision
    # Create a minimal PaymentDiscountSnapshot as audit snapshot. Use an
    # idempotent helper so repeated calls (webhook + local) reuse the same row
    # when a stable key is available. Prefer external_txn_id if present.
    defaults = dict(
        course_id=course_id,
        student=student,
        teacher_id=teacher_id,
        price_eur=0,
        discount_percent=0,
        student_pay_eur=0,
        teacher_eur=0,
        platform_eur=0,
        teacher_teo=offered_teacher_teo,
        platform_teo=Decimal("0"),
        absorption_policy="teo",
        teacher_accepted_teo=Decimal("0"),
    )

    # If caller provided a stable order_id or external id, prefer it; else
    # synthesize a stable platform id based on student/course (no timestamp)
    # to allow dedup but still be human-debuggable.
    # Here we don't have external id passed in; generate a synthetic but stable id
    synthetic_order_id = f"discount_synthetic_{student_user_id}_{course_id}"
    try:
        snap, created = get_or_create_payment_snapshot(order_id=synthetic_order_id, defaults=defaults, source="local")
    except Exception:
        # Fallback to direct create if helper fails for any reason
        snapshot = PaymentDiscountSnapshot.objects.create(**{**defaults, "order_id": synthetic_order_id, "source": "local"})
        snap = snapshot
        created = True

    # Prepare fields required by TeacherDiscountDecision.clean()
    course_price = Decimal("0.01")
    commission_rate = Decimal("50.00")
    staking_tier = "Bronze"
    if course_id:
        try:
            course_obj = Course.objects.get(id=course_id)
            # Course.price_eur exists
            course_price = course_obj.price_eur if getattr(course_obj, "price_eur", None) is not None else course_price
        except Exception:
            course_obj = None

    decision = TeacherDiscountDecision.objects.create(
        teacher_id=teacher_id,
        student=student,
        course_id=course_id,
        course_price=course_price,
        discount_percentage=0,
        teo_cost=int((teo_cost * Decimal(10 ** 18)).to_integral_value()),
        teacher_bonus=int((offered_teacher_teo * Decimal(10 ** 18)).to_integral_value()),
        teacher_commission_rate=commission_rate,
        teacher_staking_tier=staking_tier,
        decision="pending",
        expires_at=timezone.now() + timezone.timedelta(hours=24),
    )

    # Do not assume snapshot has extra linking fields; best-effort: ignore

    return {"snapshot_id": snap.id, "pending_decision_id": decision.id}


@transaction.atomic
def teacher_make_decision(*, decision_id: int, accept: bool, actor=None) -> dict:
    """Process teacher decision (accept/decline) idempotently.

    - Locks the TeacherDiscountDecision row
    - If already processed, returns current state without duplicating ledger entries
    - On accept: ensures teacher DB balance, credits it, creates DB and Blockchain
      ledger rows via get_or_create to avoid duplicates
    - On decline: credits platform (if needed) and closes snapshot without creating
      discount_accept ledger entries
    """
    Q8 = Decimal("0.00000001")

    def q8(x: Decimal) -> Decimal:
        return x.quantize(Q8, rounding=ROUND_DOWN)

    decision = (
        TeacherDiscountDecision.objects.select_for_update()
        .select_related("student", "teacher", "course")
        .get(id=decision_id)
    )

    # If actor is provided, enforce it's the teacher making the call
    if actor is not None and getattr(decision, "teacher", None) != actor:
        raise ValidationError("Actor not authorized to process this decision")

    # Idempotence: if already processed, return current state
    if decision.decision != "pending":
        snapshot = (
            PaymentDiscountSnapshot.objects.filter(student=decision.student, teacher=decision.teacher, course=decision.course)
            .order_by("-created_at")
            .first()
        )
        credited_amount = Decimal(snapshot.teacher_accepted_teo) if snapshot else Decimal("0")
        return {
            "decision_id": decision.id,
            "status": decision.decision,
            "snapshot_id": getattr(snapshot, "id", None),
            "credited": str(credited_amount),
            "credited_to": "teacher" if decision.decision == "accepted" else "platform",
        }

    # Find related snapshot (most recent)
    snapshot = (
        PaymentDiscountSnapshot.objects.filter(student=decision.student, teacher=decision.teacher, course=decision.course)
        .order_by("-created_at")
        .first()
    )

    # Amount source: snapshot.teacher_teo if present, else decision.teacher_bonus/teo_cost
    if snapshot and snapshot.teacher_teo is not None:
        amount = q8(Decimal(snapshot.teacher_teo))
    else:
        amount_wei = getattr(decision, "teacher_bonus", None) or getattr(decision, "teo_cost", 0)
        amount = q8(Decimal(amount_wei) / Decimal(10 ** 18)) if amount_wei else q8(Decimal("0"))

    platform_balance = get_platform_balance()

    if accept:
        # Ensure teacher balance exists and lock it
        DBTeoCoinBalance.objects.get_or_create(user=decision.teacher, defaults={"available_balance": Decimal("0"), "staked_balance": Decimal("0")})
        teacher_balance = DBTeoCoinBalance.objects.select_for_update().get(user=decision.teacher)

        if amount > 0:
            teacher_balance.available_balance = q8(teacher_balance.available_balance + amount)
            teacher_balance.save(update_fields=["available_balance"])

            # DB ledger: avoid duplicates
            desc = f"TEO from discount snapshot_id={getattr(snapshot, 'id', None)} decision={decision.id}"
            DBTeoCoinTransaction.objects.get_or_create(
                user=decision.teacher,
                transaction_type="discount_accept",
                description=desc,
                defaults={"amount": amount, "course_id": getattr(decision, 'course_id', None)},
            )

            # Chain ledger: best-effort
            try:
                from rewards.models import BlockchainTransaction

                BlockchainTransaction.objects.get_or_create(
                    transaction_type="discount_accept",
                    related_object_id=str(decision.id),
                    defaults={
                        "user": decision.teacher,
                        "amount": amount,
                        "status": "completed",
                        "notes": f"Teacher accepted discount decision {decision.id}",
                    },
                )
            except Exception:
                pass

        decision.decision = "accepted"
        decision.teacher_payment_completed = True if amount > 0 else False
    else:
        # Decline path: credit platform if amount > 0
        if amount > 0:
            platform_balance.available_balance = q8(platform_balance.available_balance + amount)
            platform_balance.save(update_fields=["available_balance"])
            DBTeoCoinTransaction.objects.get_or_create(
                user=platform_balance.user,
                transaction_type="bonus",
                description=f"TEO from declined discount snapshot_id={getattr(snapshot, 'id', None)} decision={decision.id}",
                defaults={"amount": amount},
            )
        decision.decision = "declined"
        decision.teacher_payment_completed = False

    decision.decision_made_at = timezone.now()
    decision.save(update_fields=["decision", "decision_made_at", "teacher_payment_completed"])

    if snapshot:
        try:
            snapshot.teacher_accepted_teo = amount if accept else Decimal("0")
            snapshot.final_teacher_teo = amount if accept else Decimal("0")
            snapshot.status = "closed"
            snapshot.closed_at = timezone.now()
            snapshot.save(update_fields=["teacher_accepted_teo", "final_teacher_teo", "status", "closed_at"])
        except Exception:
            pass

    return {
        "decision_id": decision.id,
        "status": decision.decision,
        "snapshot_id": getattr(snapshot, "id", None),
        "credited": str(amount),
        "credited_to": "teacher" if accept else "platform",
    }
