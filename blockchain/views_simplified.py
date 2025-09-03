"""
Simplified Blockchain API Views for TeoCoin System

This module provides essential REST API endpoints for blockchain operations:
- Wallet balance queries (for MetaMask integration)
- Token information (for frontend display)
- Transaction status checking (for burn deposit verification)

All complex course payment, staking, and reward pool functionality has been
moved to the DB-based TeoCoin system for improved performance and reliability.

Security Note: This implementation is for educational/testnet use only.
Production deployments should implement additional security measures.
"""

import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rewards.models import BlockchainTransaction, TokenBalance
from services.blockchain_service import blockchain_service
from services.consolidated_teocoin_service import teocoin_service
from services.db_teocoin_service import db_teocoin_service
from users.models import User
from django.conf import settings
from .services.tx_utils import create_transaction_idempotent

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """
    Get the TeoCoin balance for the authenticated user.

    Returns the current token balance for the user's linked wallet address.
    Also updates the cached balance in the database.

    Returns:
        JSON response with:
        - balance: Current token balance as string
        - wallet_address: User's linked wallet address
        - token_info: General token information
        - user_id: User ID for frontend verification
        - username: Username for debugging

    Errors:
        - 400: Wallet not linked to user account
        - 500: Blockchain query error
    """
    import time

    start_time = time.time()

    user = request.user

    try:
        # Use BlockchainService to get wallet balance
        result = blockchain_service.get_user_wallet_balance(user)

        response_time = time.time() - start_time
        logger.info(
            f"Balance API completed in {response_time:.3f}s via BlockchainService"
        )
        if response_time > 1.0:
            logger.warning(
                f"Slow Balance API: {response_time:.3f}s for user {user.username}"
            )

        return Response(result)

    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Error retrieving balance for {user.email}: {e}")

        # Fallback to old logic for safety during transition
        if not user.wallet_address:
            response_time = time.time() - start_time
            logger.info(f"Balance API (no wallet) completed in {response_time:.3f}s")
            return Response(
                {"error": "Wallet not linked", "balance": "0", "wallet_address": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # First check if we have a cached balance that's recent enough
            token_balance, created = TokenBalance.objects.get_or_create(
                user=user, defaults={"balance": Decimal("0")}
            )

            # Only query blockchain if:
            # 1. We've just created the balance record OR
            # 2. The cached balance is stale (older than 5 minutes)
            if created or token_balance.is_stale(minutes=5):
                balance = teocoin_service.get_balance(user.wallet_address)
                token_balance.balance = balance
                token_balance.save()
                logger.info(
                    f"Updated blockchain balance for {user.username} from RPC call"
                )
            else:
                balance = token_balance.balance
                logger.info(
                    f"Using cached blockchain balance for {user.username} (last updated: {token_balance.last_updated})"
                )

            return Response(
                {
                    "balance": str(balance),
                    "wallet_address": user.wallet_address,
                    "token_info": teocoin_service.get_token_info(),
                    "user_id": user.id,  # Add user ID for frontend verification
                    "username": user.username,  # Add username for debugging
                    # Indicate if we used the cache
                    "cached": not created and not token_balance.is_stale(minutes=5),
                }
            )

        except Exception as e2:
            logger.error(f"Error retrieving balance for {user.email}: {e2}")
            return Response(
                {"error": "Error retrieving wallet balance", "balance": "0"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            response_time = time.time() - start_time
            logger.info(f"Balance API completed in {response_time:.3f}s")
            if response_time > 1.0:
                logger.warning(
                    f"Slow Balance API: {response_time:.3f}s for user {user.username}"
                )


@api_view(["GET"])
def get_token_info(request):
    """
    Get general information about the TeoCoin token.

    This endpoint provides public information about the TeoCoin token
    including contract details, symbol, decimals, etc. No authentication required.

    Returns:
        JSON response with token information:
        - name: Token name
        - symbol: Token symbol
        - decimals: Number of decimal places
        - contract_address: Smart contract address
        - network: Blockchain network name

    Errors:
        - 500: Blockchain query error
    """
    try:
        token_info = teocoin_service.get_token_info()
        return Response(token_info)
    except Exception as e:
        logger.error(f"Error retrieving token info: {e}")
        return Response(
            {"error": "Error retrieving token information"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def check_transaction_status(request):
    """
    Check the status of a blockchain transaction.

    Queries the blockchain for transaction receipt and updates the local
    database record if the transaction has been confirmed or failed.

    Request Body:
        tx_hash (str): Blockchain transaction hash to check

    Returns:
        JSON response with:
        - status: Transaction status (confirmed, failed, pending)
        - block_number: Block number (if confirmed)
        - gas_used: Gas used by transaction (if confirmed)
        - transaction_hash: Transaction hash
        - message: Status message (if pending)

    Errors:
        - 400: Missing tx_hash parameter
        - 500: Blockchain query error
    """
    tx_hash = request.data.get("tx_hash")

    if not tx_hash:
        return Response(
            {"error": "tx_hash is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        receipt = teocoin_service.get_transaction_receipt(tx_hash)

        if receipt:
            # Update transaction status in database if record exists
            try:
                blockchain_tx = BlockchainTransaction.objects.get(tx_hash=tx_hash)
                if receipt["status"] == 1:
                    blockchain_tx.status = "confirmed"
                    blockchain_tx.block_number = receipt["block_number"]
                    blockchain_tx.gas_used = receipt["gas_used"]
                else:
                    blockchain_tx.status = "failed"
                blockchain_tx.save()
            except BlockchainTransaction.DoesNotExist:
                # Transaction not found in our database - this is OK
                pass

            return Response(
                {
                    "status": "confirmed" if receipt["status"] == 1 else "failed",
                    "block_number": receipt["block_number"],
                    "gas_used": receipt["gas_used"],
                    "transaction_hash": receipt["transaction_hash"],
                }
            )
        else:
            return Response(
                {"status": "pending", "message": "Transaction still in progress"}
            )

    except Exception as e:
        logger.error(f"Error checking transaction status {tx_hash}: {e}")
        return Response(
            {"error": "Error checking transaction status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onchain_mint(request):
    """
    POST /api/v1/onchain/mint/

    Body: { amount: string|number, to: string (optional) }

    This endpoint mints tokens on-chain using the platform minter key and returns
    { tx_hash, tx_id } on success. It creates an idempotent BlockchainTransaction
    record using an optional related_id if provided.
    """
    user = request.user
    amount_raw = request.data.get("amount")
    to_addr = request.data.get("to") or getattr(user, "wallet_address", None)
    related_id = request.data.get("related_id")

    if not amount_raw:
        return Response({"status": "error", "error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from decimal import Decimal

        amount = Decimal(str(amount_raw))
    except Exception:
        return Response({"status": "error", "error": "invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

    if amount <= 0:
        return Response({"status": "error", "error": "amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

    if not to_addr:
        return Response({"status": "error", "error": "recipient address required"}, status=status.HTTP_400_BAD_REQUEST)

    # create idempotent transaction record
    defaults = {"amount": amount, "from_address": None, "to_address": to_addr}
    tx, created = create_transaction_idempotent(user, "mint", related_object_id=related_id, defaults=defaults)

    if not created and tx.tx_hash:
        return Response({"status": "ok", "tx_id": tx.id, "tx_hash": tx.tx_hash})

    try:
        # mark pending
        tx.status = "pending"
        tx.save()

        # Use teocoin_service to mint synchronously
        tx_hash = teocoin_service.mint_tokens(to_addr, amount) if teocoin_service else None
        tx.tx_hash = tx_hash
        tx.status = "pending"
        tx.save()

        return Response({"status": "ok", "tx_id": tx.id, "tx_hash": tx_hash})
    except Exception as e:
        tx.status = "failed"
        tx.error_message = str(e)
        tx.save()
        return Response({"status": "error", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_deposit(request):
    """
    Verify an on-chain deposit transaction and credit the user's DB balance.

    Body:
        tx_hash: string (required) - transaction hash to verify
        wallet_address: string (optional) - user's wallet address to credit (fallback)

    The endpoint will:
    - retrieve the transaction receipt via teocoin_service
    - inspect logs for a Transfer event to the platform/custodial address
    - if valid and confirmed, credit the matching user via db_teocoin_service.credit_user
    """
    tx_hash = request.data.get("tx_hash")
    wallet_address = request.data.get("wallet_address")

    if not tx_hash:
        return Response({"success": False, "error": "tx_hash is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        receipt = teocoin_service.get_transaction_receipt(tx_hash)

        if not receipt:
            return Response({"success": False, "status": "pending", "message": "Transaction not yet mined"}, status=status.HTTP_200_OK)

        # Ensure transaction succeeded
        if receipt.get("status") != 1:
            return Response({"success": False, "error": "Transaction failed on-chain", "status": "failed"}, status=status.HTTP_200_OK)

        # Find Transfer logs targeting our platform address (PLATFORM_WALLET_ADDRESS)
        logs = receipt.get("logs") or []
        platform_address = getattr(settings, "PLATFORM_WALLET_ADDRESS", None)

        # Try to extract recipient and amount from logs if possible
        to_addr = None
        amount_wei = None

        for log in logs:
            try:
                # Only inspect logs emitted by our token contract
                # The consolidated service may already return decoded logs in some environments
                if isinstance(log, dict) and log.get("address"):
                    # Check Transfer signature in topics
                    topics = log.get("topics", [])
                    if topics and topics[0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        # topics[2] is 'to'
                        to_addr = "0x" + topics[2].hex()[-40:]
                        data_hex = log.get("data", b"").hex()
                        amount_wei = int(data_hex, 16) if data_hex else None
                        break
            except Exception:
                continue

        # Fallback: use provided wallet_address
        if not to_addr and wallet_address:
            to_addr = wallet_address

        if not to_addr:
            return Response({"success": False, "error": "Could not determine recipient from receipt"}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize checksum
        try:
            from web3 import Web3

            to_addr = Web3.to_checksum_address(to_addr)
        except Exception:
            pass

        # Find user by wallet_address
        try:
            user = User.objects.filter(wallet_address__iexact=to_addr).first()
        except Exception:
            user = None

        if not user:
            return Response({"success": False, "error": "No user found for recipient address"}, status=status.HTTP_404_NOT_FOUND)

        # Convert wei to TEO amount using token decimals
        token_info = teocoin_service.get_token_info()
        decimals = int(token_info.get("decimals", 18)) if token_info else 18
        amount = None
        if amount_wei is not None:
            amount = Decimal(amount_wei) / (Decimal(10) ** decimals)

        if amount is None or amount <= 0:
            return Response({"success": False, "error": "Invalid transfer amount"}, status=status.HTTP_400_BAD_REQUEST)

        # Credit the user via DB service
        credit_result = db_teocoin_service.credit_user(
            user=user,
            amount=amount,
            transaction_type="deposit",
            description=f"On-chain deposit {tx_hash}",
            metadata={"transaction_hash": tx_hash},
        )

        if credit_result.get("success"):
            return Response({"success": True, "message": "Deposit verified and credited", "amount": str(amount), "user_pk": user.pk, "tx_hash": tx_hash}, status=status.HTTP_200_OK)
        else:
            return Response({"success": False, "error": credit_result.get("error", "Failed to credit user")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error verifying deposit {tx_hash}: {e}")
        return Response({"success": False, "error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def wallet_withdraw(request):
    """
    Create a withdrawal request and (optionally) auto-process by minting tokens to the user's MetaMask address.

    Body:
        amount: string/decimal (required)
        metamask_address: string (optional, fallback to user.wallet_address)

    Returns:
        JSON with withdrawal_id and tx_hash (if auto-processed) or pending status.
    """
    try:
        from decimal import Decimal
        from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance

        user = request.user

        amount_raw = request.data.get("amount")
        metamask_address = request.data.get("metamask_address") or getattr(user, "wallet_address", None)

        if not amount_raw:
            return Response({"success": False, "error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount_raw))
            if amount <= 0:
                raise ValueError("Amount must be > 0")
        except Exception:
            return Response({"success": False, "error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if not metamask_address:
            return Response({"success": False, "error": "No MetaMask address provided or linked"}, status=status.HTTP_400_BAD_REQUEST)

    # Create withdrawal request using existing service (handles limits, daily caps, etc.)
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        create_result = None
        try:
            create_result = teocoin_service and None  # ensure teocoin_service is available
        except Exception:
            create_result = None

        # Use teocoin_withdrawal_service to create request and manage DB balances
        from services.teocoin_withdrawal_service import teocoin_withdrawal_service as withdrawal_svc

        result = withdrawal_svc.create_withdrawal_request(
            user=user,
            amount=amount,
            wallet_address=metamask_address,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not result.get("success"):
            return Response({"success": False, "error": result.get("error", "Failed to create withdrawal")}, status=status.HTTP_400_BAD_REQUEST)

        withdrawal_id = result.get("withdrawal_id")
        try:
            withdrawal_id = int(withdrawal_id) if withdrawal_id is not None else None
        except Exception:
            withdrawal_id = None

        # Lock user's DB balance and create a ledger transaction entry
        try:
            balance_obj = DBTeoCoinBalance.objects.select_for_update().get(user=user)
        except DBTeoCoinBalance.DoesNotExist:
            # Create a balance record if missing
            balance_obj = DBTeoCoinBalance.objects.create(user=user, available_balance=Decimal('0.00'), staked_balance=Decimal('0.00'), pending_withdrawal=Decimal('0.00'))

        # Move amount from available_balance to pending_withdrawal to avoid races
        try:
            if balance_obj.available_balance < amount:
                return Response({"success": False, "error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
            balance_obj.available_balance -= amount
            balance_obj.pending_withdrawal += amount
            balance_obj.save()

            # Create DB transaction ledger entry
            from blockchain.models import DBTeoCoinTransaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type="withdrawn",
                amount=amount,
                description=f"Withdraw request #{withdrawal_id}",
                blockchain_tx_hash=None,
            )
        except Exception as e:
            logger.error(f"Error updating DB balance for withdrawal {withdrawal_id}: {e}")
            # Attempt to rollback by marking withdrawal failed
            try:
                wr = TeoCoinWithdrawalRequest.objects.get(id=withdrawal_id)
                wr.status = "failed"
                wr.error_message = "Failed to reserve balance"
                wr.save()
            except Exception:
                pass
            return Response({"success": False, "error": "Failed to reserve balance"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Try to auto-process (mint) immediately, similar to existing API behavior
        try:
            # Only pass withdrawal_id when it's a valid int
            mint_kwargs = {
                "amount": amount,
                "to_address": metamask_address,
            }
            if isinstance(withdrawal_id, int):
                mint_kwargs["withdrawal_id"] = withdrawal_id
            mint_result = withdrawal_svc.mint_tokens_to_address(**mint_kwargs)

            # Update request record with tx hash and status
            try:
                wr = TeoCoinWithdrawalRequest.objects.get(id=withdrawal_id)
                if mint_result.get("success"):
                    wr.status = "processing"
                    wr.transaction_hash = mint_result.get("transaction_hash")
                    wr.save()

                    # update the ledger transaction with blockchain_tx_hash
                    try:
                        tx = DBTeoCoinTransaction.objects.filter(user=user, transaction_type="withdrawn").order_by("-created_at").first()
                        if tx and mint_result.get("transaction_hash"):
                            tx.blockchain_tx_hash = mint_result.get("transaction_hash")
                            tx.save()
                    except Exception:
                        logger.exception("Failed to attach blockchain_tx_hash to DB transaction")

                else:
                    wr.status = "failed"
                    wr.error_message = mint_result.get("error")
                    wr.save()
                    # revert pending_withdrawal back to available on failure
                    try:
                        balance_obj.pending_withdrawal -= amount
                        balance_obj.available_balance += amount
                        balance_obj.save()
                    except Exception:
                        logger.exception("Failed to rollback balances after mint failure")
            except Exception:
                logger.exception("Failed to update withdrawal record after mint attempt")

            # Return response with tx info if available
            if mint_result.get("success"):
                return Response({"success": True, "withdrawal_id": withdrawal_id, "tx_hash": mint_result.get("transaction_hash")}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": True, "withdrawal_id": withdrawal_id, "status": "pending", "message": "Withdrawal created but auto-processing failed"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error auto-processing withdrawal {withdrawal_id}: {e}")
            return Response({"success": True, "withdrawal_id": withdrawal_id, "status": "pending"}, status=status.HTTP_201_CREATED)

    except Exception as exc:
        logger.error(f"Error in wallet_withdraw: {exc}")
        return Response({"success": False, "error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
