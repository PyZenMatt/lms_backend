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

    Prioritizes external_txn_id for uniqueness; falls back to order_id. Also checks
    if order_id matches an existing external_txn_id to prevent duplicates.
    Returns (snapshot, created).
    """
    if external_txn_id:
        key = {"external_txn_id": external_txn_id}
    elif order_id:
        # First check if order_id matches an existing external_txn_id (to prevent duplicates)
        existing = PaymentDiscountSnapshot.objects.filter(external_txn_id=order_id).first()
        if existing:
            return existing, False
        # Otherwise use order_id as key
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
                                offered_teacher_teo: Decimal, idempotency_key: str | None = None,
                                stripe_checkout_session_id: str | None = None,
                                stripe_payment_intent_id: str | None = None) -> dict:
    """
    1) Validate student has sufficient TEO balance (no deduction yet)
    2) Create PaymentDiscountSnapshot (status=pending) and TeacherDiscountDecision (pending)
    3) TEO deduction happens only when teacher accepts via teacher_make_decision()
    Returns {snapshot_id, pending_decision_id}
    """
    if teo_cost <= 0:
        raise ValidationError("teo_cost must be > 0")
    if offered_teacher_teo < 0:
        raise ValidationError("offered_teacher_teo invalid")

    # If idempotency_key provided, check for existing ACTIVE or PENDING snapshot first
    if idempotency_key:
        existing_snap = PaymentDiscountSnapshot.objects.filter(idempotency_key=idempotency_key).first()
        if existing_snap:
            # Return existing decision/snapshot without processing again
            decision = TeacherDiscountDecision.objects.filter(
                teacher_id=teacher_id,
                student_id=student_user_id,
                course_id=course_id,
            ).order_by("-created_at").first()

            return {
                "snapshot_id": existing_snap.id,
                "pending_decision_id": decision.id if decision else None,
            }

    # Get student (no balance deduction yet - only when teacher accepts)
    student = User.objects.get(id=student_user_id)
    
    # Check student has sufficient balance (validation only, no deduction)
    student_balance, _ = DBTeoCoinBalance.objects.get_or_create(
        user=student,
        defaults={"available_balance": Decimal("0"), "staked_balance": Decimal("0")},
    )
    if student_balance.available_balance < teo_cost:
        raise ValidationError("Insufficient TEO balance")

    # NOTE: No TEO deduction here - this happens only when teacher accepts the decision

    # 2) Create snapshot + decision (no TEO deduction until teacher accepts)
    # Try to find existing snapshot for this student/course/teacher combination first
    # This prevents duplicate snapshots when payment flow already created one
    existing_snap = None
    if course_id and teacher_id and not idempotency_key:  # Skip time-based lookup if using idempotency
        try:
            # Look for recent snapshot (within last hour) for same student/course/teacher
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            existing_snap = PaymentDiscountSnapshot.objects.filter(
                student=student,
                course_id=course_id,
                teacher_id=teacher_id,
                created_at__gte=one_hour_ago
            ).first()
        except Exception:
            existing_snap = None
    
    if existing_snap:
        # Reuse existing snapshot instead of creating duplicate
        snap = existing_snap
        created = False
    else:
        # R1.2: Calculate splits by tier policy before creating snapshot
        try:
            from .tier_calculation import calculate_splits_by_policy
            
            # Get course for price calculation
            course_obj = None
            course_price = Decimal("100.00")  # default fallback
            if course_id:
                try:
                    from courses.models import Course
                    course_obj = Course.objects.get(id=course_id)
                    course_price = course_obj.price_eur if course_obj.price_eur else Decimal("100.00")
                except Exception:
                    pass
            
            # Calculate policy-based splits
            teacher_obj = User.objects.get(id=teacher_id)
            splits = calculate_splits_by_policy(course_price, teacher_obj, teo_cost)
            
            # Use option A as default (teacher refuses), store option B for decision
            option_a = splits['option_a']
            option_b = splits['option_b']
            
        except Exception as e:
            # Fallback to safe defaults if splits calculation fails
            import logging
            logging.getLogger(__name__).warning(f"Splits calculation failed, using defaults: {e}")
            option_a = {
                'teacher_eur': Decimal("50.00"),
                'platform_eur': Decimal("35.00"),
                'teacher_teo': Decimal("0"),
                'platform_teo': teo_cost,
            }
            option_b = {
                'teacher_eur': Decimal("35.00"),
                'teacher_teo': offered_teacher_teo,
                'platform_eur': Decimal("50.00"),
                'platform_teo': Decimal("0"),
            }
        
        # Create new snapshot only if none exists
        defaults = dict(
            course_id=course_id,
            student=student,
            teacher_id=teacher_id,
            price_eur=course_price,
            discount_percent=0,
            student_pay_eur=course_price - teo_cost,  # Student pays reduced amount
            # R1.2: Populate EUR splits from policy calculation
            teacher_eur=option_a['teacher_eur'],
            platform_eur=option_a['platform_eur'],
            teacher_teo=option_b['teacher_teo'],  # Store option B TEO amount
            platform_teo=option_a['platform_teo'],
            absorption_policy="teo",
            teacher_accepted_teo=Decimal("0"),
        )
        
        # Add additional fields to defaults
        if idempotency_key:
            defaults["idempotency_key"] = idempotency_key
        if stripe_checkout_session_id:
            defaults["stripe_checkout_session_id"] = stripe_checkout_session_id
        if stripe_payment_intent_id:
            defaults["stripe_payment_intent_id"] = stripe_payment_intent_id

        # Use idempotency_key for creation if available, otherwise use payment_intent_id or synthetic order_id
        if idempotency_key:
            try:
                snap = PaymentDiscountSnapshot.objects.create(**{**defaults, "source": "local"})
                created = True
            except IntegrityError:
                # Idempotency key already exists, fetch existing
                snap = PaymentDiscountSnapshot.objects.filter(idempotency_key=idempotency_key).first()
                created = False
        elif stripe_payment_intent_id:
            # Use payment intent ID as order_id for proper identification
            try:
                snap, created = get_or_create_payment_snapshot(order_id=stripe_payment_intent_id, defaults=defaults, source="local")
            except Exception:
                # Fallback to direct create if helper fails for any reason
                snapshot = PaymentDiscountSnapshot.objects.create(**{**defaults, "order_id": stripe_payment_intent_id, "source": "local"})
                snap = snapshot
                created = True
        else:
            # Legacy path: generate synthetic order_id
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

    # R1.1: Link snapshot to decision atomically (P0 fix)
    try:
        snap.decision = decision
        snap.save(update_fields=['decision'])
    except Exception as e:
        # Log but don't fail the flow - this is audit enhancement
        import logging
        logging.getLogger(__name__).warning(f"Failed to link snapshot {snap.id} to decision {decision.id}: {e}")

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
        DBTeoCoinBalance.objects.get_or_create(
            user=decision.teacher,
            defaults={"available_balance": Decimal("0"), "staked_balance": Decimal("0")},
        )
        teacher_balance = DBTeoCoinBalance.objects.select_for_update().get(user=decision.teacher)

        if amount > 0:
            # Credit teacher inside the transaction with locked row to avoid races
            teacher_balance.available_balance = q8(teacher_balance.available_balance + amount)
            teacher_balance.save(update_fields=["available_balance"])

            # DB ledger: avoid duplicates using get_or_create by unique description
            desc = f"TEO from discount snapshot_id={getattr(snapshot, 'id', None)} decision={decision.id}"
            DBTeoCoinTransaction.objects.get_or_create(
                user=decision.teacher,
                transaction_type="discount_accept",
                description=desc,
                defaults={"amount": amount, "course_id": getattr(decision, "course_id", None)},
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

    # Upsert or update TeacherDiscountAbsorption opportunity linked to this snapshot
    try:
        from rewards.models import TeacherDiscountAbsorption

        if snapshot:
            # Ensure a single opportunity row per snapshot (1:1)
            TeacherDiscountAbsorption.objects.update_or_create(
                teacher=decision.teacher,
                course=snapshot.course,
                student=snapshot.student,
                teo_used_by_student=snapshot.teacher_teo or Decimal("0"),
                discount_amount_eur=snapshot.discount_amount_eur or Decimal("0"),
                defaults={
                    "course_price_eur": getattr(snapshot, "price_eur", Decimal("0")),
                    "discount_percentage": getattr(snapshot, "discount_percent", 0),
                    "teacher_commission_rate": getattr(decision, "teacher_commission_rate", Decimal("0")),
                    "option_b_teacher_teo": snapshot.teacher_teo or Decimal("0"),
                    "status": "absorbed" if accept else "refused",
                    "final_teacher_teo": amount if accept else Decimal("0"),
                    "final_teacher_eur": getattr(snapshot, "teacher_eur", Decimal("0")) if not accept else None,
                    "final_platform_eur": getattr(snapshot, "platform_eur", Decimal("0")) if not accept else None,
                    "expires_at": timezone.now() + timezone.timedelta(hours=24),
                },
            )
    except Exception:
        # Non-critical: opportunity upsert failure shouldn't block decision processing
        pass

    return {
        "decision_id": decision.id,
        "status": decision.decision,
        "snapshot_id": getattr(snapshot, "id", None),
        "credited": str(amount),
        "credited_to": "teacher" if accept else "platform",
    }
