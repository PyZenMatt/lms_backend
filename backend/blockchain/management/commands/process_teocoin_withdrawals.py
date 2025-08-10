"""
Management command to process pending TeoCoin withdrawals
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from decimal import Decimal
import logging

from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending TeoCoin withdrawal requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--withdrawal-id',
            type=int,
            help='Process specific withdrawal ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 TeoCoin Withdrawal Processor')
        )
        self.stdout.write('=' * 50)

        # Check configuration
        if not hasattr(settings, 'PLATFORM_WALLET_ADDRESS'):
            self.stdout.write(
                self.style.ERROR('❌ PLATFORM_WALLET_ADDRESS not configured')
            )
            return

        platform_address = settings.PLATFORM_WALLET_ADDRESS
        self.stdout.write(f'🏛️ Platform wallet: {platform_address}')

        # Get pending withdrawals
        if options['withdrawal_id']:
            withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                pk=options['withdrawal_id'],
                status='pending'
            )
            if not withdrawals.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Withdrawal {options["withdrawal_id"]} not found or not pending')
                )
                return
        else:
            withdrawals = TeoCoinWithdrawalRequest.objects.filter(status='pending')

        if not withdrawals.exists():
            self.stdout.write(
                self.style.WARNING('📭 No pending withdrawals found')
            )
            return

        self.stdout.write(f'📋 Found {withdrawals.count()} pending withdrawal(s)')

        # Process each withdrawal
        for withdrawal in withdrawals:
            self.stdout.write(f'\n👤 User: {withdrawal.user.email}')
            self.stdout.write(f'💰 Amount: {withdrawal.amount} TEO')
            self.stdout.write(f'📍 To Address: {withdrawal.metamask_address}')
            self.stdout.write(f'📅 Created: {withdrawal.created_at}')

            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('🔍 DRY RUN - Would process this withdrawal')
                )
                continue

            # Test minting functionality
            result = teocoin_withdrawal_service.mint_tokens_to_address(
                amount=withdrawal.amount,
                to_address=withdrawal.metamask_address,
                withdrawal_id=withdrawal.pk
            )

            if result['success']:
                tx_hash = result.get('transaction_hash', 'demo_hash')
                gas_used = result.get('gas_used', 0)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Minted {withdrawal.amount} TEO to {withdrawal.metamask_address}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'📤 Transaction: {tx_hash}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'⛽ Gas used: {gas_used}')
                )
                
                # Mark as completed
                withdrawal.status = 'completed'
                withdrawal.transaction_hash = tx_hash
                withdrawal.save()
                
                # Update balance
                balance_obj = DBTeoCoinBalance.objects.get(user=withdrawal.user)
                balance_obj.pending_withdrawal -= withdrawal.amount
                balance_obj.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'📝 Withdrawal marked as completed')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {result["error"]}')
                )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('✅ Withdrawal processing completed!')
        )
        
        # Show updated status
        remaining = TeoCoinWithdrawalRequest.objects.filter(status='pending').count()
        self.stdout.write(f'📊 Remaining pending withdrawals: {remaining}')
