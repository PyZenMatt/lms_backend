"""
Wallet Hold/Capture Service for TEO Discount Idempotency

Handles the hold → capture pattern for TEO token discounts to prevent
double spending during the payment flow.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from services.db_teocoin_service import db_teocoin_service
from blockchain.models import DBTeoCoinTransaction
from users.models import User
from courses.models import Course

logger = logging.getLogger(__name__)


class WalletHoldService:
    """
    Service for managing TEO token holds during discount application.
    
    Supports the pattern:
    1. create_hold() - Reserve tokens without deducting
    2. capture_hold() - Convert hold to actual deduction
    3. release_hold() - Cancel hold and return tokens to available balance
    """
    
    def create_hold(
        self,
        user: User,
        amount: Decimal,
        description: str,
        course: Optional[Course] = None,
        hold_reference: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a hold for the specified TEO amount.
        
        Args:
            user: User to hold tokens for  
            amount: Amount of TEO to hold
            description: Human-readable description
            course: Related course (optional)
            hold_reference: External reference for tracking (optional)
            
        Returns:
            Hold ID if successful, None if failed
        """
        try:
            # Check if user has sufficient balance
            user_balance = db_teocoin_service.get_balance(user)
            
            if user_balance < amount:
                logger.error(
                    f"Insufficient balance for hold: user={user.username}, "
                    f"balance={user_balance}, requested={amount}"
                )
                return None
            
            with transaction.atomic():
                # First, deduct the balance using the proper service method
                success = db_teocoin_service.deduct_balance(
                    user=user,
                    amount=amount,
                    transaction_type="hold",
                    description=f"HOLD: {description}",
                    course=course
                )
                
                if not success:
                    logger.error(f"Failed to deduct balance for hold: insufficient funds")
                    return None
                
                # Create hold tracking transaction (this won't affect balance since it's already deducted)
                hold_description = f"HOLD: {description} (amount: {amount})"
                if hold_reference:
                    hold_description = f"HOLD: {description} (ref: {hold_reference}, amount: {amount})"
                
                hold_tx = DBTeoCoinTransaction.objects.create(
                    user=user,
                    amount=0,  # Balance already deducted by deduct_balance()
                    transaction_type="hold",
                    description=hold_description,
                    course=course
                )
                
                hold_id = str(hold_tx.pk)
                
                logger.info(
                    f"TEO hold created: hold_id={hold_id}, user={user.username}, "
                    f"amount={amount}, description={description}, reference={hold_reference}"
                )
                
                return hold_id
                
        except Exception as e:
            logger.error(f"Failed to create hold: {e}")
            return None
    
    def capture_hold(
        self,
        hold_id: str,
        description: str = "Payment confirmed",
        course=None
    ) -> Optional[Decimal]:
        """
        Capture (finalize) a TEO hold, making the deduction permanent.
        
        Args:
            hold_id: ID of the hold transaction to capture
            description: Reason for capture
            course: Related course (optional)
            
        Returns:
            Amount captured if successful, None if failed
        """
        try:
            with transaction.atomic():
                # Find the hold transaction
                hold_tx = DBTeoCoinTransaction.objects.select_for_update().get(
                    id=hold_id,
                    transaction_type="hold"
                )
                
                # Check if already captured
                if "[CAPTURED" in hold_tx.description:
                    logger.warning(f"Hold {hold_id} already captured")
                    # Extract amount from description
                    return self._extract_amount_from_description(hold_tx.description)
                
                # Extract hold amount from description (since amount is now 0 in hold transactions)
                hold_amount = self._extract_amount_from_description(hold_tx.description)
                
                # Create capture transaction to mark completion
                capture_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=0,  # No additional balance change, just marking capture
                    transaction_type="hold_capture",
                    description=f"CAPTURE: {description} (hold: {hold_id}, amount: {hold_amount})",
                    course=course or hold_tx.course
                )
                
                # Update hold description to indicate it was captured
                hold_tx.description = f"{hold_tx.description} [CAPTURED by {capture_tx.pk}]"
                hold_tx.save(update_fields=["description"])
                
                logger.info(
                    f"TEO hold captured: hold_id={hold_id}, capture_id={capture_tx.pk}, "
                    f"amount={hold_amount}, user={hold_tx.user.pk}"
                )
                
                return hold_amount
                
        except DBTeoCoinTransaction.DoesNotExist:
            logger.error(f"Hold transaction not found: {hold_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to capture hold {hold_id}: {e}")
            return None
    
    def release_hold(
        self,
        hold_id: str,
        reason: str = "Payment cancelled"
    ) -> Optional[Decimal]:
        """
        Release (cancel) a TEO hold, returning tokens to available balance.
        
        Args:
            hold_id: ID of the hold transaction to release
            reason: Reason for release
            
        Returns:
            Amount released if successful, None if failed
        """
        try:
            with transaction.atomic():
                # Find the hold transaction
                hold_tx = DBTeoCoinTransaction.objects.select_for_update().get(
                    id=hold_id,
                    transaction_type="hold"
                )
                
                # Check if already captured (cannot release captured holds)
                if "[CAPTURED" in hold_tx.description:
                    logger.error(f"Cannot release captured hold {hold_id}")
                    return None
                
                # Check if already released
                if "[RELEASED" in hold_tx.description:
                    logger.warning(f"Hold {hold_id} already released")
                    return self._extract_amount_from_description(hold_tx.description)
                
                # Extract hold amount (we need to get it from the description since amount is now 0)
                hold_amount = self._extract_amount_from_description(hold_tx.description)
                
                # Restore the balance using the proper service method
                success = db_teocoin_service.add_balance(
                    user=hold_tx.user,
                    amount=hold_amount,
                    transaction_type="hold_release",
                    description=f"RELEASE: {reason}",
                    course=hold_tx.course
                )
                
                if not success:
                    logger.error(f"Failed to restore balance for hold release")
                    return None
                
                # Create release transaction for tracking (balance already restored)
                release_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=0,  # Balance already restored by add_balance()
                    transaction_type="hold_release",
                    description=f"RELEASE: {reason} (hold: {hold_id}, amount: {hold_amount})",
                    course=hold_tx.course
                )
                
                # Update hold description to indicate it was released
                hold_tx.description = f"{hold_tx.description} [RELEASED by {release_tx.pk}]"
                hold_tx.save(update_fields=["description"])
                
                logger.info(
                    f"TEO hold released: hold_id={hold_id}, release_id={release_tx.pk}, "
                    f"amount={hold_amount}, user={hold_tx.user.pk}"
                )
                
                return hold_amount
                
        except DBTeoCoinTransaction.DoesNotExist:
            logger.error(f"Hold transaction not found: {hold_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to release hold {hold_id}: {e}")
            return None
    
    def get_hold_info(self, hold_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a hold transaction.
        
        Args:
            hold_id: ID of the hold transaction
            
        Returns:
            Hold information dict if found, None otherwise
        """
        try:
            hold_tx = DBTeoCoinTransaction.objects.get(
                id=hold_id,
                transaction_type="hold"
            )
            
            # Determine status from description
            status = "active"
            if "[CAPTURED" in hold_tx.description:
                status = "captured"
            elif "[RELEASED" in hold_tx.description:
                status = "released"
            
            return {
                "hold_id": hold_id,
                "user_id": hold_tx.user.pk,
                "amount": self._extract_amount_from_description(hold_tx.description),
                "description": hold_tx.description,
                "status": status,
                "created_at": hold_tx.created_at,
                "course_id": hold_tx.course.pk if hold_tx.course else None,
            }
            
        except DBTeoCoinTransaction.DoesNotExist:
            logger.error(f"Hold transaction not found: {hold_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get hold info {hold_id}: {e}")
            return None
    
    def _extract_amount_from_description(self, description: str) -> Decimal:
        """Extract amount from description field."""
        try:
            # Look for "amount: X)" pattern
            import re
            match = re.search(r'amount:\s*([0-9.]+)\)', description)
            if match:
                return Decimal(match.group(1))
        except:
            pass
        return Decimal("0")


# Default service instance
wallet_hold_service = WalletHoldService()
