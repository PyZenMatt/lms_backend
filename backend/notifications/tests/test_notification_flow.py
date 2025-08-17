#!/usr/bin/env python
"""
Test the complete TeoCoin discount flow including notifications and teacher absorption
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_complete_flow():
    """Test the entire flow from payment to teacher notification"""
    print("🔍 TESTING COMPLETE TEOCOIN DISCOUNT FLOW")
    print("=" * 60)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course, CourseEnrollment
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from services.db_teocoin_service import DBTeoCoinService
        from rewards.models import TeacherDiscountAbsorption
        from decimal import Decimal
        
        User = get_user_model()
        
        # Find a course with a teacher
        course = Course.objects.filter(teacher__isnull=False).first()
        if not course:
            print("❌ No course with teacher found")
            return
            
        teacher = course.teacher
        print(f"✅ Found course: {course.title}")
        print(f"   Teacher: {teacher.username}")
        print(f"   Price: €{course.price_eur}")
        
        # Find a student with TEO balance
        from blockchain.models import DBTeoCoinBalance
        balance_obj = DBTeoCoinBalance.objects.filter(available_balance__gt=5).first()
        if not balance_obj:
            print("❌ No student with TEO balance found")
            return
            
        student = balance_obj.user
        print(f"✅ Found student: {student.username}")
        print(f"   TEO balance: {balance_obj.available_balance}")
        
        # Test parameters
        discount_percent = 10
        original_price = course.price_eur
        discount_value_eur = original_price * Decimal(discount_percent) / Decimal('100')
        teo_cost = discount_value_eur
        
        print(f"")
        print(f"💰 Payment Details:")
        print(f"   Original price: €{original_price}")
        print(f"   Discount: {discount_percent}%")
        print(f"   TEO cost: {teo_cost} TEO")
        print(f"   Final price: €{original_price - discount_value_eur}")
        
        # Check if student has enough TEO
        if balance_obj.available_balance < teo_cost:
            print(f"❌ Insufficient TEO balance")
            return
            
        print(f"✅ Sufficient TEO balance")
        
        # Step 1: Simulate the payment flow (TEO deduction)
        print(f"")
        print(f"🔄 Step 1: Testing TEO deduction...")
        
        db_service = DBTeoCoinService()
        balance_before = db_service.get_user_balance(student)
        
        success = db_service.deduct_balance(
            user=student,
            amount=teo_cost,
            transaction_type='discount',
            description=f'TeoCoin discount for course: {course.title}',
            course_id=str(course.pk)
        )
        
        if not success:
            print(f"❌ TEO deduction failed")
            return
            
        balance_after = db_service.get_user_balance(student)
        teo_deducted = balance_before['available_balance'] - balance_after['available_balance']
        print(f"✅ TEO deducted: {teo_deducted} TEO")
        
        # Step 2: Create absorption opportunity (this should trigger notifications)
        print(f"🔄 Step 2: Creating absorption opportunity...")
        
        absorption_count_before = TeacherDiscountAbsorption.objects.count()
        
        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data={
                'discount_percentage': discount_percent,
                'teo_used': float(teo_cost),
                'discount_amount_eur': float(discount_value_eur),
                'course_price_eur': float(original_price)
            }
        )
        
        absorption_count_after = TeacherDiscountAbsorption.objects.count()
        
        print(f"✅ Absorption opportunity created:")
        print(f"   ID: {absorption.pk}")
        print(f"   Status: {absorption.status}")
        print(f"   Total absorptions: {absorption_count_before} → {absorption_count_after}")
        print(f"   Teacher TEO option: {absorption.option_b_teacher_teo} TEO")
        print(f"   Teacher EUR option: €{absorption.option_a_teacher_eur}")
        print(f"   Expires: {absorption.expires_at}")
        
        # Step 3: Check if course enrollment exists (for frontend display)
        print(f"🔄 Step 3: Checking course enrollment...")
        
        enrollment = CourseEnrollment.objects.filter(
            student=student,
            course=course
        ).first()
        
        if enrollment:
            print(f"✅ Enrollment exists:")
            print(f"   Payment method: {enrollment.payment_method}")
            print(f"   Enrolled at: {enrollment.enrolled_at}")
        else:
            print(f"⚠️  No enrollment found - this might be why course shows as not purchased")
            
            # Create enrollment for testing
            enrollment = CourseEnrollment.objects.create(
                student=student,
                course=course,
                payment_method='teocoin_discount',
                amount_paid_eur=original_price - discount_value_eur,
                amount_paid_teocoin=teo_cost,
                original_price_eur=original_price,
                discount_amount_eur=discount_value_eur
            )
            print(f"✅ Created enrollment for testing")
        
        # Step 4: Test notification system (check what should notify teacher)
        print(f"🔄 Step 4: Testing notification system...")
        
        # Check if teacher has pending absorptions
        pending_absorptions = TeacherDiscountAbsorption.objects.filter(
            teacher=teacher,
            status='pending'
        )
        
        print(f"✅ Teacher pending absorptions: {pending_absorptions.count()}")
        
        for abs_obj in pending_absorptions:
            print(f"   - ID {abs_obj.pk}: {abs_obj.course.title} ({abs_obj.hours_remaining:.1f}h remaining)")
        
        # Step 5: Test teacher dashboard API endpoints
        print(f"🔄 Step 5: Testing teacher dashboard API...")
        
        # This is what the frontend calls to get absorption opportunities
        from api.teacher_absorption_views import TeacherPendingAbsorptionsView
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth import get_user_model
        
        factory = APIRequestFactory()
        request = factory.get('/api/v1/teocoin/teacher/absorptions/')
        request.user = teacher
        
        view = TeacherPendingAbsorptionsView()
        response = view.get(request)
        
        if response.status_code == 200:
            data = response.data if hasattr(response, 'data') else {}
            print(f"✅ Teacher dashboard API works:")
            print(f"   Pending absorptions: {len(data.get('pending_absorptions', []))}")
            
            for absorption in data.get('pending_absorptions', [])[:3]:  # Show first 3
                print(f"   - Course: {absorption.get('course', {}).get('title')}")
                print(f"     TEO option: {absorption.get('options', {}).get('option_b', {}).get('teacher_teo')} TEO")
                print(f"     Time remaining: {absorption.get('timing', {}).get('hours_remaining')}h")
        else:
            print(f"❌ Teacher dashboard API failed: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   Error: {response.data}")
        
        print(f"")
        print(f"🎯 FLOW TEST SUMMARY:")
        print(f"✅ TEO deduction: Working")
        print(f"✅ Absorption creation: Working") 
        print(f"✅ Database storage: Working")
        print(f"✅ Teacher API: {'Working' if response.status_code == 200 else 'Failed'}")
        print(f"")
        print(f"📋 NEXT: Check frontend notification display")
        
        return True
        
    except Exception as e:
        print(f"❌ Flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_frontend_api_endpoints():
    """Check all API endpoints the frontend uses"""
    print(f"")
    print(f"🔍 CHECKING FRONTEND API ENDPOINTS")
    print(f"=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIRequestFactory
        
        User = get_user_model()
        teacher = User.objects.filter(is_staff=True).first()
        
        if not teacher:
            print("❌ No teacher found for API testing")
            return False
            
        factory = APIRequestFactory()
        
        # Test the main endpoints the frontend calls
        endpoints_to_test = [
            ('/api/v1/teocoin/teacher/absorptions/', 'TeacherPendingAbsorptionsView'),
            ('/api/v1/teocoin/balance/', 'TeoCoinBalanceView'),
            ('/api/v1/teocoin/transactions/', 'TransactionHistoryView'),
            ('/api/v1/teocoin/statistics/', 'PlatformStatisticsView'),
        ]
        
        print(f"Testing API endpoints for teacher: {teacher.username}")
        
        all_working = True
        
        for endpoint, view_name in endpoints_to_test:
            print(f"")
            print(f"🔧 Testing {endpoint}...")
            
            try:
                request = factory.get(endpoint)
                request.user = teacher
                
                # Import and test the view
                if 'absorptions' in endpoint:
                    from api.teacher_absorption_views import TeacherPendingAbsorptionsView
                    view = TeacherPendingAbsorptionsView()
                elif 'balance' in endpoint:
                    from api.db_teocoin_views import TeoCoinBalanceView
                    view = TeoCoinBalanceView()
                elif 'transactions' in endpoint:
                    from api.db_teocoin_views import TransactionHistoryView
                    view = TransactionHistoryView()
                elif 'statistics' in endpoint:
                    from api.db_teocoin_views import PlatformStatisticsView
                    view = PlatformStatisticsView()
                
                response = view.get(request)
                
                if response.status_code == 200:
                    print(f"✅ {view_name}: Working ({response.status_code})")
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        data = response.data
                        if 'pending_absorptions' in data:
                            print(f"   Pending absorptions: {len(data['pending_absorptions'])}")
                        elif 'available_balance' in data:
                            print(f"   Balance: {data['available_balance']}")
                        elif 'transactions' in data:
                            print(f"   Transactions: {len(data['transactions'])}")
                else:
                    print(f"❌ {view_name}: Failed ({response.status_code})")
                    if hasattr(response, 'data'):
                        print(f"   Error: {response.data}")
                    all_working = False
                        
            except Exception as e:
                print(f"❌ {view_name}: Exception - {e}")
                all_working = False
        
        return all_working
        
    except Exception as e:
        print(f"❌ API endpoint testing failed: {e}")
        return False

def check_notification_system():
    """Check if notification system is properly configured"""
    print(f"")
    print(f"🔍 CHECKING NOTIFICATION SYSTEM")
    print(f"=" * 50)
    
    try:
        # Check if notifications model works
        from notifications.models import Notification
        notification_count = Notification.objects.count()
        print(f"✅ Notifications model accessible, total notifications: {notification_count}")
        
        # Check if notification service works
        from notifications.services import teocoin_notification_service
        print(f"✅ TeoCoin notification service accessible")
        
        # Test notification creation with a teacher
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        teacher = User.objects.filter(is_staff=True).first()
        
        if teacher:
            try:
                # Test notification creation
                initial_count = Notification.objects.filter(user=teacher).count()
                
                test_notification = Notification.objects.create(
                    user=teacher,
                    message='Test notification for system check',
                    notification_type='system_message'
                )
                
                final_count = Notification.objects.filter(user=teacher).count()
                
                print(f"✅ Test notification created successfully")
                print(f"   Teacher notifications: {initial_count} → {final_count}")
                
                # Clean up test notification
                test_notification.delete()
                
            except Exception as e:
                print(f"❌ Notification creation failed: {e}")
                return False
        else:
            print(f"⚠️  No teacher found for notification testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Complete TeoCoin Flow with Notifications...")
    
    flow_ok = test_complete_flow()
    api_ok = check_frontend_api_endpoints()
    notification_ok = check_notification_system()
    
    print("\n" + "=" * 60)
    if flow_ok and api_ok and notification_ok:
        print("🎉 ALL TESTS PASSED!")
        print("📝 Complete flow is working")
    else:
        print("❌ Some issues found:")
        print(f"   Payment flow: {'✅' if flow_ok else '❌'}")
        print(f"   API endpoints: {'✅' if api_ok else '❌'}")
        print(f"   Notification system: {'✅' if notification_ok else '❌'}")
