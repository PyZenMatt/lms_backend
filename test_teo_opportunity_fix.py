#!/usr/bin/env python3
"""
Test R1 Fix: TEO Discount Opportunity Creation

This test validates that the webhook integration properly triggers
teacher notifications after TEO discount payment completion.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.base')
django.setup()

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from payments.webhooks import StripeWebhookView
from rewards.models import PaymentDiscountSnapshot
from courses.models import Course
import json

User = get_user_model()


class TestTEOOpportunityFix(TestCase):
    """Test that webhook triggers TEO discount completion notifications"""
    
    def setUp(self):
        """Set up test data"""
        self.teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            user_type='teacher'
        )
        self.student = User.objects.create_user(
            username='test_student', 
            email='student@test.com',
            user_type='student'
        )
        self.course = Course.objects.create(
            title='Test Course',
            price_eur=100,
            teacher=self.teacher
        )
        
        # Create test snapshot
        self.snapshot = PaymentDiscountSnapshot.objects.create(
            order_id='test_order_123',
            student=self.student,
            teacher=self.teacher,
            course=self.course,
            price_eur=100,
            student_pay_eur=85,
            discount_percent=15,
            status='applied',
            wallet_hold_id=456,
            stripe_checkout_session_id='cs_test_123',
            stripe_payment_intent_id='pi_test_456'
        )
    
    @patch('payments.webhooks.settle_discount_snapshot')
    @patch('courses.utils.payment_helpers.handle_teocoin_discount_completion')
    def test_teo_discount_completion_triggered_on_checkout_completed(self, mock_completion, mock_settle):
        """Test that TEO discount completion is triggered from checkout.session.completed webhook"""
        
        # Mock successful settlement
        mock_settle.return_value = True
        
        # Mock successful completion
        mock_completion.return_value = {
            'success': True,
            'enrollment': {
                'id': 123,
                'course_title': 'Test Course',
                'teacher_notification_sent': True
            }
        }
        
        # Create webhook view
        webhook_view = StripeWebhookView()
        
        # Create test session data with TEO discount metadata
        session_data = {
            'id': 'cs_test_123',
            'payment_intent': 'pi_test_456',
            'metadata': {
                'teocoin_discount_applied': 'true',
                'course_id': str(self.course.id),
                'user_id': str(self.student.id),
                'teocoin_discount_request_id': '789',
                'payment_type': 'fiat_with_teocoin_discount'
            }
        }
        
        # Call the webhook handler
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = {
                'id': 'evt_test_123',
                'type': 'checkout.session.completed',
                'data': {'object': session_data}
            }
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.body = b'test_payload'
            mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
            
            # Process webhook
            response = webhook_view.post(mock_request)
        
        # Verify settlement was called
        mock_settle.assert_called_once()
        
        # Verify TEO discount completion was called with correct metadata
        mock_completion.assert_called_once_with(session_data['metadata'])
        
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        print("✅ TEST PASSED: TEO discount completion triggered on checkout.session.completed")
    
    @patch('payments.webhooks.settle_discount_snapshot')
    @patch('courses.utils.payment_helpers.handle_teocoin_discount_completion')
    def test_teo_discount_completion_triggered_on_payment_succeeded(self, mock_completion, mock_settle):
        """Test that TEO discount completion is triggered from payment_intent.succeeded webhook"""
        
        # Mock successful settlement
        mock_settle.return_value = True
        
        # Mock successful completion
        mock_completion.return_value = {
            'success': True,
            'enrollment': {
                'id': 123,
                'teacher_notification_sent': True
            }
        }
        
        # Create webhook view
        webhook_view = StripeWebhookView()
        
        # Create test payment intent data with TEO discount metadata
        payment_intent_data = {
            'id': 'pi_test_456',
            'metadata': {
                'teocoin_discount_applied': 'true',
                'course_id': str(self.course.id),
                'user_id': str(self.student.id),
                'teocoin_discount_request_id': '789'
            }
        }
        
        # Call the webhook handler
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = {
                'id': 'evt_test_456',
                'type': 'payment_intent.succeeded',
                'data': {'object': payment_intent_data}
            }
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.body = b'test_payload'
            mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
            
            # Process webhook
            response = webhook_view.post(mock_request)
        
        # Verify settlement was called
        mock_settle.assert_called_once()
        
        # Verify TEO discount completion was called with correct metadata
        mock_completion.assert_called_once_with(payment_intent_data['metadata'])
        
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        print("✅ TEST PASSED: TEO discount completion triggered on payment_intent.succeeded")
    
    @patch('payments.webhooks.settle_discount_snapshot')
    def test_non_teo_discount_payment_not_affected(self, mock_settle):
        """Test that non-TEO discount payments work normally without triggering completion"""
        
        # Mock successful settlement
        mock_settle.return_value = True
        
        # Create webhook view
        webhook_view = StripeWebhookView()
        
        # Create test session data WITHOUT TEO discount metadata
        session_data = {
            'id': 'cs_test_123',
            'payment_intent': 'pi_test_456',
            'metadata': {
                'course_id': str(self.course.id),
                'user_id': str(self.student.id),
                'payment_type': 'card'
            }
        }
        
        with patch('courses.utils.payment_helpers.handle_teocoin_discount_completion') as mock_completion:
            # Call the webhook handler
            with patch('stripe.Webhook.construct_event') as mock_construct:
                mock_construct.return_value = {
                    'id': 'evt_test_123',
                    'type': 'checkout.session.completed',
                    'data': {'object': session_data}
                }
                
                # Create mock request
                mock_request = MagicMock()
                mock_request.body = b'test_payload'
                mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
                
                # Process webhook
                response = webhook_view.post(mock_request)
            
            # Verify settlement was called
            mock_settle.assert_called_once()
            
            # Verify TEO discount completion was NOT called
            mock_completion.assert_not_called()
            
            # Verify successful response
            self.assertEqual(response.status_code, 200)
            print("✅ TEST PASSED: Non-TEO discount payments not affected")


def run_tests():
    """Run the tests"""
    print("🔍 TESTING R1 FIX: TEO Discount Opportunity Creation")
    print("=" * 60)
    
    # Run Django tests
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.test.runner import DiscoverRunner
    from django.conf import settings
    
    setup_test_environment()
    runner = DiscoverRunner(verbosity=2, interactive=False, keepdb=True)
    
    # Run only our specific test
    failures = runner.run_tests(['__main__.TestTEOOpportunityFix'])
    
    teardown_test_environment()
    
    if failures:
        print("❌ TESTS FAILED")
        return False
    else:
        print("✅ ALL TESTS PASSED")
        return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
