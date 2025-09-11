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
        course: Optional[Course] = None
    ) -> Optional[str]:
        """
        Create a hold for the specified TEO amount.
        
        Args:
            user: User to hold tokens for  
            amount: Amount of TEO to hold
            description: Human-readable description
            course: Related course (optional)
            
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
                # Create hold transaction (negative amount to reduce available balance)
                hold_tx = DBTeoCoinTransaction.objects.create(
                    user=user,
                    amount=-amount,  # Negative amount represents hold
                    transaction_type="hold",
                    description=f"HOLD: {description} (amount: {amount})",
                    course=course
                )
                
                hold_id = str(hold_tx.pk)
                
                logger.info(
                    f"TEO hold created: hold_id={hold_id}, user={user.username}, "
                    f"amount={amount}, description={description}"
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
                
                # Extract hold amount (hold has negative amount)
                hold_amount = abs(hold_tx.amount)
                
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
                    return abs(hold_tx.amount)
                
                # Extract hold amount (hold has negative amount)
                hold_amount = abs(hold_tx.amount)
                
                # Create release transaction to return tokens
                release_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=hold_amount,  # Positive amount to restore balance
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
                "amount": abs(hold_tx.amount),
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
        course: Course = None,
        hold_reference: str = None
    ) -> Optional[str]:
        """
        Create a hold on TEO tokens (reserve without deducting).
        
        Args:
            user: User to hold tokens for
            amount: Amount of TEO to hold
            description: Human-readable description
            course: Related course (optional)
            hold_reference: External reference (e.g., order_id)
            
        Returns:
            Hold transaction ID if successful, None if failed
        """
        try:
            with transaction.atomic():
                # Check available balance
                current_balance = db_teocoin_service.get_balance(user)
                if current_balance < amount:
                    logger.warning(
                        f"Insufficient balance for hold: user={user.pk}, "
                        f"requested={amount}, available={current_balance}"
                    )
                    return None
                
                # Create hold transaction (negative amount to reduce balance)
                hold_tx = DBTeoCoinTransaction.objects.create(
                    user=user,
                    amount=-amount,  # Negative to reduce available balance
                    transaction_type="hold",
                    description=f"HOLD: {description} (ref: {hold_reference}, amount: {amount})",
                    course=course
                )
                
                hold_id = str(hold_tx.pk)
                
                logger.info(
                    f"TEO hold created: hold_id={hold_id}, user={user.pk}, "
                    f"amount={amount}, reference={hold_reference}"
                )
                
                return hold_id
                
        except Exception as e:
            logger.error(f"Failed to create TEO hold: {e}")
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
            reason: Reason for capture
            
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
                
                # Extract hold amount (hold has negative amount)
                hold_amount = abs(hold_tx.amount)
                
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
        reason: str = "Payment failed"
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
                
                # Check if already released or captured
                if "[RELEASED" in hold_tx.description:
                    logger.warning(f"Hold {hold_id} already released")
                    return self._extract_amount_from_description(hold_tx.description)
                
                if "[CAPTURED" in hold_tx.description:
                    logger.error(f"Cannot release captured hold {hold_id}")
                    return None
                
                # Extract hold amount (hold has negative amount)
                hold_amount = abs(hold_tx.amount)
                
                # Create release transaction (positive amount to return tokens)
                release_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=hold_amount,  # Positive to restore balance
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
                "amount": abs(hold_tx.amount),
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
    1. hold() - Reserve tokens without deducting
    2. capture() - Convert hold to actual deduction
    3. release() - Cancel hold and return tokens to available balance
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
            hold_reference: External reference (e.g., order_id)
            
        Returns:
            Hold transaction ID if successful, None if failed
        """
        try:
            with transaction.atomic():
                # Check available balance
                current_balance = db_teocoin_service.get_balance(user)
                if current_balance < amount:
                    logger.warning(
                        f"Insufficient balance for hold: user={user.id}, "
                        f"requested={amount}, available={current_balance}"
                    )
                    return None
                
                # Create hold transaction (negative amount but special type)
                hold_tx = DBTeoCoinTransaction.objects.create(
                    user=user,
                    amount=-amount,  # Negative to reduce available balance
                    transaction_type="hold",
                    description=f"HOLD: {description} (ref: {hold_reference})",
                    course=course
                )
                
                hold_id = str(hold_tx.id)
                
                logger.info(
                    f"TEO hold created: hold_id={hold_id}, user={user.id}, "
                    f"amount={amount}, reference={hold_reference}"
                )
                
                return hold_id
                
        except Exception as e:
            logger.error(f"Failed to create TEO hold: {e}")
            return None
    
    def capture_hold(
        self,
        hold_id: str,
        description: str,
        course: Optional[Course] = None
    ) -> bool:
        """
        Capture (finalize) a previously created hold.
        
        Args:
            hold_id: ID of the hold transaction to capture
            description: Description for the capture transaction
            course: Related course (optional)
            
        Returns:
            True if capture successful, False otherwise
        """
        try:
            with transaction.atomic():
                # Find the original hold transaction
                hold_tx = DBTeoCoinTransaction.objects.select_for_update().get(
                    id=hold_id,
                    transaction_type="hold",
                    status="completed"
                )
                
                # Verify hold is not already captured/released
                existing_capture = DBTeoCoinTransaction.objects.filter(
                    metadata__contains={"hold_id": hold_id},
                    transaction_type__in=["capture", "release"]
                ).first()
                
                if existing_capture:
                    logger.warning(
                        f"Hold {hold_id} already processed: {existing_capture.transaction_type}"
                    )
                    return existing_capture.transaction_type == "capture"
                
                # Get hold amount (stored as positive in metadata)
                hold_amount = Decimal(hold_tx.metadata.get("hold_amount", "0"))
                
                # Create capture transaction (converts hold to actual deduction)
                capture_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=Decimal("0"),  # Net zero since tokens already held
                    transaction_type="capture",
                    description=f"CAPTURE: {description}",
                    course=course or hold_tx.course,
                    status="completed",
                    metadata={
                        "hold_id": hold_id,
                        "captured_amount": str(hold_amount),
                        "captured_at": timezone.now().isoformat(),
                        "original_hold_ref": hold_tx.metadata.get("hold_reference"),
                    }
                )
                
                # Mark original hold as captured
                hold_tx.metadata["captured_by"] = str(capture_tx.id)
                hold_tx.metadata["captured_at"] = timezone.now().isoformat()
                hold_tx.save(update_fields=["metadata"])
                
                logger.info(
                    f"TEO hold captured: hold_id={hold_id}, capture_id={capture_tx.id}, "
                    f"amount={hold_amount}, user={hold_tx.user.id}"
                )
                
                return True
                
        except DBTeoCoinTransaction.DoesNotExist:
            logger.error(f"Hold transaction not found: {hold_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to capture hold {hold_id}: {e}")
            return False
    
    def release_hold(
        self,
        hold_id: str,
        reason: str = "Payment failed"
    ) -> bool:
        """
        Release (cancel) a previously created hold, returning tokens to available balance.
        
        Args:
            hold_id: ID of the hold transaction to release
            reason: Reason for releasing the hold
            
        Returns:
            True if release successful, False otherwise
        """
        try:
            with transaction.atomic():
                # Find the original hold transaction
                hold_tx = DBTeoCoinTransaction.objects.select_for_update().get(
                    id=hold_id,
                    transaction_type="hold",
                    status="completed"
                )
                
                # Verify hold is not already captured/released
                existing_action = DBTeoCoinTransaction.objects.filter(
                    metadata__contains={"hold_id": hold_id},
                    transaction_type__in=["capture", "release"]
                ).first()
                
                if existing_action:
                    logger.warning(
                        f"Hold {hold_id} already processed: {existing_action.transaction_type}"
                    )
                    return existing_action.transaction_type == "release"
                
                # Get hold amount (stored as positive in metadata)
                hold_amount = Decimal(hold_tx.metadata.get("hold_amount", "0"))
                
                # Create release transaction (returns tokens to available balance)
                release_tx = DBTeoCoinTransaction.objects.create(
                    user=hold_tx.user,
                    amount=hold_amount,  # Positive amount to restore balance
                    transaction_type="release",
                    description=f"RELEASE: {reason}",
                    course=hold_tx.course,
                    status="completed",
                    metadata={
                        "hold_id": hold_id,
                        "released_amount": str(hold_amount),
                        "released_at": timezone.now().isoformat(),
                        "release_reason": reason,
                        "original_hold_ref": hold_tx.metadata.get("hold_reference"),
                    }
                )
                
                # Mark original hold as released
                hold_tx.metadata["released_by"] = str(release_tx.id)
                hold_tx.metadata["released_at"] = timezone.now().isoformat()
                hold_tx.metadata["release_reason"] = reason
                hold_tx.save(update_fields=["metadata"])
                
                logger.info(
                    f"TEO hold released: hold_id={hold_id}, release_id={release_tx.id}, "
                    f"amount={hold_amount}, user={hold_tx.user.id}, reason={reason}"
                )
                
                return True
                
        except DBTeoCoinTransaction.DoesNotExist:
            logger.error(f"Hold transaction not found: {hold_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to release hold {hold_id}: {e}")
            return False
    
    def get_hold_status(self, hold_id: str) -> Dict[str, Any]:
        """
        Get the current status of a hold transaction.
        
        Args:
            hold_id: ID of the hold transaction
            
        Returns:
            Dict with hold status information
        """
        try:
            hold_tx = DBTeoCoinTransaction.objects.get(
                id=hold_id,
                transaction_type="hold"
            )
            
            # Check for capture/release
            action_tx = DBTeoCoinTransaction.objects.filter(
                metadata__contains={"hold_id": hold_id},
                transaction_type__in=["capture", "release"]
            ).first()
            
            status = "active"
            action_id = None
            action_type = None
            
            if action_tx:
                status = action_tx.transaction_type + "d"  # "captured" or "released"
                action_id = str(action_tx.id)
                action_type = action_tx.transaction_type
            
            return {
                "hold_id": hold_id,
                "status": status,
                "amount": hold_tx.metadata.get("hold_amount"),
                "created_at": hold_tx.created_at.isoformat() if hold_tx.created_at else None,
                "action_id": action_id,
                "action_type": action_type,
                "action_at": action_tx.created_at.isoformat() if action_tx and action_tx.created_at else None,
                "reference": hold_tx.metadata.get("hold_reference"),
            }
            
        except DBTeoCoinTransaction.DoesNotExist:
            return {"hold_id": hold_id, "status": "not_found"}
        except Exception as e:
            logger.error(f"Failed to get hold status {hold_id}: {e}")
            return {"hold_id": hold_id, "status": "error", "error": str(e)}


# Global instance
# Default service instance
wallet_hold_service = SimpleWalletHoldService()
