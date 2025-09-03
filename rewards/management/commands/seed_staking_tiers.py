from django.core.management.base import BaseCommand
from decimal import Decimal
from rewards.models import Tier


class Command(BaseCommand):
    help = "Seed default staking tiers (Bronze minimal)"

    def handle(self, *args, **options):
        bronze, created = Tier.objects.update_or_create(
            name="Bronze",
            defaults={
                "min_stake_teo": Decimal("0"),
                "teacher_split_percent": Decimal("50.00"),
                "platform_split_percent": Decimal("50.00"),
                "max_accept_discount_ratio": Decimal("1.00"),
                "teo_bonus_multiplier": Decimal("1.25"),
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created Bronze tier"))
        else:
            # update_or_create returns created=False also when it updated
            self.stdout.write(self.style.SUCCESS("Bronze tier present (created/updated)"))
