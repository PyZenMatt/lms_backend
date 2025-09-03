from django.core.management.base import BaseCommand
from decimal import Decimal
from services.discount_calc import compute_discount_breakdown

from rewards.models import PaymentDiscountSnapshot, Tier


class Command(BaseCommand):
    help = "Repair PaymentDiscountSnapshot rows by recomputing missing breakdown fields when possible"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report changes without applying")
        parser.add_argument("--limit", type=int, help="Limit number of snapshots processed")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        limit = options.get("limit")

        qs = PaymentDiscountSnapshot.objects.filter(course__isnull=False).order_by("-created_at")
        if limit:
            qs = qs[:limit]

        updated = 0
        skipped = 0

        for s in qs:
            try:
                # Detect likely-broken snapshots: zero teacher_teo or missing teacher_eur
                need_fix = (s.teacher_teo == 0 or s.teacher_eur == 0 or s.student_pay_eur == 0)
                if not need_fix:
                    skipped += 1
                    continue

                # Reconstruct tier dict if possible
                tier = None
                if s.tier_name or s.tier_teacher_split_percent:
                    tier = {
                        "teacher_split_percent": s.tier_teacher_split_percent or Decimal("50.00"),
                        "platform_split_percent": s.tier_platform_split_percent or Decimal("50.00"),
                        "max_accept_discount_ratio": s.tier_max_accept_discount_ratio or Decimal("1.00"),
                        "teo_bonus_multiplier": s.tier_teo_bonus_multiplier or Decimal("1.25"),
                        "name": s.tier_name,
                    }

                # Compute potential breakdown assuming teacher may accept TEO
                accept_ratio = None
                try:
                    if s.tier_max_accept_discount_ratio is not None:
                        accept_ratio = s.tier_max_accept_discount_ratio
                except Exception:
                    accept_ratio = None

                breakdown = compute_discount_breakdown(
                    price_eur=s.price_eur,
                    discount_percent=s.discount_percent,
                    tier=tier,
                    accept_teo=True,
                    accept_ratio=accept_ratio,
                )

                if dry_run:
                    self.stdout.write(self.style.WARNING(f"Would update snapshot {s.id}: teacher_teo {s.teacher_teo} -> {breakdown['teacher_teo']}"))
                    updated += 1
                    continue

                s.student_pay_eur = breakdown["student_pay_eur"]
                s.teacher_eur = breakdown["teacher_eur"]
                s.platform_eur = breakdown["platform_eur"]
                s.teacher_teo = breakdown["teacher_teo"]
                s.platform_teo = breakdown["platform_teo"]
                s.absorption_policy = breakdown.get("absorption_policy", s.absorption_policy)
                s.teacher_accepted_teo = breakdown.get("teacher_teo", s.teacher_accepted_teo)
                s.save()
                updated += 1

            except Exception as e:
                self.stderr.write(f"Failed to repair snapshot {s.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Snapshots processed: updated={updated}, skipped={skipped}"))
