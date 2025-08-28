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
from rewards.services.transaction_services import get_or_create_payment_snapshot
from rewards.services.transaction_services import teacher_make_decision
from users.models import User
from courses.models import Course
from rewards.serializers import (
    DiscountPreviewInputSerializer,
    DiscountConfirmInputSerializer,
    DiscountBreakdownSerializer,
    PaymentDiscountSnapshotSerializer,
)
from notifications.services import teocoin_notification_service

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
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

    return Response({"ok": True, "data": out}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_discount(request):
    serializer = DiscountConfirmInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "errors": serializer.errors}, status=422)

    data = cast(Dict[str, Any], serializer.validated_data)

    order_id = str(data.get("order_id"))
    course_id = data.get("course_id")
    student_id = data.get("student_id") or request.user.id
    teacher_id = data.get("teacher_id")

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
        price_eur=data["price_eur"],
        discount_percent=data.get("discount_percent", 0),
        tier=tier,
        accept_teo=data.get("accept_teo", False),
        accept_ratio=data.get("accept_ratio", None),
    )

    # Compute offered values (what teacher would receive if they accepted)
    # Ensure offered_ratio has a default
    offered_ratio = None
    try:
        from decimal import Decimal as _D
        # determine accept_ratio for offered calculation: use provided or tier max or 1
        if data.get("accept_ratio") is not None:
            offered_ratio = _D(str(data.get("accept_ratio")))
        else:
            offered_ratio = _D(str((tier.get("max_accept_discount_ratio") if tier and tier.get("max_accept_discount_ratio") is not None else _D("1"))))

        offered_breakdown = compute_discount_breakdown(
            price_eur=data["price_eur"],
            discount_percent=data.get("discount_percent", 0),
            tier=tier,
            accept_teo=True,
            accept_ratio=offered_ratio,
        )
    except Exception:
        offered_breakdown = None

    # Persist snapshot idempotently in a transaction. Catch IntegrityError to
    # handle concurrent inserts and return the existing snapshot as idempotent.
    # Persist snapshot idempotently in a transaction. Catch IntegrityError or
    # OperationalError (SQLite table locked during concurrent tests) to
    # handle concurrent inserts and return the existing snapshot as idempotent.
    # Predefine for type-checkers
    course_obj: Optional[Course] = None
    teacher_obj: Optional[User] = None

    with transaction.atomic():
        try:
            # Preload course and teacher for defaults to ensure teacher fallback
            course_obj = Course.objects.get(id=course_id) if course_id else None
            # Prefer explicit teacher id; else fallback to course.teacher when available
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

            # Idempotent snapshot creation using order_id as stable key
            defaults_payload = {
                "course": course_obj,
                "student": User.objects.get(id=student_id) if student_id else None,
                "teacher": teacher_obj,
                "price_eur": data["price_eur"],
                "discount_percent": int(data.get("discount_percent", 0)),
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
            }
            try:
                snap, created = get_or_create_payment_snapshot(order_id=order_id, defaults=defaults_payload, source="local")
            except Exception:
                # Fallback to direct get_or_create for robustness
                snap, created = PaymentDiscountSnapshot.objects.get_or_create(order_id=order_id, defaults=defaults_payload)
        except IntegrityError:
            # Another process created the snapshot at the same time. Fetch it.
            snap = PaymentDiscountSnapshot.objects.get(order_id=order_id)
            created = False
        except OperationalError:
            # SQLite (used in tests) can raise 'database table is locked' when
            # two threads hit the DB concurrently. Try to fetch the existing
            # snapshot a few times with a small backoff. If still missing,
            # surface a 500 so the error is visible.
            found = None
            for _ in range(5):
                try:
                    found = PaymentDiscountSnapshot.objects.filter(order_id=order_id).first()
                    if found:
                        break
                except Exception:
                    pass
                time.sleep(0.02)

            if found:
                snap = found
                created = False
            else:
                logger.exception("confirm_discount db error")
                return Response({"ok": False, "error": "database operational error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("confirm_discount db error")
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # If snapshot existed but lacked course/teacher, patch it now via queryset.update to avoid setter typing issues
    try:
        if not created and getattr(snap, "pk", None):
            updated = False
            if (not getattr(snap, "course", None)) and course_obj:
                PaymentDiscountSnapshot.objects.filter(pk=snap.pk).update(course=course_obj)
                updated = True
            if (not getattr(snap, "teacher", None)) and teacher_obj:
                PaymentDiscountSnapshot.objects.filter(pk=snap.pk).update(teacher=teacher_obj)
                updated = True
            if updated:
                snap.refresh_from_db(fields=["course", "teacher"])
    except Exception:
        logger.debug("snapshot patch skip", exc_info=True)

    # Ensure teacher_teo / teacher_accepted_teo are populated when possible.
    try:
        from decimal import Decimal as _D

        need_update = False
        try:
            curr_teacher_teo = _D(str(getattr(snap, "teacher_teo", _D("0"))))
        except Exception:
            curr_teacher_teo = _D("0")

        if curr_teacher_teo == _D("0"):
            # Prefer offered_breakdown if available
            val = None
            try:
                if offered_breakdown and offered_breakdown.get("teacher_teo") is not None:
                    val = _D(str(offered_breakdown.get("teacher_teo")))
            except Exception:
                val = None

            # Try a safe recompute if necessary
            if val is None:
                try:
                    # build accept_ratio safely
                    if data.get("accept_ratio") is not None:
                        accept_ratio = _D(str(data.get("accept_ratio")))
                    else:
                        accept_ratio = _D(str(tier.get("max_accept_discount_ratio"))) if tier and tier.get("max_accept_discount_ratio") is not None else _D("1")

                    recomputed = compute_discount_breakdown(
                        price_eur=data["price_eur"],
                        discount_percent=data.get("discount_percent", 0),
                        tier=tier,
                        accept_teo=True,
                        accept_ratio=accept_ratio,
                    )
                    if recomputed and recomputed.get("teacher_teo") is not None:
                        val = _D(str(recomputed.get("teacher_teo")))
                except Exception:
                    val = None

            # Final fallback to breakdown if present
            if val is None and breakdown and breakdown.get("teacher_teo") is not None:
                try:
                    val = _D(str(breakdown.get("teacher_teo")))
                except Exception:
                    val = None

            if val is not None and val != _D("0"):
                try:
                    q = _D("0.00000001")
                    val_q = val.quantize(q)
                    PaymentDiscountSnapshot.objects.filter(pk=snap.pk).update(
                        teacher_teo=val_q, teacher_accepted_teo=val_q
                    )
                    need_update = True
                except Exception:
                    logger.exception("failed to backfill snapshot teacher_teo")

        if need_update:
            try:
                logger.info("snapshot_backfilled", extra={
                    "order_id": order_id,
                    "snapshot_id": getattr(snap, "pk", None),
                    "offered_teacher_teo": str(getattr(snap, "teacher_teo", None)),
                })
            except Exception:
                pass
    except Exception:
        logger.exception("ensure snapshot teacher_teo block failed")

    # Attempt to create a pending TeacherDiscountDecision for this snapshot (idempotent)
    try:
        # Only if we have all actors
        if snap and snap.teacher and snap.student and snap.course:
            from courses.models import TeacherDiscountDecision as CourseTeacherDiscountDecision
            now = timezone.now()

            # Skip if a still-pending decision already exists for same trio
            existing = CourseTeacherDiscountDecision.objects.filter(
                teacher=snap.teacher,
                student=snap.student,
                course=snap.course,
                decision="pending",
                expires_at__gt=now,
            ).first()

            if not existing:
                from decimal import Decimal

                # Determine offered teacher TEO (includes bonus) as Decimal
                offered_teacher_teo_dec = None
                try:
                    if offered_breakdown and offered_breakdown.get("teacher_teo") is not None:
                        offered_teacher_teo_dec = Decimal(str(offered_breakdown.get("teacher_teo")))
                except Exception:
                    offered_teacher_teo_dec = None

                if offered_teacher_teo_dec is None:
                    # If the earlier offered_breakdown computation failed, try a
                    # safe recompute using compute_discount_breakdown with
                    # accept_teo=True and the offered_ratio we derived above.
                    try:
                        recomputed = None
                        try:
                            recomputed = compute_discount_breakdown(
                                price_eur=data["price_eur"],
                                discount_percent=data.get("discount_percent", 0),
                                tier=tier,
                                accept_teo=True,
                                accept_ratio=offered_ratio,
                            )
                        except Exception:
                            recomputed = None

                        if recomputed and recomputed.get("teacher_teo") is not None:
                            offered_teacher_teo_dec = Decimal(str(recomputed.get("teacher_teo")))
                    except Exception:
                        # Keep going to snapshot fallback below; log for diagnostics
                        logger.exception("recompute offered_breakdown failed")

                if offered_teacher_teo_dec is None:
                    try:
                        # Fallback to snapshot teacher_teo if present (may be 0 for pending)
                        offered_teacher_teo_dec = Decimal(str(snap.teacher_teo or 0))
                    except Exception:
                        offered_teacher_teo_dec = Decimal("0")

                # Split bonus portion if tier multiplier available
                bonus_dec = Decimal("0")
                try:
                    mult = Decimal(str(getattr(snap, "tier_teo_bonus_multiplier", None) or 0))
                    if mult and mult != Decimal("0"):
                        original = offered_teacher_teo_dec / mult
                        bonus_dec = offered_teacher_teo_dec - original
                except Exception:
                    bonus_dec = Decimal("0")

                # Convert to wei (int) but cap to signed 64-bit max to avoid DB overflow
                MAX_INT64 = 9223372036854775807
                teo_cost_wei = int((offered_teacher_teo_dec * Decimal(10 ** 18)).to_integral_value()) if offered_teacher_teo_dec else 0
                teacher_bonus_wei = int((bonus_dec * Decimal(10 ** 18)).to_integral_value()) if bonus_dec else 0
                if teo_cost_wei > MAX_INT64:
                    logger.warning("teo_cost wei truncated to MAX_INT64 for decision creation", extra={"original": teo_cost_wei, "order_id": order_id})
                    teo_cost_wei = MAX_INT64
                if teacher_bonus_wei > MAX_INT64:
                    logger.warning("teacher_bonus wei truncated to MAX_INT64 for decision creation", extra={"original": teacher_bonus_wei, "order_id": order_id})
                    teacher_bonus_wei = MAX_INT64

                # Commission rate snapshot
                commission_rate = snap.tier_teacher_split_percent if snap.tier_teacher_split_percent is not None else Decimal("50.00")
                staking_tier = snap.tier_name or "Bronze"

                decision = CourseTeacherDiscountDecision.objects.create(
                    teacher=snap.teacher,
                    student=snap.student,
                    course=snap.course,
                    course_price=snap.price_eur,
                    discount_percentage=int(snap.discount_percent or 0),
                    teo_cost=teo_cost_wei,
                    teacher_bonus=teacher_bonus_wei,
                    teacher_commission_rate=commission_rate,
                    teacher_staking_tier=staking_tier,
                    decision="pending",
                    expires_at=(snap.created_at + timedelta(hours=24)) if snap.created_at else (now + timedelta(hours=24)),
                )

        # Send in-app notification to teacher (best-effort)
                try:
                    teocoin_notification_service.notify_teacher_discount_pending(
                        teacher=snap.teacher,
                        student=snap.student,
                        course_title=snap.course.title if snap.course else "Corso",
                        discount_percent=int(snap.discount_percent or 0),
                        teo_cost=float((offered_teacher_teo_dec or Decimal("0")).quantize(Decimal("0.00000001"))),
                        teacher_bonus=float((bonus_dec or Decimal("0")).quantize(Decimal("0.00000001"))),
            request_id=int(getattr(snap, "id", 0)),
                        expires_at=(snap.created_at + timedelta(hours=24)) if snap.created_at else (now + timedelta(hours=24)),
                        offered_teacher_teo=offered_teacher_teo_dec,
                        offered_platform_teo=None,
            decision_id=int(getattr(decision, "id", 0)) if getattr(decision, "id", None) is not None else None,
                    )
                except Exception:
                    logger.debug("teacher discount pending notification failed")
    except Exception:
        logger.debug("decision creation skipped/failed", exc_info=True)

    # Structured logging (info) - minimal, uniform fields
    try:
        logger.info("discount_confirm", extra={
            "event": "discount_confirm",
            "order_id": order_id,
            "user_id": request.user.id if request.user else None,
            "course_id": course_id,
            "teacher_id": teacher_id,
            "student_id": student_id,
            "discount_percent": int(data.get("discount_percent", 0)),
            "accept_teo": data.get("accept_teo", False),
            "accept_ratio": data.get("accept_ratio", None),
            "tier_name": (tier.get("name") if tier else None),
            "created": created,
            "snapshot_id": getattr(snap, "id", None),
        })
    except Exception:
        logger.debug("discount_confirm logging failed")

    snapshot_data_raw = PaymentDiscountSnapshotSerializer(snap).data
    # Build a plain dict to safely attach offered_* fields
    try:
        snapshot_data: Dict[str, Any] = dict(snapshot_data_raw)  # type: ignore[arg-type]
    except Exception:
        snapshot_data = {}
    # Attach offered_* to the response payload when available (string with 8 d.p.)
    try:
        if offered_breakdown:
            from decimal import Decimal as _D
            snapshot_data["offered_teacher_teo"] = f"{_D(str(offered_breakdown.get('teacher_teo') or '0')).quantize(_D('0.00000001')):.8f}"
            snapshot_data["offered_platform_teo"] = f"{_D(str(offered_breakdown.get('platform_teo') or '0')).quantize(_D('0.00000001')):.8f}"
    except Exception:
        pass

    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    # Structured enrichment log
    try:
        logger.info("discount_pending_notified_enrichment", extra={
            "event": "discount_pending_notified_enrichment",
            "order_id": order_id,
            "snapshot_id": getattr(snap, "id", None),
            "tier_name": (tier.get("name") if tier else None),
            "offered_teacher_teo": snapshot_data.get("offered_teacher_teo"),
        })
    except Exception:
        logger.debug("discount_pending_notified_enrichment logging failed")

    return Response({"ok": True, "created": created, "snapshot": snapshot_data, "breakdown": breakdown}, status=status_code)


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

        # Get snapshots where teacher is set and likely pending (status pending)
        # Note: PaymentDiscountSnapshot.teacher_accepted_teo has default 0, not NULL,
        # so filtering by isnull=True excludes all rows; use status='pending' instead.
        qs = PaymentDiscountSnapshot.objects.filter(
            teacher=teacher, status="pending"
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
                # If a pending TeacherDiscountDecision exists for this trio, expose its id
                "pending_decision_id": None,
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
            try:
                from courses.models import TeacherDiscountDecision

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
                if dec:
                    item["pending_decision_id"] = getattr(dec, "pk", None)
            except Exception:
                # best-effort: skip if models import fails
                pass
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
