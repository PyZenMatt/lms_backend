"""
TeoCoin Discount Notification Service

Handles notifications for the TeoCoin discount system.
Sends notifications to teachers and students about discount requests and decisions.
"""

import logging
from typing import Optional, Union, Any
import decimal

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from notifications.models import Notification
from users.models import User

logger = logging.getLogger(__name__)


class TeoCoinDiscountNotificationService:
    """Service for handling TeoCoin discount system notifications"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def notify_teacher_discount_pending(
        self,
        teacher: User,
        student: User,
        course_title: str,
        discount_percent: int,
        teo_cost: float,
        teacher_bonus: float,
        request_id: int,
        expires_at: timezone.datetime,
    offered_teacher_teo: Optional[Union[float, str, decimal.Decimal]] = None,
    offered_platform_teo: Optional[Union[float, str, decimal.Decimal]] = None,
        decision_id: Optional[int] = None,
    ) -> bool:
        """
        Notify teacher that a student received a discount and they need to choose EUR vs TEO

        Args:
            teacher: Teacher user
            student: Student user
            course_title: Course title
            discount_percent: Discount percentage
            teo_cost: TEO cost from student
            teacher_bonus: TEO bonus for teacher
            request_id: Discount request ID
            expires_at: Request expiration time

            offered_teacher_teo: float = None,
            offered_platform_teo: float = None,
        """
        try:

            # Structured enrichment log: what we will notify
            try:
                # Attempt to enrich the log with snapshot/tier info when possible
                snapshot_id = None
                tier_name = None
                # Try to locate a PaymentDiscountSnapshot by order_id == request_id OR by pk == request_id
                try:
                    from rewards.models import PaymentDiscountSnapshot

                    snap = PaymentDiscountSnapshot.objects.filter(order_id=str(request_id)).first()
                    if not snap:
                        # maybe caller passed the snapshot.id (int)
                        try:
                            snap = PaymentDiscountSnapshot.objects.filter(pk=request_id).first()
                        except Exception:
                            snap = None

                    if snap:
                        snapshot_id = getattr(snap, "id", None)
                        tier_name = getattr(snap, "tier_name", None)
                except Exception:
                    snap = None

                # If offered_teacher_teo is missing, try to compute it from snapshot
                if offered_teacher_teo is None:
                    try:
                        from services.discount_calc import compute_discount_breakdown

                        if snap:
                            # Only build a tier dict if snapshot contains tier values.
                            # If all are None, prefer passing tier=None so the discount
                            # calculator can resolve the teacher's current tier.
                            tier_vals = {
                                "teacher_split_percent": getattr(snap, "tier_teacher_split_percent", None),
                                "platform_split_percent": getattr(snap, "tier_platform_split_percent", None),
                                "max_accept_discount_ratio": getattr(snap, "tier_max_accept_discount_ratio", None),
                                "teo_bonus_multiplier": getattr(snap, "tier_teo_bonus_multiplier", None),
                                "name": getattr(snap, "tier_name", None),
                            }
                            # If all tier values are falsy/None, let compute_discount_breakdown
                            # resolve tier by passing None.
                            if any(v is not None for v in tier_vals.values()):
                                tier = tier_vals
                            else:
                                tier = None
                            max_ratio = None
                            try:
                                max_ratio = (
                                    decimal.Decimal(str(tier.get("max_accept_discount_ratio")))
                                    if tier and tier.get("max_accept_discount_ratio") is not None
                                    else None
                                )
                            except Exception:
                                max_ratio = None

                            accept_ratio = max_ratio if max_ratio is not None else decimal.Decimal("1")

                            breakdown = compute_discount_breakdown(
                                price_eur=snap.price_eur,
                                discount_percent=decimal.Decimal(str(getattr(snap, "discount_percent", 0))),
                                tier=tier,
                                accept_teo=True,
                                accept_ratio=accept_ratio,
                            )
                            offered_teacher_val = breakdown.get("teacher_teo")
                            if offered_teacher_val is not None:
                                # keep numeric value but ensure decimal for formatting later
                                offered_teacher_teo = offered_teacher_val
                    except Exception:
                        offered_teacher_teo = offered_teacher_teo

                self.logger.info("discount_pending_notified_enrichment", extra={
                    "event": "discount_pending_notified_enrichment",
                    "order_id": request_id,
                    "teacher_id": getattr(teacher, "id", None),
                    "snapshot_id": snapshot_id,
                    "tier_name": tier_name,
                    "offered_teacher_teo": str(offered_teacher_teo) if offered_teacher_teo is not None else None,
                })
            except Exception:
                pass

            # Calculate time remaining
            time_remaining = expires_at - timezone.now()
            hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))

            # Prepare display values
            # normalize decimals
            try:
                teo_cost_dec = decimal.Decimal(str(teo_cost or 0))
            except Exception:
                teo_cost_dec = decimal.Decimal(0)
            try:
                teacher_bonus_dec = decimal.Decimal(str(teacher_bonus or 0))
            except Exception:
                teacher_bonus_dec = decimal.Decimal(0)

            # Offered teacher total TEO: prefer explicit offered_teacher_teo, else sum of teo_cost+bonus
            try:
                if offered_teacher_teo is not None:
                    offered_teacher_dec = decimal.Decimal(str(offered_teacher_teo))
                else:
                    offered_teacher_dec = teo_cost_dec + teacher_bonus_dec
            except Exception:
                offered_teacher_dec = teo_cost_dec + teacher_bonus_dec

            # Format strings: TEO 8 decimal places, EUR-like 2 decimals where needed
            q = decimal.Decimal("0.00000001")
            offered_teacher_str = f"{offered_teacher_dec.quantize(q):.8f}"
            teo_cost_str = f"{teo_cost_dec.quantize(q):.8f}"
            teacher_bonus_str = f"{teacher_bonus_dec.quantize(q):.8f}"

            # Build message including offered TEO (8 d.p.)
            message = (
                f"🎓 Student {student.get_full_name() or student.username} got a {discount_percent}% "
                f"discount on '{course_title}' and is enrolled! \n\n"
                f"💰 Choose your payment: \n"
                f"🪙 Accept TEO: {offered_teacher_str} TEO total (student TEO: {teo_cost_str} TEO + bonus: {teacher_bonus_str} TEO)\n"
                f"💰 Keep EUR: Full EUR commission (platform absorbs discount)\n\n"
                f"⏰ Decide within {hours_remaining} hours or EUR will be chosen automatically."
            )

            # Prefer linking directly to the TeacherDiscountDecision when available.
            # Fallback to the request/snapshot id for legacy flows.
            notification = Notification.objects.create(
                user=teacher,
                message=message,
                notification_type="teocoin_discount_pending",
                related_object_id=(decision_id if decision_id is not None else request_id),
            )

            # Structured log indicating that notification was emitted
            try:
                self.logger.info("discount_pending_notified", extra={
                    "event": "discount_pending_notified",
                    "order_id": request_id,
                    "teacher_id": getattr(teacher, "id", None),
                    "offered_teacher_teo": str(offered_teacher_dec) if offered_teacher_teo is not None else None,
                    "tier_name": None,
                })
            except Exception:
                pass

            # Send email notification if enabled
            if getattr(settings, "SEND_DISCOUNT_EMAILS", True):
                self._send_teacher_email_notification(
                    teacher=teacher,
                    student=student,
                    course_title=course_title,
                    discount_percent=discount_percent,
                    teo_cost=float(teo_cost_dec),
                    teacher_bonus=float(teacher_bonus_dec),
                    hours_remaining=hours_remaining,
                )

            self.logger.info(
                f"Teacher discount notification sent to {teacher.username} for request {request_id} (decision_id={decision_id})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to send teacher notification: {e}")
            return False

    def notify_student_teacher_decision(
        self,
        student: User,
        teacher: User,
        course_title: str,
        decision: str,  # 'accepted' or 'declined'
        teo_amount: Optional[float] = None,
    ) -> bool:
        """
        Notify student of teacher's EUR vs TEO decision

        Args:
            student: Student user
            teacher: Teacher user
            course_title: Course title
            decision: 'accepted' or 'declined'
            teo_amount: TEO amount if accepted

        Returns:
            bool: Success status
        """
        try:
            if decision == "accepted":
                message = (
                    f"🎉 Great news! Teacher {teacher.get_full_name() or teacher.username} "
                    f"accepted your {teo_amount:.2f} TEO payment for '{course_title}'!\n\n"
                    f"✅ Your discount is confirmed\n"
                    f"🪙 Your TEO tokens are being used for teacher staking benefits\n"
                    f"📚 You have full access to the course"
                )
                notification_type = "teocoin_discount_accepted"
            else:
                message = (
                    f"📊 Teacher {teacher.get_full_name() or teacher.username} chose EUR payment "
                    f"for '{course_title}'\n\n"
                    f"✅ Your discount is still confirmed (platform absorbed the cost)\n"
                    f"🪙 Your TEO tokens have been returned\n"
                    f"📚 You have full access to the course"
                )
                notification_type = "teocoin_discount_rejected"

            notification = Notification.objects.create(
                user=student, message=message, notification_type=notification_type
            )

            self.logger.info(
                f"Student decision notification sent to {student.username}: {decision}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to send student decision notification: {e}")
            return False

    def notify_teacher_timeout_warning(
        self,
        teacher: User,
        student: User,
        course_title: str,
        request_id: int,
        minutes_remaining: int,
    ) -> bool:
        """
        Send timeout warning to teacher

        Args:
            teacher: Teacher user
            student: Student user
            course_title: Course title
            request_id: Request ID
            minutes_remaining: Minutes until timeout

        Returns:
            bool: Success status
        """
        try:
            message = (
                f"⏰ URGENT: Only {minutes_remaining} minutes left to choose your payment method!\n\n"
                f"Student: {student.get_full_name() or student.username}\n"
                f"Course: '{course_title}'\n\n"
                f"If you don't choose, you'll automatically receive full EUR commission."
            )

            notification = Notification.objects.create(
                user=teacher,
                message=message,
                notification_type="teocoin_discount_pending",
                related_object_id=request_id,
            )

            # Send urgent email
            if getattr(settings, "SEND_URGENT_EMAILS", True):
                self._send_urgent_email(teacher, course_title, minutes_remaining)

            self.logger.info(
                f"Timeout warning sent to {teacher.username} for request {request_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to send timeout warning: {e}")
            return False

    def notify_request_expired(
        self, teacher: User, student: User, course_title: str, request_id: int
    ) -> bool:
        """
        Notify about expired request (auto-EUR selection)

        Args:
            teacher: Teacher user
            student: Student user
            course_title: Course title
            request_id: Request ID

        Returns:
            bool: Success status
        """
        try:
            # Notify teacher
            teacher_message = (
                f"⏰ Time expired for TeoCoin discount decision on '{course_title}'\n\n"
                f"✅ You automatically received full EUR commission\n"
                f"💰 Platform absorbed the student's discount cost\n"
                f"🪙 Student's TEO tokens were returned"
            )

            Notification.objects.create(
                user=teacher,
                message=teacher_message,
                notification_type="teocoin_discount_expired",
                related_object_id=request_id,
            )

            # Notify student
            student_message = (
                f"⏰ Teacher didn't respond in time for '{course_title}'\n\n"
                f"✅ Your discount is still confirmed\n"
                f"💰 Teacher received full EUR commission\n"
                f"🪙 Your TEO tokens have been returned\n"
                f"📚 You have full access to the course"
            )

            Notification.objects.create(
                user=student,
                message=student_message,
                notification_type="teocoin_discount_expired",
            )

            self.logger.info(f"Expiration notifications sent for request {request_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send expiration notifications: {e}")
            return False

    def create_teacher_staking_reminder(self, teacher: User, teo_amount: float) -> bool:
        """
        Remind teacher about staking benefits after accepting TEO

        Args:
            teacher: Teacher user
            teo_amount: TEO amount received

        Returns:
            bool: Success status
        """
        try:
            message = (
                f"🪙 You received {teo_amount:.2f} TEO tokens!\n\n"
                f"💡 Staking Benefits:\n"
                f"• Stake your TEO to increase commission rates\n"
                f"• Higher tiers = higher % on all future sales\n"
                f"• Compound your TEO earnings over time\n\n"
                f"🚀 Visit the Staking section to maximize your earnings!"
            )

            notification = Notification.objects.create(
                user=teacher, message=message, notification_type="bonus_received"
            )

            self.logger.info(f"Staking reminder sent to {teacher.username}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send staking reminder: {e}")
            return False

    # ========== PRIVATE METHODS ==========

    def _send_teacher_email_notification(
        self,
        teacher: User,
        student: User,
        course_title: str,
        discount_percent: int,
        teo_cost: float,
        teacher_bonus: float,
        hours_remaining: int,
    ):
        """Send email notification to teacher"""
        try:
            subject = f"Student discount decision needed - {course_title}"

            context = {
                "teacher_name": teacher.get_full_name() or teacher.username,
                "student_name": student.get_full_name() or student.username,
                "course_title": course_title,
                "discount_percent": discount_percent,
                "teo_cost": teo_cost,
                "teacher_bonus": teacher_bonus,
                "total_teo": teo_cost + teacher_bonus,
                "hours_remaining": hours_remaining,
                "dashboard_url": f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/teacher/dashboard",
            }

            html_message = render_to_string(
                "emails/teacher_discount_decision.html", context
            )
            plain_message = render_to_string(
                "emails/teacher_discount_decision.txt", context
            )

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[teacher.email],
                html_message=html_message,
                fail_silently=False,
            )

        except Exception as e:
            self.logger.error(f"Failed to send teacher email: {e}")

    def _send_urgent_email(
        self, teacher: User, course_title: str, minutes_remaining: int
    ):
        """Send urgent timeout warning email"""
        try:
            subject = f"URGENT: {minutes_remaining} minutes left - {course_title}"

            message = (
                f"Dear {teacher.get_full_name() or teacher.username},\n\n"
                f"You have only {minutes_remaining} minutes left to choose your payment method "
                f"for the discount request on '{course_title}'.\n\n"
                f"Please visit your dashboard to make your choice:\n"
                f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/teacher/dashboard\n\n"
                f"If you don't choose, you'll automatically receive full EUR commission."
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[teacher.email],
                fail_silently=False,
            )

        except Exception as e:
            self.logger.error(f"Failed to send urgent email: {e}")


# Singleton instance
teocoin_notification_service = TeoCoinDiscountNotificationService()
