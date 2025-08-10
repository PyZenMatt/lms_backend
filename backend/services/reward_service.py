"""
Reward Service for TeoArt School Platform

Handles all reward-related operations including lesson completion rewards,
course completion bonuses, achievement tracking, and TeoCoin distribution.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
import logging

from .base import TransactionalService
from .exceptions import (
    TeoArtServiceException, 
    UserNotFoundError, 
    CourseNotFoundError
)

# Models
from courses.models import Course, Lesson, LessonCompletion
from rewards.models import BlockchainTransaction, TokenBalance
from notifications.models import Notification

User = get_user_model()

logger = logging.getLogger(__name__)


class RewardServiceException(TeoArtServiceException):
    """Reward-specific exceptions"""
    pass


class RewardService(TransactionalService):
    """
    Service for handling reward operations.
    
    Manages lesson completion rewards, course completion bonuses,
    achievement tracking, and TeoCoin distribution.
    """
    
    # Reward configuration
    LESSON_COMPLETION_REWARD_RATE = Decimal('0.02')  # 2% of course price per lesson
    COURSE_COMPLETION_BONUS_RATE = Decimal('0.10')   # 10% bonus for completing entire course
    
    def __init__(self):
        super().__init__()
        self.service_name = "RewardService"
    
    def process_lesson_completion_reward(
        self,
        user_id: int,
        lesson_id: int,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process reward for lesson completion.
        
        Args:
            user_id: ID of the user who completed the lesson
            lesson_id: ID of the completed lesson
            course_id: Optional course ID (will be derived from lesson if not provided)
            
        Returns:
            Dict with reward details and transaction info
        """
        def _process_lesson_reward():
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Validate lesson
            try:
                lesson = Lesson.objects.select_related('course').get(id=lesson_id)
            except Lesson.DoesNotExist:
                raise TeoArtServiceException(f"Lesson with ID {lesson_id} not found")
            
            # Get course
            course = lesson.course
            if not course:
                raise TeoArtServiceException("Lesson is not associated with any course")
                
            # Validate course_id if provided
            if course_id and course.id != course_id:
                raise TeoArtServiceException(f"Lesson {lesson_id} does not belong to course {course_id}")
            
            # Check if user is enrolled in course
            if not course.students.filter(id=user_id).exists():
                raise TeoArtServiceException("User is not enrolled in this course")
            
            # Check if lesson completion already exists
            existing_completion = LessonCompletion.objects.filter(
                student=user,
                lesson=lesson
            ).first()
            
            if existing_completion:
                # Check if reward already processed by looking for existing transaction
                existing_transaction = BlockchainTransaction.objects.filter(
                    user=user,
                    transaction_type='lesson_reward',
                    related_object_id=str(lesson.id),
                    status='completed'
                ).first()
                
                if existing_transaction:
                    raise TeoArtServiceException("Lesson completion reward already processed")
            
            # Calculate reward amount
            reward_amount = self._calculate_lesson_reward(course, lesson)
            
            if reward_amount <= 0:
                self.log_info(f"No reward calculated for lesson {lesson_id}")
                return {
                    'reward_processed': False,
                    'reason': 'No reward amount calculated',
                    'lesson_id': lesson_id,
                    'course_id': course.id,
                    'user_id': user_id
                }
            
            # Create lesson completion record
            completion, created = LessonCompletion.objects.get_or_create(
                student=user,
                lesson=lesson
            )
            
            # Process reward
            reward_tx = self._create_reward_transaction(
                user=user,
                amount=reward_amount,
                transaction_type='lesson_reward',
                related_object_id=str(lesson_id),
                notes=f"Lesson completion reward: {lesson.title}"
            )
            
            # Send notification
            self._send_reward_notification(
                user=user,
                amount=reward_amount,
                message=f"Congratulazioni! Hai ricevuto {float(reward_amount)} TeoCoins per aver completato la lezione '{lesson.title}'",
                notification_type='lesson_reward'
            )
            
            # Check for course completion bonus
            course_completed = self._check_course_completion(user, course)
            course_bonus = None
            
            if course_completed:
                try:
                    course_bonus = self.process_course_completion_bonus(user_id, course.id)
                except Exception as e:
                    self.log_error(f"Failed to process course completion bonus: {e}")
                    # Don't fail lesson reward if bonus fails
            
            self.log_info(f"Lesson reward processed: user {user_id}, lesson {lesson_id}, amount {reward_amount}")
            
            result = {
                'reward_processed': True,
                'lesson_id': lesson_id,
                'course_id': course.id,
                'user_id': user_id,
                'lesson_title': lesson.title,
                'course_title': course.title,
                'reward_amount': float(reward_amount),
                'reward_transaction_id': reward_tx.id,
                'course_completed': course_completed
            }
            
            if course_bonus:
                result['course_completion_bonus'] = course_bonus
            
            return result
        
        try:
            return self.execute_in_transaction(_process_lesson_reward)
        except Exception as e:
            self.log_error(f"Failed to process lesson completion reward: {str(e)}")
            raise
    
    def process_course_completion_bonus(
        self,
        user_id: int,
        course_id: int
    ) -> Dict[str, Any]:
        """
        Process bonus reward for course completion.
        """
        def _process_course_bonus():
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(f"Course with ID {course_id} not found")
            
            # Check if user completed all lessons
            if not self._check_course_completion(user, course):
                raise TeoArtServiceException("Course is not fully completed")
            
            # Check if bonus already processed
            existing_bonus = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type='course_completion_bonus',
                related_object_id=str(course_id),
                status='completed'
            ).first()
            
            if existing_bonus:
                raise TeoArtServiceException("Course completion bonus already processed")
            
            # Calculate bonus amount
            bonus_amount = course.price * self.COURSE_COMPLETION_BONUS_RATE
            
            # Create bonus transaction
            bonus_tx = self._create_reward_transaction(
                user=user,
                amount=bonus_amount,
                transaction_type='course_completion_bonus',
                related_object_id=str(course_id),
                notes=f"Course completion bonus: {course.title}"
            )
            
            # Send notification
            self._send_reward_notification(
                user=user,
                amount=bonus_amount,
                message=f"Fantastico! Hai completato il corso '{course.title}' e ricevuto {float(bonus_amount)} TeoCoins bonus!",
                notification_type='course_completion_bonus'
            )
            
            result = {
                'amount': float(bonus_amount),
                'course_id': course_id,
                'course_title': course.title,
                'transaction_id': bonus_tx.id,
                'user_id': user_id
            }
            
            self.log_info(f"Course completion bonus processed: user {user_id}, course {course_id}, amount {bonus_amount}")
            return result
        
        try:
            return self.execute_in_transaction(_process_course_bonus)
        except Exception as e:
            self.log_error(f"Failed to process course completion bonus: {str(e)}")
            raise
    
    def get_user_rewards_summary(
        self,
        user_id: int,
        time_period: str = 'all'
    ) -> Dict[str, Any]:
        """
        Get comprehensive rewards summary for a user.
        
        Args:
            user_id: ID of the user
            time_period: Time filter ('week', 'month', 'year', 'all')
        """
        try:
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Calculate time filter
            now = timezone.now()
            date_filter = Q()
            
            if time_period == 'week':
                date_filter = Q(created_at__gte=now - timedelta(days=7))
            elif time_period == 'month':
                date_filter = Q(created_at__gte=now - timedelta(days=30))
            elif time_period == 'year':
                date_filter = Q(created_at__gte=now - timedelta(days=365))
            
            # Get reward transactions
            reward_transactions = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type__in=['lesson_reward', 'course_completion_bonus'],
                status='completed'
            ).filter(date_filter).order_by('-created_at')
            
            # Calculate totals
            total_rewards = reward_transactions.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            lesson_rewards = reward_transactions.filter(
                transaction_type='lesson_reward'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            course_bonuses = reward_transactions.filter(
                transaction_type='course_completion_bonus'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Get completed lessons count
            completed_lessons_query = LessonCompletion.objects.filter(student=user)
            if time_period != 'all':
                # Use completed_at field instead of created_at for LessonCompletion
                completed_at_filter = Q()
                if time_period == 'week':
                    completed_at_filter = Q(completed_at__gte=now - timedelta(days=7))
                elif time_period == 'month':
                    completed_at_filter = Q(completed_at__gte=now - timedelta(days=30))
                elif time_period == 'year':
                    completed_at_filter = Q(completed_at__gte=now - timedelta(days=365))
                completed_lessons_query = completed_lessons_query.filter(completed_at_filter)
            completed_lessons_count = completed_lessons_query.count()
            
            # Get completed courses count
            completed_courses = self._get_completed_courses_count(user)
            
            # Get current balance
            current_balance = self._get_user_balance(user)
            
            # Format recent rewards
            recent_rewards = []
            for tx in reward_transactions[:10]:  # Last 10 transactions
                recent_rewards.append({
                    'amount': float(tx.amount),
                    'type': tx.transaction_type,
                    'date': tx.created_at.isoformat(),
                    'notes': tx.notes or '',
                    'related_object_id': tx.related_object_id
                })
            
            return {
                'user_id': user_id,
                'username': user.username,
                'time_period': time_period,
                'summary': {
                    'total_rewards_earned': float(total_rewards),
                    'lesson_rewards': float(lesson_rewards),
                    'course_completion_bonuses': float(course_bonuses),
                    'current_balance': float(current_balance),
                    'completed_lessons': completed_lessons_count,
                    'completed_courses': completed_courses,
                    'total_transactions': reward_transactions.count()
                },
                'recent_rewards': recent_rewards
            }
            
        except Exception as e:
            self.log_error(f"Failed to get user rewards summary: {str(e)}")
            raise
    
    def get_reward_leaderboard(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get reward leaderboard showing top earners.
        
        Args:
            limit: Number of top users to return
        """
        try:
            # Get users with their total rewards
            user_rewards = BlockchainTransaction.objects.filter(
                transaction_type__in=['lesson_reward', 'course_completion_bonus'],
                status='completed'
            ).values('user').annotate(
                total_rewards=Sum('amount'),
                reward_count=Count('id')
            ).order_by('-total_rewards')[:limit]
            
            leaderboard = []
            for i, entry in enumerate(user_rewards, 1):
                try:
                    user = User.objects.get(id=entry['user'])
                    leaderboard.append({
                        'rank': i,
                        'user_id': user.id,
                        'username': user.username,
                        'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                        'total_rewards': float(entry['total_rewards']),
                        'reward_count': entry['reward_count']
                    })
                except User.DoesNotExist:
                    continue
            
            return leaderboard
            
        except Exception as e:
            self.log_error(f"Failed to get reward leaderboard: {str(e)}")
            raise
    
    def _calculate_lesson_reward(self, course: Course, lesson: Lesson) -> Decimal:
        """Calculate reward amount for lesson completion"""
        if not course.price or course.price <= 0:
            return Decimal('0')
        
        return course.price * self.LESSON_COMPLETION_REWARD_RATE
    
    def _check_course_completion(self, user: User, course: Course) -> bool:
        """Check if user has completed all lessons in a course"""
        total_lessons = course.lessons_in_course.count()
        if total_lessons == 0:
            return False
        
        completed_lessons = LessonCompletion.objects.filter(
            student=user,
            lesson__course=course
        ).count()
        
        return completed_lessons >= total_lessons
    
    def _get_user_balance(self, user: User) -> Decimal:
        """Get user's current TeoCoin balance"""
        try:
            balance_obj = TokenBalance.objects.get(user=user)
            return balance_obj.balance
        except TokenBalance.DoesNotExist:
            return Decimal('0')
    
    def _get_completed_courses_count(self, user: User) -> int:
        """Get count of completed courses for user"""
        user_courses = user.core_students.all()
        completed_count = 0
        
        for course in user_courses:
            if self._check_course_completion(user, course):
                completed_count += 1
                
        return completed_count
    
    def _create_reward_transaction(
        self,
        user: User,
        amount: Decimal,
        transaction_type: str,
        related_object_id: str,
        notes: str
    ) -> BlockchainTransaction:
        """Create a reward transaction record"""
        import hashlib
        import time
        
        # Generate transaction hash
        hash_input = f"{user.id}-{amount}-{transaction_type}-{time.time()}"
        tx_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
        
        return BlockchainTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            status='completed',
            transaction_hash=tx_hash,
            from_address="reward_pool",
            to_address=user.wallet_address or "pending_wallet",
            related_object_id=related_object_id,
            notes=notes
        )
    
    def _send_reward_notification(
        self,
        user: User,
        amount: Decimal,
        message: str,
        notification_type: str
    ):
        """Send notification for reward"""
        try:
            Notification.objects.create(
                user=user,
                message=message,
                notification_type=notification_type,
                related_object_id=str(int(amount))  # Convert to int for notification field
            )
            self.log_info(f"Sent reward notification to user {user.id}")
        except Exception as e:
            self.log_error(f"Failed to send reward notification: {str(e)}")
            # Don't raise exception - notification failure shouldn't break reward processing


# Global service instance
reward_service = RewardService()
