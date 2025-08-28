"""
TeoCoin Discount Payment System - Clean Implementation
Database-only Architecture: Fast, reliable, gasless TeoCoin operations

Business Logic:
- Students get discounts using database TeoCoin balance
- Teachers receive commissions based on staking tiers (database-tracked)
- Platform handles all business logic in secure database
- Clean separation between DB operations and blockchain (for withdrawal/deposit only)
"""

import logging
import os
from decimal import Decimal

import stripe
from courses.models import Course, CourseEnrollment
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from services.db_teocoin_service import DBTeoCoinService
from services.hybrid_teocoin_service import hybrid_teocoin_service
from decimal import Decimal as _Decimal
from django.utils import timezone
from datetime import timedelta
from notifications.services import teocoin_notification_service
from django.db import transaction, IntegrityError
from services.discount_calc import compute_discount_breakdown
from rewards.models import PaymentDiscountSnapshot, Tier
from rewards.services.transaction_services import get_or_create_payment_snapshot

# LEGACY IMPORTS REMOVED - using clean database services now
# from services.gas_free_v2_service import GasFreeV2Service
# from views.gas_free_v2_views import create_discount_request_v2


logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Create Stripe payment intent with TeoCoin discount integration

    POST /api/v1/courses/{course_id}/payment/create-intent/
    {
        "use_teocoin_discount": true,
        "discount_percent": 15,
        "student_address": "0x...",
        "student_signature": "0x..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user

            logger.info(
                f"💳 Creating payment intent for course {course_id} by user {user.id}"
            )

            # Extract request data
            use_teocoin_discount = request.data.get("use_teocoin_discount", False)
            discount_percent = request.data.get("discount_percent", 0)
            student_address = request.data.get("student_address", "")
            request.data.get("student_signature", "")

            # Debug: log incoming discount-related request fields (non-sensitive)
            try:
                rd = request.data
                dbg = {
                    "use_teocoin_discount": bool(rd.get("use_teocoin_discount", False)),
                    "discount_percent": rd.get("discount_percent"),
                    "discount_eur": rd.get("discount_eur"),
                    "has_breakdown": bool(rd.get("breakdown")),
                }
                logger.info(f"[CreatePaymentIntent] incoming discount payload: {dbg}")
            except Exception:
                pass

            logger.info(
                f"💳 Payment data: use_discount={use_teocoin_discount}, discount={discount_percent}%"
            )

            # Calculate pricing
            original_price = course.price_eur
            discount_amount = Decimal("0")
            final_price = original_price
            discount_request_id = None

            logger.info(f"💰 Course pricing: original=€{original_price}")

            # Validate Stripe configuration
            if not settings.STRIPE_SECRET_KEY:
                logger.error("❌ Stripe secret key not configured")
                return Response(
                    {
                        "error": "Payment system not configured",
                        "code": "STRIPE_NOT_CONFIGURED",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Process TeoCoin discount if requested
            if use_teocoin_discount and discount_percent > 0:
                try:
                    logger.info(
                        f"🔄 Processing DB TeoCoin discount: {discount_percent}% for user {user.id}"
                    )

                    # Initialize DB TeoCoin service
                    db_teo_service = DBTeoCoinService()

                    # Accept explicit discount_eur from frontend if provided (robustness)
                    discount_eur_input = request.data.get("discount_eur", None)
                    if discount_eur_input is not None:
                        try:
                            discount_value_eur = Decimal(str(discount_eur_input))
                            logger.info(f"🔎 Using frontend-provided discount_eur={discount_value_eur}")
                        except Exception:
                            # fallback to percent-based calculation
                            discount_value_eur = (
                                original_price * Decimal(discount_percent) / Decimal("100")
                            )
                    else:
                        # Calculate TEO cost (1 EUR discount = 1 TEO, matching frontend)
                        discount_value_eur = (
                            original_price * Decimal(discount_percent) / Decimal("100")
                        )

                    teo_cost = discount_value_eur  # 1 TEO = 1 EUR discount value

                    # Check student TEO balance using DB system (matches frontend)
                    student_balance_data = db_teo_service.get_user_balance(user)
                    available_teo = student_balance_data.get("available_balance", 0)

                    if available_teo < teo_cost:
                        return Response(
                            {
                                "error": f"Insufficient TEO balance. Need {teo_cost} TEO, have {available_teo} TEO",
                                "code": "INSUFFICIENT_TEO_BALANCE",
                                "required_teo": float(teo_cost),
                                "available_teo": float(available_teo),
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # NOTE: Do NOT deduct TEO here - will be deducted by ApplyDiscountView
                    # This prevents double deduction when frontend calls both endpoints
                    logger.info(
                        f"✅ TEO balance check passed: {available_teo} TEO available for {teo_cost} TEO cost"
                    )

                    # Student gets guaranteed discount (TEO will be deducted separately)
                    discount_amount = discount_value_eur
                    final_price = original_price - discount_amount

                    logger.info(
                        f"✅ TeoCoin discount calculated: {discount_percent}% off €{original_price}"
                    )
                    logger.info(
                        f"💰 Student will pay €{final_price} (TEO deduction handled separately)"
                    )
                    logger.info(
                        f"📋 TEO will be deducted by ApplyDiscountView to prevent double deduction"
                    )

                    # Teacher will be notified through the absorption dashboard

                except Exception as e:
                    logger.error(f"Discount creation error: {e}")
                    return Response(
                        {
                            "error": "TeoCoin discount system error",
                            "details": str(e),
                            "code": "DISCOUNT_SYSTEM_ERROR",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            # Validate and set Stripe configuration with robust error handling
            stripe_secret = settings.STRIPE_SECRET_KEY

            # Check for common configuration issues
            if not stripe_secret:
                logger.error("❌ STRIPE_SECRET_KEY is None or empty")
                return Response(
                    {
                        "error": "Payment system not configured - missing secret key",
                        "code": "STRIPE_KEY_MISSING",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if (
                "your_str" in str(stripe_secret)
                or "example" in str(stripe_secret).lower()
            ):
                logger.error(
                    f"❌ STRIPE_SECRET_KEY appears to be a placeholder: {str(stripe_secret)[:20]}..."
                )
                # Try to get from environment directly as fallback
                stripe_secret = os.getenv("STRIPE_SECRET_KEY")
                if not stripe_secret or "your_str" in str(stripe_secret):
                    return Response(
                        {
                            "error": "Payment system misconfigured - placeholder key detected",
                            "code": "STRIPE_KEY_PLACEHOLDER",
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                logger.warning("⚠️ Used fallback environment variable for Stripe key")

            if len(str(stripe_secret)) < 20:
                logger.error(
                    f"❌ STRIPE_SECRET_KEY too short: {len(str(stripe_secret))} chars"
                )
                return Response(
                    {
                        "error": "Payment system misconfigured - invalid key length",
                        "code": "STRIPE_KEY_INVALID_LENGTH",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Create Stripe payment intent for final price
            logger.info(f"💳 Creating Stripe payment intent for €{final_price} (discount_amount={discount_amount})")

            stripe.api_key = stripe_secret
            logger.info(
                f"🔑 Stripe API key set to: {str(stripe.api_key)[:15]}...{str(stripe.api_key)[-4:] if stripe.api_key else 'NONE'}"
            )

            # Validate final price
            if final_price <= 0:
                logger.error(f"❌ Invalid final price: €{final_price}")
                return Response(
                    {"error": "Invalid payment amount", "code": "INVALID_AMOUNT"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            intent_data = {
                "amount": int(final_price * 100),  # Convert to cents
                "currency": "eur",
                "metadata": {
                    "course_id": course_id,
                    "user_id": user.id,
                    "original_price": str(original_price),
                    "discount_amount": str(discount_amount),
                    "discount_percent": discount_percent,
                    "use_teocoin_discount": str(use_teocoin_discount),
                    "student_address": student_address,
                },
            }

            # Add discount request ID if applicable
            if discount_request_id:
                intent_data["metadata"]["discount_request_id"] = str(
                    discount_request_id
                )

            logger.info(f"💳 Stripe intent data: {intent_data}")

            try:
                payment_intent = stripe.PaymentIntent.create(**intent_data)
                logger.info(f"✅ Stripe payment intent created: {payment_intent.id}")
                # Persist a PaymentDiscountSnapshot now (idempotent). This ensures
                # a snapshot exists as soon as the payment intent is created so
                # teacher notifications and frontend can rely on it.
                try:
                    if use_teocoin_discount and discount_amount > 0:
                        # Resolve tier from teacher profile if available
                        tier = None
                        tp = getattr(course.teacher, "teacher_profile", None)
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

                        breakdown = compute_discount_breakdown(
                            price_eur=original_price,
                            discount_percent=_Decimal(str(discount_percent if 'discount_percent' in locals() else 0)),
                            tier=tier,
                            accept_teo=False,
                            accept_ratio=None,
                        )

                        from django.db import IntegrityError

                        defaults_payload = {
                            "course": course,
                            "student": user,
                            "teacher": course.teacher if getattr(course, "teacher", None) else None,
                            "price_eur": original_price,
                            "discount_percent": int(discount_percent) if 'discount_percent' in locals() else 0,
                            "student_pay_eur": breakdown.get("student_pay_eur"),
                            "teacher_eur": breakdown.get("teacher_eur"),
                            "platform_eur": breakdown.get("platform_eur"),
                            "teacher_teo": breakdown.get("teacher_teo"),
                            "platform_teo": breakdown.get("platform_teo"),
                            "absorption_policy": breakdown.get("absorption_policy", "none"),
                            "teacher_accepted_teo": breakdown.get("teacher_teo", 0),
                            "tier_name": (tier.get("name") if tier else None),
                            "tier_teacher_split_percent": (tier.get("teacher_split_percent") if tier else None),
                            "tier_platform_split_percent": (tier.get("platform_split_percent") if tier else None),
                            "tier_max_accept_discount_ratio": (tier.get("max_accept_discount_ratio") if tier else None),
                            "tier_teo_bonus_multiplier": (tier.get("teo_bonus_multiplier") if tier else None),
                        }
                        try:
                            # Try to find an existing local snapshot created by the frontend
                            # (order_id like 'local_...' or synthetic) for same student/course
                            # and attach the external payment id to avoid duplicates.
                            from django.db import transaction as dj_transaction
                            from django.db.models import Q

                            attached = None
                            with dj_transaction.atomic():
                                # First try: match snapshots for same course where student is the current user
                                # or student is missing, and with common local prefixes.
                                attached = (
                                    PaymentDiscountSnapshot.objects.select_for_update()
                                    .filter(course=course, external_txn_id__isnull=True)
                                    .filter(Q(student=user) | Q(student__isnull=True))
                                    .filter(
                                        Q(order_id__startswith='local_') |
                                        Q(order_id__startswith='discount_synthetic_') |
                                        Q(order_id__startswith='discount_')
                                    )
                                    .order_by('-created_at')
                                    .first()
                                )
                                # If found, attach stripe id
                                if attached:
                                    attached.external_txn_id = str(payment_intent.id)
                                    attached.source = 'stripe'
                                    attached.save(update_fields=['external_txn_id', 'source'])
                            if attached:
                                snap = attached
                                created = False
                            else:
                                snap, created = get_or_create_payment_snapshot(order_id=str(payment_intent.id), defaults=defaults_payload, source="stripe")
                        except Exception:
                            snap, created = PaymentDiscountSnapshot.objects.get_or_create(order_id=str(payment_intent.id), defaults=defaults_payload)
                except Exception:
                    logger.exception("Failed to persist PaymentDiscountSnapshot at intent creation")
            except Exception as stripe_err:
                logger.error(f"❌ Stripe API error: {stripe_err}")
                return Response(
                    {
                        "error": f"Stripe payment error: {str(stripe_err)}",
                        "code": "STRIPE_API_ERROR",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "success": True,
                    "client_secret": payment_intent.client_secret,
                    "payment_intent_id": payment_intent.id,
                    "pricing": {
                        "original_price": str(original_price),
                        "discount_amount": str(discount_amount),
                        "final_price": str(final_price),
                        "discount_percent": discount_percent,
                    },
                    "discount_request_id": discount_request_id,
                    "course": {
                        "title": course.title,
                        "instructor": (
                            course.teacher.username if course.teacher else "Unknown"
                        ),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return Response(
                {
                    "error": "Failed to create payment intent",
                    "details": str(e),
                    "code": "PAYMENT_INTENT_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConfirmPaymentView(APIView):
    """
    Confirm successful payment and enroll student

    POST /api/v1/courses/{course_id}/payment/confirm/
    {
        "payment_intent_id": "pi_...",
        "process_discount": true
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            payment_intent_id = request.data.get("payment_intent_id")
            process_discount = request.data.get("process_discount", True)

            if not payment_intent_id:
                return Response(
                    {
                        "error": "Payment intent ID required",
                        "code": "MISSING_PAYMENT_INTENT",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify payment with Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status != "succeeded":
                return Response(
                    {
                        "error": "Payment not completed",
                        "payment_status": payment_intent.status,
                        "code": "PAYMENT_NOT_COMPLETED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract metadata
            from decimal import Decimal

            metadata = payment_intent.metadata
            discount_request_id = metadata.get("discount_request_id")
            use_teocoin_discount = metadata.get("use_teocoin_discount") == "True"
            original_price = Decimal(metadata.get("original_price", "0"))
            discount_amount = Decimal(metadata.get("discount_amount", "0"))
            metadata.get("student_address", "")

            # Check if already enrolled
            existing_enrollment = CourseEnrollment.objects.filter(
                student=user, course=course
            ).first()

            if existing_enrollment:
                return Response(
                    {
                        "error": "Already enrolled in this course",
                        "enrollment_id": existing_enrollment.pk,
                        "code": "ALREADY_ENROLLED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create enrollment with proper payment tracking
            final_price = original_price - discount_amount
            payment_method = "teocoin_discount" if use_teocoin_discount else "stripe"

            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                payment_method=payment_method,
                stripe_payment_intent_id=payment_intent_id,
                amount_paid_eur=final_price,
                original_price_eur=original_price,
                discount_amount_eur=discount_amount,
                teocoin_discount_request_id=discount_request_id,
            )

            logger.info(
                f"✅ Student enrolled: {user.username} in {course.title} for €{final_price}"
            )

            # CRITICAL: Deduct TeoCoin AFTER payment confirmed and enrollment created
            if use_teocoin_discount and discount_amount > 0:
                try:
                    logger.info(
                        f"💰 Payment confirmed, now deducting TeoCoin: {discount_amount} TEO"
                    )
                    db_teo_service = DBTeoCoinService()
                    pre_balance = db_teo_service.get_available_balance(user)
                    logger.info(
                        f"💰 TeoCoin balance before deduction: {pre_balance} TEO"
                    )

                    # Check if discount was already applied for this course
                    from blockchain.models import DBTeoCoinTransaction

                    existing_discount = DBTeoCoinTransaction.objects.filter(
                        user=user,
                        course=course,
                        transaction_type="spent_discount",
                        amount__lt=0,  # Negative amount indicates deduction
                    ).first()

                    if existing_discount:
                        logger.info(
                            f"✅ TeoCoin discount already applied: {abs(existing_discount.amount)} TEO for course {course_id}"
                        )
                        logger.info(
                            f"💡 Skipping duplicate deduction - discount was already processed"
                        )
                    else:
                        # Apply TeoCoin deduction for the first time
                        logger.info(
                            f"🔄 Applying TeoCoin deduction for course {course_id}..."
                        )

                        success = db_teo_service.deduct_balance(
                            user=user,
                            amount=discount_amount,
                            transaction_type="spent_discount",
                            description=f"TeoCoin discount for course: {course.title} ({discount_amount} TEO)",
                            course=course,
                        )

                        post_balance = db_teo_service.get_available_balance(user)
                        logger.info(
                            f"💰 TeoCoin balance after deduction: {post_balance} TEO"
                        )

                        if success:
                            logger.info(
                                f"✅ SUCCESS: TeoCoin deducted after payment - {discount_amount} TEO"
                            )
                            logger.info(
                                f"💰 Balance change: {pre_balance} → {post_balance} TEO"
                            )
                        else:
                            logger.error(
                                f"❌ FAILED: Could not deduct TeoCoin after payment - {discount_amount} TEO"
                            )
                            logger.error(
                                f"❌ This is a critical bug - discount applied but TeoCoin not deducted!"
                            )

                except Exception as e:
                    logger.error(f"❌ TeoCoin deduction error after payment: {e}")
                    logger.error(
                        f"❌ Course: {course.title}, User: {user.email}, Amount: {discount_amount} TEO"
                    )

            # Process teacher notification for discount decision
            teacher_notification_sent = False
            if use_teocoin_discount and discount_request_id and process_discount:
                try:
                    # Teacher has 2 hours to decide: Accept TEO vs Keep EUR
                    # This is handled by the TeoCoin discount service
                    teacher_notification_sent = True
                    logger.info(
                        f"📧 Teacher notification sent for discount request {discount_request_id}"
                    )

                except Exception as e:
                    logger.error(f"Teacher notification error: {e}")

            # Award purchase bonus TEO to student using clean database system
            try:
                from decimal import Decimal

                # 5 TEO bonus for course purchase
                purchase_bonus = Decimal("5.0")
                success = hybrid_teocoin_service.add_balance(
                    user=user,
                    amount=purchase_bonus,
                    transaction_type="course_purchase_bonus",
                    description=f"Purchase bonus for course: {course.title}",
                    course_id=str(course_id),
                )
                if success:
                    logger.info(
                        f"🪙 {purchase_bonus} TEO purchase bonus awarded to {user.email}"
                    )
                else:
                    logger.error(f"Failed to award purchase bonus to {user.email}")
            except Exception as e:
                logger.error(f"TEO purchase bonus error: {e}")

            # Persist discount snapshot idempotently
            try:
                # Determine discount_percent and accept flags
                discount_percent = int(metadata.get("discount_percent", 0))
                accept_teo = bool(request.data.get("accept_teo", False))
                accept_ratio = request.data.get("accept_ratio", None)
                if accept_ratio is not None:
                    try:
                        accept_ratio = _Decimal(str(accept_ratio))
                    except Exception:
                        accept_ratio = None

                # Resolve tier from teacher profile if available
                tier = None
                tp = getattr(course.teacher, "teacher_profile", None)
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

                breakdown = compute_discount_breakdown(
                    price_eur=original_price,
                    discount_percent=_Decimal(str(discount_percent)),
                    tier=tier,
                    accept_teo=accept_teo,
                    accept_ratio=accept_ratio,
                )

                # Persist snapshot idempotently; handle race via IntegrityError
                defaults_payload = {
                    "course": course,
                    "student": user,
                    "teacher": course.teacher if getattr(course, "teacher", None) else None,
                    "price_eur": original_price,
                    "discount_percent": discount_percent,
                    "student_pay_eur": breakdown["student_pay_eur"],
                    "teacher_eur": breakdown["teacher_eur"],
                    "platform_eur": breakdown["platform_eur"],
                    "teacher_teo": breakdown["teacher_teo"],
                    "platform_teo": breakdown["platform_teo"],
                    "absorption_policy": breakdown.get("absorption_policy", "none"),
                    "teacher_accepted_teo": breakdown.get("teacher_teo", 0),
                    "tier_name": (tier.get("name") if tier else None),
                    "tier_teacher_split_percent": (tier.get("teacher_split_percent") if tier else None),
                    "tier_platform_split_percent": (tier.get("platform_split_percent") if tier else None),
                    "tier_max_accept_discount_ratio": (tier.get("max_accept_discount_ratio") if tier else None),
                    "tier_teo_bonus_multiplier": (tier.get("teo_bonus_multiplier") if tier else None),
                }
                try:
                    # If a local snapshot exists for this student/course, attach the
                    # external payment_intent id to that snapshot instead of creating
                    # a new one with the stripe id.
                    from django.db import transaction as dj_transaction
                    from django.db.models import Q

                    attached = None
                    with dj_transaction.atomic():
                        attached = (
                            PaymentDiscountSnapshot.objects.select_for_update()
                            .filter(course=course, external_txn_id__isnull=True)
                            .filter(Q(student=user) | Q(student__isnull=True))
                            .filter(
                                Q(order_id__startswith='local_') |
                                Q(order_id__startswith='discount_synthetic_') |
                                Q(order_id__startswith='discount_')
                            )
                            .order_by('-created_at')
                            .first()
                        )
                        if attached:
                            attached.external_txn_id = str(payment_intent_id)
                            attached.source = 'stripe'
                            attached.save(update_fields=['external_txn_id', 'source'])
                    if attached:
                        snap = attached
                        created = False
                    else:
                        snap, created = get_or_create_payment_snapshot(order_id=str(payment_intent_id), defaults=defaults_payload, source="stripe")
                except Exception:
                    snap, created = PaymentDiscountSnapshot.objects.get_or_create(order_id=str(payment_intent_id), defaults=defaults_payload)

                # Structured logging for confirm snapshot
                try:
                    logger.info("discount_confirm", extra={
                        "event": "discount_confirm",
                        "order_id": str(payment_intent_id),
                        "user_id": user.id,
                        "course_id": course_id,
                        "teacher_id": course.teacher.id if getattr(course, "teacher", None) else None,
                        "student_id": user.id,
                        "discount_percent": discount_percent,
                        "accept_teo": accept_teo,
                        "accept_ratio": str(accept_ratio) if accept_ratio is not None else None,
                        "tier_name": (tier.get("name") if tier else None),
                        "created": created,
                        "snapshot_id": getattr(snap, "id", None),
                    })
                except Exception:
                    logger.debug("discount_confirm logging failed")

                # Ensure teacher receives an in-app notification for this snapshot
                try:
                    # Compute teacher_bonus from tier multiplier if available
                    teacher_teo_decimal = breakdown.get("teacher_teo", 0)
                    teacher_bonus = 0
                    try:
                        mult = tier.get("teo_bonus_multiplier") if tier else None
                        if mult:
                            # if teacher_teo includes bonus, extract bonus portion
                            teacher_bonus = float(Decimal(str(teacher_teo_decimal)) - (Decimal(str(teacher_teo_decimal)) / Decimal(str(mult))))
                    except Exception:
                        teacher_bonus = 0

                    # expiration: 24 hours from snapshot creation
                    expires_at = (snap.created_at + timedelta(hours=24)) if getattr(snap, 'created_at', None) else (timezone.now() + timedelta(hours=24))

                    # Log the notify call with offered preview when possible
                    try:
                        from services.discount_calc import compute_discount_breakdown
                        offered_preview = compute_discount_breakdown(
                            price_eur=snap.price_eur,
                            discount_percent=snap.discount_percent,
                            tier=None,
                            accept_teo=True,
                            accept_ratio=1,
                        )
                        offered_teacher_preview = offered_preview.get("teacher_teo")
                    except Exception:
                        offered_teacher_preview = breakdown.get("teacher_teo", 0)

                    try:
                        logger.info("discount_notify_call", extra={
                            "event": "discount_notify_call",
                            "order_id": getattr(snap, "order_id", None),
                            "snapshot_id": getattr(snap, "id", None),
                            "offered_teacher_teo": str(offered_teacher_preview),
                        })
                    except Exception:
                        pass

                    teocoin_notification_service.notify_teacher_discount_pending(
                        teacher=snap.teacher,
                        student=snap.student,
                        course_title=snap.course.title if snap.course else "",
                        discount_percent=int(snap.discount_percent or 0),
                        teo_cost=float(breakdown.get("teacher_teo", 0)),
                        teacher_bonus=teacher_bonus,
                        request_id=snap.id,
                        expires_at=expires_at,
                        offered_teacher_teo=float(offered_teacher_preview) if offered_teacher_preview is not None else None,
                    )
                except Exception as e:
                    logger.error(f"Failed to send teocoin teacher notification for snapshot {getattr(snap,'id',None)}: {e}")

            except Exception as e:
                logger.error(f"Payment confirmation error: {e}")
                return Response(
                    {
                        "error": "Failed to confirm payment",
                        "details": str(e),
                        "code": "PAYMENT_CONFIRMATION_ERROR",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            # Outer catch-all for ConfirmPaymentView
            logger.error(f"Payment confirmation outer error: {e}")
            return Response(
                {
                    "error": "Failed to confirm payment",
                    "details": str(e),
                    "code": "PAYMENT_CONFIRMATION_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaymentSummaryView(APIView):
    """
    Get payment summary for a course including TeoCoin discount calculations

    GET /api/v1/courses/{course_id}/payment/summary/?discount_percent=15&student_address=0x...
    """

    # TEMPORARY: Remove authentication for debugging frontend issue
    # permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)

            # Base pricing
            original_price = course.price_eur

            # Course information
            course_info = {
                "id": course.pk,  # Use .pk instead of .id for better compatibility
                "title": course.title,
                "instructor": course.teacher.username if course.teacher else "Unknown",
                "description": (
                    course.description[:200] + "..."
                    if len(course.description) > 200
                    else course.description
                ),
                "duration_hours": getattr(course, "duration_hours", None),
                "skill_level": getattr(course, "skill_level", None),
            }

            # Student enrollment status
            user = request.user
            # Handle anonymous users for debugging
            if user.is_authenticated:
                is_enrolled = CourseEnrollment.objects.filter(
                    student=user, course=course
                ).exists()
            else:
                is_enrolled = False

            # Create pricing options array for frontend compatibility
            pricing_options = []

            # Always add fiat payment option
            pricing_options.append(
                {
                    "method": "fiat",
                    "price": str(original_price),
                    "currency": "EUR",
                    "description": "Pay with Credit/Debit Card",
                    "reward": "50",  # TEO rewards for fiat payment
                    "disabled": False,
                }
            )

            # Add TeoCoin discount option if available AND teacher has wallet
            teacher_has_wallet = bool(getattr(course.teacher, "wallet_address", None))

            if (
                hasattr(course, "teocoin_discount_percent")
                and course.teocoin_discount_percent > 0
                and teacher_has_wallet
            ):

                # Use compute_discount_breakdown to provide server-truth breakdown
                discount_percent = int(course.teocoin_discount_percent)
                try:
                    # Resolve tier from teacher profile if available
                    tier = None
                    tp = getattr(course.teacher, "teacher_profile", None)
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

                    breakdown = compute_discount_breakdown(
                        price_eur=original_price,
                        discount_percent=_Decimal(str(discount_percent)),
                        tier=tier,
                        accept_teo=False,
                        accept_ratio=None,
                    )

                    pricing_options.append(
                        {
                            "method": "teocoin",
                            "price": str(breakdown["teacher_teo"]),
                            "currency": "TEO",
                            "description": f"Use TEO for {discount_percent}% discount",
                            "discount": discount_percent,
                            "discount_percent": discount_percent,
                            "final_price_eur": str(breakdown["student_pay_eur"]),
                            "savings_eur": str((original_price - breakdown["student_pay_eur"])),
                            "disabled": False,
                            "breakdown": breakdown,
                        }
                    )
                except Exception as e:
                    logger.exception(f"Error computing discount breakdown for course {course_id}: {e}")
                    # Fallback to previous simple representation
                    discount_amount = (
                        original_price * _Decimal(discount_percent) / _Decimal("100")
                    )
                    final_price = original_price - discount_amount
                    teo_cost_eur = discount_amount
                    teo_cost_tokens = int(teo_cost_eur * 10)

                    pricing_options.append(
                        {
                            "method": "teocoin",
                            "price": str(teo_cost_tokens),
                            "currency": "TEO",
                            "description": f"Use TEO for {discount_percent}% discount",
                            "discount": discount_percent,
                            "discount_percent": discount_percent,
                            "final_price_eur": str(final_price),
                            "savings_eur": str(discount_amount),
                            "disabled": False,
                        }
                    )
            elif (
                hasattr(course, "teocoin_discount_percent")
                and course.teocoin_discount_percent > 0
                and not teacher_has_wallet
            ):
                # Add disabled TeoCoin option with explanation
                pricing_options.append(
                    {
                        "method": "teocoin",
                        "price": "N/A",
                        "currency": "TEO",
                        "description": "TeoCoin discount unavailable (teacher wallet not connected)",
                        "discount": int(course.teocoin_discount_percent),
                        "discount_percent": int(course.teocoin_discount_percent),
                        "final_price_eur": str(original_price),
                        "savings_eur": "0",
                        "disabled": True,
                        "disabled_reason": "Teacher wallet address not configured",
                    }
                )

            # Basic pricing summary for backward compatibility
            pricing_summary = {
                "original_price": str(original_price),
                "currency": "EUR",
                "discount_available": hasattr(course, "teocoin_discount_percent")
                and course.teocoin_discount_percent > 0,
                "max_discount_percent": (
                    int(course.teocoin_discount_percent)
                    if hasattr(course, "teocoin_discount_percent")
                    else 0
                ),
            }

            return Response(
                {
                    "success": True,
                    "course": course_info,
                    "pricing": pricing_summary,
                    "pricing_options": pricing_options,
                    "student_status": {
                        "is_enrolled": is_enrolled,
                        "can_enroll": not is_enrolled,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Payment summary error: {e}")
            return Response(
                {
                    "error": "Failed to get payment summary",
                    "details": str(e),
                    "code": "PAYMENT_SUMMARY_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeoCoinDiscountStatusView(APIView):
    """
    Get status of TeoCoin discount requests for student

    GET /api/v1/courses/{course_id}/payment/discount-status/?student_address=0x...
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            student_address = request.query_params.get("student_address", "")

            if not student_address:
                return Response(
                    {
                        "error": "Student address required",
                        "code": "MISSING_STUDENT_ADDRESS",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get discount requests for this student and course
            # For now, return a simple response since we're migrating to Gas-Free V2
            # TODO: Implement proper V2 request tracking

            return Response(
                {
                    "success": True,
                    "latest_request": None,  # No active requests for now
                    "requests": [],
                    "message": "Migrating to Gas-Free V2 system",
                }
            )

        except Exception as e:
            logger.error(f"Discount status error: {e}")
            return Response(
                {
                    "error": "Failed to get discount status",
                    "details": str(e),
                    "code": "DISCOUNT_STATUS_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
