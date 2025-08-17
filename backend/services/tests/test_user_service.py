"""
Basic tests for UserService

Quick tests to verify UserService functionality during development.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from services import UserService
from services.exceptions import UserNotFoundError

User = get_user_model()


class UserServiceTestCase(TestCase):
    """Test cases for UserService"""
    
    def setUp(self):
        """Set up test data"""
        self.user_service = UserService()
        
        # Create test users
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        
        self.teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher',
            is_approved=False
        )
    
    def test_get_user_profile_data_student(self):
        """Test getting student profile data"""
        profile_data = self.user_service.get_user_profile_data(self.student)
        
        self.assertEqual(profile_data['username'], 'test_student')
        self.assertEqual(profile_data['email'], 'student@test.com')
        self.assertEqual(profile_data['role'], 'student')
        self.assertIsInstance(profile_data['courses'], list)
    
    def test_get_user_profile_data_teacher(self):
        """Test getting teacher profile data"""
        profile_data = self.user_service.get_user_profile_data(self.teacher)
        
        self.assertEqual(profile_data['username'], 'test_teacher')
        self.assertEqual(profile_data['email'], 'teacher@test.com')
        self.assertEqual(profile_data['role'], 'teacher')
        self.assertIsInstance(profile_data['courses'], list)
    
    def test_get_pending_teachers(self):
        """Test getting pending teachers list"""
        pending_teachers = self.user_service.get_pending_teachers()
        
        self.assertEqual(len(pending_teachers), 1)
        self.assertEqual(pending_teachers[0]['email'], 'teacher@test.com')
        self.assertEqual(pending_teachers[0]['username'], 'test_teacher')
    
    def test_approve_teacher_success(self):
        """Test successful teacher approval"""
        result = self.user_service.approve_teacher(self.teacher.id)
        
        self.assertEqual(result['teacher_id'], self.teacher.id)
        self.assertEqual(result['teacher_email'], 'teacher@test.com')
        
        # Verify teacher is approved in database
        self.teacher.refresh_from_db()
        self.assertTrue(self.teacher.is_approved)
    
    def test_approve_teacher_not_found(self):
        """Test teacher approval with non-existent teacher"""
        with self.assertRaises(UserNotFoundError):
            self.user_service.approve_teacher(99999)
    
    def test_reject_teacher_success(self):
        """Test successful teacher rejection"""
        result = self.user_service.reject_teacher(
            self.teacher.id, 
            reason="Test rejection"
        )
        
        self.assertEqual(result['teacher_id'], self.teacher.id)
        self.assertEqual(result['teacher_email'], 'teacher@test.com')
        self.assertEqual(result['rejection_reason'], "Test rejection")
    
    def test_reject_teacher_not_found(self):
        """Test teacher rejection with non-existent teacher"""
        with self.assertRaises(UserNotFoundError):
            self.user_service.reject_teacher(99999)
