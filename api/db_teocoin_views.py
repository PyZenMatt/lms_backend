"""
DB TeoCoin API Views
REST API endpoints for the new database-based TeoCoin system
"""

import logging
from decimal import Decimal

from blockchain.models import TeoCoinWithdrawalRequest
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from services.db_teocoin_service import DBTeoCoinService

logger = logging.getLogger(__name__)


class TeoCoinBalanceView(APIView):
    """Get user's DB TeoCoin balance"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's TeoCoin balance"""
        try:
            db_service = DBTeoCoinService()
            balance_data = db_service.get_user_balance(request.user)

            return Response({"success": True, "balance": balance_data})

        except Exception as e:
            # Log full exception with traceback for debugging
            logger.exception(f"Error getting balance for user {getattr(request.user, 'id', None)}: {e}")
            # Surface the exception message in development to help debug client-side.
            # (In production, consider hiding internal errors.)
            return Response(
                {"success": False, "error": "Failed to get balance", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CalculateDiscountView(APIView):
    """Calculate discount for a course"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Calculate discount based on user's balance and course price"""
        try:
            course_price = Decimal(str(request.data.get("course_price", 0)))
            request.data.get("course_id")

            if course_price <= 0:
                return Response(
                    {"success": False, "error": "Invalid course price"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            db_service = DBTeoCoinService()
            discount_info = db_service.calculate_discount(
                user=request.user, course_price=course_price
            )

            return Response({"success": True, "discount": discount_info})

        except Exception as e:
            logger.error(f"Error calculating discount for user {request.user.id}: {e}")
            return Response(
                {"success": False, "error": "Failed to calculate discount"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplyDiscountView(APIView):
    """Apply TeoCoin discount for course purchase"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        DEPRECATED: Apply TeoCoin discount

        This endpoint is now deprecated to prevent premature TeoCoin deduction.
        TeoCoin is now deducted automatically in ConfirmPaymentView after Stripe payment succeeds.
        """
        try:
            logger.warning(
                f"🚨 DEPRECATED: ApplyDiscountView called by user {request.user.id}"
            )
            logger.warning("🚨 This endpoint should not be called directly by frontend")
            logger.warning(
                "🚨 TeoCoin deduction now happens after payment confirmation"
            )

            # Return error to prevent frontend from using this endpoint
            return Response(
                {
                    "success": False,
                    "error": "This endpoint is deprecated. TeoCoin discount is now applied automatically after payment confirmation.",
                    "code": "ENDPOINT_DEPRECATED",
                    "message": "Please use the payment flow instead. TeoCoin will be deducted only after successful payment.",
                    "migration_note": "Frontend should not call this endpoint directly",
                },
                status=status.HTTP_410_GONE,
            )  # 410 = Gone (deprecated)

        except Exception as e:
            logger.error(f"Error in deprecated ApplyDiscountView: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "Endpoint deprecated - use payment flow instead",
                },
                status=status.HTTP_410_GONE,
            )


class PurchaseCourseView(APIView):
    """Purchase course entirely with TeoCoin"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Purchase course with TeoCoin"""
        try:
            course_id = request.data.get("course_id")
            teo_amount = Decimal(str(request.data.get("teo_amount", "0")))

            if not course_id or teo_amount <= 0:
                return Response(
                    {
                        "success": False,
                        "error": "Course ID and TeoCoin amount required",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check user balance
            db_service = DBTeoCoinService()
            balance = db_service.get_user_balance(request.user)
            if balance["available_balance"] < teo_amount:
                return Response(
                    {
                        "success": False,
                        "error": f'Insufficient balance. Available: {balance["available_balance"]} TEO, Required: {teo_amount} TEO',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Deduct TeoCoin for course purchase
            success = db_service.deduct_balance(
                user=request.user,
                amount=teo_amount,
                transaction_type="purchase",
                description=f"Course purchase: {course_id}",
                course_id=course_id,
            )

            if not success:
                return Response(
                    {"success": False, "error": "Failed to purchase course"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # TODO: Integrate with course enrollment system
            # This should enroll the user in the course

            # Get updated balance
            new_balance_data = db_service.get_user_balance(request.user)

            return Response(
                {
                    "success": True,
                    "type": "teocoin_payment",
                    "message": "Course purchased successfully with TeoCoin",
                    "teo_used": float(teo_amount),
                    "new_balance": float(new_balance_data["available_balance"]),
                    "course_id": course_id,
                }
            )

        except Exception as e:
            logger.error(f"Error purchasing course with TeoCoin: {e}")
            return Response(
                {"success": False, "error": "Failed to purchase course"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WithdrawTokensView(APIView):
    """Create withdrawal request to MetaMask"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create withdrawal request and auto-process it immediately"""
        try:
            amount = request.data.get("amount")
            wallet_address = request.data.get("wallet_address")

            if not amount or not wallet_address:
                return Response(
                    {"success": False, "error": "Amount and wallet address required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Import services
            from decimal import Decimal

            from services.teocoin_withdrawal_service import teocoin_withdrawal_service

            try:
                amount_decimal = Decimal(str(amount))
            except (ValueError, TypeError):
                return Response(
                    {"success": False, "error": "Invalid amount format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get client IP for security
            ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
                0
            ] or request.META.get("REMOTE_ADDR")

            # Create withdrawal request using the enhanced service
            result = teocoin_withdrawal_service.create_withdrawal_request(
                user=request.user,
                amount=amount_decimal,
                wallet_address=wallet_address,
                ip_address=ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            if result["success"]:
                withdrawal_id = result["withdrawal_id"]

                # 🚀 AUTO-PROCESS: Immediately mint the tokens
                logger.info(
                    f"🎯 Auto-processing withdrawal #{withdrawal_id} for {request.user.email}"
                )

                mint_result = teocoin_withdrawal_service.mint_tokens_to_address(
                    amount=amount_decimal,
                    to_address=wallet_address,
                    withdrawal_id=withdrawal_id,
                )

                if mint_result["success"]:
                    # Update withdrawal to completed
                    from blockchain.models import (
                        DBTeoCoinBalance,
                        TeoCoinWithdrawalRequest,
                    )

                    withdrawal = TeoCoinWithdrawalRequest.objects.get(id=withdrawal_id)
                    withdrawal.status = "completed"
                    withdrawal.transaction_hash = mint_result.get(
                        "transaction_hash", "demo"
                    )
                    withdrawal.save()

                    # Update user balance
                    balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                        user=request.user,
                        defaults={
                            "available_balance": Decimal("0.00"),
                            "staked_balance": Decimal("0.00"),
                            "pending_withdrawal": Decimal("0.00"),
                        },
                    )
                    balance_obj.pending_withdrawal -= amount_decimal
                    balance_obj.save()

                    logger.info(
                        f"✅ Auto-processed withdrawal #{withdrawal_id} successfully"
                    )

                    return Response(
                        {
                            "success": True,
                            "message": f"✅ {amount_decimal} TEO minted successfully to your MetaMask wallet!",
                            "withdrawal_id": withdrawal_id,
                            "amount": str(amount_decimal),
                            "wallet_address": wallet_address,
                            "status": "completed",
                            "transaction_hash": mint_result.get("transaction_hash"),
                            "gas_used": mint_result.get("gas_used"),
                            "auto_processed": True,
                        }
                    )
                else:
                    logger.warning(
                        f"⚠️ Auto-processing failed for #{withdrawal_id}: {mint_result.get('error')}"
                    )

                    # Return pending status as fallback
                    return Response(
                        {
                            "success": True,
                            "message": "Withdrawal request created - processing in background",
                            "withdrawal_id": withdrawal_id,
                            "status": "pending",
                            "auto_processed": False,
                            "note": "Auto-processing failed, will be processed manually",
                        }
                    )
            else:
                return Response(
                    {"success": False, "error": result["error"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error creating withdrawal for user {request.user.id}: {e}")
            return Response(
                {"success": False, "error": "Failed to create withdrawal request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WithdrawalStatusView(APIView):
    """Get withdrawal request status"""

    permission_classes = [IsAuthenticated]

    def get(self, request, withdrawal_id):
        """Get status of specific withdrawal request"""
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id, user=request.user
            )

            return Response(
                {
                    "success": True,
                    "withdrawal": {
                        "id": withdrawal.pk,
                        "amount": str(withdrawal.amount),
                        "metamask_address": withdrawal.metamask_address,
                        "status": withdrawal.status,
                        "transaction_hash": withdrawal.transaction_hash,
                        "created_at": withdrawal.created_at.isoformat(),
                        "completed_at": (
                            withdrawal.completed_at.isoformat()
                            if withdrawal.completed_at
                            else None
                        ),
                        "error_message": withdrawal.error_message,
                    },
                }
            )

        except TeoCoinWithdrawalRequest.DoesNotExist:
            return Response(
                {"success": False, "error": "Withdrawal request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error getting withdrawal status: {e}")
            return Response(
                {"success": False, "error": "Failed to get withdrawal status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TransactionHistoryView(APIView):
    """Get user's transaction history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's TeoCoin transaction history"""
        try:
            limit = int(request.GET.get("limit", 50))
            db_service = DBTeoCoinService()
            transactions = db_service.get_user_transactions(
                user=request.user, limit=limit
            )

            return Response({"success": True, "transactions": transactions})

        except Exception as e:
            logger.error(f"Error getting transactions for user {request.user.id}: {e}")
            return Response(
                {"success": False, "error": "Failed to get transaction history"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PlatformStatisticsView(APIView):
    """Get platform-wide TeoCoin statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get platform TeoCoin statistics"""
        try:
            db_service = DBTeoCoinService()
            stats = db_service.get_platform_statistics()

            # Return basic stats for all authenticated users
            return Response({"success": True, "statistics": stats})

        except Exception as e:
            logger.error(f"Error getting platform statistics: {e}")
            return Response(
                {"success": False, "error": "Failed to get platform statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreditUserView(APIView):
    """Credit TEO to user (admin only)"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Credit TEO tokens to a user"""
        try:
            # Check if user is admin/staff
            if not request.user.is_staff:
                return Response(
                    {"success": False, "error": "Admin access required"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            user_id = request.data.get("user_id")
            amount = request.data.get("amount")
            reason = request.data.get("reason", "Admin credit")

            if not user_id or not amount:
                return Response(
                    {"success": False, "error": "User ID and amount required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from django.contrib.auth import get_user_model

            User = get_user_model()

            target_user = User.objects.get(id=user_id)

            db_service = DBTeoCoinService()
            result = db_service.add_balance(
                user=target_user,
                amount=amount,
                transaction_type="admin_credit",
                description=reason,
            )

            return Response(result)

        except Exception as e:
            logger.error(f"Error crediting user: {e}")
            return Response(
                {"success": False, "error": "Failed to credit user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
