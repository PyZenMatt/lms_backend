from decimal import Decimal
import logging

from django.db import transaction, IntegrityError, OperationalError
import time
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from services.discount_calc import compute_discount_breakdown
from typing import Any, Dict, Optional, cast
from rewards.models import PaymentDiscountSnapshot, Tier
from rewards.services.transaction_services import get_or_create_payment_snapshot, apply_discount_and_snapshot
from rewards.services.transaction_services import teacher_make_decision
from users.models import User
from courses.models import Course
from rewards.serializers import (
    DiscountPreviewInputSerializer,
    DiscountConfirmInputSerializer,
    DiscountBreakdownSerializer,
    PaymentDiscountSnapshotSerializer,
)
from drf_spectacular.utils import extend_schema
from services.db_teocoin_service import db_teocoin_service
from math import ceil
from django.conf import settings
from notifications.services import teocoin_notification_service
from core.decorators.web3_gate import require_web3_enabled

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@extend_schema(
    operation_id="rewards_discounts_preview_create",
    request=DiscountPreviewInputSerializer,
    responses={200: DiscountBreakdownSerializer},
)
def preview_discount(request):
    serializer = DiscountPreviewInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "errors": serializer.errors}, status=422)

    data = cast(Dict[str, Any], serializer.validated_data)

    # Resolve tier based on teacher_id if present
    tier = None
    teacher_id = data.get("teacher_id")
    if teacher_id:
        try:
            teacher = User.objects.get(id=int(teacher_id))
            tp = getattr(teacher, "teacher_profile", None)
            if tp:
                tier_obj = Tier.objects.filter(name=tp.staking_tier, is_active=True).first()
                if tier_obj:
                    tier = {
                        "teacher_split_percent": tier_obj.teacher_split_percent,
                        "platform_split_percent": tier_obj.platform_split_percent,
                        "max_accept_discount_ratio": tier_obj.max_accept_discount_ratio,
                        "teo_bonus_multiplier": tier_obj.teo_bonus_multiplier,
                        "name": tier_obj.name,
                    }
        except Exception:
            tier = None

    result = compute_discount_breakdown(
        price_eur=data["price_eur"],
        discount_percent=data.get("discount_percent", 0),
        tier=tier,
        accept_teo=data.get("accept_teo", False),
        accept_ratio=data.get("accept_ratio", None),
    )

    out = DiscountBreakdownSerializer(result).data if isinstance(result, dict) else result
    # Compute tokens_required based on rule: RATE_TEOCOIN_EUR (default 1.0)
    try:
        rate = float(getattr(settings, "RATE_TEOCOIN_EUR", 1.0))
        discount_percent = float(data.get("discount_percent", 0) or 0)
        price = float(data.get("price_eur", 0) or 0)
        tokens_required = int(ceil((price * (discount_percent / 100.0)) / (rate if rate > 0 else 1.0)))
    except Exception:
        tokens_required = 0

    # Read user DB balance (available)
    try:
        balance = db_teocoin_service.get_balance(request.user)
        # balance is Decimal
        balance_numeric = float(balance)
    except Exception:
        balance_numeric = 0.0

    eligible = balance_numeric >= tokens_required

    # Attach tokens/balance eligibility into the response wrapper
    # Structured logging for preview (non-blocking)
    try:
        logger.info("discount_preview", extra={
            "event": "discount_preview",
            "order_id": None,
            "user_id": request.user.id if request.user else None,
            "course_id": data.get("course_id"),
            "teacher_id": data.get("teacher_id"),
            "student_id": data.get("student_id"),
            "discount_percent": data.get("discount_percent"),
            "accept_teo": data.get("accept_teo"),
            "accept_ratio": data.get("accept_ratio"),
            "tier_name": (tier.get("name") if tier else None),
        })
    except Exception:
        logger.debug("discount_preview logging failed")

    return Response({"ok": True, "data": out, "tokens_required": tokens_required, "balance": balance_numeric, "eligible": eligible}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_web3_enabled
@extend_schema(
    operation_id="rewards_discounts_confirm_create",
    request=DiscountConfirmInputSerializer,
    responses={200: PaymentDiscountSnapshotSerializer, 201: PaymentDiscountSnapshotSerializer},
)
def confirm_discount(request):
    serializer = DiscountConfirmInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "errors": serializer.errors}, status=422)

    data = cast(Dict[str, Any], serializer.validated_data)

    order_id = str(data.get("order_id"))
    course_id = data.get("course_id")
    student_id = data.get("student_id") or request.user.id
    teacher_id = data.get("teacher_id")
    
    # Extract or generate checkout_session_id for idempotency
    checkout_session_id = data.get("checkout_session_id")
    if not checkout_session_id:
        # Extract from order_id if it follows our pattern, otherwise use order_id
        if order_id.startswith("local_") or order_id.startswith("discount_"):
            checkout_session_id = order_id
        else:
            checkout_session_id = f"session_{order_id}"
    
    # Generate idempotency key: user + course + session
    student = User.objects.get(id=student_id) if student_id else request.user
    course_obj = Course.objects.get(id=course_id) if course_id else None
    idempotency_key = f"{student.id}_{course_id}_{checkout_session_id}"
    
    # IDEMPOTENCY CHECK: Look for existing active discount for this session
    existing_discount = PaymentDiscountSnapshot.objects.filter(
        student=student,
        course=course_obj,
    checkout_session_id=checkout_session_id,
    status__in=["applied", "confirmed", "pending"]
    ).first()
    
    if existing_discount:
        # Check if this is a different discount amount (5→10→15 scenario)
        requested_discount_percent = int(data.get("discount_percent", 0))
        if existing_discount.discount_percent != requested_discount_percent:
            # SUPERSEDE: Mark old discount as superseded and release its hold
            try:
                from services.wallet_hold_service import WalletHoldService
                wallet_hold_service = WalletHoldService()
                
                with transaction.atomic():
                    if existing_discount.wallet_hold_id:
                        wallet_hold_service.release_hold(
                            existing_discount.wallet_hold_id,
                            f"Superseded by new {requested_discount_percent}% discount"
                        )
                    
                    existing_discount.status = "superseded"
                    existing_discount.save(update_fields=["status"])
                
                logger.info(
                    f"Superseded existing discount: snapshot_id={existing_discount.id}, "
                    f"old_percent={existing_discount.discount_percent}, "
                    f"new_percent={requested_discount_percent}"
                )
                
                # Continue to create new discount below
                
            except Exception as e:
                logger.error(f"Failed to supersede existing discount: {e}")
                return Response(
                    {"ok": False, "error": "Failed to update discount"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # IDEMPOTENT: Same discount already applied, return existing
            logger.info(
                f"Idempotent discount request: returning existing snapshot_id={existing_discount.id}, "
                f"idempotency_key={idempotency_key}"
            )
            
            # Count duplicate prevention for telemetry
            try:
                logger.info("duplicate_prevented", extra={
                    "event": "duplicate_prevented",
                    "idempotency_key": idempotency_key,
                    "order_id": order_id,
                    "existing_snapshot_id": existing_discount.id,
                    "user_id": student.id,
                })
            except Exception:
                pass
            
            snapshot_data = PaymentDiscountSnapshotSerializer(existing_discount).data
            breakdown = {
                "student_pay_eur": existing_discount.student_pay_eur,
                "teacher_eur": existing_discount.teacher_eur,
                "platform_eur": existing_discount.platform_eur,
                "teacher_teo": existing_discount.teacher_teo,
                "platform_teo": existing_discount.platform_teo,
            }
            
            return Response(
                {"ok": True, "created": False, "snapshot": snapshot_data, "breakdown": breakdown},
                status=status.HTTP_200_OK
            )

    # SERVER-SIDE DISCOUNT CALCULATION: Ignore client values, compute server-side
    # Fixed discount amounts: 5, 10, 15 EUR (not percentages)
    requested_tokens = data.get("tokens_to_spend", 0)
    if requested_tokens in [5, 10, 15]:
        discount_amount_eur = Decimal(str(requested_tokens))
        discount_percent = int((discount_amount_eur / course_obj.price_eur * 100).to_integral_value()) if course_obj else 0
    else:
        # Fallback to percentage-based for backward compatibility
        discount_percent = int(data.get("discount_percent", 0))
        discount_amount_eur = course_obj.price_eur * Decimal(discount_percent) / Decimal("100") if course_obj else Decimal("0")
    
    # Validate discount amount
    if discount_amount_eur <= 0:
        return Response(
            {"ok": False, "error": "Invalid discount amount"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Resolve tier
    tier = None
    if teacher_id:
        try:
            teacher = User.objects.get(id=int(teacher_id))
            tp = getattr(teacher, "teacher_profile", None)
            if tp:
                tier_obj = Tier.objects.filter(name=tp.staking_tier, is_active=True).first()
                if tier_obj:
                    tier = {
                        "teacher_split_percent": tier_obj.teacher_split_percent,
                        "platform_split_percent": tier_obj.platform_split_percent,
                        "max_accept_discount_ratio": tier_obj.max_accept_discount_ratio,
                        "teo_bonus_multiplier": tier_obj.teo_bonus_multiplier,
                        "name": tier_obj.name,
                    }
        except Exception:
            tier = None

    breakdown = compute_discount_breakdown(
        price_eur=course_obj.price_eur if course_obj else data["price_eur"],
        discount_percent=discount_percent,
        tier=tier,
        accept_teo=data.get("accept_teo", False),
        accept_ratio=data.get("accept_ratio", None),
    )

    # CHECK TEO BALANCE AND CREATE HOLD
    try:
        from services.wallet_hold_service import WalletHoldService
        wallet_hold_service = WalletHoldService()
        
        # Check if user has sufficient TEO balance
        user_balance = float(db_teocoin_service.get_balance(student))
        if user_balance < float(discount_amount_eur):
            logger.info("discount_rejected_insufficient_balance", extra={
                "event": "discount_rejected_insufficient_balance",
                "user_id": student.id,
                "order_id": order_id,
                "tokens_required": float(discount_amount_eur),
                "balance": user_balance,
            })
            return Response(
                {"ok": False, "error": "INSUFFICIENT_TOKENS"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create TEO hold (reserve tokens without deducting)
        hold_id = wallet_hold_service.create_hold(
            user=student,
            amount=discount_amount_eur,
            description=f"Discount hold for course {course_obj.title if course_obj else course_id}",
            course=course_obj,
            hold_reference=order_id
        )
        
        if not hold_id:
            logger.error(f"Failed to create TEO hold for user {student.id}, amount {discount_amount_eur}")
            return Response(
                {"ok": False, "error": "HOLD_CREATION_FAILED"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"TEO hold creation error: {e}")
        return Response(
            {"ok": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # CREATE DISCOUNT SNAPSHOT WITH APPLIED STATUS
    # Predefine for type-checkers
    teacher_obj: Optional[User] = None

    with transaction.atomic():
        try:
            # Preload teacher for defaults to ensure teacher fallback
            teacher_obj = None
            if teacher_id:
                try:
                    teacher_obj = User.objects.get(id=teacher_id)
                except Exception:
                    teacher_obj = None
            if not teacher_obj and course_obj:
                try:
                    teacher_obj = course_obj.teacher
                except Exception:
                    teacher_obj = None

            # Create snapshot with APPLIED status and hold reference
            defaults_payload = {
                "course": course_obj,
                "student": student,
                "teacher": teacher_obj,
                "price_eur": course_obj.price_eur if course_obj else data["price_eur"],
                "discount_percent": discount_percent,
                "discount_amount_eur": discount_amount_eur,
                "student_pay_eur": breakdown["student_pay_eur"],
                "teacher_eur": breakdown["teacher_eur"],
                "platform_eur": breakdown["platform_eur"],
                "teacher_teo": breakdown.get("teacher_teo", 0),
                "platform_teo": breakdown.get("platform_teo", 0),
                "absorption_policy": breakdown.get("absorption_policy", "none"),
                "teacher_accepted_teo": breakdown.get("teacher_teo", 0),
                "tier_name": (tier.get("name") if tier else None),
                "tier_teacher_split_percent": (tier.get("teacher_split_percent") if tier else None),
                "tier_platform_split_percent": (tier.get("platform_split_percent") if tier else None),
                "tier_max_accept_discount_ratio": (tier.get("max_accept_discount_ratio") if tier else None),
                "tier_teo_bonus_multiplier": (tier.get("teo_bonus_multiplier") if tier else None),
                
                # NEW IDEMPOTENCY FIELDS
                # Use 'applied' to indicate a hold with successful TEO reservation
                "status": "applied",
                "checkout_session_id": checkout_session_id,
                "idempotency_key": idempotency_key,
                "wallet_hold_id": hold_id,
                "applied_at": timezone.now(),
                
                # STRIPE CORRELATION FIELDS
                "stripe_checkout_session_id": data.get("stripe_checkout_session_id"),
                "stripe_payment_intent_id": data.get("stripe_payment_intent_id"),
            }
            
            # Create snapshot with unique constraint protection
            try:
                # R1.1 Fix: Use apply_discount_and_snapshot to create snapshot WITH decision atomically
                logger.info(f"🔍 DISCOUNT_VIEWS R1.1 Fix evaluation: accept_teo={data.get('accept_teo', False)}, teacher={teacher_obj.username if teacher_obj else None}, teacher_teo={breakdown.get('teacher_teo', 0)}")
                
                if data.get("accept_teo", False) and teacher_obj and breakdown.get("teacher_teo", 0) > 0:
                    logger.info(f"✅ DISCOUNT_VIEWS Using R1.1 Fix - creating snapshot with decision atomically")
                    try:
                        # Create snapshot + decision atomically using R1.1 pattern
                        from decimal import Decimal as _Decimal
                        result = apply_discount_and_snapshot(
                            student_user_id=student.id,
                            teacher_id=teacher_obj.id,
                            course_id=course_obj.id if course_obj else None,
                            teo_cost=discount_amount_eur,  # Total discount amount in TEO
                            offered_teacher_teo=_Decimal(str(breakdown["teacher_teo"])),
                            idempotency_key=idempotency_key
                        )
                        # Get the created snapshot
                        snap = PaymentDiscountSnapshot.objects.get(id=result["snapshot_id"])
                        created = True
                        logger.info(f"✅ DISCOUNT_VIEWS R1.1 Fix success - created snapshot {snap.id} with decision {result['pending_decision_id']}")
                    except Exception as e:
                        logger.error(f"❌ DISCOUNT_VIEWS R1.1 Fix failed with exception: {e} - falling back to non-R1.1")
                        # Fallback to non-R1.1 on any error
                        snap, created = get_or_create_payment_snapshot(
                            order_id=order_id, 
                            defaults=defaults_payload, 
                            source="local"
                        )
                else:
                    logger.warning(f"❌ DISCOUNT_VIEWS R1.1 Fix conditions not met - using fallback (accept_teo={data.get('accept_teo', False)}, teacher={teacher_obj.username if teacher_obj else None}, teacher_teo={breakdown.get('teacher_teo', 0)})")
                    # Fallback to non-R1.1 for non-TEO transactions
                    snap, created = get_or_create_payment_snapshot(
                        order_id=order_id, 
                        defaults=defaults_payload, 
                        source="local"
                    )
            except Exception:
                # Fallback to direct get_or_create for robustness
                snap, created = PaymentDiscountSnapshot.objects.get_or_create(
                    order_id=order_id, 
                    defaults=defaults_payload
                )
                
        except IntegrityError as ie:
            # Handle race condition - another process created snapshot at same time
            logger.warning(f"IntegrityError creating snapshot: {ie}")
            try:
                # Try to find existing snapshot by checkout_session_id
                snap = PaymentDiscountSnapshot.objects.get(
                    student=student,
                    course=course_obj,
                    checkout_session_id=checkout_session_id,
                    status__in=["applied", "confirmed", "pending"]
                )
                created = False
                # Release our hold since we're using existing snapshot
                if hold_id:
                    wallet_hold_service.release_hold(hold_id, "Duplicate creation - using existing snapshot")
            except PaymentDiscountSnapshot.DoesNotExist:
                # Constraint violation but no matching snapshot found - return error
                return Response(
                    {"ok": False, "error": "Constraint violation creating discount"},
                    status=status.HTTP_409_CONFLICT
                )
        except Exception as e:
            logger.exception("confirm_discount snapshot creation error")
            # Release hold on error
            if hold_id:
                wallet_hold_service.release_hold(hold_id, f"Creation error: {str(e)}")
            return Response(
                {"ok": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # STRUCTURED LOGGING FOR TELEMETRY
    try:
        logger.info("discount_confirm", extra={
            "event": "discount_confirm",
            "order_id": order_id,
            "user_id": student.id,
            "course_id": course_id,
            "teacher_id": teacher_id,
            "student_id": student.id,
            "discount_percent": discount_percent,
            "discount_amount_eur": str(discount_amount_eur),
            "idempotency_key": idempotency_key,
            "checkout_session_id": checkout_session_id,
            "wallet_hold_id": hold_id,
            "created": created,
                    "snapshot_id": getattr(snap, "id", None),
                    "status": "pending",
        })
    except Exception:
        logger.debug("discount_confirm logging failed")

    # TODO: Create teacher notification (existing logic can be reused)
    # This will be handled by post-payment confirmation in ConfirmPaymentView

    snapshot_data_raw = PaymentDiscountSnapshotSerializer(snap).data
    try:
        snapshot_data: Dict[str, Any] = dict(snapshot_data_raw)
    except Exception:
        snapshot_data = {}

    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    
    return Response(
        {
            "ok": True,
            "created": created,
            "snapshot": snapshot_data,
            "breakdown": breakdown,
            "hold_id": hold_id,
            "status": "pending",
        },
        status=status_code,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def missing_snapshots_for_teachers(request):
    """
    Return PaymentDiscountSnapshot entries that likely missed a teacher notification.

    Criteria:
    - snapshot has a teacher set
    - and there is no Notification with notification_type 'teocoin_discount_pending' and related_object_id == snapshot.id
    This helps the frontend backfill older transactions into the teacher inbox.
    """
    try:
        from notifications.models import Notification
        from courses.models import TeacherDiscountDecision

        # Only return snapshots for the authenticated teacher
        snaps = (
            PaymentDiscountSnapshot.objects.filter(teacher=request.user)
            .order_by("-created_at")
            .all()
        )

        missing = []
        for s in snaps:
            # Resolve or create a pending decision for this snapshot trio (idempotent lookup only)
            dec = (
                TeacherDiscountDecision.objects.filter(
                    teacher=s.teacher,
                    student=s.student,
                    course=s.course,
                    decision="pending",
                )
                .order_by("-created_at")
                .first()
            )

            notif_exists = False
            if dec:
                notif_exists = Notification.objects.filter(
                    user=s.teacher,
                    notification_type__in=["teocoin_discount_pending"],
                    related_object_id=getattr(dec, "pk", None),
                ).exists()
            else:
                # Legacy check as last resort (older notifications may have snapshot.id)
                notif_exists = Notification.objects.filter(
                    user=s.teacher,
                    notification_type__in=["teocoin_discount_pending"],
                    related_object_id=getattr(s, "pk", None),
                ).exists()

            if not notif_exists:
                missing.append(
                    {
                        "id": getattr(s, "pk", None),
                        "order_id": s.order_id,
                        "course_title": s.course.title if s.course else None,
                        "student_username": s.student.username if s.student else None,
                        "discount_percent": int(s.discount_percent) if s.discount_percent is not None else 0,
                        "teacher_teo": str(s.teacher_teo),
                        "teacher_eur": str(s.teacher_eur),
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "pending_decision_id": getattr(dec, "pk", None),
                    }
                )

        return Response({"ok": True, "missing": missing})
    except Exception as e:
        logger.exception("missing_snapshots_for_teachers error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backfill_snapshots_to_decisions(request):
    """
    Convert missing PaymentDiscountSnapshot entries into real TeacherDiscountDecision
    records and create an in-app Notification for the teacher so the existing
    teacher-choices API can be used to accept/decline.

    Input JSON (optional): {"snapshot_ids": [1,2,3]}
    If omitted, will process all snapshots for the authenticated teacher that
    currently do not have a 'teocoin_discount_pending' Notification.

    This endpoint is idempotent: it will skip snapshots that already have a
    corresponding Notification.
    """
    try:
        from notifications.models import Notification
        from courses.models import TeacherDiscountDecision
        from django.db import transaction
        from decimal import Decimal

        teacher = request.user
        snapshot_ids = cast(Dict[str, Any], request.data).get("snapshot_ids")

        snaps_qs = PaymentDiscountSnapshot.objects.filter(teacher=teacher).order_by("-created_at")
        if snapshot_ids:
            snaps_qs = snaps_qs.filter(id__in=snapshot_ids)

        created: list[Dict[str, Any]] = []
        skipped: list[Any] = []

        for s in snaps_qs:
            # Skip snapshots with missing critical relations
            if not s.course or not s.student:
                skipped.append(getattr(s, "pk", None))
                continue

            with transaction.atomic():
                # Build or locate pending decision for trio
                # Convert decimal TEO to wei (bigint)
                teo_decimal = Decimal(s.teacher_teo or 0)
                # teacher_bonus calculation: if tier multiplier exists, compute bonus portion
                bonus_decimal = Decimal(0)
                try:
                    if s.tier_teo_bonus_multiplier:
                        mult = Decimal(s.tier_teo_bonus_multiplier)
                        if mult and mult != Decimal(0):
                            original = teo_decimal / mult
                            bonus_decimal = teo_decimal - original
                except Exception:
                    bonus_decimal = Decimal(0)

                # Convert to wei (int) but cap to signed 64-bit max to avoid DB overflow
                MAX_INT64 = 9223372036854775807
                teo_cost_wei = int((teo_decimal * Decimal(10 ** 18)).to_integral_value()) if teo_decimal else 0
                teacher_bonus_wei = int((bonus_decimal * Decimal(10 ** 18)).to_integral_value()) if bonus_decimal else 0
                if teo_cost_wei > MAX_INT64:
                    logger.warning("teo_cost wei truncated to MAX_INT64 during backfill", extra={"original": teo_cost_wei, "snapshot_id": getattr(s, 'pk', None)})
                    teo_cost_wei = MAX_INT64
                if teacher_bonus_wei > MAX_INT64:
                    logger.warning("teacher_bonus wei truncated to MAX_INT64 during backfill", extra={"original": teacher_bonus_wei, "snapshot_id": getattr(s, 'pk', None)})
                    teacher_bonus_wei = MAX_INT64

                decision = (
                    TeacherDiscountDecision.objects.filter(
                        teacher=s.teacher,
                        student=s.student,
                        course=s.course,
                        decision="pending",
                    )
                    .order_by("-created_at")
                    .first()
                )
                if not decision:
                    decision = TeacherDiscountDecision.objects.create(
                        teacher=s.teacher,
                        student=s.student,
                        course=s.course,
                        course_price=s.price_eur,
                        discount_percentage=s.discount_percent,
                        teo_cost=teo_cost_wei,
                        teacher_bonus=teacher_bonus_wei,
                        teacher_commission_rate=(s.tier_teacher_split_percent or Decimal("50.00")),
                        teacher_staking_tier=(s.tier_name or "Bronze"),
                        decision="pending",
                        expires_at=(s.created_at + timedelta(hours=24)),
                    )

                # Idempotency: notification keyed by decision id
                exists = Notification.objects.filter(
                    user=s.teacher,
                    notification_type__in=["teocoin_discount_pending"],
                    related_object_id=getattr(decision, "pk", None),
                ).exists()
                if exists:
                    skipped.append(getattr(s, "pk", None))
                    continue

                # Create notification linking to the decision id so FE actions can resolve correctly
                msg = (
                    f"Scelta TeoCoin richiesta per {s.course.title if s.course else 'corso'}: "
                    f"lo studente {s.student.username} ha usato uno sconto ({s.discount_percent}%)."
                )
                Notification.objects.create(
                    user=s.teacher,
                    message=msg,
                    notification_type="teocoin_discount_pending",
                    related_object_id=getattr(decision, "pk", None),
                    link=None,
                )

                created.append({
                    "snapshot_id": getattr(s, "pk", None),
                    "decision_id": getattr(decision, "pk", None),
                })

        return Response({"ok": True, "created": created, "skipped": skipped})
    except Exception as e:
        logger.exception("backfill_snapshots_to_decisions error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pending_discount_snapshots(request):
    """
    Return list of pending PaymentDiscountSnapshot entries for the authenticated teacher.
    Each snapshot includes offered_teacher_teo / offered_platform_teo (strings 8 d.p.) when possible.
    Ordered by expires_at if available, otherwise created_at ascending.
    """
    try:
        teacher = request.user

        # Get snapshots where teacher owns the course and needs to make a decision
        # Use course__teacher relation since snapshot.teacher field may not be populated
        # CRITICAL: Only include snapshots that have a linked decision (can be accepted/declined)
        qs = PaymentDiscountSnapshot.objects.filter(
            course__teacher=teacher,  # Filter by course teacher instead of direct teacher field
            status__in=["pending", "applied", "confirmed"],  # Actionable statuses
            decision__isnull=False  # ONLY snapshots with decisions can be acted upon
        ).order_by("created_at")

        items = []
        for s in qs:
            data = PaymentDiscountSnapshotSerializer(s).data
            # serializer.data may be a ReturnList/OrderedDict - coerce to dict for safe key access
            try:
                data_map: Dict[str, Any] = dict(data)  # type: ignore[arg-type]
            except Exception:
                data_map = {}
            # Normalize fields for FE: include course_title, student_name, deadline if available
            item = {
                "id": getattr(s, "id", None),
                # Use the linked decision if available, otherwise look for compatible decision
                "pending_decision_id": s.decision.id if s.decision else None,
                "order_id": getattr(s, "order_id", None),
                "course_title": s.course.title if s.course else None,
                "student_name": s.student.username if s.student else None,
                "teacher_eur": str(s.teacher_eur),
                "platform_eur": str(s.platform_eur),
                "teacher_teo": str(s.teacher_teo),
                "offered_teacher_teo": data_map.get("offered_teacher_teo"),
                "offered_platform_teo": data_map.get("offered_platform_teo"),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "status": "pending",
                "raw": data,
            }
            # Since we filter by decision__isnull=False, every snapshot has a valid decision
            # No need for fallback decision lookup
            items.append(item)

        # Sort by offered deadline if present in raw (expires_at) else by created_at
        items.sort(key=lambda x: x.get("raw", {}).get("expires_at") or x.get("created_at"))

        return Response(items)
    except Exception as e:
        logger.exception("pending_discount_snapshots error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_teacher_choice(request, decision_id: int):
    """
    Accept a teacher discount decision and credit TEO to teacher.

    This uses the existing teacher_make_decision atomic helper to perform
    DB balance updates and snapshot write. Additionally, create a
    BlockchainTransaction row so the frontend wallet transactions list
    shows the accepted amount immediately, and remove the related
    'teocoin_discount_pending' Notification so the inbox clears.
    """
    # Call service to apply decision (accept=True)
    try:
        res = teacher_make_decision(decision_id=decision_id, accept=True, actor=request.user)
    except Exception as e:
        logger.exception("accept_teacher_choice service error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create a BlockchainTransaction record for FE visibility if credited > 0 (best-effort)
    try:
        from rewards.models import BlockchainTransaction
        from courses.models import TeacherDiscountDecision
        from decimal import Decimal
        from notifications.models import Notification

        credited_str = res.get("credited") if isinstance(res, dict) else None
        if credited_str:
            credited = Decimal(str(credited_str))
            if credited > 0:
                dec = TeacherDiscountDecision.objects.get(pk=decision_id)
                exists = BlockchainTransaction.objects.filter(
                    user=dec.teacher,
                    related_object_id=str(decision_id),
                    transaction_type="discount_accept",
                ).exists()
                if not exists:
                    BlockchainTransaction.objects.create(
                        user=dec.teacher,
                        amount=credited,
                        transaction_type="discount_accept",
                        status="completed",
                        notes=f"Teacher accepted discount decision {decision_id}",
                        related_object_id=str(decision_id),
                    )

        # Delete any pending notification linking to this decision so the inbox clears
        try:
            Notification.objects.filter(
                user=request.user,
                notification_type__in=["teocoin_discount_pending"],
                related_object_id=decision_id,
            ).delete()
        except Exception:
            logger.debug("failed to delete related notification for decision %s", decision_id)
    except Exception:
        logger.exception("failed to create BlockchainTransaction for accept")

    return Response({"ok": True, "result": res}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def decline_teacher_choice(request, decision_id: int):
    """Decline choice: close snapshot and mark decision as declined (idempotent).

    Uses teacher_make_decision with accept=False to centralize logic.
    """
    try:
        res = teacher_make_decision(decision_id=decision_id, accept=False, actor=request.user)
        # Remove pending notification linking to this decision
        try:
            from notifications.models import Notification

            Notification.objects.filter(
                user=request.user,
                notification_type__in=["teocoin_discount_pending"],
                related_object_id=decision_id,
            ).delete()
        except Exception:
            logger.debug("failed to delete related notification for decision %s", decision_id)

        return Response({"ok": True, "result": res}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("decline_teacher_choice error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
