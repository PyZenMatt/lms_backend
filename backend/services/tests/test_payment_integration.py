"""
Integration tests for refactored payment views using PaymentService
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from unittest.mock import patch, MagicMock

from courses.models import Course
from rewards.models import BlockchainTransaction

User = get_user_model()


class PaymentViewsIntegrationTestCase(TestCase):
    """Integration tests for payment views"""
    
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
        
        # Create API client
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Get JWT token for user authentication"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_purchase_course_initiate_success(self, mock_balance):
        """Test course purchase initiation through API"""
        mock_balance.return_value = Decimal('200.00')
        
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request to initiate purchase
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.student.wallet_address,
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertTrue(response.data['payment_required'])
        self.assertEqual(response.data['course_id'], self.course.id)
        self.assertEqual(response.data['course_price'], 100.0)
        self.assertEqual(response.data['teacher_amount'], 85.0)
        self.assertEqual(response.data['commission_amount'], 15.0)
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_purchase_course_insufficient_balance(self, mock_balance):
        """Test course purchase with insufficient balance"""
        mock_balance.return_value = Decimal('50.00')  # Less than course price
        
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.student.wallet_address,
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient TeoCoins', response.data['error'])
    
    @patch('services.payment_service.PaymentService._verify_payment_transaction')
    def test_purchase_course_complete_success(self, mock_verify):
        """Test successful course purchase completion"""
        mock_verify.return_value = True
        
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request to complete purchase
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.student.wallet_address,
            'transaction_hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
            'payment_confirmed': True
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Course purchased successfully', response.data['message'])
        self.assertEqual(response.data['total_paid'], 100.0)
        self.assertEqual(response.data['teacher_received'], 85.0)
        self.assertEqual(response.data['platform_commission'], 15.0)
        self.assertTrue(response.data['enrollment_confirmed'])
        
        # Verify student is enrolled
        self.course.refresh_from_db()
        self.assertIn(self.student, self.course.students.all())
        
        # Verify transactions were recorded
        self.assertTrue(
            BlockchainTransaction.objects.filter(
                transaction_type='course_purchase',
                user=self.student
            ).exists()
        )
    
    def test_purchase_course_missing_wallet(self):
        """Test course purchase without wallet address"""
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request without wallet
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Wallet address is required', response.data['error'])
    
    def test_purchase_course_teacher_cannot_purchase(self):
        """Test that teachers cannot purchase courses"""
        # Authenticate teacher
        token = self.get_jwt_token(self.teacher)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.teacher.wallet_address,
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only students can purchase courses', response.data['error'])
    
    def test_purchase_course_already_enrolled(self):
        """Test purchasing course when already enrolled"""
        # Enroll student first
        self.course.students.add(self.student)
        
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.student.wallet_address,
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already enrolled', response.data['error'])
    
    def test_purchase_course_nonexistent(self):
        """Test purchasing non-existent course"""
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request to non-existent course
        url = reverse('course-purchase', kwargs={'course_id': 99999})
        data = {
            'wallet_address': self.student.wallet_address,
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Course with ID 99999 not found', response.data['error'])
    
    @patch('services.payment_service.PaymentService._verify_payment_transaction')
    def test_purchase_course_verification_failed(self, mock_verify):
        """Test course purchase with failed verification"""
        mock_verify.return_value = False
        
        # Authenticate student
        token = self.get_jwt_token(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': self.student.wallet_address,
            'transaction_hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
            'payment_confirmed': True
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('verification failed', response.data['error'])
    
    def test_purchase_course_unauthenticated(self):
        """Test that purchase requires authentication"""
        # Make request without authentication
        url = reverse('course-purchase', kwargs={'course_id': self.course.id})
        data = {
            'wallet_address': '0x123',
            'payment_confirmed': False
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
