"""
Core Tests for TeoCoin Discount System - Essential Functionality

Tests the critical components of the discount system:
- TeoCoinDiscountService calculations
- Database model integrity  
- Notification system
- Business logic validation
"""

from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from courses.models import Course, CourseEnrollment
from notifications.models import Notification
from services.teocoin_discount_service import TeoCoinDiscountService
from notifications.services import TeoCoinDiscountNotificationService

User = get_user_model()


class TeoCoinDiscountCalculationTests(TestCase):
    """Test core discount calculations"""
    
    def setUp(self):
        """Set up test service"""
        self.service = TeoCoinDiscountService()
    
    def test_basic_teo_cost_calculation(self):
        """Test basic TEO cost calculations"""
        # Test 10% discount on €100 course
        teo_cost, teacher_bonus = self.service.calculate_teo_cost(
            Decimal('100.00'), 10
        )
        
        # Expected: 10% of €100 = €10 discount
        # €10 * 10 TEO/EUR rate = 100 TEO (in wei: 100 * 10^18)
        # Teacher bonus: 25% of 100 TEO = 25 TEO
        expected_teo_cost = int(100 * 10**18)
        expected_teacher_bonus = int(25 * 10**18)
        
        self.assertEqual(teo_cost, expected_teo_cost)
        self.assertEqual(teacher_bonus, expected_teacher_bonus)
    
    def test_different_discount_percentages(self):
        """Test calculations with different discount percentages"""
        test_cases = [
            (Decimal('50.00'), 5, 25, 6.25),    # €50, 5% = 25 TEO + 6.25 bonus
            (Decimal('200.00'), 15, 300, 75),   # €200, 15% = 300 TEO + 75 bonus
            (Decimal('33.33'), 10, 33.33, 8.3325)  # €33.33, 10% = 33.33 TEO + 8.3325 bonus
        ]
        
        for price, discount_percent, expected_teo, expected_bonus in test_cases:
            teo_cost, teacher_bonus = self.service.calculate_teo_cost(price, discount_percent)
            
            # Convert from wei to TEO for comparison
            teo_amount = teo_cost / 10**18
            bonus_amount = teacher_bonus / 10**18
            
            self.assertAlmostEqual(teo_amount, expected_teo, places=4)
            self.assertAlmostEqual(bonus_amount, expected_bonus, places=4)
    
    def test_discount_validation(self):
        """Test discount percentage validation"""
        # Valid percentages should not raise errors
        valid_discounts = [5, 10, 15]
        for discount in valid_discounts:
            try:
                self.service._validate_discount_request(
                    '0x1234567890123456789012345678901234567890',
                    '0x0987654321098765432109876543210987654321',
                    1,
                    Decimal('100.00'),
                    discount
                )
            except ValueError as e:
                self.fail(f"Valid discount {discount}% should not raise ValueError: {e}")
        
        # Invalid percentages should raise errors
        invalid_discounts = [0, 4, 16, 50]
        for discount in invalid_discounts:
            with self.assertRaises(ValueError):
                self.service._validate_discount_request(
                    '0x1234567890123456789012345678901234567890',
                    '0x0987654321098765432109876543210987654321',
                    1,
                    Decimal('100.00'),
                    discount
                )


