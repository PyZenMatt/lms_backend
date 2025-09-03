from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import timedelta

from rewards.models import PaymentDiscountSnapshot


class Command(BaseCommand):
    help = "Backfill PaymentDiscountSnapshot into TeacherDiscountDecision + Notification for teachers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--teacher-id",
            type=int,
            help="Only process snapshots for this teacher id",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not create objects, only report what would be done",
        )

    def handle(self, *args, **options):
        teacher_id = options.get("teacher_id")
        dry_run = options.get("dry_run")

        qs = PaymentDiscountSnapshot.objects.filter(teacher__isnull=False).order_by("-created_at")
        if teacher_id:
            qs = qs.filter(teacher__id=teacher_id)

        total = qs.count()
        created = 0
        skipped = 0

        for s in qs:
            # Skip if Notification already exists
            from notifications.models import Notification

            exists = Notification.objects.filter(
                user=s.teacher, notification_type__in=["teocoin_discount_pending"], related_object_id=s.id
            ).exists()
            if exists:
                skipped += 1
                continue

            if not s.course or not s.student:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(self.style.WARNING(f"Would create decision+notification for snapshot {s.id}"))
                created += 1
                continue

            # Create decision + notification
            try:
                from courses.models import TeacherDiscountDecision
                from django.db import transaction

                with transaction.atomic():
                    teo_decimal = Decimal(s.teacher_teo or 0)
                    bonus_decimal = Decimal(0)
                    try:
                        if s.tier_teo_bonus_multiplier:
                            mult = Decimal(s.tier_teo_bonus_multiplier)
                            if mult and mult != Decimal(0):
                                original = teo_decimal / mult
                                bonus_decimal = teo_decimal - original
                    except Exception:
                        bonus_decimal = Decimal(0)

                    teo_cost_wei = int((teo_decimal * Decimal(10 ** 18)).to_integral_value()) if teo_decimal else 0
                    teacher_bonus_wei = int((bonus_decimal * Decimal(10 ** 18)).to_integral_value()) if bonus_decimal else 0

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

                    Notification.objects.create(
                        user=s.teacher,
                        message=f"Scelta TeoCoin richiesta per {s.course.title if s.course else 'corso'}: lo studente {s.student.username} ha usato uno sconto ({s.discount_percent}%).",
                        notification_type="teocoin_discount_pending",
                        related_object_id=s.id,
                        link=None,
                    )

                    created += 1

            except Exception as e:
                self.stderr.write(f"Failed to backfill snapshot {s.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Processed {total} snapshots, created={created}, skipped={skipped}"))
