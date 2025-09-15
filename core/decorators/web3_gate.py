import logging
import time
from functools import wraps
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _web3_enabled() -> bool:
    # Two ways in the codebase to indicate DB-only TeoCoin system
    # - env var `TEOCOIN_SYSTEM=database`
    # - boolean `USE_DB_TEOCOIN_SYSTEM` True
    try:
        if getattr(settings, "TEOCOIN_SYSTEM", None) == "database":
            return False
        if getattr(settings, "USE_DB_TEOCOIN_SYSTEM", False):
            return False
    except Exception:
        # If settings are not accessible for some reason, default to enabled
        return True
    return True


def require_web3_enabled(view_func):
    """Decorator that returns 410 when web3 features are disabled.

    Response body: {"code":"feature_disabled","reason":"web3_disabled"}

    Also logs a structured `web3_gate_hit` entry with path, user_id/anon and timestamp.
    This is intentionally lightweight and has no side-effects besides logging.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        enabled = _web3_enabled()
        if not enabled:
            user = getattr(request, "user", None)
            user_id = getattr(user, "id", None) if user and getattr(user, "is_authenticated", False) else "anon"
            ts = int(time.time())
            logger.info(
                "web3_gate_hit %s",
                {"path": request.path, "user_id": user_id, "ts": ts},
            )
            return JsonResponse({"code": "feature_disabled", "reason": "web3_disabled"}, status=410)
        return view_func(request, *args, **kwargs)

    return _wrapped


# Usage / Fallback
# - Apply `@require_web3_enabled` to view functions or `@method_decorator(require_web3_enabled)`
#   to class-based view methods.
# - To remove the gate, delete the decorator annotations from the target view(s).
# - This file intentionally avoids database access or migrations and only reads Django
#   settings to make it safe to include in docs-only or low-risk patches.
