"""
Payment Service for TeoArt School Platform

Handles all payment-related operations including course purchases,
commission calculations, blockchain transactions, and payment verification.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from users.models import User
import uuid
import logging

from .base import TransactionalService
from .exceptions import (
    TeoArtServiceException, 
    UserNotFoundError, 
    CourseNotFoundError,
    InsufficientTeoCoinsError,
    BlockchainTransactionError
)

# Models
from courses.models import Course
from rewards.models import BlockchainTransaction

# User is now imported directly above

logger = logging.getLogger(__name__)


class PaymentServiceException(TeoArtServiceException):
    """Payment-specific exceptions"""
    pass


class PaymentService(TransactionalService):
    def create_hybrid_payment_intent(
        self,
        user_id: int,
        course_id: int,
        teocoin_to_spend: Decimal,
        wallet_address: str
    ) -> Dict[str, Any]:
        """
        Create a hybrid payment intent: deduct TeoCoin for discount, pay remainder with fiat (Stripe).
        Args:
            user_id: User ID
            course_id: Course ID
            teocoin_to_spend: Amount of TeoCoin to spend for discount
            wallet_address: User's wallet address
        Returns:
            dict: Success status, client_secret, payment_intent_id, discounted_amount, discount_applied, etc.
        """
        def _hybrid_intent():
            # Validate user and course
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)

            # Validate wallet
            if not wallet_address:
                raise PaymentServiceException("Wallet address required for hybrid payment", "WALLET_REQUIRED", 400)

            # Validate not already enrolled
            from courses.models import CourseEnrollment
            if CourseEnrollment.objects.filter(student=user, course=course).exists():
                raise PaymentServiceException("Already enrolled in this course", "ALREADY_ENROLLED", 400)

            # Validate teocoin_to_spend
            if teocoin_to_spend <= 0:
                raise PaymentServiceException("TeoCoin amount must be positive", "INVALID_TEOCOIN_AMOUNT", 400)

            # Check user balance
            balance = self._get_user_balance(wallet_address)
            if balance < teocoin_to_spend:
                raise InsufficientTeoCoinsError(required=float(teocoin_to_spend), available=float(balance))

            # Calculate discount: assume 1 TEO = 1 EUR discount, but cap at max allowed by course discount percent
            max_discount_eur = (course.price_eur * Decimal(course.teocoin_discount_percent or 0) / 100).quantize(Decimal('0.01'))
            teocoin_to_use = min(teocoin_to_spend, max_discount_eur)
            if teocoin_to_use <= 0:
                raise PaymentServiceException("No discount available for this course", "NO_DISCOUNT", 400)

            # Calculate new price
            discounted_price = (course.price_eur - teocoin_to_use).quantize(Decimal('0.01'))
            if discounted_price < 0:
                discounted_price = Decimal('0.00')

            # Deduct TeoCoin: create a pending BlockchainTransaction (actual transfer after Stripe success)
            pending_tx = BlockchainTransaction.objects.create(
                user=user,
                amount=-teocoin_to_use,
                transaction_type='hybrid_discount_pending',
                status='pending',
                from_address=wallet_address,
                to_address=getattr(settings, 'REWARD_POOL_ADDRESS', 'reward_pool'),
                related_object_id=str(course.pk),
                notes=f"Hybrid payment discount for course: {course.title}"
            )

            # Create Stripe payment intent for discounted price
            try:
                import stripe
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
                intent = stripe.PaymentIntent.create(
                    amount=int(discounted_price * 100),
                    currency='eur',
                    payment_method_types=['card'],
                    metadata={
                        'course_id': course.id,
                        'user_id': user.pk,
                        'payment_type': 'hybrid',
                        'teocoin_discount': str(teocoin_to_use),
                        'course_title': course.title,
                        'student_email': user.email
                    },
                    description=f"Hybrid payment for course: {course.title}"
                )
            except ImportError:
                raise PaymentServiceException("Stripe not installed. Please install stripe package.", "STRIPE_NOT_INSTALLED", 500)
            except stripe.error.StripeError as e:
                raise PaymentServiceException(f"Payment processing error: {str(e)}", "STRIPE_ERROR", 400)

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'discounted_amount': float(discounted_price),
                'discount_applied': float(teocoin_to_use),
                'original_price': float(course.price_eur),
                'teocoin_pending_tx_id': pending_tx.id,
                'course_title': course.title,
                'teocoin_reward': course.teocoin_reward
            }

        try:
            return self.execute_in_transaction(_hybrid_intent)
        except Exception as e:
            self.log_error(f"Failed to create hybrid payment intent: {str(e)}")
            raise

    def process_successful_hybrid_payment(
        self,
        payment_intent_id: str,
        course_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Complete hybrid payment: confirm Stripe, finalize TeoCoin deduction, enroll user.
        """
        def _process_hybrid():
            try:
                import stripe
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            except ImportError:
                raise PaymentServiceException("Stripe not installed", "STRIPE_NOT_INSTALLED", 500)

            # Validate user and course
            try:
                user = User.objects.get(pk=user_id)
                course = Course.objects.get(id=course_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)

            # Verify payment with Stripe
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            except stripe.error.StripeError as e:
                raise PaymentServiceException(f"Payment verification error: {str(e)}", "STRIPE_VERIFICATION_ERROR", 400)

            if intent.status != 'succeeded':
                raise PaymentServiceException(f"Payment not successful. Status: {intent.status}", "PAYMENT_NOT_SUCCESSFUL", 400)

            # Find pending hybrid discount transaction
            pending_tx = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type='hybrid_discount_pending',
                related_object_id=str(course.id),
                status='pending'
            ).order_by('-created_at').first()
            if not pending_tx:
                raise PaymentServiceException("No pending TeoCoin discount found for this payment", "NO_PENDING_DISCOUNT", 400)

            # Mark TeoCoin deduction as completed
            pending_tx.status = 'completed'
            pending_tx.transaction_type = 'hybrid_discount'
            pending_tx.save()

            # Enroll user
            from courses.models import CourseEnrollment
            if CourseEnrollment.objects.filter(student=user, course=course).exists():
                raise PaymentServiceException("Already enrolled in this course", "ALREADY_ENROLLED", 400)

            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                payment_method='hybrid',
                amount_paid_eur=Decimal(intent.amount) / 100,
                amount_paid_teocoin=abs(pending_tx.amount),
                stripe_payment_intent_id=payment_intent_id,
                teocoin_reward_given=course.teocoin_reward,
                enrolled_at=__import__('django.utils.timezone').utils.timezone.now()
            )

            # Award TeoCoin reward if configured (reuse logic from fiat)
            teocoin_reward_given = Decimal('0')
            reward_status = 'none'
            if course.teocoin_reward > 0:
                try:
                    from blockchain.views import teocoin_service
                    if user.wallet_address:
                        try:
                            mint_result = teocoin_service.mint_tokens(
                                user.wallet_address,
                                float(course.teocoin_reward)
                            )
                            if mint_result:
                                teocoin_reward_given = course.teocoin_reward
                                reward_status = 'distributed'
                                BlockchainTransaction.objects.create(
                                    user=user,
                                    transaction_type='reward',
                                    amount=course.teocoin_reward,
                                    status='completed',
                                    transaction_hash=mint_result,
                                    related_object_id=str(course.id),
                                    notes=f"Hybrid payment reward for course: {course.title}"
                                )
                        except Exception as mint_error:
                            teocoin_reward_given = course.teocoin_reward
                            reward_status = 'pending'
                            BlockchainTransaction.objects.create(
                                user=user,
                                transaction_type='reward',
                                amount=course.teocoin_reward,
                                status='pending',
                                related_object_id=str(course.id),
                                notes=f"Pending hybrid payment reward for course: {course.title} (Mint error: {str(mint_error)})"
                            )
                    else:
                        teocoin_reward_given = course.teocoin_reward
                        reward_status = 'pending_wallet'
                        BlockchainTransaction.objects.create(
                            user=user,
                            transaction_type='reward',
                            amount=course.teocoin_reward,
                            status='pending',
                            related_object_id=str(course.id),
                            notes=f"Pending hybrid payment reward for course: {course.title} (No wallet connected)"
                        )
                except Exception as blockchain_error:
                    teocoin_reward_given = course.teocoin_reward
                    reward_status = 'failed'
                    BlockchainTransaction.objects.create(
                        user=user,
                        transaction_type='reward',
                        amount=course.teocoin_reward,
                        status='failed',
                        related_object_id=str(course.id),
                        notes=f"Failed hybrid payment reward for course: {course.title} (Error: {str(blockchain_error)})"
                    )

            # Send notifications (reuse logic)
            try:
                from notifications.models import Notification
                if reward_status == 'distributed':
                    message = f"🎉 Successfully enrolled in '{course.title}' via hybrid payment! Received {teocoin_reward_given} TEO reward in your wallet."
                elif reward_status == 'pending_wallet':
                    message = f"✅ Successfully enrolled in '{course.title}' via hybrid payment! {teocoin_reward_given} TEO reward pending - connect your wallet to claim."
                elif reward_status == 'pending':
                    message = f"✅ Successfully enrolled in '{course.title}' via hybrid payment! {teocoin_reward_given} TEO reward will be processed shortly."
                elif reward_status == 'failed':
                    message = f"✅ Successfully enrolled in '{course.title}' via hybrid payment! {teocoin_reward_given} TEO reward pending (technical issue)."
                else:
                    message = f"✅ Successfully enrolled in '{course.title}' via hybrid payment!"
                Notification.objects.create(
                    user=user,
                    message=message,
                    notification_type='course_purchased'
                )
                if course.teacher != user:
                    Notification.objects.create(
                        user=course.teacher,
                        message=f"New student {user.get_full_name() or user.username} enrolled in your course '{course.title}' (€{enrollment.amount_paid_eur} + {enrollment.amount_paid_teocoin} TEO)",
                        notification_type='course_enrollment'
                    )
            except Exception as notification_error:
                self.log_error(f"Notification failed: {notification_error}")

            return {
                'success': True,
                'enrollment': {
                    'id': enrollment.id,
                    'course_title': course.title,
                    'payment_method': enrollment.payment_method,
                    'amount_paid_eur': enrollment.amount_paid_eur,
                    'amount_paid_teocoin': enrollment.amount_paid_teocoin,
                    'enrolled_at': enrollment.enrolled_at
                },
                'teocoin_reward': {
                    'amount': teocoin_reward_given,
                    'status': reward_status
                },
                'amount_paid': enrollment.amount_paid_eur,
                'message': message
            }

        try:
            return self.execute_in_transaction(_process_hybrid)
        except Exception as e:
            self.log_error(f"Failed to process hybrid payment: {str(e)}")
            raise
    """
    Service for handling payment operations.
    
    Handles course purchases, commission calculations with dynamic staking tiers,
    blockchain verification, and transaction recording.
    """
    
    # CORRECTED: Fallback commission rate for non-teachers (matches Bronze tier business logic)
    DEFAULT_COMMISSION_RATE = Decimal('0.50')  # 50% fallback (matches Bronze tier)
    
    def __init__(self):
        super().__init__()
        self.service_name = "PaymentService"
    
    def get_teacher_commission_rate(self, teacher_user) -> Decimal:
        """
        Get dynamic commission rate for a teacher based on staking tier
        
        Args:
            teacher_user: User object for the teacher
            
        Returns:
            Decimal: Commission rate (0.50 for 50%, 0.25 for 25%, etc.)
        """
        try:
            # Check if user is teacher and has profile
            if teacher_user.role != 'teacher':
                return self.DEFAULT_COMMISSION_RATE
            
            if not hasattr(teacher_user, 'teacher_profile') or not teacher_user.teacher_profile:
                self.log_warning(f"Teacher {teacher_user.email} missing TeacherProfile - using default rate")
                return self.DEFAULT_COMMISSION_RATE
            
            # Get commission rate from teacher profile
            profile = teacher_user.teacher_profile
            commission_decimal = profile.commission_rate_decimal
            
            self.log_info(f"Teacher {teacher_user.email} commission: {profile.commission_rate}% ({profile.staking_tier} tier)")
            return commission_decimal
            
        except Exception as e:
            self.log_error(f"Error getting commission rate for {teacher_user.email}: {e}")
            return self.DEFAULT_COMMISSION_RATE
    
    def update_teacher_commission_from_staking(self, teacher_user) -> bool:
        """
        Update teacher's commission rate based on current staking info
        
        Args:
            teacher_user: User object for the teacher
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if teacher_user.role != 'teacher':
                return False
            
            if not hasattr(teacher_user, 'teacher_profile') or not teacher_user.teacher_profile:
                self.log_error(f"Cannot update commission for {teacher_user.email} - no TeacherProfile")
                return False
            
            # Get staking service and current staking info
            from services.teocoin_staking_service import teocoin_staking_service
            
            if not teacher_user.wallet_address:
                self.log_warning(f"Teacher {teacher_user.email} has no wallet address for staking lookup")
                return False
            
            # Get staking info from blockchain
            staking_info = teocoin_staking_service.get_user_staking_info(teacher_user.wallet_address)
            
            if staking_info and staking_info.get('success'):
                # Update teacher profile with new staking data
                profile = teacher_user.teacher_profile
                old_rate = profile.commission_rate
                
                profile.update_from_staking_info(staking_info)
                
                self.log_info(f"Updated {teacher_user.email} commission: {old_rate}% → {profile.commission_rate}% ({profile.staking_tier})")
                return True
            else:
                self.log_warning(f"Could not get staking info for {teacher_user.email}")
                return False
                
        except Exception as e:
            self.log_error(f"Error updating commission from staking for {teacher_user.email}: {e}")
            return False
    
    def initiate_course_purchase(
        self,
        user_id: int,
        course_id: int,
        wallet_address: str
    ) -> Dict[str, Any]:
        """
        Initiate a course purchase workflow.
        
        Returns payment requirements and details.
        """
        def _initiate_operation():
            # Validate user
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Validate user role
            if user.role != 'student':
                raise PaymentServiceException(
                    "Only students can purchase courses",
                    "INVALID_USER_ROLE",
                    403
                )
            
            # Check if course is approved
            if not course.is_approved:
                raise PaymentServiceException(
                    "Course is not available for purchase",
                    "COURSE_NOT_APPROVED",
                    403
                )
            
            # Check if user already enrolled
            if user in course.students.all():
                raise PaymentServiceException(
                    "User already enrolled in this course",
                    "ALREADY_ENROLLED",
                    400
                )
            
            # Check teacher has wallet
            if not course.teacher.wallet_address:
                raise PaymentServiceException(
                    "Teacher wallet not configured",
                    "TEACHER_WALLET_MISSING",
                    400
                )
            
            # Update user wallet if needed
            if not user.wallet_address or user.wallet_address.lower() != wallet_address.lower():
                user.wallet_address = wallet_address
                user.save()
            
            # Check balance
            balance = self._get_user_balance(wallet_address)
            if balance < course.price_eur:
                raise InsufficientTeoCoinsError(
                    required=float(course.price_eur),
                    available=float(balance)
                )
            # Calculate payment breakdown with dynamic commission rate
            commission_rate = self.get_teacher_commission_rate(course.teacher)
            commission_amount = course.price_eur * commission_rate
            teacher_amount = course.price_eur - commission_amount
            
            return {
                'payment_required': True,
                'course_id': course.pk,
                'course_title': course.title,
                'course_price': float(course.price_eur),
                'teacher_amount': float(teacher_amount),
                'commission_amount': float(commission_amount),
                'commission_rate': f"{float(commission_rate * 100)}%",
                'teacher_address': course.teacher.wallet_address,
                'student_address': wallet_address,
                'student_balance': float(balance),
                'payment_breakdown': {
                    'total_price': float(course.price_eur),
                    'teacher_receives': float(teacher_amount),
                    'platform_commission': float(commission_amount),
                    'commission_percentage': float(commission_rate * 100)
                }
            }
        
        try:
            return self.execute_in_transaction(_initiate_operation)
        except Exception as e:
            self.log_error(f"Failed to initiate course purchase: {str(e)}")
            raise
    
    def complete_course_purchase(
        self,
        user_id: int,
        course_id: int,
        transaction_hash: str,
        wallet_address: str
    ) -> Dict[str, Any]:
        """
        Complete a course purchase after blockchain payment.
        
        Verifies payment and enrolls user in course.
        """
        def _complete_operation():
            # Validate user
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Check if transaction already processed
            if BlockchainTransaction.objects.filter(transaction_hash=transaction_hash).exists():
                raise PaymentServiceException(
                    "Transaction already processed",
                    "TRANSACTION_ALREADY_PROCESSED",
                    400
                )
            
            # Verify blockchain transaction
            if not self._verify_payment_transaction(
                transaction_hash, 
                wallet_address, 
                course.teacher.wallet_address,
                course.price_eur
            ):
                raise PaymentServiceException(
                    "Blockchain transaction verification failed",
                    "TRANSACTION_VERIFICATION_FAILED",
                    400
                )
            
            # Calculate amounts with dynamic commission rate
            commission_rate = self.get_teacher_commission_rate(course.teacher)
            commission_amount = course.price_eur * commission_rate
            teacher_amount = course.price_eur - commission_amount
            
            # Enroll student in course
            course.students.add(user)
            
            # Record purchase transaction
            purchase_tx = BlockchainTransaction.objects.create(
                user=user,
                amount=-course.price_eur,
                transaction_type='course_purchase',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=course.teacher.wallet_address,
                related_object_id=str(course.pk),
                notes=f"Course purchase: {course.title}"
            )
            
            # Record teacher earnings
            teacher_tx = BlockchainTransaction.objects.create(
                user=course.teacher,
                amount=teacher_amount,
                transaction_type='course_earned',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=course.teacher.wallet_address,
                related_object_id=str(course.pk),
                notes=f"Earnings from course sale: {course.title}"
            )
            
            # Record commission transaction
            commission_tx = BlockchainTransaction.objects.create(
                user=user,
                amount=-commission_amount,
                transaction_type='platform_commission',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=getattr(settings, 'REWARD_POOL_ADDRESS', 'reward_pool'),
                related_object_id=str(course.pk),
                notes=f"Platform commission from course purchase: {course.title}"
            )
            
            # Send notifications
            self._send_purchase_notifications(course, user, course.teacher)
            
            self.log_info(f"Course purchase completed: user {user_id} -> course {course_id}")
            
            return {
                'success': True,
                'message': 'Course purchased successfully',
                'course_id': course.pk,
                'course_title': course.title,
                'student_id': user.pk,
                'student_username': user.username,
                'total_paid': float(course.price_eur),
                'teacher_received': float(teacher_amount),
                'platform_commission': float(commission_amount),
                'transaction_hash': transaction_hash,
                'enrollment_confirmed': True,
                'transactions_recorded': {
                    'purchase_id': purchase_tx.id,
                    'teacher_earning_id': teacher_tx.id,
                    'commission_id': commission_tx.id
                }
            }
        
        try:
            return self.execute_in_transaction(_complete_operation)
        except Exception as e:
            self.log_error(f"Failed to complete course purchase: {str(e)}")
            raise
    
    def get_user_purchase_history(
        self,
        user_id: int,
        transaction_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's purchase history.
        """
        try:
            # Validate user
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Build query
            queryset = BlockchainTransaction.objects.filter(user=user)
            
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            
            # Order by newest first
            queryset = queryset.order_by('-created_at')
            
            if limit:
                queryset = queryset[:limit]
            
            transactions = []
            for tx in queryset:
                # Get related course if available
                related_course = None
                if tx.related_object_id and tx.transaction_type in ['course_purchase', 'course_earned']:
                    try:
                        course = Course.objects.get(id=int(tx.related_object_id))
                        related_course = {
                            'id': course.pk,
                            'title': course.title,
                            'teacher': course.teacher.username
                        }
                    except (Course.DoesNotExist, ValueError):
                        pass
                
                transactions.append({
                    'id': tx.pk,
                    'amount': float(tx.amount),
                    'transaction_type': tx.transaction_type,
                    'status': tx.status,
                    'transaction_hash': tx.transaction_hash,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'notes': tx.notes,
                    'created_at': tx.created_at.isoformat(),
                    'related_course': related_course
                })
            
            self.log_info(f"Retrieved {len(transactions)} transactions for user {user_id}")
            return transactions
            
        except Exception as e:
            self.log_error(f"Failed to get user purchase history: {str(e)}")
            raise
    
    def get_course_sales_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get sales statistics for a course.
        """
        try:
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Get purchase transactions
            purchase_transactions = BlockchainTransaction.objects.filter(
                transaction_type='course_purchase',
                related_object_id=str(course_id)
            )
            
            # Get earning transactions (for teacher)
            earning_transactions = BlockchainTransaction.objects.filter(
                transaction_type='course_earned',
                related_object_id=str(course_id)
            )
            
            # Calculate stats
            total_sales = purchase_transactions.count()
            total_revenue = sum(abs(tx.amount) for tx in purchase_transactions)
            total_teacher_earnings = sum(tx.amount for tx in earning_transactions)
            total_commission = total_revenue - total_teacher_earnings
            
            return {
                'course_id': course.pk,
                'course_title': course.title,
                'teacher_id': course.teacher.pk,
                'teacher_username': course.teacher.username,
                'total_sales': total_sales,
                'total_revenue': float(total_revenue),
                'teacher_earnings': float(total_teacher_earnings),
                'platform_commission': float(total_commission),
                'average_sale_value': float(total_revenue / total_sales) if total_sales > 0 else 0,
                'commission_rate': f"{float(self.DEFAULT_COMMISSION_RATE * 100)}%"
            }
            
        except Exception as e:
            self.log_error(f"Failed to get course sales stats: {str(e)}")
            raise
    
    def _get_user_balance(self, wallet_address: str) -> Decimal:
        """Get user's TeoCoins balance"""
        try:
            from blockchain.views import teocoin_service
            balance = teocoin_service.get_balance(wallet_address)
            return Decimal(str(balance))
        except Exception as e:
            self.log_error(f"Failed to get balance for {wallet_address}: {str(e)}")
            return Decimal('0')
    
    def _verify_payment_transaction(
        self, 
        tx_hash: str, 
        from_address: str, 
        to_address: str, 
        expected_amount: Decimal
    ) -> bool:
        """Verify blockchain payment transaction"""
        try:
            # Check our database first
            related_transactions = BlockchainTransaction.objects.filter(
                transaction_hash=tx_hash
            )
            
            if related_transactions.exists():
                for tx in related_transactions:
                    if (tx.from_address and tx.to_address and
                        tx.from_address.lower() == from_address.lower() and
                        tx.to_address.lower() == to_address.lower() and
                        abs(tx.amount) >= expected_amount * Decimal('0.85')):
                        return True
            
            # Fallback to blockchain verification
            return self._verify_blockchain_transaction(tx_hash, from_address, to_address, expected_amount)
            
        except Exception as e:
            self.log_error(f"Transaction verification failed: {str(e)}")
            return False
    
    def _verify_blockchain_transaction(
        self, 
        tx_hash: str, 
        from_address: str, 
        to_address: str, 
        expected_amount: Decimal
    ) -> bool:
        """Verify transaction on the blockchain"""
        try:
            # Check for simulated transactions (testing)
            if tx_hash.startswith("0x") and len(tx_hash) == 66:
                simulated_tx = BlockchainTransaction.objects.filter(
                    transaction_hash=tx_hash,
                    transaction_type='simulated_payment',
                    status='completed'
                ).first()
                
                if simulated_tx:
                    return (simulated_tx.from_address.lower() == from_address.lower() and
                            simulated_tx.to_address.lower() == to_address.lower() and
                            simulated_tx.amount >= expected_amount)
            
            # Real blockchain verification
            from blockchain.views import teocoin_service
            
            receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
            if receipt["status"] != 1:
                return False
            
            tx = teocoin_service.w3.eth.get_transaction(tx_hash)
            contract_addr = getattr(teocoin_service, 'contract_address', None)
            
            if tx.get("to") and contract_addr:
                if str(tx.get("to")).lower() != str(contract_addr).lower():
                    return False
            
            transfer_events = teocoin_service.contract.events.Transfer().process_receipt(receipt)
            
            for event in transfer_events:
                event_from = event.args['from'].lower()
                event_to = event.args['to'].lower()
                event_amount = Decimal(str(teocoin_service.w3.from_wei(event.args['value'], 'ether')))
                
                if (event_from == from_address.lower() and 
                    event_to == to_address.lower() and
                    event_amount >= expected_amount):
                    return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Blockchain verification failed: {str(e)}")
            return False
    
    def _send_purchase_notifications(self, course, student, teacher):
        """Send notifications for course purchase"""
        try:
            from courses.signals import notify_course_purchase
            notify_course_purchase(course, student, teacher)
        except Exception as e:
            self.log_error(f"Failed to send purchase notifications: {str(e)}")

    # ========== FIAT PAYMENT METHODS ==========
    
    def create_fiat_payment_intent(
        self,
        user_id: int,
        course_id: int,
        amount_eur: Decimal
    ) -> Dict[str, Any]:
        """
        Create Stripe payment intent for fiat payment
        
        Args:
            user_id: User ID
            course_id: Course ID  
            amount_eur: Amount in EUR
            
        Returns:
            dict: Success status, client_secret, payment_intent_id or error
        """
        def _create_intent():
            # Import Stripe here to avoid import issues if not configured
            try:
                import stripe
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            except ImportError:
                raise PaymentServiceException(
                    "Stripe not installed. Please install stripe package.",
                    "STRIPE_NOT_INSTALLED",
                    500
                )
            
            # Validate user
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Validate amount
            if amount_eur <= 0:
                raise PaymentServiceException(
                    "Invalid payment amount",
                    "INVALID_AMOUNT",
                    400
                )
            
            # Check if user is already enrolled
            from courses.models import CourseEnrollment
            if CourseEnrollment.objects.filter(student=user, course=course).exists():
                raise PaymentServiceException(
                    "Already enrolled in this course",
                    "ALREADY_ENROLLED",
                    400
                )
            
            # Create Stripe payment intent
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(amount_eur * 100),  # Stripe uses cents
                    currency='eur',
                    payment_method_types=['card'],
                    metadata={
                        'course_id': course.id,
                        'user_id': user.pk,
                        'payment_type': 'course_purchase',
                        'teocoin_reward': str(course.teocoin_reward),
                        'course_title': course.title,
                        'student_email': user.email
                    },
                    description=f"Course: {course.title}"
                )
                
                return {
                    'success': True,
                    'client_secret': intent.client_secret,
                    'payment_intent_id': intent.id,
                    'amount': amount_eur,
                    'course_title': course.title,
                    'teocoin_reward': course.teocoin_reward
                }
                
            except stripe.error.StripeError as e:
                raise PaymentServiceException(
                    f"Payment processing error: {str(e)}",
                    "STRIPE_ERROR",
                    400
                )
        
        try:
            return self.execute_in_transaction(_create_intent)
        except Exception as e:
            self.log_error(f"Failed to create fiat payment intent: {str(e)}")
            raise
    
    def process_successful_fiat_payment(
        self,
        payment_intent_id: str,
        course_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Handle successful fiat payment completion
        
        Args:
            payment_intent_id: Stripe payment intent ID
            course_id: Course ID
            user_id: User ID
            
        Returns:
            dict: Success status, enrollment, teocoin_reward or error
        """
        def _process_payment():
            # Import Django settings for Stripe configuration
            from django.conf import settings
            
            # Import Stripe
            try:
                import stripe
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            except ImportError:
                raise PaymentServiceException(
                    "Stripe not installed",
                    "STRIPE_NOT_INSTALLED", 
                    500
                )
            
            # Validate user and course
            try:
                user = User.objects.get(pk=user_id)
                course = Course.objects.get(id=course_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Verify payment with Stripe
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            except stripe.error.StripeError as e:
                raise PaymentServiceException(
                    f"Payment verification error: {str(e)}",
                    "STRIPE_VERIFICATION_ERROR",
                    400
                )
            
            if intent.status != 'succeeded':
                raise PaymentServiceException(
                    f"Payment not successful. Status: {intent.status}",
                    "PAYMENT_NOT_SUCCESSFUL",
                    400
                )
            
            # Double-check enrollment doesn't exist
            from courses.models import CourseEnrollment
            existing_enrollment = CourseEnrollment.objects.filter(
                student=user, 
                course=course
            ).first()
            
            if existing_enrollment:
                raise PaymentServiceException(
                    "Already enrolled in this course",
                    "ALREADY_ENROLLED",
                    400
                )
            
            # Create enrollment record
            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                payment_method='fiat',
                amount_paid_eur=Decimal(intent.amount) / 100,
                stripe_payment_intent_id=payment_intent_id,
                teocoin_reward_given=course.teocoin_reward,
                enrolled_at=timezone.now()
            )
            
            # ✅ EXECUTE TEOCOIN TRANSFER FOR HYBRID PAYMENTS
            teocoin_transfer_result = None
            if intent.metadata and intent.metadata.get('teocoin_discount_applied'):
                try:
                    # Check if this was a hybrid payment with TeoCoin discount
                    discount_percent = float(intent.metadata.get('teocoin_discount_percent', 0))
                    student_wallet = intent.metadata.get('student_wallet_address')
                    teacher_wallet = intent.metadata.get('teacher_wallet_address')
                    
                    if discount_percent > 0 and student_wallet and teacher_wallet:
                        self.log_info(f"🪙 Executing TeoCoin transfer for hybrid payment: {discount_percent}% discount")
                        
                        # Calculate TEO amounts
                        course_price_eur = float(course.price_eur or course.price or 0)
                        discount_amount_eur = course_price_eur * discount_percent / 100
                        teo_required = discount_amount_eur * 10  # 1 EUR = 10 TEO
                        
                        # Execute the blockchain transfer via API call
                        import requests
                        
                        # Calculate commission using dynamic rate
                        teacher_commission_rate = self.get_teacher_commission_rate(course.teacher)
                        teacher_percentage = Decimal('1.00') - teacher_commission_rate
                        teo_required_decimal = Decimal(str(teo_required))
                        
                        transfer_data = {
                            'student_address': student_wallet,
                            'teacher_address': teacher_wallet,
                            'course_price': str(teo_required_decimal),
                            'course_id': course_id,
                            'teacher_amount': str(teo_required_decimal * teacher_percentage),  # 50% to teacher
                            'commission_amount': str(teo_required_decimal * teacher_commission_rate),  # Dynamic commission
                            'approval_tx_hash': f'payment_intent_{payment_intent_id}'
                        }
                        
                        # Make internal API call to execute blockchain transfer
                        blockchain_response = requests.post(
                            f"http://localhost:8000/api/v1/blockchain/execute-course-payment/",
                            json=transfer_data,
                            headers={'Authorization': f'Bearer {intent.metadata.get("auth_token", "")}'},
                            timeout=30
                        )
                        
                        if blockchain_response.status_code == 200:
                            blockchain_result = blockchain_response.json()
                            teocoin_transfer_result = blockchain_result.get('teacher_payment_tx')
                            
                            # Update enrollment with TeoCoin transfer details
                            enrollment.payment_method = 'hybrid'
                            enrollment.transaction_hash = teocoin_transfer_result
                            enrollment.save()
                            
                            self.log_info(f"✅ TeoCoin transfer completed: {teo_required} TEO transferred")
                            
                            # Record the TeoCoin transfer transaction
                            BlockchainTransaction.objects.create(
                                user=user,
                                transaction_type='payment_discount',
                                amount=Decimal(str(teo_required)),
                                status='completed',
                                transaction_hash=teocoin_transfer_result,
                                related_object_id=str(course.id),
                                notes=f"TeoCoin discount payment for course: {course.title} ({discount_percent}% discount)"
                            )
                        else:
                            self.log_error(f"❌ TeoCoin transfer failed: {blockchain_response.text}")
                            
                except Exception as e:
                    self.log_error(f"❌ TeoCoin transfer execution failed: {str(e)}")
                    # Don't fail the entire payment process if TeoCoin transfer fails
                    # The Stripe payment already succeeded
            
            # Award TeoCoin reward if configured
            teocoin_reward_given = Decimal('0')
            reward_status = 'none'
            
            if course.teocoin_reward > 0:
                try:
                    from blockchain.views import teocoin_service
                    
                    if user.wallet_address:
                        # User has wallet - give rewards immediately
                        try:
                            mint_result = teocoin_service.mint_tokens(
                                user.wallet_address,
                                float(course.teocoin_reward)
                            )
                            
                            if mint_result:  # Transaction hash returned
                                teocoin_reward_given = course.teocoin_reward
                                reward_status = 'distributed'
                                
                                # Record the successful reward transaction
                                BlockchainTransaction.objects.create(
                                    user=user,
                                    transaction_type='reward',
                                    amount=course.teocoin_reward,
                                    status='completed',
                                    transaction_hash=mint_result,
                                    related_object_id=str(course.id),
                                    notes=f"Fiat payment reward for course: {course.title}"
                                )
                                
                                self.log_info(f"✅ TeoCoin reward distributed: {course.teocoin_reward} TEO to {user.username}")
                            else:
                                # Minting failed - record as pending
                                teocoin_reward_given = course.teocoin_reward
                                reward_status = 'pending'
                                
                                BlockchainTransaction.objects.create(
                                    user=user,
                                    transaction_type='reward',
                                    amount=course.teocoin_reward,
                                    status='pending',
                                    related_object_id=str(course.id),
                                    notes=f"Pending fiat payment reward for course: {course.title} (Mint returned None)"
                                )
                                
                                self.log_error(f"❌ TeoCoin minting returned None for {user.username}")
                            
                        except Exception as mint_error:
                            # Minting failed - record as pending
                            teocoin_reward_given = course.teocoin_reward
                            reward_status = 'pending'
                            
                            BlockchainTransaction.objects.create(
                                user=user,
                                transaction_type='reward',
                                amount=course.teocoin_reward,
                                status='pending',
                                related_object_id=str(course.id),
                                notes=f"Pending fiat payment reward for course: {course.title} (Mint error: {str(mint_error)})"
                            )
                            
                            self.log_error(f"❌ TeoCoin minting failed: {mint_error}")
                    else:
                        # User has no wallet - record as pending reward
                        teocoin_reward_given = course.teocoin_reward
                        reward_status = 'pending_wallet'
                        
                        BlockchainTransaction.objects.create(
                            user=user,
                            transaction_type='reward',
                            amount=course.teocoin_reward,
                            status='pending',
                            related_object_id=str(course.id),
                            notes=f"Pending fiat payment reward for course: {course.title} (No wallet connected)"
                        )
                        
                        self.log_info(f"💰 TeoCoin reward pending (no wallet): {course.teocoin_reward} TEO for {user.username}")
                    
                except Exception as blockchain_error:
                    # Log error but don't fail the enrollment
                    teocoin_reward_given = course.teocoin_reward
                    reward_status = 'failed'
                    
                    self.log_error(f"🚨 TeoCoin reward system error: {blockchain_error}")
                    
                    # Still record the attempted reward
                    BlockchainTransaction.objects.create(
                        user=user,
                        transaction_type='reward',
                        amount=course.teocoin_reward,
                        status='failed',
                        related_object_id=str(course.id),
                        notes=f"Failed fiat payment reward for course: {course.title} (Error: {str(blockchain_error)})"
                    )
            
            # Send notifications
            try:
                from notifications.models import Notification
                
                # Create appropriate message based on reward status
                if reward_status == 'distributed':
                    message = f"🎉 Successfully enrolled in '{course.title}' via fiat payment! Received {teocoin_reward_given} TEO reward in your wallet."
                elif reward_status == 'pending_wallet':
                    message = f"✅ Successfully enrolled in '{course.title}' via fiat payment! {teocoin_reward_given} TEO reward pending - connect your wallet to claim."
                elif reward_status == 'pending':
                    message = f"✅ Successfully enrolled in '{course.title}' via fiat payment! {teocoin_reward_given} TEO reward will be processed shortly."
                elif reward_status == 'failed':
                    message = f"✅ Successfully enrolled in '{course.title}' via fiat payment! {teocoin_reward_given} TEO reward pending (technical issue)."
                else:
                    message = f"✅ Successfully enrolled in '{course.title}' via fiat payment!"
                
                Notification.objects.create(
                    user=user,
                    message=message,
                    notification_type='course_purchased'
                )
                
                # Notify teacher
                if course.teacher != user:
                    Notification.objects.create(
                        user=course.teacher,
                        message=f"New student {user.get_full_name() or user.username} enrolled in your course '{course.title}' (€{enrollment.amount_paid_eur})",
                        notification_type='course_enrollment'
                    )
                    
            except Exception as notification_error:
                self.log_error(f"Notification failed: {notification_error}")
            
            return {
                'success': True,
                'enrollment': {
                    'id': enrollment.id,
                    'course_title': course.title,
                    'payment_method': enrollment.payment_method,
                    'amount_paid_eur': enrollment.amount_paid_eur,
                    'enrolled_at': enrollment.enrolled_at
                },
                'teocoin_reward': {
                    'amount': teocoin_reward_given,
                    'status': reward_status,
                    'message': 'Reward distributed immediately' if reward_status == 'distributed' 
                              else 'Reward pending - connect wallet' if reward_status == 'pending_wallet'
                              else 'Reward processing' if reward_status == 'pending'
                              else 'Reward failed - contact support' if reward_status == 'failed'
                              else 'No reward configured'
                },
                'amount_paid': enrollment.amount_paid_eur,
                'message': message
            }
        
        try:
            from django.utils import timezone
            return self.execute_in_transaction(_process_payment)
        except Exception as e:
            self.log_error(f"Failed to process fiat payment: {str(e)}")
            raise

    def get_payment_summary(self, user_id: int, course_id: int) -> Dict[str, Any]:
        """
        Get payment options summary for a course
        
        Args:
            user_id: User ID
            course_id: Course ID
            
        Returns:
            dict: Payment options and user eligibility
        """
        try:
            user = User.objects.get(pk=user_id)
            course = Course.objects.get(id=course_id)
        except User.DoesNotExist:
            raise UserNotFoundError(user_id)
        except Course.DoesNotExist:
            raise CourseNotFoundError(course_id)
        
        # Check if already enrolled
        from courses.models import CourseEnrollment
        enrollment = CourseEnrollment.objects.filter(student=user, course=course).first()
        if enrollment:
            return {
                'already_enrolled': True,
                'enrollment': {
                    'payment_method': enrollment.payment_method,
                    'amount_paid_eur': enrollment.amount_paid_eur,
                    'amount_paid_teocoin': enrollment.amount_paid_teocoin,
                    'enrolled_at': enrollment.enrolled_at
                }
            }
        
        # Always return both payment options for frontend compatibility
        pricing_options = []
        # Fiat option
        pricing_options.append({
            'method': 'fiat',
            'price': course.price_eur,
            'currency': 'EUR',
            'reward': course.teocoin_reward,
            'description': f'€{course.price_eur} + {course.teocoin_reward} TEO reward',
            'disabled': course.price_eur == 0
        })
        # TeoCoin option
        teocoin_discount_amount = course.get_teocoin_discount_amount() if course.price_eur > 0 else 0
        pricing_options.append({
            'method': 'teocoin',
            'price': teocoin_discount_amount,  # TEO needed for discount (not discounted price)
            'currency': 'TEO',
            'discount': course.teocoin_discount_percent if course.price_eur > 0 else 0,
            'description': f'{teocoin_discount_amount} TEO for {course.teocoin_discount_percent}% discount' if course.price_eur > 0 else 'Not available for free courses',
            'disabled': course.price_eur == 0
        })
        
        # Only add free option for actually free courses
        if course.price_eur == 0:
            pricing_options.append({
                'method': 'free',
                'price': 0,
                'currency': 'FREE',
                'reward': course.teocoin_reward,
                'description': f'Free + {course.teocoin_reward} TEO reward',
                'disabled': False
            })

        # Check TeoCoin balance if applicable
        teocoin_balance = Decimal('0')
        if user.wallet_address:
            try:
                balance = self._get_user_balance(user.wallet_address)
                teocoin_balance = Decimal(str(balance))
            except:
                pass

        can_pay_with_teocoin = False
        if course.price_eur > 0 and course.get_teocoin_discount_amount() > 0:
            can_pay_with_teocoin = bool(user.wallet_address) and teocoin_balance >= course.get_teocoin_discount_amount()

        return {
            'already_enrolled': False,
            'pricing_options': pricing_options,
            'user_teocoin_balance': teocoin_balance,
            'can_pay_with_teocoin': can_pay_with_teocoin,
            'wallet_connected': bool(user.wallet_address),
            'course_approved': course.is_approved
        }


# Global service instance
payment_service = PaymentService()
