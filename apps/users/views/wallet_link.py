from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

from apps.common.response_utils import ok, err

User = get_user_model()
import logging

logger = logging.getLogger(__name__)


def _set_nonce_on_user(user, nonce):
    # store nonce temporarily on user instance in DB if field exists, otherwise on cache attribute
    try:
        user.wallet_nonce = nonce
        user.save(update_fields=["wallet_nonce"]) if hasattr(user, "wallet_nonce") else None
    except Exception:
        # best-effort: attach attribute in-memory (will not persist across processes)
        setattr(user, "_wallet_nonce", nonce)


def _get_and_clear_nonce(user):
    try:
        n = getattr(user, "wallet_nonce", None)
        if n:
            user.wallet_nonce = ""
            user.save(update_fields=["wallet_nonce"]) if hasattr(user, "wallet_nonce") else None
            return n
    except Exception:
        pass
    n = getattr(user, "_wallet_nonce", None)
    if n:
        try:
            delattr(user, "_wallet_nonce")
        except Exception:
            pass
    return n


@method_decorator(csrf_exempt, name="dispatch")
class WalletChallengeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wallet_challenge"

    def post(self, request, *args, **kwargs):
        # generate a nonce and optional message
        nonce = get_random_string(32)
        message = f"Link wallet for user {request.user.pk} - nonce: {nonce}"
        _set_nonce_on_user(request.user, nonce)
        return ok({"nonce": nonce, "message": message})


@method_decorator(csrf_exempt, name="dispatch")
class WalletLinkView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wallet_link"

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        address = data.get("address")
        signature = data.get("signature")
        if not address or not signature:
            return err("MISSING_PARAMS", "address and signature required", 400)

        nonce = _get_and_clear_nonce(request.user)
        if not nonce:
            logger.warning("wallet_link: nonce_missing user=%s", request.user.pk)
            return err("NONCE_MISSING", "No challenge nonce found; request a new challenge", 400)

        # Construct expected message
        expected_message = f"Link wallet for user {request.user.pk} - nonce: {nonce}"

        # Verify signature using eth_account if available, otherwise accept naive (TODO)
        try:
            from eth_account.messages import encode_defunct
            from eth_account.account import Account

            msg = encode_defunct(text=expected_message)
            recovered = Account.recover_message(msg, signature=signature)
            if recovered.lower() != address.lower():
                logger.warning("wallet_link_invalid_signature user=%s address=%s nonce=%s", request.user.pk, address, nonce[:8])
                return err("INVALID_SIGNATURE", "Signature does not match address", 401)
        except Exception as e:
            logger.error("wallet_link_verify_failed user=%s err=%s", request.user.pk, str(e))
            # If eth_account not installed, reject with explicit error
            return err("SERVER_MISCONFIG", f"Server cannot verify signature: {str(e)}", 500)

        # Persist wallet address on user
        try:
            request.user.wallet_address = address
            # reset nonce field if present
            try:
                request.user.wallet_nonce = ""
            except Exception:
                pass
            request.user.save(update_fields=["wallet_address"]) if hasattr(request.user, "wallet_address") else request.user.save()
        except Exception as e:
            logger.error("wallet_link_save_failed user=%s err=%s", request.user.pk, str(e))
            return err("DB_SAVE_FAILED", f"Could not save wallet address: {str(e)}", 500)
        logger.info("wallet_link_ok user=%s address=%s", request.user.pk, address)
        return ok({"wallet_address": address}, message="Wallet linked")
