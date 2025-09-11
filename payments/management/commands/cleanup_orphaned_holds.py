"""
Clean up orphaned TEO holds from failed or abandoned payments

This command implements Step 3 of the correlation plan:
"Error & timeout - su payment_intent.payment_failed rilascia hold, cron cleanup per HOLD orfani"

Finds PaymentDiscountSnapshot entries with status='applied' that are older than 
a threshold (default 2 hours) and releases their associated holds.
"""

import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from rewards.models import PaymentDiscountSnapshot
from services.wallet_hold_service import WalletHoldService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up orphaned TEO holds from abandoned discount applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=2,
            help='Maximum age in hours for applied discounts before considering them orphaned (default: 2)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it'
        )

    def handle(self, *args, **options):
        max_age_hours = options['max_age_hours']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        
        self.stdout.write(f"🔍 Looking for orphaned TEO holds older than {max_age_hours} hours ({cutoff_time})")
        
        # Find snapshots with status='applied' that are old enough to be considered orphaned
        orphaned_snapshots = PaymentDiscountSnapshot.objects.filter(
            status='applied',
            applied_at__lt=cutoff_time,
            wallet_hold_id__isnull=False
        ).order_by('applied_at')
        
        count = orphaned_snapshots.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No orphaned TEO holds found"))
            return
        
        self.stdout.write(f"🧹 Found {count} orphaned TEO holds to clean up")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes will be made"))
            for snapshot in orphaned_snapshots:
                self.stdout.write(
                    f"  Would release hold {snapshot.wallet_hold_id} for snapshot {snapshot.id} "
                    f"(user: {snapshot.student.username}, course: {snapshot.course.title if snapshot.course else 'N/A'}, "
                    f"applied: {snapshot.applied_at})"
                )
            return
        
        wallet_hold_service = WalletHoldService()
        success_count = 0
        error_count = 0
        
        for snapshot in orphaned_snapshots:
            try:
                with transaction.atomic():
                    self.stdout.write(
                        f"🔄 Releasing hold {snapshot.wallet_hold_id} for snapshot {snapshot.id} "
                        f"(user: {snapshot.student.username}, applied: {snapshot.applied_at})"
                    )
                    
                    # Release the hold
                    success = wallet_hold_service.release_hold(
                        hold_id=snapshot.wallet_hold_id,
                        description=f"TEO hold released due to timeout - snapshot {snapshot.id} cleanup"
                    )
                    
                    if success:
                        # Update snapshot status to expired
                        snapshot.status = 'expired'
                        snapshot.save(update_fields=['status'])
                        
                        success_count += 1
                        self.stdout.write(
                            f"  ✅ Successfully released hold {snapshot.wallet_hold_id}"
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Failed to release hold {snapshot.wallet_hold_id}")
                        )
                        
            except Exception as e:
                error_count += 1
                logger.error(f"Error cleaning up snapshot {snapshot.id}: {e}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error processing snapshot {snapshot.id}: {e}")
                )
        
        self.stdout.write("")
        self.stdout.write(f"📊 Cleanup completed:")
        self.stdout.write(f"  ✅ Successfully cleaned: {success_count}")
        self.stdout.write(f"  ❌ Errors: {error_count}")
        self.stdout.write(f"  📈 Total processed: {success_count + error_count}")
        
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS(f"🎉 Successfully cleaned up {success_count} orphaned TEO holds"))
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"⚠️  {error_count} errors occurred during cleanup"))
