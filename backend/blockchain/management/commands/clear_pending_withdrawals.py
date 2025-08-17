"""
Management command to clear pending TeoCoin withdrawals
"""

import logging

from blockchain.models import DBTeoCoinBalance, TeoCoinWithdrawalRequest
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear all pending TeoCoin withdrawals and return amounts to user balances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="Clear pending withdrawals for specific user ID only",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        dry_run = options.get("dry_run")

        # Get pending withdrawals
        pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
            status__in=["pending", "processing"]
        )

        if user_id:
            pending_withdrawals = pending_withdrawals.filter(user_id=user_id)

        if not pending_withdrawals.exists():
            self.stdout.write(self.style.SUCCESS("No pending withdrawals found."))
            return

        self.stdout.write(f"Found {pending_withdrawals.count()} pending withdrawals:")

        total_returned = 0

        for withdrawal in pending_withdrawals:
            self.stdout.write(
                f"  - ID: {withdrawal.id}, User: {withdrawal.user.username}, "
                f"Amount: {withdrawal.amount} TEO, Status: {withdrawal.status}"
            )
            total_returned += float(withdrawal.amount)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN: Would return {total_returned} TEO to user balances"
                )
            )
            return

        # Confirm action
        if not options.get("user_id"):
            confirm = input(
                f"\nThis will cancel {pending_withdrawals.count()} withdrawals "
                f"and return {total_returned} TEO to user balances. Continue? (y/N): "
            )
            if confirm.lower() not in ["y", "yes"]:
                self.stdout.write(self.style.WARNING("Operation cancelled."))
                return

        # Process withdrawals
        cancelled_count = 0
        returned_amount = 0

        with transaction.atomic():
            for withdrawal in pending_withdrawals:
                try:
                    # Get or create user balance
                    balance, created = DBTeoCoinBalance.objects.get_or_create(
                        user=withdrawal.user, defaults={"available_balance": 0}
                    )

                    # Return amount to balance
                    balance.available_balance += withdrawal.amount
                    balance.save()

                    # Mark withdrawal as cancelled
                    withdrawal.status = "cancelled"
                    withdrawal.save()

                    cancelled_count += 1
                    returned_amount += float(withdrawal.amount)

                    self.stdout.write(
                        f"✓ Cancelled withdrawal {withdrawal.id}: "
                        f"{withdrawal.amount} TEO returned to {withdrawal.user.username}"
                    )

                except Exception as e:
                    logger.error(f"Failed to cancel withdrawal {withdrawal.id}: {e}")
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to cancel withdrawal {withdrawal.id}: {e}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {cancelled_count} withdrawals cancelled, "
                f"{returned_amount} TEO returned to user balances"
            )
        )
