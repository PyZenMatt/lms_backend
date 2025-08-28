"""
Teacher Discount Absorption Service
Handles the business logic for teachers choosing between EUR vs TEO compensation
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rewards.models import TeacherDiscountAbsorption
from services.db_teocoin_service import DBTeoCoinService
from users.models import TeacherProfile


class TeacherDiscountAbsorptionService:
    """
    Service for managing teacher discount absorption choices
    """

    @staticmethod
    def create_absorption_opportunity(student, teacher, course, discount_data):
        """
        Create a new discount absorption opportunity when a student uses TeoCoin discount

        Args:
            student: User who purchased the course
            teacher: User who owns the course
            course: Course that was purchased
            discount_data: Dict containing discount information
                - discount_percentage: 5, 10, or 15
                - teo_used: Amount of TEO used by student
                - discount_amount_eur: EUR value of discount
                - course_price_eur: Original course price
        """
        teo_service = DBTeoCoinService()

        # Derive teacher tier and commission from TeacherProfile (source of truth)
        # Fallback to defaults if profile is missing
        try:
            teacher_profile = TeacherProfile.objects.get(user=teacher)
            # Ensure profile values reflect current staking state
            try:
                teacher_profile.update_tier_and_commission()
                teacher_profile.save()
            except Exception:
                pass

            tier_map = {"Bronze": 0, "Silver": 1, "Gold": 2, "Platinum": 3, "Diamond": 4}
            teacher_tier = tier_map.get(teacher_profile.staking_tier, 0)
            teacher_commission_rate = teacher_profile.commission_rate
        except TeacherProfile.DoesNotExist:
            teacher_tier = 0
            teacher_commission_rate = Decimal("50")

        # Calculate both options before creating the object
        course_price_eur = Decimal(str(discount_data["course_price_eur"]))
        discount_amount_eur = Decimal(str(discount_data["discount_amount_eur"]))
        teo_used_by_student = Decimal(str(discount_data["teo_used"]))
        teacher_commission_rate_decimal = Decimal(str(teacher_commission_rate))

        # Option A: Standard commission, platform absorbs discount
        option_a_teacher_eur = course_price_eur * teacher_commission_rate_decimal / Decimal("100")
        option_a_platform_eur = course_price_eur - option_a_teacher_eur

        # Option B: Teacher absorbs discount, gets TEO + 25% bonus
        option_b_teacher_eur = option_a_teacher_eur - discount_amount_eur
        option_b_teacher_teo = teo_used_by_student * Decimal("1.25")  # 25% bonus
        option_b_platform_eur = option_a_platform_eur + discount_amount_eur

        # Create the absorption opportunity with all fields populated
        absorption = TeacherDiscountAbsorption.objects.create(
            teacher=teacher,
            course=course,
            student=student,
            course_price_eur=course_price_eur,
            discount_percentage=discount_data["discount_percentage"],
            teo_used_by_student=teo_used_by_student,
            discount_amount_eur=discount_amount_eur,
            teacher_tier=teacher_tier,
            teacher_commission_rate=teacher_commission_rate_decimal,
            expires_at=timezone.now() + timedelta(hours=24),  # 24 hour window
            # Option A (Default EUR)
            option_a_teacher_eur=option_a_teacher_eur,
            option_a_platform_eur=option_a_platform_eur,
            # Option B (Absorb Discount for TEO)
            option_b_teacher_eur=option_b_teacher_eur,
            option_b_teacher_teo=option_b_teacher_teo,
            option_b_platform_eur=option_b_platform_eur,
        )

        # Send notification to teacher about the new absorption opportunity
        try:
            from notifications.services import teocoin_notification_service

            try:
                from services.discount_calc import compute_discount_breakdown
                offered = compute_discount_breakdown(
                    price_eur=course_price_eur,
                    discount_percent=Decimal(str(discount_data["discount_percentage"])),
                    tier=None,
                    accept_teo=True,
                    accept_ratio=Decimal("1"),
                )
                offered_teacher = float(offered.get("teacher_teo") or 0)
                offered_platform = float(offered.get("platform_teo") or 0)
            except Exception:
                offered_teacher = float(option_b_teacher_teo)
                offered_platform = 0.0

            teocoin_notification_service.notify_teacher_discount_pending(
                teacher=teacher,
                student=student,
                course_title=course.title,
                discount_percent=discount_data["discount_percentage"],
                teo_cost=float(teo_used_by_student),
                teacher_bonus=float(option_b_teacher_teo - teo_used_by_student),
                request_id=absorption.pk,
                expires_at=absorption.expires_at,
                offered_teacher_teo=offered_teacher,
                offered_platform_teo=offered_platform,
            )
        except Exception:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Failed to send teacher notification for absorption %s", absorption.pk)

        # Debug log creation
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                "Created TeacherDiscountAbsorption id=%s for teacher=%s course=%s",
                absorption.pk,
                getattr(teacher, "email", str(getattr(teacher, "id", "unknown"))),
                getattr(course, "id", "unknown"),
            )
        except Exception:
            pass

        return absorption

    @staticmethod
    def process_teacher_choice(absorption_id, choice, teacher):
        """
        Process teacher's choice for discount absorption

        Args:
            absorption_id: ID of the TeacherDiscountAbsorption
            choice: 'absorb' or 'refuse'
            teacher: Teacher making the choice
        """
        try:
            absorption = TeacherDiscountAbsorption.objects.get(
                id=absorption_id, teacher=teacher, status="pending"
            )
        except TeacherDiscountAbsorption.DoesNotExist:
            raise ValueError("Invalid absorption opportunity or already processed")

        if absorption.is_expired:
            absorption.auto_expire()
            raise ValueError("This opportunity has expired")

        # Process the choice
        absorption.make_choice(choice)

        # If teacher chose to absorb, add TEO to their balance
        if choice == "absorb" and absorption.status == "absorbed":
            teo_service = DBTeoCoinService()
            teo_service.add_balance(
                user=teacher,
                amount=Decimal(str(absorption.final_teacher_teo)),
                transaction_type="discount_absorption",
                description=f"Absorbed discount for course: {absorption.course.title}",
            )

        # Send notification to student about teacher's decision
        try:
            from notifications.services import teocoin_notification_service

            decision = "accepted" if choice == "absorb" else "declined"
            teo_amount = (
                float(absorption.final_teacher_teo) if choice == "absorb" else None
            )

            teocoin_notification_service.notify_student_teacher_decision(
                student=absorption.student,
                teacher=teacher,
                course_title=absorption.course.title,
                decision=decision,
                teo_amount=teo_amount,
            )

            # If teacher accepted TEO, send staking reminder
            if choice == "absorb":
                teocoin_notification_service.create_teacher_staking_reminder(
                    teacher=teacher, teo_amount=float(absorption.final_teacher_teo)
                )

        except Exception as e:
            # Log error but don't fail the whole process
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send decision notifications: {e}")

        return absorption

    @staticmethod
    def get_pending_absorptions(teacher):
        """
        Get all pending absorption opportunities for a teacher
        """
        return (
            TeacherDiscountAbsorption.objects.filter(
                teacher=teacher, status="pending", expires_at__gt=timezone.now()
            )
            .select_related("course", "student")
            .order_by("expires_at")
        )

    @staticmethod
    def get_teacher_absorption_history(teacher, days=30):
        """
        Get teacher's absorption history for the last N days
        """
        since_date = timezone.now() - timedelta(days=days)

        return (
            TeacherDiscountAbsorption.objects.filter(
                teacher=teacher, created_at__gte=since_date
            )
            .select_related("course", "student")
            .order_by("-created_at")
        )

    @staticmethod
    def get_teacher_absorption_stats(teacher, days=30):
        """
        Get statistics about teacher's absorption activity
        """
        since_date = timezone.now() - timedelta(days=days)

        absorptions = TeacherDiscountAbsorption.objects.filter(
            teacher=teacher, created_at__gte=since_date
        )

        total_opportunities = absorptions.count()
        absorbed_count = absorptions.filter(status="absorbed").count()
        refused_count = absorptions.filter(status="refused").count()
        expired_count = absorptions.filter(status="expired").count()
        pending_count = absorptions.filter(status="pending").count()

        # Calculate totals
        total_eur_earned = sum(
            a.final_teacher_eur for a in absorptions if a.final_teacher_eur is not None
        )
        total_teo_earned = sum(a.final_teacher_teo for a in absorptions)

        absorption_rate = (
            (absorbed_count / total_opportunities * 100)
            if total_opportunities > 0
            else 0
        )

        return {
            "total_opportunities": total_opportunities,
            "absorbed_count": absorbed_count,
            "refused_count": refused_count,
            "expired_count": expired_count,
            "pending_count": pending_count,
            "absorption_rate": round(absorption_rate, 1),
            "total_eur_earned": total_eur_earned,
            "total_teo_earned": total_teo_earned,
            "days": days,
        }

    @staticmethod
    def expire_old_absorptions():
        """
        Auto-expire old pending absorptions (to be run as a cron job)
        """
        expired_absorptions = TeacherDiscountAbsorption.objects.filter(
            status="pending", expires_at__lt=timezone.now()
        )

        count = 0
        for absorption in expired_absorptions:
            absorption.auto_expire()

            # Send expiration notification
            try:
                from notifications.services import teocoin_notification_service

                teocoin_notification_service.notify_request_expired(
                    teacher=absorption.teacher,
                    student=absorption.student,
                    course_title=absorption.course.title,
                    request_id=absorption.pk,
                )
            except Exception as e:
                # Log error but continue processing
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to send expiration notification for absorption {absorption.pk}: {e}"
                )

            count += 1

        return count

    @staticmethod
    def calculate_platform_savings():
        """
        Calculate how much money the platform saved through teacher absorptions
        """
        absorbed_absorptions = TeacherDiscountAbsorption.objects.filter(
            status="absorbed"
        )

        total_discount_absorbed = sum(
            a.discount_amount_eur for a in absorbed_absorptions
        )

        return {
            "total_discount_absorbed_eur": total_discount_absorbed,
            "absorption_count": absorbed_absorptions.count(),
        }
