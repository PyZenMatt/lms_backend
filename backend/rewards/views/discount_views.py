from decimal import Decimal
import logging

from django.db import transaction, IntegrityError, OperationalError
import time
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from services.discount_calc import compute_discount_breakdown
from rewards.models import PaymentDiscountSnapshot, Tier
from users.models import User
from courses.models import Course
from rewards.serializers import (
    DiscountPreviewInputSerializer,
    DiscountConfirmInputSerializer,
    DiscountBreakdownSerializer,
    PaymentDiscountSnapshotSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview_discount(request):
    serializer = DiscountPreviewInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"ok": False, "errors": serializer.errors}, status=422)

    data = serializer.validated_data

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

    data = serializer.validated_data

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

    # Persist snapshot idempotently in a transaction. Catch IntegrityError to
    # handle concurrent inserts and return the existing snapshot as idempotent.
    # Persist snapshot idempotently in a transaction. Catch IntegrityError or
    # OperationalError (SQLite table locked during concurrent tests) to
    # handle concurrent inserts and return the existing snapshot as idempotent.
    with transaction.atomic():
        try:
            snap, created = PaymentDiscountSnapshot.objects.get_or_create(
                order_id=order_id,
                defaults={
                    "course": Course.objects.get(id=course_id) if course_id else None,
                    "student": User.objects.get(id=student_id) if student_id else None,
                    "teacher": User.objects.get(id=teacher_id) if teacher_id else None,
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
                },
            )
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

    snapshot_data = PaymentDiscountSnapshotSerializer(snap).data
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response({"ok": True, "created": created, "snapshot": snapshot_data, "breakdown": breakdown}, status=status_code)
