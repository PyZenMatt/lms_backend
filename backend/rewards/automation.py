# rewards/automation.py
"""
Automated reward system for TeoArt educational platform
Handles automated TeoCoin rewards for course and lesson completion
"""

import logging
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from users.models import User
from courses.models import Course, Lesson, LessonCompletion, CourseEnrollment
from rewards.models import TokenBalance, BlockchainTransaction
from notifications.models import Notification

logger = logging.getLogger(__name__)


class AutomatedRewardSystem:
    """
    Automated reward system for educational milestones
    """
    
    # Reward configuration (percentages of course price)
    LESSON_COMPLETION_REWARD_BASE = 0.02  # 2% of course price per lesson
    COURSE_COMPLETION_BONUS = 0.10        # 10% bonus for completing entire course
    ACHIEVEMENT_BONUS = 0.05              # 5% for special achievements
    
    # Maximum total rewards per course (to prevent exploitation)
    MAX_COURSE_REWARDS_PERCENTAGE = 0.25  # 25% of course price max
    
    def __init__(self):
        self.blockchain_enabled = True
        try:
            from blockchain.blockchain import TeoCoinService
            self.blockchain_service = TeoCoinService()
        except Exception as e:
            logger.warning(f"Blockchain service unavailable: {e}")
            self.blockchain_enabled = False

    def calculate_lesson_reward(self, course: Course, lesson: Lesson) -> int:
        """
        Calculate reward for completing a lesson
        """
        base_reward = int(course.price * self.LESSON_COMPLETION_REWARD_BASE)
        
        # Add difficulty multiplier based on lesson type
        multiplier = 1.0
        if hasattr(lesson, 'lesson_type'):
            if lesson.lesson_type == 'video':
                multiplier = 1.2
            elif lesson.lesson_type == 'practical':
                multiplier = 1.5
        
        # Check if course has remaining reward budget
        total_distributed = getattr(course, 'reward_distributed', 0)
        max_rewards = int(course.price * self.MAX_COURSE_REWARDS_PERCENTAGE)
        remaining_budget = max_rewards - total_distributed
        
        calculated_reward = int(base_reward * multiplier)
        return min(calculated_reward, remaining_budget, course.price // 10)  # Max 10% per lesson

    def calculate_course_completion_bonus(self, course: Course) -> int:
        """
        Calculate bonus reward for completing entire course
        """
        bonus = int(course.price * self.COURSE_COMPLETION_BONUS)
        
        # Check remaining budget
        total_distributed = getattr(course, 'reward_distributed', 0)
        max_rewards = int(course.price * self.MAX_COURSE_REWARDS_PERCENTAGE)
        remaining_budget = max_rewards - total_distributed
        
        return min(bonus, remaining_budget)

    def reward_lesson_completion(self, student: User, lesson: Lesson, course: Course = None):
        """
        Award TeoCoin reward for lesson completion
        """
        if not course:
            course = lesson.course
            
        if not course:
            logger.error(f"No course found for lesson {lesson.id}")
            return False

        try:
            with transaction.atomic():
                # Calculate reward
                reward_amount = self.calculate_lesson_reward(course, lesson)
                
                if reward_amount <= 0:
                    logger.info(f"No reward calculated for lesson {lesson.id} - budget exhausted")
                    return False

                # Award traditional TeoCoin
                student.add_teo_coins(
                    reward_amount,
                    transaction_type='lesson_completion_reward',
                    related_object_id=lesson.id
                )

                # Update course reward tracking
                if hasattr(course, 'reward_distributed'):
                    course.reward_distributed = (course.reward_distributed or 0) + reward_amount
                    course.save(update_fields=['reward_distributed'])

                # Create notification
                Notification.objects.create(
                    user=student,
                    message=f"🎉 Hai completato la lezione '{lesson.title}' e guadagnato {reward_amount} TeoCoins!",
                    notification_type='lesson_completed',
                    related_object_id=lesson.id
                )

                # Try blockchain reward if enabled
                if self.blockchain_enabled:
                    self._award_blockchain_tokens(student, reward_amount, 'lesson_completion', lesson.id)

                logger.info(f"Awarded {reward_amount} TeoCoins to {student.username} for lesson {lesson.id}")
                return True

        except Exception as e:
            logger.error(f"Error rewarding lesson completion: {e}")
            return False

    def check_and_reward_course_completion(self, student: User, course: Course):
        """
        Check if student completed all lessons and award course completion bonus
        """
        try:
            total_lessons = course.lessons.count()
            completed_lessons = LessonCompletion.objects.filter(
                student=student,
                lesson__course=course
            ).count()

            if total_lessons > 0 and completed_lessons >= total_lessons:
                # Student completed all lessons
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={'completed': True}
                )
                
                if not enrollment.completed:
                    enrollment.completed = True
                    enrollment.save()
                    
                    # Award completion bonus
                    self._award_course_completion_bonus(student, course)
                    return True
                    
        except Exception as e:
            logger.error(f"Error checking course completion: {e}")
            
        return False

    def _award_course_completion_bonus(self, student: User, course: Course):
        """
        Award bonus for completing entire course
        """
        try:
            with transaction.atomic():
                bonus_amount = self.calculate_course_completion_bonus(course)
                
                if bonus_amount <= 0:
                    logger.info(f"No completion bonus available for course {course.id}")
                    return

                # Award traditional TeoCoin
                student.add_teo_coins(
                    bonus_amount,
                    transaction_type='course_completion_bonus',
                    related_object_id=course.id
                )

                # Update course reward tracking
                if hasattr(course, 'reward_distributed'):
                    course.reward_distributed = (course.reward_distributed or 0) + bonus_amount
                    course.save(update_fields=['reward_distributed'])

                # Create notifications
                Notification.objects.create(
                    user=student,
                    message=f"🎓 Congratulazioni! Hai completato il corso '{course.title}' e ricevuto {bonus_amount} TeoCoins bonus!",
                    notification_type='course_completed',
                    related_object_id=course.id
                )

                # Notify teacher
                Notification.objects.create(
                    user=course.teacher,
                    message=f"🎉 Lo studente {student.username} ha completato il tuo corso '{course.title}'!",
                    notification_type='student_completed_course',
                    related_object_id=course.id
                )

                # Try blockchain reward if enabled
                if self.blockchain_enabled:
                    self._award_blockchain_tokens(student, bonus_amount, 'course_completion', course.id)

                logger.info(f"Awarded {bonus_amount} TeoCoins completion bonus to {student.username} for course {course.id}")

        except Exception as e:
            logger.error(f"Error awarding course completion bonus: {e}")

    def _award_blockchain_tokens(self, user: User, amount: int, reward_type: str, related_id: int):
        """
        Award blockchain tokens if wallet is connected and blockchain is enabled
        """
        if not self.blockchain_enabled:
            return

        try:
            # Check if user has connected wallet
            if not user.wallet_address:
                logger.info(f"User {user.username} has no wallet connected for blockchain reward")
                return

            # Create blockchain transaction record
            blockchain_tx = BlockchainTransaction.objects.create(
                user=user,
                transaction_type='reward',
                amount=amount,
                status='pending',
                related_object_id=related_id,
                metadata={
                    'reward_type': reward_type,
                    'traditional_teocoin_amount': amount
                }
            )

            # Try to mint tokens on blockchain
            try:
                tx_hash = self.blockchain_service.mint_tokens(user.wallet_address, Decimal(amount))
                if tx_hash:
                    blockchain_tx.blockchain_tx_hash = tx_hash
                    blockchain_tx.status = 'completed'
                    blockchain_tx.save()
                    
                    # Update user's token balance
                    token_balance, created = TokenBalance.objects.get_or_create(
                        user=user,
                        defaults={'balance': 0}
                    )
                    token_balance.balance += amount
                    token_balance.save()
                    
                    logger.info(f"Successfully minted {amount} blockchain tokens for {user.username}")
                else:
                    blockchain_tx.status = 'failed'
                    blockchain_tx.save()
                    
            except Exception as blockchain_error:
                logger.error(f"Blockchain minting failed: {blockchain_error}")
                blockchain_tx.status = 'failed'
                blockchain_tx.error_message = str(blockchain_error)
                blockchain_tx.save()

        except Exception as e:
            logger.error(f"Error in blockchain token award: {e}")

    def calculate_achievement_reward(self, achievement_type: str, course: Course = None) -> int:
        """
        Calculate reward for achievements (future implementation)
        """
        base_amount = 50  # Base achievement reward
        
        if course:
            base_amount = int(course.price * self.ACHIEVEMENT_BONUS)
            
        # Achievement type multipliers
        multipliers = {
            'first_course_completed': 2.0,
            'perfect_scores': 1.5,
            'fast_completion': 1.3,
            'helpful_peer': 1.2,
            'consecutive_logins': 1.1
        }
        
        multiplier = multipliers.get(achievement_type, 1.0)
        return int(base_amount * multiplier)

    def award_achievement(self, student: User, achievement_type: str, course: Course = None):
        """
        Award achievement-based rewards
        """
        try:
            reward_amount = self.calculate_achievement_reward(achievement_type, course)
            
            if reward_amount > 0:
                student.add_teo_coins(
                    reward_amount,
                    transaction_type='achievement_reward',
                    related_object_id=course.id if course else None
                )

                # Create notification
                achievement_messages = {
                    'first_course_completed': f"🏆 Primo corso completato! Hai guadagnato {reward_amount} TeoCoins!",
                    'perfect_scores': f"⭐ Punteggi perfetti! Hai guadagnato {reward_amount} TeoCoins!",
                    'fast_completion': f"⚡ Completamento veloce! Hai guadagnato {reward_amount} TeoCoins!",
                    'helpful_peer': f"🤝 Peer helper! Hai guadagnato {reward_amount} TeoCoins!",
                    'consecutive_logins': f"📅 Accessi consecutivi! Hai guadagnato {reward_amount} TeoCoins!"
                }

                message = achievement_messages.get(
                    achievement_type, 
                    f"🎯 Achievement sbloccato! Hai guadagnato {reward_amount} TeoCoins!"
                )

                Notification.objects.create(
                    user=student,
                    message=message,
                    notification_type='achievement_unlocked',
                    related_object_id=course.id if course else None
                )

                # Try blockchain reward
                if self.blockchain_enabled and student.wallet_address:
                    self._award_blockchain_tokens(student, reward_amount, 'achievement', course.id if course else 0)

                logger.info(f"Awarded {reward_amount} TeoCoins to {student.username} for achievement: {achievement_type}")

        except Exception as e:
            logger.error(f"Error awarding achievement: {e}")

    def get_student_reward_summary(self, student: User, course: Course = None):
        """
        Get summary of rewards earned by student
        """
        from courses.models import Lesson
        
        # Start with all transactions for the student
        queryset = BlockchainTransaction.objects.filter(user=student)
        
        if course:
            # For course-specific summary, we need different logic for different transaction types
            course_transactions = []
            
            # Course completion bonuses: related_object_id = course.id
            course_bonuses = queryset.filter(
                transaction_type='course_completion_bonus',
                related_object_id=course.id
            )
            course_transactions.extend(course_bonuses)
            
            # Lesson completion rewards: related_object_id = lesson.id, need to find lessons in this course
            lesson_ids = list(course.lessons.values_list('id', flat=True))
            lesson_rewards = queryset.filter(
                transaction_type='lesson_completion_reward',
                related_object_id__in=lesson_ids
            )
            course_transactions.extend(lesson_rewards)
            
            # Achievement rewards: related_object_id = course.id (if course-specific)
            achievement_rewards = queryset.filter(
                transaction_type='achievement_reward',
                related_object_id=course.id
            )
            course_transactions.extend(achievement_rewards)
            
            # Create a queryset from the filtered transactions
            transaction_ids = [tx.id for tx in course_transactions]
            reward_transactions = BlockchainTransaction.objects.filter(id__in=transaction_ids)
        else:
            # For overall summary, include all reward transactions
            reward_transactions = queryset.filter(
                transaction_type__in=[
                    'lesson_completion_reward',
                    'course_completion_bonus', 
                    'achievement_reward'
                ]
            )
        
        total_earned = sum(tx.amount for tx in reward_transactions if tx.amount > 0)
        
        return {
            'total_reward_earned': total_earned,
            'lesson_rewards': reward_transactions.filter(transaction_type='lesson_completion_reward').count(),
            'course_bonuses': reward_transactions.filter(transaction_type='course_completion_bonus').count(),
            'achievements': reward_transactions.filter(transaction_type='achievement_reward').count(),
            'recent_rewards': reward_transactions.order_by('-created_at')[:5]
        }


# Initialize global reward system instance
reward_system = AutomatedRewardSystem()
