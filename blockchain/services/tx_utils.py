from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

from rewards.models import BlockchainTransaction

logger = logging.getLogger(__name__)


def create_transaction_idempotent(user, transaction_type, related_object_id=None, defaults=None):
    """Create or return existing BlockchainTransaction for idempotent operations.

    Strategy:
    - Try to find an existing record matching user, transaction_type and related_object_id
      (if related_object_id provided).
    - If not found, attempt to create; on IntegrityError (race) fetch the existing one.

    Returns: (instance, created: bool)
    """
    defaults = defaults or {}
    qs_filter = {"user": user, "transaction_type": transaction_type}
    if related_object_id:
        qs_filter["related_object_id"] = related_object_id

    # fast path: existing
    existing = BlockchainTransaction.objects.filter(**qs_filter).first()
    if existing:
        return existing, False

    # attempt create inside atomic block
    try:
        with transaction.atomic():
            obj = BlockchainTransaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                related_object_id=related_object_id,
                **defaults,
            )
            return obj, True
    except IntegrityError as e:
        logger.warning("tx_idempotent_race: fetching existing tx after IntegrityError: %s", e)
        obj = BlockchainTransaction.objects.filter(**qs_filter).first()
        if obj:
            return obj, False
        raise
