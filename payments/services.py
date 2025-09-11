from django.db import transaction
from rewards.models import PaymentDiscountSnapshot
from services.wallet_hold_service import WalletHoldService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def settle_discount_snapshot(snapshot: PaymentDiscountSnapshot, provider_event_id: str, external_txn_id: str | None = None) -> bool:
    """Settle a pending discount snapshot idempotently.

    Args:
        snapshot: PaymentDiscountSnapshot instance to settle
        provider_event_id: Stripe event ID for logging
        external_txn_id: External transaction ID (payment intent, checkout session)

    Returns: True if settled (or already confirmed), False on error.
    """
    try:
        # Idempotent: if snapshot already confirmed, nothing to do
        if snapshot.status == 'confirmed':
            logger.info(f"Snapshot {snapshot.id} already confirmed - idempotent success")
            return True

        # Must have a wallet_hold_id created earlier
        if not snapshot.wallet_hold_id:
            logger.error(f"Snapshot {snapshot.id} has no wallet_hold_id - cannot settle")
            return False

        with transaction.atomic():
            # Capture the hold
            hold_service = WalletHoldService()
            logger.info(f"Capturing hold {snapshot.wallet_hold_id} for snapshot {snapshot.id}")
            
            ok = hold_service.capture_hold(
                hold_id=snapshot.wallet_hold_id,
                description=f"Captured via webhook event {provider_event_id} for snapshot {snapshot.id}"
            )
            
            if not ok:
                logger.error(f"Failed to capture hold {snapshot.wallet_hold_id} for snapshot {snapshot.id}")
                return False

            # Update snapshot status
            snapshot.status = 'confirmed'
            snapshot.confirmed_at = timezone.now()
            if external_txn_id:
                snapshot.external_txn_id = external_txn_id
            snapshot.save(update_fields=['status', 'confirmed_at', 'external_txn_id'])

            logger.info(f"✅ Successfully settled snapshot {snapshot.id} with hold {snapshot.wallet_hold_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error settling snapshot {snapshot.id}: {e}", exc_info=True)
        return False
