"""
Tests for Reward Service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock

from courses.models import Course, Lesson, LessonCompletion
from rewards.models import BlockchainTransaction, TokenBalance
from notifications.models import Notification
from services.reward_service import reward_service
from services.exceptions import (
    UserNotFoundError, 
    CourseNotFoundError,
    TeoArtServiceException
)

User = get_user_model()


class RewardServiceTestCase(TestCase):
    """Test cases for RewardService"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass',
            role='student',
            first_name='Student',
            last_name='One',
            wallet_address='0x1234567890123456789012345678901234567890'
        )
        
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.com',
            password='testpass',
            role='teacher',
            first_name='Teacher',
            last_name='One',
            wallet_address='0x0987654321098765432109876543210987654321',
            is_approved=True
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='A test course',
            price=Decimal('100.00'),
            teacher=self.teacher,
            is_approved=True
        )
        
        # Create test lessons
        self.lesson1 = Lesson.objects.create(
            title='Lesson 1',
            content='Test lesson 1 content',
            course=self.course,
            teacher=self.teacher,
            order=1
        )
        
        self.lesson2 = Lesson.objects.create(
            title='Lesson 2',
            content='Test lesson 2 content',
            course=self.course,
            teacher=self.teacher,
            order=2
        )
        
        # Enroll student in course
        self.course.students.add(self.student)
        
        # Create token balance for student
        TokenBalance.objects.create(
            user=self.student,
            balance=Decimal('50.00')
        )
    
    def test_process_lesson_completion_reward_success(self):
        """Test successful lesson completion reward processing"""
        result = reward_service.process_lesson_completion_reward(
            user_id=self.student.id,
            lesson_id=self.lesson1.id,
            course_id=self.course.id
        )
        
        self.assertTrue(result['reward_processed'])
        self.assertEqual(result['lesson_id'], self.lesson1.id)
        self.assertEqual(result['course_id'], self.course.id)
        self.assertEqual(result['user_id'], self.student.id)
        self.assertEqual(result['lesson_title'], self.lesson1.title)
        self.assertEqual(result['course_title'], self.course.title)
        self.assertEqual(result['reward_amount'], 2.0)  # 2% of 100
        self.assertFalse(result['course_completed'])  # Only 1 of 2 lessons completed
        
        # Verify lesson completion was created
        completion = LessonCompletion.objects.get(
            student=self.student,
            lesson=self.lesson1
        )
        self.assertIsNotNone(completion.completed_at)
        
        # Verify transaction was created
        transaction = BlockchainTransaction.objects.get(
            user=self.student,
            transaction_type='lesson_reward',
            related_object_id=str(self.lesson1.id)
        )
        self.assertEqual(transaction.amount, Decimal('2.00'))
        self.assertEqual(transaction.status, 'completed')
        
        # Verify notification was sent
        notification = Notification.objects.get(
            user=self.student,
            notification_type='lesson_reward'
        )
        self.assertIn('2.0 TeoCoins', notification.message)
        self.assertIn(self.lesson1.title, notification.message)
    
    def test_process_lesson_completion_reward_course_completion(self):
        """Test lesson completion reward with course completion bonus"""
        # Complete first lesson
        reward_service.process_lesson_completion_reward(
            user_id=self.student.id,
            lesson_id=self.lesson1.id
        )
        
        # Complete second lesson (should trigger course completion)
        result = reward_service.process_lesson_completion_reward(
            user_id=self.student.id,
            lesson_id=self.lesson2.id
        )
        
        self.assertTrue(result['reward_processed'])
        self.assertTrue(result['course_completed'])
        self.assertIn('course_completion_bonus', result)
        
        # Check course completion bonus
        bonus = result['course_completion_bonus']
        self.assertEqual(bonus['amount'], 10.0)  # 10% of 100
        
        # Verify bonus transaction was created
        bonus_transaction = BlockchainTransaction.objects.get(
            user=self.student,
            transaction_type='course_completion_bonus',
            related_object_id=str(self.course.id)
        )
        self.assertEqual(bonus_transaction.amount, Decimal('10.00'))
    
    def test_process_lesson_completion_reward_user_not_found(self):
        """Test lesson completion reward with non-existent user"""
        with self.assertRaises(UserNotFoundError):
            reward_service.process_lesson_completion_reward(
                user_id=99999,
                lesson_id=self.lesson1.id
            )
    
    def test_process_lesson_completion_reward_lesson_not_found(self):
        """Test lesson completion reward with non-existent lesson"""
        with self.assertRaises(TeoArtServiceException) as cm:
            reward_service.process_lesson_completion_reward(
                user_id=self.student.id,
                lesson_id=99999
            )
        
        self.assertIn("Lesson with ID 99999 not found", str(cm.exception))
    
    def test_process_lesson_completion_reward_user_not_enrolled(self):
        """Test lesson completion reward for non-enrolled user"""
        # Create another student not enrolled in course
        other_student = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass',
            role='student'
        )
        
        with self.assertRaises(TeoArtServiceException) as cm:
            reward_service.process_lesson_completion_reward(
                user_id=other_student.id,
                lesson_id=self.lesson1.id
            )
        
        self.assertIn("User is not enrolled in this course", str(cm.exception))
    
    def test_process_lesson_completion_reward_already_processed(self):
        """Test lesson completion reward already processed"""
        # Process reward first time
        reward_service.process_lesson_completion_reward(
            user_id=self.student.id,
            lesson_id=self.lesson1.id
        )
        
        # Try to process again
        with self.assertRaises(TeoArtServiceException) as cm:
            reward_service.process_lesson_completion_reward(
                user_id=self.student.id,
                lesson_id=self.lesson1.id
            )
        
        self.assertIn("Lesson completion reward already processed", str(cm.exception))
    
    def test_process_lesson_completion_reward_no_course_price(self):
        """Test lesson completion reward with course having no price"""
        # Create course with no price
        free_course = Course.objects.create(
            title='Free Course',
            description='A free course',
            price=Decimal('0.00'),
            teacher=self.teacher
        )
        
        free_lesson = Lesson.objects.create(
            title='Free Lesson',
            content='Free lesson content',
            course=free_course,
            teacher=self.teacher,
            order=1
        )
        
        free_course.students.add(self.student)
        
        result = reward_service.process_lesson_completion_reward(
            user_id=self.student.id,
            lesson_id=free_lesson.id
        )
        
        self.assertFalse(result['reward_processed'])
        self.assertEqual(result['reason'], 'No reward amount calculated')
    
    def test_process_course_completion_bonus_success(self):
        """Test successful course completion bonus processing"""
        # Complete all lessons first
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson2
        )
        
        result = reward_service.process_course_completion_bonus(
            user_id=self.student.id,
            course_id=self.course.id
        )
        
        self.assertEqual(result['amount'], Decimal('10.00'))  # 10% of 100
        self.assertEqual(result['course_id'], self.course.id)
        self.assertEqual(result['course_title'], self.course.title)
        self.assertIn('transaction_id', result)
        
        # Verify transaction was created
        transaction = BlockchainTransaction.objects.get(id=result['transaction_id'])
        self.assertEqual(transaction.amount, Decimal('10.00'))
        self.assertEqual(transaction.transaction_type, 'course_completion_bonus')
    
    def test_process_course_completion_bonus_not_completed(self):
        """Test course completion bonus when course not fully completed"""
        # Only complete first lesson
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        with self.assertRaises(TeoArtServiceException) as cm:
            reward_service.process_course_completion_bonus(
                user_id=self.student.id,
                course_id=self.course.id
            )
        
        self.assertIn("Course is not fully completed", str(cm.exception))
    
    def test_process_course_completion_bonus_already_processed(self):
        """Test course completion bonus already processed"""
        # Complete all lessons
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson2
        )
        
        # Create existing bonus transaction
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('10.00'),
            transaction_type='course_completion_bonus',
            status='completed',
            related_object_id=str(self.course.id),
            transaction_hash='existing_bonus'
        )
        
        with self.assertRaises(TeoArtServiceException) as cm:
            reward_service.process_course_completion_bonus(
                user_id=self.student.id,
                course_id=self.course.id
            )
        
        self.assertIn("Course completion bonus already processed", str(cm.exception))
    
    def test_get_user_rewards_summary(self):
        """Test getting user rewards summary"""
        # Create some reward transactions
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('2.00'),
            transaction_type='lesson_reward',
            status='completed',
            related_object_id=str(self.lesson1.id),
            notes='Lesson 1 reward'
        )
        
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('2.00'),
            transaction_type='lesson_reward',
            status='completed',
            related_object_id=str(self.lesson2.id),
            notes='Lesson 2 reward'
        )
        
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('10.00'),
            transaction_type='course_completion_bonus',
            status='completed',
            related_object_id=str(self.course.id),
            notes='Course completion bonus'
        )
        
        # Create lesson completions
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson2
        )
        
        summary = reward_service.get_user_rewards_summary(self.student.id)
        
        self.assertEqual(summary['user_id'], self.student.id)
        self.assertEqual(summary['username'], self.student.username)
        self.assertEqual(summary['time_period'], 'all')
        
        # Check summary totals
        summary_data = summary['summary']
        self.assertEqual(summary_data['total_rewards_earned'], 14.0)  # 2 + 2 + 10
        self.assertEqual(summary_data['lesson_rewards'], 4.0)  # 2 + 2
        self.assertEqual(summary_data['course_completion_bonuses'], 10.0)
        self.assertEqual(summary_data['current_balance'], 50.0)  # From TokenBalance
        self.assertEqual(summary_data['completed_lessons'], 2)
        self.assertEqual(summary_data['completed_courses'], 1)
        self.assertEqual(summary_data['total_transactions'], 3)
        
        # Check recent rewards
        self.assertEqual(len(summary['recent_rewards']), 3)
        self.assertEqual(summary['recent_rewards'][0]['amount'], 10.0)  # Most recent first
    
    def test_get_user_rewards_summary_time_filter(self):
        """Test getting user rewards summary with time filter"""
        # Create old transaction (more than a week ago)
        old_transaction = BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('5.00'),
            transaction_type='lesson_reward',
            status='completed',
            related_object_id=str(self.lesson1.id),
            notes='Old lesson reward'
        )
        
        # Manually set old date
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=10)
        old_transaction.created_at = old_date
        old_transaction.save()
        
        # Create recent transaction
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('2.00'),
            transaction_type='lesson_reward',
            status='completed',
            related_object_id=str(self.lesson2.id),
            notes='Recent lesson reward'
        )
        
        # Get summary for last week
        summary = reward_service.get_user_rewards_summary(
            self.student.id,
            time_period='week'
        )
        
        # Should only include recent transaction
        self.assertEqual(summary['summary']['total_rewards_earned'], 2.0)
        self.assertEqual(summary['summary']['total_transactions'], 1)
    
    def test_get_reward_leaderboard(self):
        """Test getting reward leaderboard"""
        # Create another student
        student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass',
            role='student'
        )
        
        # Create transactions for both students
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('10.00'),
            transaction_type='lesson_reward',
            status='completed'
        )
        
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('5.00'),
            transaction_type='course_completion_bonus',
            status='completed'
        )
        
        BlockchainTransaction.objects.create(
            user=student2,
            amount=Decimal('8.00'),
            transaction_type='lesson_reward',
            status='completed'
        )
        
        leaderboard = reward_service.get_reward_leaderboard(limit=5)
        
        self.assertEqual(len(leaderboard), 2)
        
        # Check first place (student with 15.00 total)
        first_place = leaderboard[0]
        self.assertEqual(first_place['rank'], 1)
        self.assertEqual(first_place['user_id'], self.student.id)
        self.assertEqual(first_place['username'], self.student.username)
        self.assertEqual(first_place['total_rewards'], 15.0)
        self.assertEqual(first_place['reward_count'], 2)
        
        # Check second place (student2 with 8.00 total)
        second_place = leaderboard[1]
        self.assertEqual(second_place['rank'], 2)
        self.assertEqual(second_place['user_id'], student2.id)
        self.assertEqual(second_place['total_rewards'], 8.0)
        self.assertEqual(second_place['reward_count'], 1)
    
    def test_calculate_lesson_reward(self):
        """Test lesson reward calculation"""
        reward = reward_service._calculate_lesson_reward(self.course, self.lesson1)
        expected = Decimal('100.00') * Decimal('0.02')  # 2% of course price
        self.assertEqual(reward, expected)
    
    def test_check_course_completion(self):
        """Test course completion checking"""
        # No completions yet
        self.assertFalse(reward_service._check_course_completion(self.student, self.course))
        
        # Complete first lesson
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        self.assertFalse(reward_service._check_course_completion(self.student, self.course))
        
        # Complete second lesson
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson2
        )
        self.assertTrue(reward_service._check_course_completion(self.student, self.course))
    
    def test_get_user_balance(self):
        """Test getting user balance"""
        balance = reward_service._get_user_balance(self.student)
        self.assertEqual(balance, Decimal('50.00'))
        
        # Test user without balance
        balance = reward_service._get_user_balance(self.teacher)
        self.assertEqual(balance, Decimal('0'))
    
    def test_create_reward_transaction(self):
        """Test creating reward transaction"""
        transaction = reward_service._create_reward_transaction(
            user=self.student,
            amount=Decimal('5.00'),
            transaction_type='test_reward',
            related_object_id='123',
            notes='Test reward transaction'
        )
        
        self.assertEqual(transaction.user, self.student)
        self.assertEqual(transaction.amount, Decimal('5.00'))
        self.assertEqual(transaction.transaction_type, 'test_reward')
        self.assertEqual(transaction.status, 'completed')
        self.assertEqual(transaction.related_object_id, '123')
        self.assertEqual(transaction.notes, 'Test reward transaction')
        self.assertIsNotNone(transaction.transaction_hash)
        self.assertEqual(transaction.from_address, 'reward_pool')
    
    def test_send_reward_notification(self):
        """Test sending reward notification"""
        reward_service._send_reward_notification(
            user=self.student,
            amount=Decimal('5.00'),
            message='Test reward notification',
            notification_type='test_reward'
        )
        
        notification = Notification.objects.get(
            user=self.student,
            notification_type='test_reward'
        )
        self.assertEqual(notification.message, 'Test reward notification')
        self.assertEqual(notification.related_object_id, 5)
