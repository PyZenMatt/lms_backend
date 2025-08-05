"""
Django Management Command: Process TeoCoin Withdrawals
This command processes pending withdrawal requests and mints tokens to user wallets.

Usage:
    python manage.py process_withdrawals
    python manage.py process_withdrawals --dry-run
    python manage.py process_withdrawals --limit 10
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
from services.teocoin_withdrawal_service import teocoin_withdrawal_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending TeoCoin withdrawal requests (Phase 1 - Ready for blockchain integration)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of withdrawals to process (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Process withdrawals even if blockchain connection is not available'
        )

    def handle(self, *args, **options):
        """
        Main command handler for processing withdrawals
        """
        limit = options['limit']
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"🚀 TeoCoin Withdrawal Processor - Phase 1\n"
                f"Processing up to {limit} pending withdrawals..."
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )
        
        try:
            # Get pending withdrawals
            pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                status='pending'
            ).order_by('created_at')[:limit]
            
            if not pending_withdrawals.exists():
                self.stdout.write(
                    self.style.SUCCESS("✅ No pending withdrawals to process")
                )
                return
            
            self.stdout.write(f"📋 Found {pending_withdrawals.count()} pending withdrawals")
            
            # Check blockchain connection (for future implementation)
            blockchain_ready = self._check_blockchain_connection()
            
            if not blockchain_ready and not force:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ Blockchain connection not available. Use --force to process anyway."
                    )
                )
                return
            
            processed_count = 0
            failed_count = 0
            
            for withdrawal in pending_withdrawals:
                try:
                    if dry_run:
                        self._show_withdrawal_info(withdrawal)
                    else:
                        success = self._process_withdrawal(withdrawal, blockchain_ready)
                        if success:
                            processed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Processed withdrawal #{withdrawal.id} - "
                                    f"{withdrawal.amount} TEO to {withdrawal.metamask_address[:10]}..."
                                )
                            )
                        else:
                            failed_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"❌ Failed to process withdrawal #{withdrawal.id}"
                                )
                            )
                
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Error processing withdrawal #{withdrawal.id}: {e}"
                        )
                    )
                    logger.error(f"Withdrawal processing error: {e}")
            
            # Summary
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n📊 Processing Summary:\n"
                        f"   ✅ Processed: {processed_count}\n"
                        f"   ❌ Failed: {failed_count}\n"
                        f"   📝 Total: {processed_count + failed_count}"
                    )
                )
            
        except Exception as e:
            raise CommandError(f"Command failed: {e}")
    
    def _check_blockchain_connection(self) -> bool:
        """
        Check if blockchain connection is available (Phase 2 implementation)
        For Phase 1, this returns False since we're not yet minting tokens
        """
        try:
            # This will be implemented in Phase 2 when we add blockchain integration
            web3_service = teocoin_withdrawal_service.web3
            if web3_service and hasattr(web3_service, 'isConnected'):
                return web3_service.isConnected()
            
            # For Phase 1, return False (not yet implemented)
            return False
            
        except Exception as e:
            logger.warning(f"Blockchain connection check failed: {e}")
            return False
    
    def _show_withdrawal_info(self, withdrawal):
        """Show withdrawal information for dry run"""
        self.stdout.write(
            f"📤 Withdrawal #{withdrawal.id}:\n"
            f"   👤 User: {withdrawal.user.email}\n"
            f"   💰 Amount: {withdrawal.amount} TEO\n"
            f"   📱 Address: {withdrawal.metamask_address}\n"
            f"   📅 Created: {withdrawal.created_at}\n"
            f"   🏠 IP: {withdrawal.ip_address or 'N/A'}\n"
        )
    
    @transaction.atomic
    def _process_withdrawal(self, withdrawal, blockchain_ready: bool) -> bool:
        """
        Process individual withdrawal
        
        Phase 1: Mark as processing and prepare for blockchain integration
        Phase 2: Will include actual blockchain minting
        """
        try:
            # Phase 1: Update status to processing
            withdrawal.status = 'processing'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            if blockchain_ready:
                # Phase 2: This will mint tokens to user's MetaMask
                # For now, we simulate successful blockchain processing
                success = self._mint_tokens_to_metamask(withdrawal)
                
                if success:
                    # Mark as completed
                    withdrawal.status = 'completed'
                    withdrawal.completed_at = timezone.now()
                    withdrawal.save()
                    
                    # Update user's pending withdrawal balance
                    balance_obj = DBTeoCoinBalance.objects.get(user=withdrawal.user)
                    balance_obj.pending_withdrawal -= withdrawal.amount
                    balance_obj.save()
                    
                    return True
                else:
                    # Mark as failed
                    withdrawal.status = 'failed'
                    withdrawal.error_message = 'Blockchain minting failed'
                    withdrawal.save()
                    
                    # Return funds to available balance
                    self._refund_withdrawal(withdrawal)
                    return False
            else:
                # Phase 1: Keep as processing until blockchain is ready
                self.stdout.write(
                    self.style.WARNING(
                        f"⏳ Withdrawal #{withdrawal.id} marked as processing "
                        f"(awaiting blockchain integration)"
                    )
                )
                return True
                
        except Exception as e:
            # Mark as failed and refund
            withdrawal.status = 'failed'
            withdrawal.error_message = f'Processing error: {str(e)}'
            withdrawal.save()
            
            self._refund_withdrawal(withdrawal)
            logger.error(f"Withdrawal processing error: {e}")
            return False
    
    def _mint_tokens_to_metamask(self, withdrawal) -> bool:
        """
        Mint TEO tokens to user's MetaMask wallet
        
        Phase 1: Placeholder for blockchain integration
        Phase 2: Will implement actual Web3 minting
        """
        # Phase 1: Simulate successful minting
        # This will be replaced with actual blockchain code in Phase 2
        
        self.stdout.write(
            self.style.WARNING(
                f"🔧 Phase 1: Simulating mint of {withdrawal.amount} TEO "
                f"to {withdrawal.metamask_address} (blockchain integration pending)"
            )
        )
        
        # Simulate gas cost tracking
        withdrawal.gas_used = 21000  # Typical gas for token mint
        withdrawal.gas_price_gwei = Decimal('20.0')  # 20 Gwei
        withdrawal.gas_cost_eur = Decimal('0.001')  # ~$0.001 on Polygon
        withdrawal.transaction_hash = f"0x{'0' * 64}"  # Placeholder hash
        withdrawal.save()
        
        return True  # Always succeed in Phase 1
    
    def _refund_withdrawal(self, withdrawal):
        """
        Refund failed withdrawal back to user's available balance
        """
        try:
            balance_obj = DBTeoCoinBalance.objects.get(user=withdrawal.user)
            balance_obj.available_balance += withdrawal.amount
            balance_obj.pending_withdrawal -= withdrawal.amount
            balance_obj.save()
            
            # Record refund transaction
            from services.db_teocoin_service import db_teocoin_service
            db_teocoin_service.add_balance(
                user=withdrawal.user,
                amount=withdrawal.amount,
                transaction_type='withdrawal_refund',
                description=f"Refund for failed withdrawal #{withdrawal.id}"
            )
            
            logger.info(f"Refunded {withdrawal.amount} TEO to {withdrawal.user.email}")
            
        except Exception as e:
            logger.error(f"Withdrawal refund error: {e}")
