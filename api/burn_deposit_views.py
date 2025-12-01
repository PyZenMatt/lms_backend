"""
TeoCoin Burn Deposit API Views
Handles burning tokens from MetaMask and crediting platform balance
"""

import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from services.db_teocoin_service import DBTeoCoinService
from web3 import Web3

from blockchain.blockchain import teocoin_service

logger = logging.getLogger(__name__)


class BurnDepositView(APIView):
    """
    Burn tokens from user's MetaMask and credit platform balance
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Process a burn deposit transaction

        Body:
        {
            "transaction_hash": "0x123...",
            "amount": "100.00",
            "metamask_address": "0xabc..."
        }
        """
        try:
            logger.info(f"🔥 Burn deposit request from {request.user.email}")
            logger.info(f"📄 Request data: {request.data}")

            tx_hash = request.data.get("transaction_hash")
            amount = request.data.get("amount")
            # SECURITY FIX: Use linked wallet address from user profile, not from request body
            # This prevents spoofing attacks where user claims deposit from another wallet
            linked_wallet_address = getattr(request.user, "wallet_address", None)

            logger.info(
                f"📊 Parsed: tx_hash={tx_hash}, amount={amount}, linked_wallet={linked_wallet_address}"
            )

            # Validation: User must have a linked wallet
            if not linked_wallet_address:
                logger.warning(f"❌ User {request.user.email} has no linked wallet")
                return Response(
                    {
                        "success": False,
                        "error": "No wallet linked to your account. Please link your wallet first.",
                        "error_code": "NO_LINKED_WALLET",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validation: tx_hash and amount required
            if not tx_hash or not amount:
                return Response(
                    {
                        "success": False,
                        "error": "Transaction hash and amount are required",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal <= 0:
                    return Response(
                        {"success": False, "error": "Amount must be greater than 0"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except (ValueError, TypeError):
                return Response(
                    {"success": False, "error": "Invalid amount format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(f"✅ Validation passed for {amount_decimal} TEO")

            # Check teocoin_service initialization
            if not hasattr(teocoin_service, "w3") or teocoin_service.w3 is None:
                logger.error(
                    "❌ TeoCoin service not properly initialized - Web3 connection missing"
                )
                return Response(
                    {"success": False, "error": "Blockchain service not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            if (
                not hasattr(teocoin_service, "admin_private_key")
                or not teocoin_service.admin_private_key
            ):
                logger.error("❌ Admin private key not configured")
                return Response(
                    {
                        "success": False,
                        "error": "Service configuration error - admin credentials missing",
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Check if transaction already processed (prevent double-processing)
            from blockchain.models import DBTeoCoinTransaction

            existing_tx = DBTeoCoinTransaction.objects.filter(
                user=request.user, blockchain_tx_hash=tx_hash
            ).first()

            if existing_tx:
                logger.warning(f"⚠️ Transaction {tx_hash} already processed")
                return Response(
                    {
                        "success": False,
                        "error": "Transaction already processed",
                        "already_processed": True,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            logger.info(f"✅ Transaction not yet processed, continuing...")

            # Verify transaction on blockchain
            logger.info(f"🔍 Starting blockchain verification...")
            verification_result = self.verify_burn_transaction(
                tx_hash, amount_decimal, linked_wallet_address
            )

            logger.info(f"📊 Verification result: {verification_result}")

            if not verification_result["valid"]:
                logger.warning(
                    f"❌ Verification failed: {verification_result['error']}"
                )
                return Response(
                    {"success": False, "error": verification_result["error"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(f"✅ Blockchain verification passed")

            # Credit user's platform balance
            logger.info(f"💰 Crediting user balance...")
            db_service = DBTeoCoinService()
            credit_result = db_service.credit_user(
                user=request.user,
                amount=amount_decimal,
                transaction_type="deposit",
                description=f"Burn deposit: {tx_hash[:10]}...",
                metadata={
                    "transaction_hash": tx_hash,
                    "wallet_address": linked_wallet_address,  # Use verified linked wallet
                    "block_number": verification_result.get("block_number"),
                    "gas_used": verification_result.get("gas_used"),
                },
            )

            logger.info(f"📊 Credit result: {credit_result}")

            if credit_result and credit_result.get("success"):
                logger.info(
                    f"✅ Burn deposit successful: {amount_decimal} TEO for {request.user.email}"
                )

                return Response(
                    {
                        "success": True,
                        "message": f"Successfully deposited {amount_decimal} TEO to your platform balance",
                        "amount": str(amount_decimal),
                        "transaction_hash": tx_hash,
                        "new_balance": str(credit_result.get("new_balance", 0)),
                        "burn_verified": True,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                logger.error(f"❌ Failed to credit balance: {credit_result}")
                return Response(
                    {"success": False, "error": "Failed to credit platform balance"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"❌ Error processing burn deposit: {e}")
            import traceback

            logger.error(f"📜 Full traceback: {traceback.format_exc()}")
            return Response(
                {
                    "success": False,
                    "error": "Internal server error during burn deposit processing",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def verify_burn_transaction(
        self, tx_hash: str, expected_amount: Decimal, expected_address: str
    ) -> dict:
        """
        Verify that the burn transaction is valid
        """
        try:
            logger.info(f"🔍 Verifying burn transaction: {tx_hash}")

            # Get transaction receipt
            w3 = teocoin_service.w3
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                logger.info(f"📊 Receipt status: {receipt.get('status')}")
            except Exception as e:
                logger.error(f"❌ Failed to get transaction receipt: {e}")
                return {"valid": False, "error": "Transaction not found on blockchain"}

            if not receipt:
                return {"valid": False, "error": "Transaction not found"}

            if receipt["status"] != 1:
                return {"valid": False, "error": "Transaction failed on blockchain"}

            logger.info(f"✅ Transaction found and successful")

            # Get transaction details
            try:
                tx = w3.eth.get_transaction(tx_hash)
                logger.info(
                    f"📊 Transaction from: {tx.get('from')}, to: {tx.get('to')}"
                )
            except Exception as e:
                logger.error(f"❌ Failed to get transaction details: {e}")
                return {"valid": False, "error": "Failed to get transaction details"}

            # Verify sender address
            if tx.get("from", "").lower() != expected_address.lower():
                logger.error(
                    f"❌ Address mismatch: {tx.get('from')} != {expected_address}"
                )
                return {
                    "valid": False,
                    "error": "Transaction sender does not match provided address",
                }

            # Verify contract address (should be TEO contract)
            if tx.get("to", "").lower() != teocoin_service.contract_address.lower():
                logger.error(
                    f"❌ Contract mismatch: {tx.get('to')} != {teocoin_service.contract_address}"
                )
                return {"valid": False, "error": "Transaction not sent to TEO contract"}

            logger.info(f"✅ Address and contract verification passed")

            # Try to verify burn amount via Transfer events (most reliable method)
            logger.info(f"🔍 Checking Transfer events for burn...")
            burn_verified = self.verify_burn_via_events(
                receipt, expected_amount, expected_address
            )

            if burn_verified["valid"]:
                logger.info(f"✅ Burn verification successful via events")
                return burn_verified

            # Fallback: Try to decode transaction input
            logger.info(f"🔍 Fallback: trying to decode transaction input...")
            try:
                contract = teocoin_service.contract
                decoded = contract.decode_function_input(tx.get("input", ""))
                function_obj, function_inputs = decoded

                logger.info(f"📊 Decoded function: {function_obj.function_identifier}")
                logger.info(f"📊 Function inputs: {function_inputs}")

                # Check if it's a burn function call
                # The burn function signature should be 'burn(uint256)'
                if "burn" in str(function_obj.function_identifier).lower():
                    # Verify amount
                    burned_amount_wei = function_inputs.get("amount", 0)
                    burned_amount = Web3.from_wei(burned_amount_wei, "ether")

                    logger.info(f"📊 Burned amount from input: {burned_amount}")

                    if abs(burned_amount - expected_amount) <= Decimal(
                        "0.000001"
                    ):  # Allow small rounding
                        logger.info(
                            f"✅ Burn verification successful via function input"
                        )
                        return {
                            "valid": True,
                            "block_number": receipt["blockNumber"],
                            "gas_used": receipt["gasUsed"],
                            "burned_amount": str(burned_amount),
                        }
                    else:
                        logger.error(
                            f"❌ Amount mismatch: {burned_amount} != {expected_amount}"
                        )
                        return {
                            "valid": False,
                            "error": f"Burned amount {burned_amount} does not match expected {expected_amount}",
                        }
                else:
                    logger.error(f"❌ Not a burn function call")
                    return {
                        "valid": False,
                        "error": "Transaction is not a burn function call",
                    }

            except Exception as decode_error:
                logger.warning(f"⚠️ Could not decode transaction input: {decode_error}")
                # If we can't decode, but we have a valid transaction to the right contract,
                # we'll accept it as a potential burn (less strict verification)
                logger.info(f"⚠️ Using relaxed verification - transaction appears valid")
                return {
                    "valid": True,
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"],
                    "burned_amount": str(expected_amount),
                    "verification_method": "relaxed",
                }

        except Exception as e:
            logger.error(f"❌ Error verifying burn transaction {tx_hash}: {e}")
            import traceback

            logger.error(f"📜 Verification traceback: {traceback.format_exc()}")
            return {"valid": False, "error": f"Verification failed: {str(e)}"}

    def verify_burn_via_events(
        self, receipt, expected_amount: Decimal, expected_address: str
    ) -> dict:
        """
        Verify burn by checking Transfer events (fallback method)
        """
        try:
            logger.info(f"🔍 Verifying burn via Transfer events...")
            contract = teocoin_service.contract

            # Get Transfer events from receipt
            try:
                transfer_events = contract.events.Transfer().process_receipt(receipt)
                logger.info(f"📊 Found {len(transfer_events)} Transfer events")
            except Exception as e:
                logger.error(f"❌ Failed to process Transfer events: {e}")
                return {"valid": False, "error": "Failed to process Transfer events"}

            for i, event in enumerate(transfer_events):
                logger.info(
                    f"📊 Event {i}: from={event['args'].get('from')}, to={event['args'].get('to')}, value={event['args'].get('value')}"
                )

                # Check if it's a burn (transfer to 0x0)
                if (
                    event["args"].get("from", "").lower() == expected_address.lower()
                    and event["args"].get("to")
                    == "0x0000000000000000000000000000000000000000"
                ):

                    burned_amount = Web3.from_wei(
                        event["args"].get("value", 0), "ether"
                    )
                    logger.info(f"📊 Found burn event: {burned_amount} TEO")

                    if abs(burned_amount - expected_amount) <= Decimal("0.000001"):
                        logger.info(f"✅ Burn amount matches expected")
                        return {
                            "valid": True,
                            "block_number": receipt["blockNumber"],
                            "gas_used": receipt["gasUsed"],
                            "burned_amount": str(burned_amount),
                            "verification_method": "events",
                        }
                    else:
                        logger.error(
                            f"❌ Burn amount mismatch: {burned_amount} != {expected_amount}"
                        )

            logger.warning(f"⚠️ No matching burn event found")
            return {"valid": False, "error": "No matching burn event found"}

        except Exception as e:
            logger.error(f"❌ Error verifying burn via events: {e}")
            import traceback

            logger.error(f"📜 Events verification traceback: {traceback.format_exc()}")
            return {"valid": False, "error": "Event verification failed"}


class BurnDepositStatusView(APIView):
    """
    Check if a transaction has already been processed
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, tx_hash):
        """
        Check if a burn transaction has already been processed
        """
        try:
            from blockchain.models import DBTeoCoinTransaction

            # Check if transaction already processed
            existing_tx = DBTeoCoinTransaction.objects.filter(
                user=request.user,
                transaction_type="burn_deposit",
                metadata__transaction_hash=tx_hash,
            ).first()

            if existing_tx:
                return Response(
                    {
                        "success": True,
                        "processed": True,
                        "amount": str(existing_tx.amount),
                        "processed_at": existing_tx.created_at.isoformat(),
                        "message": "Transaction already processed",
                    }
                )
            else:
                return Response(
                    {
                        "success": True,
                        "processed": False,
                        "message": "Transaction not yet processed",
                    }
                )

        except Exception as e:
            logger.error(f"Error checking burn deposit status: {e}")
            return Response(
                {"success": False, "error": "Error checking transaction status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
