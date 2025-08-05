"""
DB-based TeoCoin Service
Handles TeoCoin operations using database instead of blockchain.
This service maintains all business logic while using DB for speed and reliability.
"""

from decimal import Decimal
from typing import Dict, Optional, List, Tuple, Any, TYPE_CHECKING
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

from blockchain.models import (
    DBTeoCoinBalance, 
    DBTeoCoinTransaction, 
    TeoCoinWithdrawalRequest
)
from users.models import TeacherProfile

User = get_user_model()
logger = logging.getLogger(__name__)


class DBTeoCoinService:
    """
    Database-based TeoCoin service that replaces blockchain operations
    with fast, reliable database operations while preserving all business logic.
    """
    
    def __init__(self):
        """Initialize the service"""
        self.platform_commission_wallet = "platform_commission"
    
    # ========== BALANCE MANAGEMENT ==========
    
    def get_user_balance(self, user: User) -> Dict[str, Decimal]:
        """
        Get user's complete TeoCoin balance breakdown
        
        Returns:
            Dict with available_balance, staked_balance, pending_withdrawal
        """
        balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
            user=user,
            defaults={
                'available_balance': Decimal('0.00'),
                'staked_balance': Decimal('0.00'),
                'pending_withdrawal': Decimal('0.00')
            }
        )
        
        # For students, exclude staking completely (students don't stake)
        if hasattr(user, 'role') and getattr(user, 'role', None) == 'student':
            return {
                'available_balance': balance_obj.available_balance,
                'staked_balance': Decimal('0.00'),  # Students don't have staking
                'pending_withdrawal': balance_obj.pending_withdrawal,
                'total_balance': balance_obj.available_balance + balance_obj.pending_withdrawal
            }
        else:
            # For teachers and admins, include staking
            return {
                'available_balance': balance_obj.available_balance,
                'staked_balance': balance_obj.staked_balance,
                'pending_withdrawal': balance_obj.pending_withdrawal,
                'total_balance': (
                    balance_obj.available_balance + 
                    balance_obj.staked_balance + 
                    balance_obj.pending_withdrawal
                )
            }
    
    def get_available_balance(self, user: User) -> Decimal:
        """Get user's available TeoCoin balance for spending"""
        balance_data = self.get_user_balance(user)
        return balance_data['available_balance']
    
    def get_staked_balance(self, user: User) -> Decimal:
        """Get user's staked TeoCoin balance"""
        balance_data = self.get_user_balance(user)
        return balance_data['staked_balance']
    
    @transaction.atomic
    def add_balance(self, user: User, amount: Decimal, transaction_type: str, 
                   description: str = "", course_id: Optional[str] = None) -> bool:
        """
        Add TeoCoin to user's available balance
        
        Args:
            user: User to credit
            amount: Amount to add
            transaction_type: Type of transaction (earn_lesson, purchase, etc.)
            description: Transaction description
            course_id: Optional course ID for context
            
        Returns:
            bool: Success status
        """
        try:
            # Get or create balance record
            balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                user=user,
                defaults={
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00')
                }
            )
            
            # Update available balance
            balance_obj.available_balance += amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                course_id=course_id
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding balance: {e}")
            return False
    
    @transaction.atomic
    def deduct_balance(self, user: User, amount: Decimal, transaction_type: str,
                      description: str = "", course_id: Optional[str] = None) -> bool:
        """
        Deduct TeoCoin from user's available balance
        
        Args:
            user: User to debit
            amount: Amount to deduct
            transaction_type: Type of transaction (discount, stake, etc.)
            description: Transaction description
            course_id: Optional course ID for context
            
        Returns:
            bool: Success status
        """
        try:
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            
            # Check if sufficient balance
            if balance_obj.available_balance < amount:
                return False
            
            # Update available balance
            balance_obj.available_balance -= amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=-amount,  # Negative for deduction
                description=description,
                course_id=course_id
            )
            
            return True
            
        except DBTeoCoinBalance.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error deducting balance: {e}")
            return False
    
    # ========== STAKING OPERATIONS ==========
    
    @transaction.atomic
    def stake_tokens(self, user, amount: Decimal) -> bool:
        """
        Stake TeoCoin tokens (move from available to staked balance)
        Only available for teachers and admins, not students.
        
        Args:
            user: User staking tokens
            amount: Amount to stake
            
        Returns:
            bool: Success status
        """
        try:
            # Students cannot stake tokens
            if hasattr(user, 'role') and getattr(user, 'role', None) == 'student':
                logger.warning(f"Student {user.email} attempted to stake tokens - not allowed")
                return False
                
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            
            # Check if sufficient available balance
            if balance_obj.available_balance < amount:
                return False
            
            # Move from available to staked
            balance_obj.available_balance -= amount
            balance_obj.staked_balance += amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='stake',
                amount=amount,
                description=f"Staked {amount} TEO"
            )
            
            # Update teacher tier and commission rate
            try:
                teacher_profile = TeacherProfile.objects.get(user=user)
                teacher_profile.update_tier_and_commission()
            except TeacherProfile.DoesNotExist:
                pass  # User is not a teacher
            
            return True
            
        except DBTeoCoinBalance.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error staking tokens: {e}")
            return False
    
    @transaction.atomic
    def unstake_tokens(self, user, amount: Decimal) -> bool:
        """
        Unstake TeoCoin tokens (move from staked to available balance)
        Only available for teachers and admins, not students.
        
        Args:
            user: User unstaking tokens
            amount: Amount to unstake
            
        Returns:
            bool: Success status
        """
        try:
            # Students cannot unstake tokens (they shouldn't have any staked)
            if hasattr(user, 'role') and getattr(user, 'role', None) == 'student':
                logger.warning(f"Student {user.email} attempted to unstake tokens - not allowed")
                return False
                
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            
            # Check if sufficient staked balance
            if balance_obj.staked_balance < amount:
                return False
            
            # Move from staked to available
            balance_obj.staked_balance -= amount
            balance_obj.available_balance += amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='unstake',
                amount=amount,
                description=f"Unstaked {amount} TEO"
            )
            
            # Update teacher tier and commission rate
            try:
                teacher_profile = TeacherProfile.objects.get(user=user)
                teacher_profile.update_tier_and_commission()
            except TeacherProfile.DoesNotExist:
                pass  # User is not a teacher
            
            return True
            
        except DBTeoCoinBalance.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error unstaking tokens: {e}")
            return False
    
    # ========== DISCOUNT SYSTEM ==========
    
    def calculate_discount(self, user: User, course_price: Decimal) -> Dict[str, Decimal]:
        """
        Calculate TeoCoin discount for a course purchase
        
        Args:
            user: User purchasing course
            course_price: Original course price in EUR
            
        Returns:
            Dict with discount_amount, final_price, teo_required
        """
        available_balance = self.get_available_balance(user)
        
        # Maximum 50% discount
        max_discount = course_price * Decimal('0.5')
        
        # TEO exchange rate: 1 TEO = 1 EUR
        teo_available_for_discount = min(available_balance, max_discount)
        
        discount_amount = teo_available_for_discount
        final_price = course_price - discount_amount
        
        return {
            'discount_amount': discount_amount,
            'final_price': final_price,
            'teo_required': teo_available_for_discount,
            'discount_percentage': (discount_amount / course_price * 100) if course_price > 0 else Decimal('0')
        }
    
    @transaction.atomic
    def apply_course_discount(self, user: User, course_price: Decimal, 
                            course_id: str, course_title: str = "") -> Dict[str, Any]:
        """
        Apply TeoCoin discount to a course purchase
        
        Args:
            user: User purchasing course
            course_price: Original course price
            course_id: Course identifier
            course_title: Course title for description
            
        Returns:
            Dict with success status and transaction details
        """
        discount_info = self.calculate_discount(user, course_price)
        teo_required = discount_info['teo_required']
        
        if teo_required == 0:
            return {
                'success': True,
                'discount_applied': Decimal('0.00'),
                'final_price': course_price,
                'message': 'No TeoCoin available for discount'
            }
        
        # Deduct TeoCoin for discount
        success = self.deduct_balance(
            user=user,
            amount=teo_required,
            transaction_type='course_discount',
            description=f"Discount for course: {course_title}",
            course_id=course_id
        )
        
        if success:
            return {
                'success': True,
                'discount_applied': discount_info['discount_amount'],
                'final_price': discount_info['final_price'],
                'teo_used': teo_required,
                'message': f'Applied {discount_info["discount_percentage"]:.1f}% discount'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to apply discount'
            }
    
    # ========== TEACHER REWARDS ==========
    
    @transaction.atomic
    def reward_teacher_lesson_completion(self, teacher: User, student: User, 
                                       lesson_reward: Decimal = Decimal('1.0')) -> bool:
        """
        Reward teacher when student completes a lesson
        
        Args:
            teacher: Teacher to reward
            student: Student who completed lesson
            lesson_reward: Base reward amount
            
        Returns:
            bool: Success status
        """
        try:
            # Get teacher's commission rate (based on staking tier)
            commission_rate = Decimal('0.50')  # Default 50%
            
            try:
                teacher_profile = TeacherProfile.objects.get(user=teacher)
                commission_rate = teacher_profile.commission_rate / 100
            except TeacherProfile.DoesNotExist:
                pass  # Use default commission rate
            
            # Calculate platform commission
            platform_commission = lesson_reward * commission_rate
            teacher_reward = lesson_reward - platform_commission
            
            # Reward teacher
            teacher_success = self.add_balance(
                user=teacher,
                amount=teacher_reward,
                transaction_type='lesson_reward',
                description=f"Lesson completion reward (student: {student.username})"
            )
            
            # Platform keeps commission (recorded for transparency)
            platform_success = self._record_platform_commission(
                amount=platform_commission,
                description=f"Platform commission from teacher {teacher.username}"
            )
            
            return teacher_success and platform_success
            
        except Exception as e:
            print(f"Error rewarding teacher: {e}")
            return False
    
    def _record_platform_commission(self, amount: Decimal, description: str) -> bool:
        """Record platform commission (internal method)"""
        try:
            # Create a transaction record for platform commission
            # Note: We don't need a User for platform transactions
            DBTeoCoinTransaction.objects.create(
                user=None,  # Platform transactions have no user
                transaction_type='platform_commission',
                amount=amount,
                balance_after=Decimal('0.00'),  # Platform balance not tracked in user system
                description=description,
                status='completed'
            )
            return True
        except Exception as e:
            print(f"Error recording platform commission: {e}")
            return False
    
    # ========== WITHDRAWAL SYSTEM ==========
    
    @transaction.atomic
    def request_withdrawal(self, user: User, amount: Decimal, 
                          metamask_address: str) -> Dict[str, Any]:
        """
        Create withdrawal request to move TEO to MetaMask
        
        Args:
            user: User requesting withdrawal
            amount: Amount to withdraw
            metamask_address: User's MetaMask wallet address
            
        Returns:
            Dict with success status and request details
        """
        try:
            # Check available balance
            available_balance = self.get_available_balance(user)
            
            if available_balance < amount:
                return {
                    'success': False,
                    'message': 'Insufficient balance for withdrawal'
                }
            
            # Move from available to pending withdrawal
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            balance_obj.available_balance -= amount
            balance_obj.pending_withdrawal += amount
            balance_obj.save()
            
            # Create withdrawal request
            withdrawal_request = TeoCoinWithdrawalRequest.objects.create(
                user=user,
                amount=amount,
                metamask_address=metamask_address,
                status='pending'
            )
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='withdrawal_request',
                amount=-amount,
                balance_after=balance_obj.available_balance + balance_obj.staked_balance,
                description=f"Withdrawal request to {metamask_address}",
                status='pending'
            )
            
            return {
                'success': True,
                'request_id': withdrawal_request.id,
                'message': 'Withdrawal request created successfully'
            }
            
        except Exception as e:
            print(f"Error creating withdrawal request: {e}")
            return {
                'success': False,
                'message': f'Error creating withdrawal request: {e}'
            }
    
    def get_pending_withdrawals(self, user: Optional[User] = None) -> List[Dict]:
        """
        Get pending withdrawal requests
        
        Args:
            user: Specific user (None for all users - admin only)
            
        Returns:
            List of withdrawal request dictionaries
        """
        queryset = TeoCoinWithdrawalRequest.objects.filter(status='pending')
        
        if user:
            queryset = queryset.filter(user=user)
        
        return [
            {
                'id': req.id,
                'user': req.user.username if req.user else 'Unknown',
                'amount': req.amount,
                'metamask_address': req.metamask_address,
                'created_at': req.created_at,
                'status': req.status
            }
            for req in queryset.order_by('-created_at')
        ]
    
    # ========== TRANSACTION HISTORY ==========
    
    def get_user_transactions(self, user: User, limit: int = 50) -> List[Dict]:
        """
        Get user's transaction history
        
        Args:
            user: User to get transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        transactions = DBTeoCoinTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:limit]
        
        return [
            {
                'id': tx.id,
                'type': tx.transaction_type,
                'amount': tx.amount,
                'description': tx.description,
                'created_at': tx.created_at
            }
            for tx in transactions
        ]
    
    # ========== BURN DEPOSIT OPERATIONS ==========
    
    @transaction.atomic
    def credit_user(self, user: User, amount: Decimal, transaction_type: str = 'deposit',
                   description: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Credit user's account with TeoCoin from burn deposit
        
        Args:
            user: User to credit
            amount: Amount to credit
            transaction_type: Type of transaction (must match DBTeoCoinTransaction.TRANSACTION_TYPES)
            description: Transaction description
            metadata: Additional transaction metadata (stored in blockchain_tx_hash)
            
        Returns:
            Dict with success status and new balance
        """
        try:
            # Get or create balance record
            balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                user=user,
                defaults={
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00')
                }
            )
            
            # Update available balance
            balance_obj.available_balance += amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Extract transaction hash from metadata for storage
            tx_hash = None
            if metadata and 'transaction_hash' in metadata:
                tx_hash = metadata['transaction_hash']
            
            # Record transaction
            transaction_record = DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                blockchain_tx_hash=tx_hash
            )
            
            logger.info(f"✅ Credited {amount} TEO to {user.email} via {transaction_type}")
            
            return {
                'success': True,
                'new_balance': balance_obj.available_balance,
                'transaction_id': transaction_record.id
            }
            
        except Exception as e:
            logger.error(f"Error crediting user {user.email}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== ADMIN/PLATFORM OPERATIONS ==========
    
    def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get platform-wide TeoCoin statistics
        
        Returns:
            Dict with platform statistics
        """
        total_users = DBTeoCoinBalance.objects.count()
        total_circulating = DBTeoCoinBalance.objects.aggregate(
            total_available=Sum('available_balance'),
            total_staked=Sum('staked_balance'),
            total_pending=Sum('pending_withdrawal')
        )
        
        total_transactions = DBTeoCoinTransaction.objects.count()
        pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
            status='pending'
        ).count()
        
        return {
            'total_users_with_balance': total_users,
            'total_available_balance': total_circulating['total_available'] or Decimal('0.00'),
            'total_staked_balance': total_circulating['total_staked'] or Decimal('0.00'),
            'total_pending_withdrawal': total_circulating['total_pending'] or Decimal('0.00'),
            'total_transactions': total_transactions,
            'pending_withdrawal_requests': pending_withdrawals
        }


# Singleton instance
db_teocoin_service = DBTeoCoinService()
