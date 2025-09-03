"""
Teacher Choice API - Handle TeoCoin discount decisions

This API allows teachers to:
1. View pending discount requests
2. Accept/decline TeoCoin discount requests
3. Configure their choice preferences
4. View earnings comparisons for each choice
"""

from decimal import Decimal
import logging
from django.db import transaction
from typing import Any

from courses.models import TeacherChoicePreference, TeacherDiscountDecision
from courses.serializers import (
    TeacherChoicePreferenceSerializer,
    TeacherDiscountDecisionSerializer,
)
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.permissions import IsTeacher
from decimal import Decimal
from rewards.models import PaymentDiscountSnapshot, BlockchainTransaction, TokenBalance
from services.reward_service import reward_service


class TeacherChoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher discount decisions
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherDiscountDecisionSerializer

    # pyright: ignore[reportIncompatibleMethodOverride]
    def get_queryset(self) -> Any:
        """Return only decisions for the current teacher"""
        return TeacherDiscountDecision.objects.filter(
            teacher=self.request.user
        ).select_related("student", "course")

    def partial_update(self, request, *args, **kwargs):
        """
        Standardize decision update via PATCH /teacher-choices/{id}/ with body like
        {"status": "accepted"|"rejected"|"declined"} or {"decision": ...}.
        Accept common synonyms and enforce ownership and expiration.
        """
        try:
            instance = self.get_object()

            # Ownership already enforced by queryset; double-check for clarity
            if instance.teacher_id != request.user.id:
                return Response({"success": False, "error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            raw_status = request.data.get("status") or request.data.get("decision")
            if not raw_status:
                return Response({"success": False, "error": "Missing status"}, status=status.HTTP_400_BAD_REQUEST)

            val = str(raw_status).strip().lower()
            # Map common synonyms
            if val in ("accept", "accepted", "approve", "approved", "true", "yes"):
                new_decision = "accepted"
            elif val in ("reject", "rejected", "declined", "decline", "false", "no"):
                new_decision = "declined"
            else:
                return Response({"success": False, "error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate current state
            if instance.decision != "pending":
                return Response({"success": False, "error": f"Decision already {instance.decision}"}, status=status.HTTP_409_CONFLICT)
            if instance.is_expired:
                # Allow a small time skew for test and init delays (10s)
                if (timezone.now() - instance.expires_at).total_seconds() > 10:
                    return Response({"success": False, "error": "Decision period has expired"}, status=status.HTTP_409_CONFLICT)

            # Apply state change
            with transaction.atomic():
                pre_status = instance.decision
                instance.decision = new_decision
                instance.decision_made_at = timezone.now()
                instance.save(update_fields=["decision", "decision_made_at", "updated_at"])

            earnings_accepted = instance.teacher_earnings_if_accepted
            earnings_declined = instance.teacher_earnings_if_declined

            payload = {
                "success": True,
                "decision_id": instance.id,
                "decision": instance.decision,
                "earnings": {
                    "accepted": {
                        "fiat": str(earnings_accepted["fiat"]),
                        "teo": str(earnings_accepted["teo"]),
                    },
                    "declined": {
                        "fiat": str(earnings_declined["fiat"]),
                        "teo": str(earnings_declined["teo"]),
                    },
                },
            }
            # Structured log
            try:
                logging.getLogger(__name__).info(
                    "teacher_choice_partial_update",
                    extra={
                        "event": "teacher_choice_partial_update",
                        "decision_id": instance.id,
                        "teacher_id": request.user.id,
                        "pre_status": pre_status,
                        "post_status": instance.decision,
                    },
                )
            except Exception:
                pass

            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Get all pending discount requests for the teacher"""
        pending_requests = (
            self.get_queryset()
            .filter(decision="pending", expires_at__gt=timezone.now())
            .order_by("-created_at")
        )

        serializer = self.get_serializer(pending_requests, many=True)
        return Response(
            {
                "success": True,
                "pending_requests": serializer.data,
                "count": pending_requests.count(),
            }
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept a TeoCoin discount request"""
        try:
            decision = self.get_object()

            # Validate decision can be made. Allow small time skew for init/test delays (10s)
            if decision.is_expired:
                if (timezone.now() - decision.expires_at).total_seconds() > 10:
                    return Response(
                        {"success": False, "error": "Decision period has expired"},
                        status=status.HTTP_409_CONFLICT,
                    )

            if decision.decision == "accepted":
                # Already accepted: best-effort backfill snapshot/ledger to ensure consistency
                try:
                    from decimal import Decimal, ROUND_DOWN

                    # Prefer the snapshot teacher_teo (source of truth) when available
                    snap = (
                        PaymentDiscountSnapshot.objects.filter(
                            teacher=decision.teacher,
                            student=decision.student,
                            course=decision.course,
                        )
                        .order_by("-created_at")
                        .first()
                    )

                    if snap and getattr(snap, "teacher_teo", None) is not None and Decimal(str(snap.teacher_teo)) != Decimal("0"):
                        teo_amount = Decimal(str(snap.teacher_teo))
                    else:
                        teo_amount = Decimal(str(decision.teacher_earnings_if_accepted.get("teo", 0)))

                    teo_amount_q = teo_amount.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

                    if snap and (getattr(snap, "teacher_accepted_teo", None) is None or Decimal(str(snap.teacher_accepted_teo)) == Decimal("0")):
                        PaymentDiscountSnapshot.objects.filter(pk=snap.pk).update(teacher_accepted_teo=teo_amount_q)

                    # Ensure ledger exists
                    existing_tx = BlockchainTransaction.objects.filter(
                        user=decision.teacher,
                        transaction_type="course_earned",
                        related_object_id=str(decision.course.id) if decision.course else None,
                        amount=teo_amount_q,
                        status__in=["completed", "confirmed"],
                    ).first()
                    if not existing_tx:
                        reward_service._create_reward_transaction(
                            user=decision.teacher,
                            amount=teo_amount_q,
                            transaction_type="course_earned",
                            related_object_id=str(decision.course.id) if decision.course else "",
                            notes=f"Course earned payout for decision {decision.id} (idempotent)",
                        )
                        # TokenBalance best-effort
                        try:
                            token_balance, _ = TokenBalance.objects.get_or_create(user=decision.teacher)
                            token_balance.balance = (token_balance.balance or Decimal("0")) + teo_amount_q
                            token_balance.save()
                        except Exception:
                            pass
                except Exception:
                    pass

                # Idempotent success
                ser = self.get_serializer(decision)
                return Response({"success": True, "decision": ser.data}, status=status.HTTP_200_OK)
            if decision.decision == "declined":
                return Response(
                    {"success": False, "error": "Decision already declined"},
                    status=status.HTTP_409_CONFLICT,
                )

            # Update decision (atomic)
            with transaction.atomic():
                pre_status = decision.decision
                decision.decision = "accepted"
                decision.decision_made_at = timezone.now()
                decision.save(update_fields=["decision", "decision_made_at", "updated_at"])

                # Attempt to update the immutable snapshot: find the most
                # relevant PaymentDiscountSnapshot for this trio and set the
                # teacher_accepted_teo to the accepted amount (8 d.p.).
                try:
                    snap = (
                        PaymentDiscountSnapshot.objects.filter(
                            teacher=decision.teacher,
                            student=decision.student,
                            course=decision.course,
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    if snap:
                        # teacher_earnings_if_accepted returns Decimal teo amount
                        teo_amount = Decimal(str(decision.teacher_earnings_if_accepted.get("teo", 0)))
                        # Quantize to 8 d.p.
                        from decimal import ROUND_DOWN

                        teo_amount_q = teo_amount.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                        PaymentDiscountSnapshot.objects.filter(pk=snap.pk).update(teacher_accepted_teo=teo_amount_q)
                except Exception:
                    # Best-effort: don't fail the accept if snapshot update fails
                    pass

                # Schedule ledger creation AFTER this transaction commits so
                # that we don't create ledger entries that might be rolled back
                # with the decision change. The ledger creation is idempotent
                # (checks for existing_tx) and will mark teacher_payment_completed
                # only when the ledger is successfully created.
                def _create_ledger_and_mark():
                    try:
                        # Re-fetch fresh decision row to avoid stale state
                        dec = TeacherDiscountDecision.objects.select_related("teacher", "course").get(pk=decision.pk)

                        # Prefer snapshot value to avoid truncated wei stored on decision
                        snap_local = (
                            PaymentDiscountSnapshot.objects.filter(
                                teacher=dec.teacher,
                                student=dec.student,
                                course=dec.course,
                            )
                            .order_by("-created_at")
                            .first()
                        )
                        if snap_local and getattr(snap_local, "teacher_teo", None) is not None and Decimal(str(snap_local.teacher_teo)) != Decimal("0"):
                            teo_amount = Decimal(str(snap_local.teacher_teo))
                        else:
                            teo_amount = Decimal(str(dec.teacher_earnings_if_accepted.get("teo", 0)))
                        teo_amount_q = teo_amount.quantize(Decimal("0.00000001"))

                        existing_tx = BlockchainTransaction.objects.filter(
                            user=dec.teacher,
                            transaction_type="course_earned",
                            related_object_id=str(dec.course.id) if dec.course else None,
                            amount=teo_amount_q,
                            status__in=["completed", "confirmed"],
                        ).first()

                        if not existing_tx:
                            # Create ledger transaction
                            tx = reward_service._create_reward_transaction(
                                user=dec.teacher,
                                amount=teo_amount_q,
                                transaction_type="course_earned",
                                related_object_id=str(dec.course.id) if dec.course else "",
                                notes=f"Course earned payout for decision {dec.id}",
                            )

                            # Update or create TokenBalance
                            try:
                                token_balance, _ = TokenBalance.objects.get_or_create(user=dec.teacher)
                                token_balance.balance = (token_balance.balance or Decimal("0")) + teo_amount_q
                                token_balance.save()
                            except Exception:
                                # best-effort: log and continue
                                logging.getLogger(__name__).exception(
                                    "Failed to update TokenBalance for teacher %s", dec.teacher_id
                                )

                        # Mark payment completed (whether existing_tx or newly created)
                        TeacherDiscountDecision.objects.filter(pk=dec.pk).update(
                            teacher_payment_completed=True, updated_at=timezone.now()
                        )
                    except Exception:
                        logging.getLogger(__name__).exception(
                            "Failed to create ledger/mark teacher_payment_completed for decision %s", decision.pk
                        )

                # Register to run after commit
                transaction.on_commit(_create_ledger_and_mark)

            # Calculate earnings breakdown
            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined

            # Structured log
            try:
                logging.getLogger(__name__).info(
                    "teacher_choice_accept",
                    extra={
                        "event": "teacher_choice_accept",
                        "decision_id": decision.id,
                        "teacher_id": request.user.id,
                        "pre_status": pre_status,
                        "post_status": decision.decision,
                    },
                )
            except Exception:
                pass

            # Return updated decision object
            ser = self.get_serializer(decision)
            return Response(
                {
                    "success": True,
                    "decision": ser.data,
                    "earnings": {
                        "choice_made": "accepted",
                        "fiat_amount": str(earnings_accepted["fiat"]),
                        "teo_amount": str(earnings_accepted["teo"]),
                        "total_teo": str(earnings_accepted["total_teo"]),
                        "alternative_fiat": str(earnings_declined["fiat"]),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """Decline a TeoCoin discount request"""
        try:
            decision = self.get_object()

            # Validate decision can be made. Allow small time skew for init/test delays (10s)
            if decision.is_expired:
                if (timezone.now() - decision.expires_at).total_seconds() > 10:
                    return Response(
                        {"success": False, "error": "Decision period has expired"},
                        status=status.HTTP_409_CONFLICT,
                    )
            if decision.decision == "declined":
                # Idempotent success
                ser = self.get_serializer(decision)
                return Response({"success": True, "decision": ser.data}, status=status.HTTP_200_OK)
            if decision.decision == "accepted":
                return Response(
                    {"success": False, "error": "Decision already accepted"},
                    status=status.HTTP_409_CONFLICT,
                )

            # Update decision (atomic)
            with transaction.atomic():
                pre_status = decision.decision
                decision.decision = "declined"
                decision.decision_made_at = timezone.now()
                decision.save(update_fields=["decision", "decision_made_at", "updated_at"])

            # Calculate earnings breakdown
            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined

            # Structured log
            try:
                logging.getLogger(__name__).info(
                    "teacher_choice_decline",
                    extra={
                        "event": "teacher_choice_decline",
                        "decision_id": decision.id,
                        "teacher_id": request.user.id,
                        "pre_status": pre_status,
                        "post_status": decision.decision,
                    },
                )
            except Exception:
                pass

            # Return updated decision object
            ser = self.get_serializer(decision)
            return Response(
                {
                    "success": True,
                    "decision": ser.data,
                    "earnings": {
                        "choice_made": "declined",
                        "fiat_amount": str(earnings_declined["fiat"]),
                        "teo_amount": str(earnings_declined["teo"]),
                        "alternative_fiat_loss": str(earnings_accepted["fiat"]),
                        "alternative_teo_loss": str(earnings_accepted["teo"]),
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def earnings_comparison(self, request, pk=None):
        """Compare earnings for accepting vs declining"""
        try:
            decision = self.get_object()

            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined

            # Calculate the difference
            fiat_difference = earnings_declined["fiat"] - earnings_accepted["fiat"]
            teo_gained = earnings_accepted["teo"]

            return Response(
                {
                    "success": True,
                    "decision_id": decision.id,
                    "course": {
                        "title": (
                            decision.course.title
                            if decision.course
                            else f"Course #{decision.course.id}"
                        ),
                        "price": str(decision.course_price),
                        "discount_percent": decision.discount_percentage,
                    },
                    "student": {
                        "email": decision.student.email,
                        "teo_cost": decision.teo_cost_display,
                    },
                    "teacher_tier": {
                        "current_tier": decision.teacher_staking_tier,
                        "commission_rate": f"{decision.teacher_commission_rate}%",
                    },
                    "comparison": {
                        "accept_teocoin": {
                            "fiat_earnings": str(earnings_accepted["fiat"]),
                            "teo_earnings": str(earnings_accepted["teo"]),
                            "description": f'€{earnings_accepted["fiat"]} + {earnings_accepted["teo"]} TEO',
                        },
                        "decline_teocoin": {
                            "fiat_earnings": str(earnings_declined["fiat"]),
                            "teo_earnings": str(earnings_declined["teo"]),
                            "description": f'€{earnings_declined["fiat"]} + 0 TEO',
                        },
                        "trade_off": {
                            "fiat_loss_if_accept": str(fiat_difference),
                            "teo_gain_if_accept": str(teo_gained),
                            "recommendation": (
                                "accept"
                                if teo_gained > fiat_difference * 2
                                else "consider"
                            ),
                        },
                    },
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TeacherPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher choice preferences
    """

    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherChoicePreferenceSerializer

    # pyright: ignore[reportIncompatibleMethodOverride]
    def get_queryset(self) -> Any:
        """Return preference for the current teacher"""
        return TeacherChoicePreference.objects.filter(teacher=self.request.user)

    # pyright: ignore[reportIncompatibleMethodOverride]
    def get_object(self) -> Any:
        """Get or create preference for the current teacher"""
        preference, created = TeacherChoicePreference.objects.get_or_create(
            teacher=self.request.user
        )
        return preference

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get current teacher preferences"""
        preference = self.get_object()
        serializer = self.get_serializer(preference)

        return Response(
            {
                "success": True,
                "preferences": serializer.data,
                "description": {
                    "always_accept": "Automatically accept all TeoCoin discounts",
                    "always_decline": "Automatically decline all TeoCoin discounts",
                    "manual": "Review each discount request manually",
                    "threshold_based": f"Auto-accept if TEO amount > {preference.minimum_teo_threshold or 0}",
                },
            }
        )

    @action(detail=False, methods=["post"])
    def update_preference(self, request):
        """Update teacher choice preferences"""
        try:
            preference = self.get_object()

            # Validate preference choice
            valid_choices = [
                choice[0] for choice in TeacherChoicePreference.PREFERENCE_CHOICES
            ]
            new_preference = request.data.get("preference")

            if new_preference not in valid_choices:
                return Response(
                    {
                        "success": False,
                        "error": f"Invalid preference. Must be one of: {valid_choices}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update preference
            preference.preference = new_preference

            # Handle threshold-based preference
            if new_preference == "threshold_based":
                threshold = request.data.get("minimum_teo_threshold")
                if not threshold or Decimal(str(threshold)) <= 0:
                    return Response(
                        {
                            "success": False,
                            "error": "minimum_teo_threshold required for threshold_based preference",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                preference.minimum_teo_threshold = Decimal(str(threshold))

            # Update notification preferences
            if "email_notifications" in request.data:
                preference.email_notifications = bool(
                    request.data["email_notifications"]
                )
            if "immediate_notifications" in request.data:
                preference.immediate_notifications = bool(
                    request.data["immediate_notifications"]
                )

            preference.save()

            serializer = self.get_serializer(preference)
            return Response(
                {
                    "success": True,
                    "message": "Preferences updated successfully",
                    "preferences": serializer.data,
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get teacher decision statistics"""
        try:
            # Get all decisions for this teacher
            decisions = TeacherDiscountDecision.objects.filter(teacher=request.user)

            total = decisions.count()
            accepted = decisions.filter(decision="accepted").count()
            declined = decisions.filter(decision="declined").count()
            pending = decisions.filter(
                decision="pending", expires_at__gt=timezone.now()
            ).count()
            expired = (
                decisions.filter(decision="expired").count()
                + decisions.filter(
                    decision="pending", expires_at__lte=timezone.now()
                ).count()
            )

            # Calculate earnings
            accepted_decisions = decisions.filter(decision="accepted")
            total_fiat_earned = sum(
                [d.teacher_earnings_if_accepted["fiat"] for d in accepted_decisions]
            )
            total_teo_earned = sum(
                [d.teacher_earnings_if_accepted["teo"] for d in accepted_decisions]
            )

            declined_decisions = decisions.filter(decision="declined")
            total_fiat_from_declined = sum(
                [d.teacher_earnings_if_declined["fiat"] for d in declined_decisions]
            )

            return Response(
                {
                    "success": True,
                    "statistics": {
                        "total_requests": total,
                        "accepted": accepted,
                        "declined": declined,
                        "pending": pending,
                        "expired": expired,
                        "acceptance_rate": (
                            f"{(accepted/total*100):.1f}%" if total > 0 else "0%"
                        ),
                    },
                    "earnings": {
                        "total_fiat_from_teocoin": str(total_fiat_earned),
                        "total_teo_earned": str(total_teo_earned),
                        "total_fiat_from_declined": str(total_fiat_from_declined),
                        # Estimate TEO value
                        "teo_value_estimate": f'{total_teo_earned * Decimal("1.2"):.2f} EUR',
                    },
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