class DatabaseModelTests(TestCase):
    """Test database model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com'
        )
        
        self.student = User.objects.create_user(
            username='test_student',
            email='student@test.com'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course for discount system',
            price_eur=Decimal('100.00'),
            teacher=self.teacher,
            is_approved=True
        )
    
    def test_course_enrollment_with_teocoin_discount(self):
        """Test CourseEnrollment with TeoCoin discount fields"""
        # Create enrollment with TeoCoin discount
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            payment_method='teocoin_discount',
            amount_paid_eur=Decimal('90.00'),  # 10% discount applied
            original_price_eur=Decimal('100.00'),
            discount_amount_eur=Decimal('10.00'),
            teocoin_discount_request_id=123
        )
        
        # Verify all TeoCoin discount fields are saved correctly
        self.assertEqual(enrollment.payment_method, 'teocoin_discount')
        self.assertEqual(enrollment.original_price_eur, Decimal('100.00'))
        self.assertEqual(enrollment.discount_amount_eur, Decimal('10.00'))
        self.assertEqual(enrollment.amount_paid_eur, Decimal('90.00'))
        self.assertEqual(enrollment.teocoin_discount_request_id, 123)
    
    def test_payment_method_choices_include_teocoin_discount(self):
        """Test that teocoin_discount is available as payment method"""
        enrollment = CourseEnrollment()
        payment_methods = [choice[0] for choice in enrollment.PAYMENT_METHODS]
        
        # Verify teocoin_discount is in the choices
        self.assertIn('teocoin_discount', payment_methods)
        
        # Verify other expected payment methods are also present
        expected_methods = ['fiat', 'teocoin', 'teocoin_discount', 'free', 'admin']
        for method in expected_methods:
            self.assertIn(method, payment_methods)
    
    def test_course_teacher_relationship(self):
        """Test Course-Teacher relationship works correctly"""
        # Verify teacher can access their courses
        teacher_courses = self.teacher.courses_created.all()
        self.assertIn(self.course, teacher_courses)
        
        # Verify course references correct teacher
        self.assertEqual(self.course.teacher, self.teacher)


class NotificationSystemTests(TestCase):
    """Test notification system functionality"""
    
    def setUp(self):
        """Set up notification test data"""
        self.notification_service = TeoCoinDiscountNotificationService()
        
        self.student = User.objects.create_user(
            username='notif_student',
            email='student@test.com'
        )
        
        self.teacher = User.objects.create_user(
            username='notif_teacher',
            email='teacher@test.com'
        )
    
    def test_teacher_notification_creation(self):
        """Test teacher discount notification creation"""
        expires_at = timezone.now() + timedelta(hours=2)
        
        # Send teacher notification
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
        
        # Verify notification was sent successfully
        self.assertTrue(success)
        
        # Verify notification was created in database
        notification = Notification.objects.filter(
            user=self.teacher,
            notification_type='teocoin_discount_pending',
            related_object_id=1
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('Student notif_student got a 10%', notification.message)
        self.assertIn('Accept TEO: 100.00 TEO + 25.00 bonus', notification.message)
        self.assertIn('Keep EUR: Full EUR commission', notification.message)
    
    def test_student_acceptance_notification(self):
        """Test student notification for teacher TEO acceptance"""
        success = self.notification_service.notify_student_teacher_decision(
            student=self.student,
            teacher=self.teacher,
            course_title='Test Course',
            decision='accepted',
            teo_amount=125.0
        )
        
        self.assertTrue(success)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.student,
            notification_type='teocoin_discount_accepted'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('accepted your 125.00 TEO payment', notification.message)
        self.assertIn('Your discount is confirmed', notification.message)
    
    def test_student_decline_notification(self):
        """Test student notification for teacher EUR choice"""
        success = self.notification_service.notify_student_teacher_decision(
            student=self.student,
            teacher=self.teacher,
            course_title='Test Course',
            decision='declined'
        )
        
        self.assertTrue(success)
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=self.student,
            notification_type='teocoin_discount_rejected'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertIn('chose EUR payment', notification.message)
        self.assertIn('Your discount is still confirmed', notification.message)
        self.assertIn('Your TEO tokens have been returned', notification.message)
    
    def test_timeout_warning_notification(self):
        """Test timeout warning notification"""
        success = self.notification_service.notify_teacher_timeout_warning(
            teacher=self.teacher,
            student=self.student,
            course_title='Test Course',
            request_id=1,
            minutes_remaining=30
        )
        
        self.assertTrue(success)
        
        # Check urgent notification was created
        notification = Notification.objects.filter(
            user=self.teacher,
            notification_type='teocoin_discount_pending',
            related_object_id=1
        ).order_by('-created_at').first()
        
        self.assertIsNotNone(notification)
        self.assertIn('URGENT', notification.message)
        self.assertIn('30 minutes left', notification.message)


class BusinessLogicTests(TestCase):
    """Test business logic calculations"""
    
    def test_platform_economics_scenarios(self):
        """Test platform economics in different scenarios"""
        # Base scenario: €100 course, 50% platform commission, 10% student discount
        original_price = Decimal('100.00')
        platform_commission_rate = Decimal('0.50')  # 50%
        discount_percent = 10
        
        # Calculate base values
        platform_commission = original_price * platform_commission_rate  # €50
        teacher_commission = original_price - platform_commission  # €50
        discount_amount = original_price * discount_percent / 100  # €10
        student_payment = original_price - discount_amount  # €90
        
        # Scenario 1: Teacher accepts TEO
        # Teacher gets: €50 - €10 (absorbed discount) = €40 + TEO tokens
        teacher_eur_with_teo = teacher_commission - discount_amount
        platform_keeps = platform_commission  # Platform doesn't absorb discount
        
        # Scenario 2: Teacher declines TEO (keeps EUR)
        # Teacher gets: €50 (full commission)
        # Platform absorbs: €10 discount cost
        teacher_eur_without_teo = teacher_commission
        platform_with_absorption = platform_commission - discount_amount
        
        # Verify calculations
        self.assertEqual(student_payment, Decimal('90.00'))
        self.assertEqual(discount_amount, Decimal('10.00'))
        self.assertEqual(teacher_eur_with_teo, Decimal('40.00'))
        self.assertEqual(platform_keeps, Decimal('50.00'))
        self.assertEqual(teacher_eur_without_teo, Decimal('50.00'))
        self.assertEqual(platform_with_absorption, Decimal('40.00'))
    
    def test_teo_rate_conversion(self):
        """Test TEO to EUR rate conversion accuracy"""
        # Current rate: 1 TEO = 0.10 EUR discount value (TEO_TO_EUR_RATE = 10)
        service = TeoCoinDiscountService()
        
        test_scenarios = [
            (Decimal('10.00'), 10, 100),    # €10 discount = 100 TEO
            (Decimal('5.00'), 5, 250),      # €5 discount = 50 TEO from €100 course at 5%
            (Decimal('30.00'), 15, 300),    # €30 discount = 300 TEO from €200 course at 15%
        ]
        
        for discount_eur, discount_percent, expected_teo in test_scenarios:
            # Calculate what course price would give us this discount
            course_price = discount_eur * 100 / discount_percent
            
            teo_cost, _ = service.calculate_teo_cost(course_price, discount_percent)
            teo_amount = teo_cost / 10**18  # Convert from wei
            
            self.assertAlmostEqual(teo_amount, expected_teo, places=2)


if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
