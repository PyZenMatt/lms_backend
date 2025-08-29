from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

from common.response_utils import ok, err

User = get_user_model()
import logging

logger = logging.getLogger(__name__)


def _set_nonce_on_user(user, nonce):
    try:
        user.wallet_nonce = nonce
        # Prefer DB persistence when available
        if hasattr(user, "wallet_nonce"):
            user.save(update_fields=["wallet_nonce"])
            logger.debug("_set_nonce_on_user: persisted to DB user=%s", getattr(user, "pk", None))
        else:
            logger.debug("_set_nonce_on_user: wallet_nonce attribute missing on model, falling back to in-memory")
    except Exception:
        setattr(user, "_wallet_nonce", nonce)
        logger.exception("_set_nonce_on_user: exception saving wallet_nonce to DB, using in-memory for user=%s", getattr(user, "pk", None))


def _get_and_clear_nonce(user):
    try:
        n = getattr(user, "wallet_nonce", None)
        if n:
            # Clear persisted nonce
            if hasattr(user, "wallet_nonce"):
                user.wallet_nonce = ""
                user.save(update_fields=["wallet_nonce"])
                logger.debug("_get_and_clear_nonce: read+cleared DB nonce user=%s", getattr(user, "pk", None))
            else:
                logger.debug("_get_and_clear_nonce: wallet_nonce attribute missing on model, cannot clear DB field user=%s", getattr(user, "pk", None))
            return n
    except Exception:
        pass
    n = getattr(user, "_wallet_nonce", None)
    if n:
        try:
            delattr(user, "_wallet_nonce")
            logger.debug("_get_and_clear_nonce: read+cleared in-memory nonce user=%s", getattr(user, "pk", None))
        except Exception:
            pass
    return n


@method_decorator(csrf_exempt, name="dispatch")
class WalletChallengeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wallet_challenge"

    def post(self, request, *args, **kwargs):
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

        expected_message = f"Link wallet for user {request.user.pk} - nonce: {nonce}"

        try:
            from eth_account.messages import encode_defunct
            from eth_account.account import Account

            msg = encode_defunct(text=expected_message)
            recovered = Account.recover_message(msg, signature=signature)
            logger.debug("wallet_link: recovered=%s expected_addr=%s sig_prefix=%s user=%s", recovered, address, (signature or '')[:16], request.user.pk)
            if recovered.lower() != address.lower():
                logger.warning("wallet_link_invalid_signature user=%s address=%s nonce=%s", request.user.pk, address, nonce[:8])
                return err("INVALID_SIGNATURE", "Signature does not match address", 401)
        except Exception as e:
            logger.error("wallet_link_verify_failed user=%s err=%s", request.user.pk, str(e))
            return err("SERVER_MISCONFIG", f"Server cannot verify signature: {str(e)}", 500)

        try:
            request.user.wallet_address = address
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


    def delete(self, request, *args, **kwargs):
        """Unlink wallet from authenticated user"""
        try:
            request.user.wallet_address = None
            try:
                request.user.wallet_nonce = ""
            except Exception:
                pass
            request.user.save(update_fields=["wallet_address"]) if hasattr(request.user, "wallet_address") else request.user.save()
            logger.info("wallet_unlink_ok user=%s", request.user.pk)
            return ok({}, message="Wallet unlinked")
        except Exception as e:
            logger.error("wallet_unlink_failed user=%s err=%s", request.user.pk, str(e))
            return err("DB_SAVE_FAILED", "Could not unlink wallet", 500)
