"""Application-level constants for TeoCoin wallet/transaction flows.

Keep these separate from model choices to avoid DB migrations while providing
stable names for services and views.
"""
from decimal import Decimal

# Chain transaction types
TX_MINT = "mint"
TX_BURN = "burn"

# Standard status values (align with BlockchainTransaction.STATUS_CHOICES)
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# DB transaction types mapping (use existing DB choices to avoid migrations)
# For a mint (DB -> chain) we record a withdrawal in the DB ledger
DB_TX_WITHDRAWN = "withdrawn"
# For a burn (chain -> DB) we record a deposit in the DB ledger
DB_TX_DEPOSIT = "deposit"

# Decimal quantization helpers (where needed)
DECIMAL_PRECISION_2 = Decimal("0.01")
DECIMAL_PRECISION_8 = Decimal("0.00000001")

__all__ = [
    "TX_MINT",
    "TX_BURN",
    "STATUS_PENDING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "DB_TX_WITHDRAWN",
    "DB_TX_DEPOSIT",
    "DECIMAL_PRECISION_2",
    "DECIMAL_PRECISION_8",
    # Maximum single mint/burn operation (sane upper bound to avoid accidents)
    "MAX_MINT_BURN",
]

# Maximum allowed amount per operation (TEO)
MAX_MINT_BURN = Decimal("100000")
