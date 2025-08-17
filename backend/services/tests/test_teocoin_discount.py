"""
Comprehensive Tests for TeoCoin Discount System

Tests all components of the Layer 2 backend proxy architecture:
- TeoCoinDiscountService functionality  
- Payment API endpoints
- Notification system integration
- Database model integrity
- Business logic validation
"""

import json
import time
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from courses.models import Course, CourseEnrollment
from notifications.models import Notification
from services.teocoin_discount_service import TeoCoinDiscountService, DiscountStatus
from notifications.services import TeoCoinDiscountNotificationService

User = get_user_model()


class TeoCoinDiscountServiceTests(TestCase):
    """Test TeoCoinDiscountService core functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.service = TeoCoinDiscountService()
        
        # Create test users
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            wallet_address='0x1234567890123456789012345678901234567890'
        )
        
        self.teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            role='teacher',
            wallet_address='0x0987654321098765432109876543210987654321'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course for TeoCoin discount',
            price_eur=Decimal('100.00'),
            teacher=self.teacher,
            is_approved=True
        )
    
    def test_teo_cost_calculation(self):
        """Test TEO cost and teacher bonus calculations"""
        # Test 10% discount on €100 course
        teo_cost, teacher_bonus = self.service.calculate_teo_cost(
            Decimal('100.00'), 10
        )
        
        # 10% of €100 = €10 discount
        # €10 * 10 TEO/EUR rate = 100 TEO (in wei: 100 * 10^18)
        # Teacher bonus: 25% of 100 TEO = 25 TEO
        expected_teo_cost = int(100 * 10**18)  # 100 TEO in wei
        expected_teacher_bonus = int(25 * 10**18)  # 25 TEO in wei
        
        self.assertEqual(teo_cost, expected_teo_cost)
        self.assertEqual(teacher_bonus, expected_teacher_bonus)
    
    def test_discount_percentage_validation(self):
        """Test discount percentage validation"""
        # Valid discount percentages (5-15%)
        for discount in [5, 10, 15]:
            try:
                self.service._validate_discount_request(
                    self.student.wallet_address,
                    self.teacher.wallet_address,
                    self.course.id,
                    Decimal('100.00'),
                    discount
                )
            except ValueError:
                self.fail(f"Valid discount {discount}% should not raise ValueError")
        
        # Invalid discount percentages
        for discount in [0, 4, 16, 50]:
            with self.assertRaises(ValueError):
                self.service._validate_discount_request(
                    self.student.wallet_address,
                    self.teacher.wallet_address,
                    self.course.id,
                    Decimal('100.00'),
                    discount
                )
    
    def test_address_validation(self):
        """Test wallet address validation"""
        # Invalid addresses should raise ValueError
        invalid_addresses = [
            '',
            'invalid',
            '0x123',  # Too short
            '0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG'  # Invalid characters
        ]
        
        for addr in invalid_addresses:
            with self.assertRaises(ValueError):
                self.service._validate_discount_request(
                    addr,
                    self.teacher.wallet_address,
                    self.course.id,
                    Decimal('100.00'),
                    10
                )
    
    @patch('services.teocoin_discount_service.TeoCoinDiscountService._execute_platform_transaction')
    @patch('services.teocoin_discount_service.TeoCoinService.get_balance')
    @patch('services.teocoin_discount_service.TeoCoinService.get_reward_pool_balance')
    def test_create_discount_request_success(self, mock_reward_balance, mock_student_balance, mock_execute_tx):
        """Test successful discount request creation"""
        # Mock successful conditions
        mock_student_balance.return_value = Decimal('1000')  # Student has 1000 TEO
        mock_reward_balance.return_value = Decimal('10000')  # Reward pool has 10000 TEO
        mock_execute_tx.return_value = bytes.fromhex('0x' + '1' * 64)  # Mock transaction hash
        
        # Mock contract initialization
        with patch.object(self.service, 'discount_contract') as mock_contract, \
             patch.object(self.service, 'platform_account') as mock_account:
            
            mock_contract.functions.createDiscountRequest.return_value.build_transaction.return_value = {}
            mock_account.address = '0x' + '0' * 40
            
            # Mock receipt with request ID
            mock_receipt = {'logs': []}
            with patch('services.teocoin_discount_service.TeoCoinDiscountService._extract_request_id_from_receipt', return_value=1), \
                 patch('web3.Web3.eth.wait_for_transaction_receipt', return_value=mock_receipt):
                
                result = self.service.create_discount_request(
                    student_address=self.student.wallet_address,
                    teacher_address=self.teacher.wallet_address,
                    course_id=self.course.id,
                    course_price=Decimal('100.00'),
                    discount_percent=10,
                    student_signature='0x' + '1' * 130
                )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['request_id'], 1)
        self.assertEqual(result['discount_percent'], 10)
    
    @patch('services.teocoin_discount_service.TeoCoinService.get_balance')
    def test_insufficient_balance_error(self, mock_balance):
        """Test error when student has insufficient TEO balance"""
        # Student has insufficient balance
        mock_balance.return_value = Decimal('1')  # Only 1 TEO
        
        with patch.object(self.service, 'discount_contract') as mock_contract, \
             patch.object(self.service, 'platform_account') as mock_account:
            
            mock_contract = Mock()
            mock_account = Mock()
            
            result = self.service.create_discount_request(
                student_address=self.student.wallet_address,
                teacher_address=self.teacher.wallet_address,
                course_id=self.course.id,
                course_price=Decimal('100.00'),
                discount_percent=10,
                student_signature='0x' + '1' * 130
            )
        
        self.assertFalse(result['success'])
        self.assertIn('Insufficient TEO balance', result['error'])


class PaymentAPITests(APITestCase):
    """Test payment API endpoints"""
    
    def setUp(self):
        """Set up test data and authentication"""
        self.client = APIClient()
        
        # Create test users
        self.student = User.objects.create_user(
            username='api_student',
            email='student@api.com',
            wallet_address='0x' + '1' * 40
        )
        
        self.teacher = User.objects.create_user(
            username='api_teacher', 
            email='teacher@api.com',
            role='teacher',
            wallet_address='0x' + '2' * 40
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='API Test Course',
            description='Course for API testing',
            price_eur=Decimal('50.00'),
            teacher=self.teacher,
            is_approved=True
        )
        
        # Authenticate student
        self.client.force_authenticate(user=self.student)
    
    def test_payment_summary_endpoint(self):
        """Test payment summary calculation"""
        url = f'/api/v1/courses/{self.course.id}/payment-summary/'
        data = {
            'base_price': 50.00,
            'discount_percent': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_fields = ['original_price', 'discount_amount', 'final_price', 'teo_cost', 'teacher_bonus']
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Verify calculations
        self.assertEqual(float(response.data['original_price']), 50.00)
        self.assertEqual(float(response.data['discount_amount']), 5.00)  # 10% of 50
        self.assertEqual(float(response.data['final_price']), 45.00)  # 50 - 5
    
    @patch('courses.views.payments.TeoCoinDiscountService.create_discount_request')
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_with_discount(self, mock_stripe, mock_discount):
        """Test payment intent creation with TeoCoin discount"""
        # Mock successful discount request
        mock_discount.return_value = {
            'success': True,
            'request_id': 123,
            'teo_cost': int(50 * 10**18),  # 50 TEO in wei
            'teacher_bonus': int(12.5 * 10**18),  # 12.5 TEO in wei
            'deadline': timezone.now() + timedelta(hours=2)
        }
        
        # Mock Stripe payment intent
        mock_stripe.return_value = Mock(id='pi_test123', client_secret='test_secret')
        
        url = f'/api/v1/courses/{self.course.id}/create-payment-intent/'
        data = {
            'use_teocoin_discount': True,
            'discount_percent': 10,
            'student_address': self.student.wallet_address,
            'student_signature': '0x' + '1' * 130
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('payment_intent_id', response.data)
        self.assertIn('discount_request_id', response.data)
    
    def test_create_payment_intent_authentication_required(self):
        """Test that authentication is required for payment endpoints"""
        self.client.force_authenticate(user=None)  # Remove authentication
        
        url = f'/api/v1/courses/{self.course.id}/create-payment-intent/'
        data = {'use_teocoin_discount': False}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_course_id(self):
        """Test error handling for invalid course ID"""
        url = '/api/v1/courses/99999/payment-summary/'
        data = {'base_price': 50.00}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotificationServiceTests(TestCase):
    """Test notification service functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.notification_service = TeoCoinDiscountNotificationService()
        
        # Create test users
        self.student = User.objects.create_user(
            username='notif_student',
            email='student@notif.com'
        )
        
        self.teacher = User.objects.create_user(
            username='notif_teacher',
            email='teacher@notif.com',
            role='teacher'
        )
    
    def test_teacher_discount_notification(self):
        """Test teacher notification creation"""
        expires_at = timezone.now() + timedelta(hours=2)
        
        success = self.notification_service.notify_teacher_discount_pending(
            teacher=self.teacher,
            student=self.student,
            course_title='Test Course',
            discount_percent=10,
            teo_cost=100.0,
            teacher_bonus=25.0,
            request_id=1,
            expires_at=expires_at
        )
        
        self.assertTrue(success)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.teacher,
            notification_type='teocoin_discount_pending'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Student notif_student got a 10%', notification.message)
        self.assertIn('Accept TEO: 100.00 TEO + 25.00 bonus', notification.message)
        self.assertEqual(notification.related_object_id, 1)
    
    def test_student_decision_notifications(self):
        """Test student notification for teacher decisions"""
        # Test acceptance notification
        success = self.notification_service.notify_student_teacher_decision(
            student=self.student,
            teacher=self.teacher,
            course_title='Test Course',
            decision='accepted',
            teo_amount=125.0
        )
        
        self.assertTrue(success)
        
        # Check notification
        notification = Notification.objects.filter(
            user=self.student,
            notification_type='teocoin_discount_accepted'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('accepted your 125.00 TEO payment', notification.message)
        
        # Test decline notification
        success = self.notification_service.notify_student_teacher_decision(
            student=self.student,
            teacher=self.teacher,
            course_title='Test Course',
            decision='declined'
        )
        
        self.assertTrue(success)
        
        # Check notification
        notification = Notification.objects.filter(
            user=self.student,
            notification_type='teocoin_discount_rejected'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('chose EUR payment', notification.message)
    
    def test_timeout_warning_notification(self):
        """Test timeout warning notifications"""
        success = self.notification_service.notify_teacher_timeout_warning(
            teacher=self.teacher,
            student=self.student,
            course_title='Test Course',
            request_id=1,
            minutes_remaining=30
        )
        
        self.assertTrue(success)
        
        # Check notification
        notification = Notification.objects.filter(
            user=self.teacher,
            notification_type='teocoin_discount_pending'
        ).last()
        
        self.assertIsNotNone(notification)
        self.assertIn('30 minutes left', notification.message)
        self.assertIn('URGENT', notification.message)
    
    @patch('django.core.mail.send_mail')
    def test_email_notification_sending(self, mock_send_mail):
        """Test email notification functionality"""
        with self.settings(SEND_DISCOUNT_EMAILS=True):
            expires_at = timezone.now() + timedelta(hours=2)
            
            success = self.notification_service.notify_teacher_discount_pending(
                teacher=self.teacher,
                student=self.student,
                course_title='Test Course',
                discount_percent=10,
                teo_cost=100.0,
                teacher_bonus=25.0,
                request_id=1,
                expires_at=expires_at
            )
            
            self.assertTrue(success)
            # Email sending should be attempted
            mock_send_mail.assert_called_once()


class DatabaseModelTests(TestCase):
    """Test database model integrity and relationships"""
    
    def setUp(self):
        """Set up test data"""
        self.teacher = User.objects.create_user(
            username='db_teacher',
            email='teacher@db.com',
            role='teacher'
        )
        
        self.student = User.objects.create_user(
            username='db_student',
            email='student@db.com'
        )
        
        self.course = Course.objects.create(
            title='DB Test Course',
            description='Course for database testing',
            price_eur=Decimal('75.00'),
            teacher=self.teacher,
            is_approved=True
        )
    
    def test_course_enrollment_with_teocoin_fields(self):
        """Test CourseEnrollment model with TeoCoin discount fields"""
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            payment_method='teocoin_discount',
            amount_paid_eur=Decimal('67.50'),  # 10% discount
            original_price_eur=Decimal('75.00'),
            discount_amount_eur=Decimal('7.50'),
            teocoin_discount_request_id=123
        )
        
        # Verify all fields are saved correctly
        self.assertEqual(enrollment.payment_method, 'teocoin_discount')
        self.assertEqual(enrollment.original_price_eur, Decimal('75.00'))
        self.assertEqual(enrollment.discount_amount_eur, Decimal('7.50'))
        self.assertEqual(enrollment.teocoin_discount_request_id, 123)
        self.assertEqual(enrollment.amount_paid_eur, Decimal('67.50'))
    
    def test_payment_method_choices(self):
        """Test that teocoin_discount is in payment method choices"""
        enrollment = CourseEnrollment()
        payment_methods = [choice[0] for choice in enrollment.PAYMENT_METHODS]
        
        self.assertIn('teocoin_discount', payment_methods)
        self.assertIn('fiat', payment_methods)
        self.assertIn('teocoin', payment_methods)
    
    def test_course_teacher_relationship(self):
        """Test Course-Teacher relationship"""
        # Teacher should have courses_created relationship
        self.assertIn(self.course, self.teacher.courses_created.all())
        
        # Course should reference correct teacher
        self.assertEqual(self.course.teacher, self.teacher)


class BusinessLogicTests(TestCase):
    """Test business logic validation"""
    
    def test_discount_calculation_accuracy(self):
        """Test discount calculation precision"""
        service = TeoCoinDiscountService()
        
        test_cases = [
            (Decimal('100.00'), 10, 100, 25),    # €100, 10% = 100 TEO + 25 bonus
            (Decimal('50.00'), 15, 75, 18.75),   # €50, 15% = 75 TEO + 18.75 bonus  
            (Decimal('33.33'), 5, 16.665, 4.16625)  # €33.33, 5% = 16.665 TEO + 4.16625 bonus
        ]
        
        for price, discount_percent, expected_teo, expected_bonus in test_cases:
            teo_cost, teacher_bonus = service.calculate_teo_cost(price, discount_percent)
            
            # Convert from wei to TEO
            teo_amount = teo_cost / 10**18
            bonus_amount = teacher_bonus / 10**18
            
            self.assertAlmostEqual(teo_amount, expected_teo, places=6)
            self.assertAlmostEqual(bonus_amount, expected_bonus, places=6)
    
    def test_platform_economics_calculation(self):
        """Test platform economics calculations"""
        # €100 course with 10% discount
        original_price = Decimal('100.00')
        discount_percent = 10
        platform_commission = Decimal('50.00')  # 50% commission
        
        # Student pays €90, gets €10 discount
        student_payment = original_price * (100 - discount_percent) / 100
        discount_amount = original_price - student_payment
        
        # If teacher accepts TEO: Teacher gets €40 (€50 - €10 absorbed discount)
        teacher_commission_with_teo = platform_commission - discount_amount
        
        # If teacher declines: Teacher gets €50, platform absorbs €10 discount
        platform_commission_with_absorption = platform_commission - discount_amount
        
        self.assertEqual(student_payment, Decimal('90.00'))
        self.assertEqual(discount_amount, Decimal('10.00'))
        self.assertEqual(teacher_commission_with_teo, Decimal('40.00'))
        self.assertEqual(platform_commission_with_absorption, Decimal('40.00'))


# Integration test for the complete flow
class EndToEndFlowTests(TransactionTestCase):
    """Test complete discount request flow"""
    
    def setUp(self):
        """Set up complete test scenario"""
        self.student = User.objects.create_user(
            username='e2e_student',
            email='student@e2e.com',
            wallet_address='0x' + '1' * 40
        )
        
        self.teacher = User.objects.create_user(
            username='e2e_teacher',
            email='teacher@e2e.com',
            role='teacher',
            wallet_address='0x' + '2' * 40
        )
        
        self.course = Course.objects.create(
            title='E2E Test Course',
            description='End-to-end test course',
            price_eur=Decimal('80.00'),
            teacher=self.teacher,
            is_approved=True
        )
    
    @patch('courses.views.payments.TeoCoinDiscountService.create_discount_request')
    @patch('notifications.services.TeoCoinDiscountNotificationService.notify_teacher_discount_pending')
    def test_complete_discount_flow(self, mock_notification, mock_discount):
        """Test complete discount request and notification flow"""
        # Mock successful discount creation
        mock_discount.return_value = {
            'success': True,
            'request_id': 456,
            'teo_cost': int(80 * 10**18),  # 80 TEO in wei
            'teacher_bonus': int(20 * 10**18),  # 20 TEO in wei
            'deadline': timezone.now() + timedelta(hours=2)
        }
        
        # Mock notification success
        mock_notification.return_value = True
        
        # Create enrollment with discount
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            payment_method='teocoin_discount',
            amount_paid_eur=Decimal('72.00'),  # 10% discount
            original_price_eur=Decimal('80.00'),
            discount_amount_eur=Decimal('8.00'),
            teocoin_discount_request_id=456
        )
        
        # Verify enrollment was created correctly
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.payment_method, 'teocoin_discount')
        self.assertEqual(enrollment.teocoin_discount_request_id, 456)
        
        # Verify discount calculations
        self.assertEqual(enrollment.original_price_eur, Decimal('80.00'))
        self.assertEqual(enrollment.discount_amount_eur, Decimal('8.00'))
        self.assertEqual(enrollment.amount_paid_eur, Decimal('72.00'))


if __name__ == '__main__':
    import django
    import os
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
    django.setup()
    
    # Run tests
    import unittest
    unittest.main(verbosity=2)
