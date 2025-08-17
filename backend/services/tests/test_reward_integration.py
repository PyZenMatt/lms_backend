"""
Integration tests for Reward Service endpoints
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json

from courses.models import Course, Lesson, LessonCompletion
from rewards.models import BlockchainTransaction, TokenBalance
from notifications.models import Notification

User = get_user_model()


class RewardServiceIntegrationTestCase(TestCase):
    """Integration tests for RewardService with actual HTTP endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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
        
        # Create test course with lessons
        self.course = Course.objects.create(
            title='Test Course',
            description='A test course',
            price=Decimal('100.00'),
            teacher=self.teacher,
            is_approved=True
        )
        
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
        
        # Create token balance
        TokenBalance.objects.create(
            user=self.student,
            balance=Decimal('50.00')
        )
        
        # URLs for testing
        self.lesson_complete_url = reverse('rewards:complete-lesson')
        self.rewards_summary_url = reverse('rewards:user-rewards-summary')
        self.leaderboard_url = reverse('rewards:reward-leaderboard')
    
    def test_complete_lesson_reward_endpoint_success(self):
        """Test lesson completion reward through endpoint"""
        self.client.force_authenticate(user=self.student)
        
        data = {
            'lesson_id': self.lesson1.id
        }
        
        response = self.client.post(self.lesson_complete_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertTrue(response_data['reward_processed'])
        self.assertEqual(response_data['lesson_id'], self.lesson1.id)
        self.assertEqual(response_data['course_id'], self.course.id)
        self.assertEqual(response_data['reward_amount'], 2.0)
        self.assertFalse(response_data['course_completed'])
        
        # Verify lesson completion was created
        self.assertTrue(
            LessonCompletion.objects.filter(
                user=self.student,
                lesson=self.lesson1,
                completed=True,
                reward_processed=True
            ).exists()
        )
        
        # Verify transaction was created
        self.assertTrue(
            BlockchainTransaction.objects.filter(
                user=self.student,
                transaction_type='lesson_reward',
                amount=Decimal('2.00'),
                status='completed'
            ).exists()
        )
        
        # Verify notification was sent
        self.assertTrue(
            Notification.objects.filter(
                user=self.student,
                notification_type='lesson_reward'
            ).exists()
        )
    
    def test_complete_lesson_with_course_completion(self):
        """Test lesson completion that triggers course completion bonus"""
        self.client.force_authenticate(user=self.student)
        
        # Complete first lesson
        response1 = self.client.post(self.lesson_complete_url, {
            'lesson_id': self.lesson1.id
        })
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Complete second lesson (should trigger course completion)
        response2 = self.client.post(self.lesson_complete_url, {
            'lesson_id': self.lesson2.id
        })
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        response_data = response2.json()
        
        self.assertTrue(response_data['course_completed'])
        self.assertIn('course_completion_bonus', response_data)
        
        bonus = response_data['course_completion_bonus']
        self.assertEqual(bonus['amount'], 10.0)
        
        # Verify bonus transaction was created
        self.assertTrue(
            BlockchainTransaction.objects.filter(
                user=self.student,
                transaction_type='course_completion_bonus',
                amount=Decimal('10.00'),
                status='completed'
            ).exists()
        )
        
        # Verify bonus notification was sent
        self.assertTrue(
            Notification.objects.filter(
                user=self.student,
                notification_type='course_completion_bonus'
            ).exists()
        )
    
    def test_complete_lesson_unauthenticated(self):
        """Test lesson completion without authentication"""
        data = {'lesson_id': self.lesson1.id}
        response = self.client.post(self.lesson_complete_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_complete_lesson_invalid_lesson(self):
        """Test lesson completion with invalid lesson ID"""
        self.client.force_authenticate(user=self.student)
        
        data = {'lesson_id': 99999}
        response = self.client.post(self.lesson_complete_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('error', response_data)
    
    def test_complete_lesson_not_enrolled(self):
        """Test lesson completion for non-enrolled user"""
        # Create another student not enrolled in course
        other_student = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass',
            role='student'
        )
        
        self.client.force_authenticate(user=other_student)
        
        data = {'lesson_id': self.lesson1.id}
        response = self.client.post(self.lesson_complete_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('User is not enrolled', response_data['error'])
    
    def test_complete_lesson_already_completed(self):
        """Test completing the same lesson twice"""
        self.client.force_authenticate(user=self.student)
        
        data = {'lesson_id': self.lesson1.id}
        
        # Complete lesson first time
        response1 = self.client.post(self.lesson_complete_url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Try to complete again
        response2 = self.client.post(self.lesson_complete_url, data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response2.json()
        self.assertIn('already processed', response_data['error'])
    
    def test_user_rewards_summary_endpoint(self):
        """Test user rewards summary endpoint"""
        self.client.force_authenticate(user=self.student)
        
        # Create some test data
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('5.00'),
            transaction_type='lesson_reward',
            status='completed',
            notes='Test lesson reward'
        )
        
        LessonCompletion.objects.create(
            user=self.student,
            lesson=self.lesson1,
            completed=True,
            reward_processed=True
        )
        
        response = self.client.get(self.rewards_summary_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['user_id'], self.student.id)
        self.assertEqual(response_data['username'], self.student.username)
        self.assertEqual(response_data['time_period'], 'all')
        
        summary = response_data['summary']
        self.assertEqual(summary['total_rewards_earned'], 5.0)
        self.assertEqual(summary['current_balance'], 50.0)
        self.assertEqual(summary['completed_lessons'], 1)
        self.assertEqual(summary['total_transactions'], 1)
        
        self.assertIn('recent_rewards', response_data)
    
    def test_user_rewards_summary_with_time_filter(self):
        """Test user rewards summary with time period filter"""
        self.client.force_authenticate(user=self.student)
        
        # Create test transaction
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('3.00'),
            transaction_type='lesson_reward',
            status='completed'
        )
        
        # Test with week filter
        response = self.client.get(self.rewards_summary_url, {'time_period': 'week'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['time_period'], 'week')
        self.assertEqual(response_data['summary']['total_rewards_earned'], 3.0)
    
    def test_user_rewards_summary_unauthenticated(self):
        """Test rewards summary without authentication"""
        response = self.client.get(self.rewards_summary_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_reward_leaderboard_endpoint(self):
        """Test reward leaderboard endpoint"""
        # Create another student for competition
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
            user=student2,
            amount=Decimal('15.00'),
            transaction_type='lesson_reward',
            status='completed'
        )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.leaderboard_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(len(response_data), 2)
        
        # Check leaderboard order (highest rewards first)
        first_place = response_data[0]
        self.assertEqual(first_place['rank'], 1)
        self.assertEqual(first_place['user_id'], student2.id)
        self.assertEqual(first_place['total_rewards'], 15.0)
        
        second_place = response_data[1]
        self.assertEqual(second_place['rank'], 2)
        self.assertEqual(second_place['user_id'], self.student.id)
        self.assertEqual(second_place['total_rewards'], 10.0)
    
    def test_reward_leaderboard_with_limit(self):
        """Test reward leaderboard with limit parameter"""
        # Create multiple students
        for i in range(5):
            student = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='testpass',
                role='student'
            )
            
            BlockchainTransaction.objects.create(
                user=student,
                amount=Decimal(str(i + 1)),
                transaction_type='lesson_reward',
                status='completed'
            )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.leaderboard_url, {'limit': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Should return only top 3
        self.assertEqual(len(response_data), 3)
        
        # Check that they are in correct order
        self.assertEqual(response_data[0]['total_rewards'], 5.0)  # Highest
        self.assertEqual(response_data[1]['total_rewards'], 4.0)
        self.assertEqual(response_data[2]['total_rewards'], 3.0)
    
    def test_reward_leaderboard_unauthenticated(self):
        """Test leaderboard without authentication"""
        response = self.client.get(self.leaderboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_data_formats(self):
        """Test endpoints with invalid data formats"""
        self.client.force_authenticate(user=self.student)
        
        # Test lesson completion with missing lesson_id
        response = self.client.post(self.lesson_complete_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test lesson completion with invalid lesson_id format
        response = self.client.post(self.lesson_complete_url, {
            'lesson_id': 'invalid'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test rewards summary with invalid time_period
        response = self.client.get(self.rewards_summary_url, {
            'time_period': 'invalid'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test leaderboard with invalid limit
        response = self.client.get(self.leaderboard_url, {
            'limit': 'invalid'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_endpoint_response_formats(self):
        """Test that all endpoints return properly formatted JSON responses"""
        self.client.force_authenticate(user=self.student)
        
        # Test lesson completion response format
        response = self.client.post(self.lesson_complete_url, {
            'lesson_id': self.lesson1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check required fields are present
        required_fields = [
            'reward_processed', 'lesson_id', 'course_id', 'user_id',
            'lesson_title', 'course_title', 'reward_amount', 'course_completed'
        ]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Test rewards summary response format
        response = self.client.get(self.rewards_summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        summary_fields = [
            'user_id', 'username', 'time_period', 'summary', 'recent_rewards'
        ]
        for field in summary_fields:
            self.assertIn(field, data)
        
        # Check summary structure
        summary = data['summary']
        summary_required = [
            'total_rewards_earned', 'lesson_rewards', 'course_completion_bonuses',
            'current_balance', 'completed_lessons', 'completed_courses', 'total_transactions'
        ]
        for field in summary_required:
            self.assertIn(field, summary)
        
        # Test leaderboard response format
        response = self.client.get(self.leaderboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIsInstance(data, list)
        if data:  # If there are entries
            leaderboard_fields = [
                'rank', 'user_id', 'username', 'full_name',
                'total_rewards', 'reward_count'
            ]
            for field in leaderboard_fields:
                self.assertIn(field, data[0])
