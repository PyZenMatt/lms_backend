import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rewards.services.wallet_services import mint_teo, burn_teo
from core.decorators.web3_gate import require_web3_enabled
from rewards import constants
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_web3_enabled
def mint(request):
    try:
        user = request.user
        # Only allow operations on own wallet (no user in body)
        if request.data.get("user"):
            return Response({"ok": False, "error": "user cannot be set in request body"}, status=status.HTTP_400_BAD_REQUEST)
        amount = Decimal(str(request.data.get("amount", 0)))
        idem_key = request.data.get("idem_key")
        if amount <= 0:
            return Response({"ok": False, "error": "amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)
        if not idem_key:
            return Response({"ok": False, "error": "idem_key required"}, status=status.HTTP_400_BAD_REQUEST)
        # Validate decimals: max 8 dp for chain
        if (amount * 10**8) != (amount * 10**8).quantize(Decimal("1")):
            return Response({"ok": False, "error": "amount has too many decimal places (max 8)"}, status=status.HTTP_400_BAD_REQUEST)
        if amount > constants.MAX_MINT_BURN:
            return Response({"ok": False, "error": f"amount exceeds maximum {constants.MAX_MINT_BURN}"}, status=status.HTTP_400_BAD_REQUEST)

        result = mint_teo(user=user, amount=amount, idem_key=idem_key)
        return Response({"ok": True, "result": result})

    except Exception as e:
        logger.exception("mint error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@require_web3_enabled
def burn(request):
    try:
        user = request.user
        if request.data.get("user"):
            return Response({"ok": False, "error": "user cannot be set in request body"}, status=status.HTTP_400_BAD_REQUEST)
        amount = Decimal(str(request.data.get("amount", 0)))
        idem_key = request.data.get("idem_key")
        if amount <= 0:
            return Response({"ok": False, "error": "amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)
        if not idem_key:
            return Response({"ok": False, "error": "idem_key required"}, status=status.HTTP_400_BAD_REQUEST)
        # Validate decimals: max 8 dp for chain
        if (amount * 10**8) != (amount * 10**8).quantize(Decimal("1")):
            return Response({"ok": False, "error": "amount has too many decimal places (max 8)"}, status=status.HTTP_400_BAD_REQUEST)
        if amount > constants.MAX_MINT_BURN:
            return Response({"ok": False, "error": f"amount exceeds maximum {constants.MAX_MINT_BURN}"}, status=status.HTTP_400_BAD_REQUEST)

        result = burn_teo(user=user, amount=amount, idem_key=idem_key)
        return Response({"ok": True, "result": result})

    except Exception as e:
        logger.exception("burn error: %s", e)
        return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health(request):
    """Simple health check for wallet endpoints (useful for FE CORS/JWT checks)."""
    return Response({"ok": True})
