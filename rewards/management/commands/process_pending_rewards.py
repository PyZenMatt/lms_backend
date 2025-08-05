"""
Management command to process pending reward transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from rewards.models import BlockchainTransaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process all pending reward transactions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of transactions to process',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        limit = options.get('limit')
        
        self.stdout.write("🔄 Processing pending reward transactions...")
        self.stdout.write("=" * 60)
        
        # Get pending reward transactions
        pending_rewards = BlockchainTransaction.objects.filter(
            status='pending',
            transaction_type__in=['exercise_reward', 'review_reward']
        ).order_by('created_at')
        
        if limit:
            pending_rewards = pending_rewards[:limit]
        
        total_count = pending_rewards.count()
        self.stdout.write(f"📊 Found {total_count} pending reward transactions")
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No pending reward transactions to process"))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No actual processing will be done"))
            for tx in pending_rewards:
                self.stdout.write(f"Would process: {tx.user.username} - {tx.amount} TEO ({tx.transaction_type})")
            return
        
        processed = 0
        failed = 0
        
        for tx in pending_rewards:
            try:
                self.stdout.write(f"\n🔄 Processing: {tx.user.username} - {tx.amount} TEO ({tx.transaction_type})")
                
                # Check if user has wallet address
                if not tx.user.wallet_address:
                    self.stdout.write(self.style.ERROR(f"❌ User {tx.user.username} has no wallet address"))
                    tx.status = 'failed'
                    tx.error_message = 'User has no wallet address'
                    tx.save()
                    failed += 1
                    continue
                
                # Mint tokens to user's wallet using TeoCoinService
                description = f"{tx.transaction_type.replace('_', ' ').title()} - {tx.notes}"
                
                try:
                    # Import blockchain service
                    from blockchain.blockchain import TeoCoinService
                    teocoin_service = TeoCoinService()
                    
                    # Mint tokens (amount is already in proper decimal format)
                    tx_hash = teocoin_service.mint_tokens(
                        tx.user.wallet_address,
                        tx.amount
                    )
                    
                    if tx_hash:
                        # Update transaction with success
                        tx.status = 'completed'
                        tx.tx_hash = tx_hash
                        tx.transaction_hash = tx_hash
                        tx.confirmed_at = timezone.now()
                        tx.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"✅ Success! TX Hash: {tx_hash}"))
                        processed += 1
                    else:
                        # Mark as failed
                        tx.status = 'failed'
                        tx.error_message = 'Blockchain transaction failed - no tx hash returned'
                        tx.save()
                        
                        self.stdout.write(self.style.ERROR(f"❌ Failed: No tx hash returned"))
                        failed += 1
                        
                except Exception as blockchain_error:
                    # Mark as failed with error
                    tx.status = 'failed'
                    tx.error_message = f'Blockchain error: {str(blockchain_error)}'
                    tx.save()
                    
                    self.stdout.write(self.style.ERROR(f"❌ Blockchain error: {blockchain_error}"))
                    failed += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Unexpected error processing transaction {tx.pk}: {e}"))
                failed += 1
        
        self.stdout.write(f"\n📊 PROCESSING COMPLETE")
        self.stdout.write(f"✅ Processed successfully: {processed}")
        self.stdout.write(f"❌ Failed: {failed}")
        self.stdout.write(f"📝 Total: {processed + failed}")
        
        if processed > 0:
            self.stdout.write(self.style.SUCCESS(f"🎉 Successfully processed {processed} reward transactions!"))
        if failed > 0:
            self.stdout.write(self.style.WARNING(f"⚠️ {failed} transactions failed to process"))
