from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from rewards.models import BlockchainTransaction
from blockchain.models import DBTeoCoinTransaction
from services.db_teocoin_service import db_teocoin_service
from blockchain import adapter as blockchain_adapter
from rewards import constants
import logging
from blockchain.models import DBTeoCoinBalance


logger = logging.getLogger(__name__)


def _quantize_chain_amount(amount: Decimal) -> Decimal:
    # BlockchainTransaction stores 8 decimals
    return amount.quantize(constants.DECIMAL_PRECISION_8)


@transaction.atomic
def mint_teo(*, user, amount: Decimal, idem_key: str) -> dict:
    """Mint TEO to user's wallet: DB decreases, chain increases.

    Idempotent on idem_key via BlockchainTransaction.related_object_id
    """
    if amount is None:
        raise ValueError("amount is required")

    try:
        amount = Decimal(str(amount))
    except Exception:
        raise ValueError("amount must be a valid decimal")

    if amount <= 0:
        raise ValueError("amount must be > 0")

    # Validate maximum
    if amount > constants.MAX_MINT_BURN:
        raise ValueError(f"amount exceeds maximum allowed ({constants.MAX_MINT_BURN})")


    # Idempotence: get_or_create chain transaction first
    chain_tx, created = BlockchainTransaction.objects.get_or_create(
        transaction_type=constants.TX_MINT,
        related_object_id=str(idem_key),
        user=user,
        defaults={
            "amount": _quantize_chain_amount(amount),
            "status": constants.STATUS_PENDING,
            "notes": f"Mint requested idem_key={idem_key}",
        },
    )

    if not created:
        # If exists, return current status without duplicating DB operations
        logger.info("mint idempotent hit user_id=%s idem_key=%s status=%s", getattr(user, "id", None), idem_key, chain_tx.status)
        return {
            "status": chain_tx.status,
            "db_tx_id": None,
            "chain_tx_id": chain_tx.id,
            "tx_hash": chain_tx.tx_hash,
        }

    # Now we are the creator of the chain transaction: lock balance row and deduct DB balance
    # Lock the user's DBTeoCoinBalance to avoid races
    try:
        DBTeoCoinBalance.objects.select_for_update().get(user=user)
    except DBTeoCoinBalance.DoesNotExist:
        # ensure a balance exists (deduct_balance will fail later if needed)
        DBTeoCoinBalance.objects.create(user=user, available_balance=Decimal("0.00"))

    success = db_teocoin_service.deduct_balance(
        user=user,
        amount=amount,
        transaction_type=constants.DB_TX_WITHDRAWN,
        description=f"Mint to chain; idem_key={idem_key}",
    )
    if not success:
        # Mark chain tx failed and raise so the caller sees the error and DB isn't left deducted
        chain_tx.status = constants.STATUS_FAILED
        chain_tx.error_message = "Insufficient DB balance"
        chain_tx.save(update_fields=["status", "error_message"])
        raise ValueError("Insufficient DB balance for mint")

    # call adapter
    try:
        tx_hash = blockchain_adapter.send_mint(user, amount)
        chain_tx.tx_hash = tx_hash
        chain_tx.status = constants.STATUS_COMPLETED
        chain_tx.confirmed_at = timezone.now()
        chain_tx.save(update_fields=["tx_hash", "status", "confirmed_at"])

        # db_teocoin_service.deduct_balance already created a DB transaction record
        # Optionally update any DB transaction linking to chain hash if needed.
        return {
            "status": chain_tx.status,
            "db_tx_id": None,
            "chain_tx_id": chain_tx.id,
            "tx_hash": tx_hash,
        }

    except Exception as exc:
        # mark chain tx failed and re-raise to trigger outer rollback
        chain_tx.status = constants.STATUS_FAILED
        chain_tx.error_message = str(exc)
        chain_tx.save(update_fields=["status", "error_message"])
        raise


@transaction.atomic
def burn_teo(*, user, amount: Decimal, idem_key: str) -> dict:
    """Burn TEO from user's wallet on chain and credit DB balance.

    Idempotent on idem_key via BlockchainTransaction.related_object_id
    """
    if amount is None or Decimal(amount) <= 0:
        raise ValueError("amount must be > 0")

    amount = Decimal(str(amount))

    # Idempotence: get_or_create chain transaction
    chain_tx, created = BlockchainTransaction.objects.get_or_create(
        transaction_type=constants.TX_BURN,
        related_object_id=str(idem_key),
        user=user,
        defaults={
            "amount": _quantize_chain_amount(amount),
            "status": constants.STATUS_PENDING,
            "notes": f"Burn requested idem_key={idem_key}",
        },
    )

    if not created:
        return {
            "status": chain_tx.status,
            "db_tx_id": None,
            "chain_tx_id": chain_tx.id,
            "tx_hash": chain_tx.tx_hash,
        }

    try:
        tx_hash = blockchain_adapter.send_burn(user, amount)
        chain_tx.tx_hash = tx_hash
        chain_tx.status = constants.STATUS_COMPLETED
        chain_tx.confirmed_at = timezone.now()
        chain_tx.save(update_fields=["tx_hash", "status", "confirmed_at"])

        # After chain success, credit DB (deposit) via service which records the DB tx
        db_result = db_teocoin_service.credit_user(
            user=user,
            amount=amount,
            transaction_type=constants.DB_TX_DEPOSIT,
            description=f"Burn from chain completed; idem_key={idem_key}",
            metadata={"transaction_hash": tx_hash},
        )

        return {
            "status": chain_tx.status,
            "db_tx_id": db_result.get("transaction_id"),
            "chain_tx_id": chain_tx.id,
            "tx_hash": tx_hash,
        }

    except Exception as exc:
        chain_tx.status = constants.STATUS_FAILED
        chain_tx.error_message = str(exc)
        chain_tx.save(update_fields=["status", "error_message"])
        # Do not credit DB on failure
        raise
