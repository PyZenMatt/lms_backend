# Hint map for T-003.G coverage script
# Map canonical Path regex -> list of candidate modules to check for decorator presence.
# Use this to detect "composed" URLs where the path is assembled via urls/includes.
HINT_MAP = {
    r'^/api/v1/rewards/wallet/mint/$': ['rewards/views/wallet_views.py'],
    r'^/api/v1/rewards/wallet/burn/$': ['rewards/views/wallet_views.py'],
    r'^/api/v1/teocoin/withdraw/$': ['api/teocoin_views.py', 'services/teocoin_withdrawal_service.py'],
    r'^/api/v1/teocoin/withdrawals/admin/process-pending/$': ['api/withdrawal_views.py', 'blockchain/management/commands/process_teocoin_withdrawals.py'],
    r'^/api/v1/teocoin/withdrawals/admin/mint/$': ['api/withdrawal_views.py'],
    # discounts confirm is handled by rewards app; included here as a hint for triage
    r'^/api/v1/rewards/discounts/confirm/$': ['rewards/views/discount_views.py', 'rewards/views/checkout_views.py'],
}

# Helper: given a path, return candidate module paths relative to lms_backend/ directory.
import re

def candidates_for(path):
    for pattern, modules in HINT_MAP.items():
        if re.match(pattern, path):
            return modules
    return []
