from decimal import Decimal
from uuid import uuid4
import time
import logging

logger = logging.getLogger(__name__)


def _call_chain_simulator(user, amount: Decimal, op: str) -> str:
    """Simulate chain call with a tiny delay. Returns a fake tx hash.

    In production replace this with real Web3 calls that honour timeouts and
    return the transaction hash.
    """
    # Simulate network latency
    time.sleep(0.05)
    tx_hash = "0x" + uuid4().hex
    logger.info("chain_simulator %s user=%s amount=%s tx=%s", op, getattr(user, 'id', None), amount, tx_hash)
    return tx_hash


def send_mint(user, amount: Decimal, timeout_seconds: int = 10, retries: int = 1) -> str:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return _call_chain_simulator(user, amount, "mint")
        except Exception as exc:
            last_exc = exc
            logger.warning("send_mint attempt=%s failed: %s", attempt, exc)
            time.sleep(0.1 * (attempt + 1))
    raise last_exc if last_exc is not None else RuntimeError("send_mint failed")


def send_burn(user, amount: Decimal, timeout_seconds: int = 10, retries: int = 1) -> str:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return _call_chain_simulator(user, amount, "burn")
        except Exception as exc:
            last_exc = exc
            logger.warning("send_burn attempt=%s failed: %s", attempt, exc)
            time.sleep(0.1 * (attempt + 1))
    raise last_exc if last_exc is not None else RuntimeError("send_burn failed")
