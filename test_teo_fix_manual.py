#!/usr/bin/env python3
"""
Manual Test: Validate TEO Discount Webhook Integration Fix

Tests that the webhook now properly calls handle_teocoin_discount_completion
when processing TEO discount payments.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.base')
django.setup()

from unittest.mock import patch, MagicMock
from payments.webhooks import StripeWebhookView
from rewards.models import PaymentDiscountSnapshot
from courses.models import Course
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_webhook_integration():
    """Test that TEO discount completion is properly integrated"""
    
    print("🔍 TESTING R1 FIX: TEO Discount Webhook Integration")
    print("=" * 55)
    
    # Create test data
    try:
        teacher = User.objects.filter(role='teacher').first()
        student = User.objects.filter(role='student').first()
        
        if not teacher:
            # Try to find any user and assume they can be a teacher
            teacher = User.objects.first()
        if not student:
            # Create a test student if none exists
            student = User.objects.exclude(id=teacher.id).first() if teacher else User.objects.first()
            
        course = Course.objects.first()
        
        if not all([teacher, student, course]):
            print("❌ Missing test data (teacher, student, or course)")
            return False
            
        print(f"✅ Test data found:")
        print(f"   Teacher: {teacher.username}")
        print(f"   Student: {student.username}")
        print(f"   Course: {course.title}")
        
        # Create test snapshot
        snapshot = PaymentDiscountSnapshot.objects.create(
            order_id='test_fix_123',
            student=student,
            teacher=teacher,
            course=course,
            price_eur=100,
            student_pay_eur=85,
            discount_percent=15,
            status='applied',
            wallet_hold_id=999,
            stripe_checkout_session_id='cs_test_fix_123',
            stripe_payment_intent_id='pi_test_fix_123'
        )
        print(f"✅ Test snapshot created: {snapshot.id}")
        
        # Test checkout.session.completed webhook
        print("\n🔍 Testing checkout.session.completed webhook...")
        
        webhook_view = StripeWebhookView()
        
        # Mock the external dependencies
        with patch('payments.webhooks.settle_discount_snapshot') as mock_settle, \
             patch('courses.utils.payment_helpers.handle_teocoin_discount_completion') as mock_completion, \
             patch('stripe.Webhook.construct_event') as mock_construct:
            
            # Mock successful settlement
            mock_settle.return_value = True
            
            # Mock successful completion with expected return structure
            mock_completion.return_value = {
                'success': True,
                'enrollment': {
                    'id': 123,
                    'course_title': course.title,
                    'teacher_notification_sent': True
                }
            }
            
            # Create test webhook event
            session_data = {
                'id': 'cs_test_fix_123',
                'payment_intent': 'pi_test_fix_123',
                'metadata': {
                    'teocoin_discount_applied': 'true',
                    'course_id': str(course.id),
                    'user_id': str(student.id),
                    'teocoin_discount_request_id': '789',
                    'payment_type': 'fiat_with_teocoin_discount'
                }
            }
            
            mock_construct.return_value = {
                'id': 'evt_test_fix_123',
                'type': 'checkout.session.completed',
                'data': {'object': session_data}
            }
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.body = b'test_payload'
            mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
            
            # Process webhook
            response = webhook_view.post(mock_request)
            
            # Verify results
            if response.status_code == 200:
                print("✅ Webhook returned 200 OK")
            else:
                print(f"❌ Webhook returned {response.status_code}")
                return False
                
            if mock_settle.called:
                print("✅ settle_discount_snapshot was called")
            else:
                print("❌ settle_discount_snapshot was NOT called")
                return False
                
            if mock_completion.called:
                print("✅ handle_teocoin_discount_completion was called")
                called_with = mock_completion.call_args[0][0]  # First argument
                print(f"   Called with metadata: {called_with}")
                
                # Verify correct metadata was passed
                if called_with.get('teocoin_discount_applied') == 'true':
                    print("✅ Correct TEO discount metadata passed")
                else:
                    print("❌ Incorrect metadata passed")
                    return False
            else:
                print("❌ handle_teocoin_discount_completion was NOT called")
                return False
        
        # Test payment_intent.succeeded webhook
        print("\n🔍 Testing payment_intent.succeeded webhook...")
        
        with patch('payments.webhooks.settle_discount_snapshot') as mock_settle, \
             patch('courses.utils.payment_helpers.handle_teocoin_discount_completion') as mock_completion, \
             patch('stripe.Webhook.construct_event') as mock_construct:
            
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
            
            # Create test webhook event
            payment_intent_data = {
                'id': 'pi_test_fix_123',
                'metadata': {
                    'teocoin_discount_applied': 'true',
                    'course_id': str(course.id),
                    'user_id': str(student.id),
                    'teocoin_discount_request_id': '789'
                }
            }
            
            mock_construct.return_value = {
                'id': 'evt_test_fix_456',
                'type': 'payment_intent.succeeded',
                'data': {'object': payment_intent_data}
            }
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.body = b'test_payload'
            mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
            
            # Process webhook
            response = webhook_view.post(mock_request)
            
            # Verify results
            if response.status_code == 200:
                print("✅ Webhook returned 200 OK")
            else:
                print(f"❌ Webhook returned {response.status_code}")
                return False
                
            if mock_completion.called:
                print("✅ handle_teocoin_discount_completion was called")
            else:
                print("❌ handle_teocoin_discount_completion was NOT called")
                return False
        
        # Test non-TEO discount payment (should not trigger completion)
        print("\n🔍 Testing non-TEO discount payment...")
        
        with patch('payments.webhooks.settle_discount_snapshot') as mock_settle, \
             patch('courses.utils.payment_helpers.handle_teocoin_discount_completion') as mock_completion, \
             patch('stripe.Webhook.construct_event') as mock_construct:
            
            # Mock successful settlement
            mock_settle.return_value = True
            
            # Create test webhook event WITHOUT TEO discount metadata
            session_data = {
                'id': 'cs_test_normal_123',
                'payment_intent': 'pi_test_normal_123',
                'metadata': {
                    'course_id': str(course.id),
                    'user_id': str(student.id),
                    'payment_type': 'card'
                }
            }
            
            mock_construct.return_value = {
                'id': 'evt_test_normal_123',
                'type': 'checkout.session.completed',
                'data': {'object': session_data}
            }
            
            # Create mock request
            mock_request = MagicMock()
            mock_request.body = b'test_payload'
            mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'test_sig'}
            
            # Process webhook
            response = webhook_view.post(mock_request)
            
            # Verify results
            if response.status_code == 200:
                print("✅ Webhook returned 200 OK")
            else:
                print(f"❌ Webhook returned {response.status_code}")
                return False
                
            if mock_settle.called:
                print("✅ settle_discount_snapshot was called")
            else:
                print("❌ settle_discount_snapshot was NOT called")
                return False
                
            if not mock_completion.called:
                print("✅ handle_teocoin_discount_completion was NOT called (correct for non-TEO payment)")
            else:
                print("❌ handle_teocoin_discount_completion was called (should not happen for non-TEO payment)")
                return False
        
        # Cleanup
        snapshot.delete()
        print(f"\n✅ Test snapshot cleaned up")
        
        print("\n🎉 ALL TESTS PASSED - R1 Fix is working correctly!")
        print("📋 Summary:")
        print("   ✅ TEO discount webhooks trigger teacher notification completion")
        print("   ✅ Non-TEO discount webhooks are unaffected")
        print("   ✅ Both checkout.session.completed and payment_intent.succeeded work")
        print("   ✅ Correct metadata is passed to completion handler")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_webhook_integration()
    sys.exit(0 if success else 1)
