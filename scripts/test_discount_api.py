#!/usr/bin/env python3
"""
Test API TeoCoin apply-discount endpoint
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from services.db_teocoin_service import DBTeoCoinService
from decimal import Decimal

def test_apply_discount():
    """Test the TeoCoin discount functionality"""
    
    print("🧪 Test TeoCoin Apply Discount")
    print("=" * 50)
    
    User = get_user_model()
    
    # 1. Get or create a test user
    try:
        test_user = User.objects.filter(role='student').first()
        if not test_user:
            print("❌ No student user found for testing")
            return
        
        print(f"✅ Using test user: {test_user.username} ({test_user.email})")
        
        # 2. Check current balance
        db_service = DBTeoCoinService()
        balance = db_service.get_user_balance(test_user)
        print(f"📊 Current balance: {balance}")
        
        # 3. Add some balance if needed
        if balance['available_balance'] < Decimal('10'):
            print("💰 Adding test balance...")
            db_service.add_balance(
                user=test_user,
                amount=Decimal('100'),
                transaction_type='test',
                description='Test balance for discount'
            )
            balance = db_service.get_user_balance(test_user)
            print(f"📊 New balance: {balance}")
        
        # 4. Recupera un corso esistente
        from courses.models import Course
        test_course = Course.objects.first()
        if not test_course:
            print("❌ No course found for testing")
            return
        test_course_price = test_course.price_eur
        print(f"📝 Using test course: {test_course.title} (ID: {test_course.pk}) - Price: €{test_course_price}")

        # 5. Test discount calculation
        discount_info = db_service.calculate_discount(
            user=test_user,
            course_price=test_course_price
        )
        print(f"🎯 Discount calculation for €{test_course_price}: {discount_info}")

        # 6. Test applying discount
        if discount_info['can_apply_discount']:
            print(f"💳 Attempting to apply discount...")
            success = db_service.deduct_balance(
                user=test_user,
                amount=discount_info['teo_required'],
                transaction_type='discount',
                description='Test discount application',
                course_id=str(test_course.pk)
            )
            if success:
                print("✅ Discount applied successfully!")
                final_balance = db_service.get_user_balance(test_user)
                print(f"📊 Final balance: {final_balance}")
            else:
                print("❌ Failed to apply discount")
        else:
            print("⚠️ Cannot apply discount with current balance")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        print(f"❌ Error during test: {e}")
        import traceback
        try:
            test_user = User.objects.filter(role='student').first()
            if not test_user:
                print("❌ No student user found for testing")
                return
            print(f"✅ Using test user: {test_user.username} ({test_user.email})")

            # 2. Check current balance
            db_service = DBTeoCoinService()
            balance = db_service.get_user_balance(test_user)
            print(f"📊 Current balance: {balance}")

            # 3. Add some balance if needed
            if balance['available_balance'] < Decimal('10'):
                print("💰 Adding test balance...")
                db_service.add_balance(
                    user=test_user,
                    amount=Decimal('100'),
                    transaction_type='test',
                    description='Test balance for discount'
                )
                balance = db_service.get_user_balance(test_user)
                print(f"📊 New balance: {balance}")

            # 4. Recupera un corso esistente
            from courses.models import Course
            test_course = Course.objects.first()
            if not test_course:
                print("❌ No course found for testing")
                return
            test_course_price = test_course.price_eur
            print(f"📝 Using test course: {test_course.title} (ID: {test_course.pk}) - Price: €{test_course_price}")

            # 5. Test discount calculation
            discount_info = db_service.calculate_discount(
                user=test_user,
                course_price=test_course_price
            )
            print(f"🎯 Discount calculation for €{test_course_price}: {discount_info}")

            # 6. Test applying discount
            if discount_info['can_apply_discount']:
                print(f"💳 Attempting to apply discount...")
                success = db_service.deduct_balance(
                    user=test_user,
                    amount=discount_info['teo_required'],
                    transaction_type='discount',
                    description='Test discount application',
                    course_id=str(test_course.pk)
                )
                if success:
                    print("✅ Discount applied successfully!")
                    final_balance = db_service.get_user_balance(test_user)
                    print(f"📊 Final balance: {final_balance}")
                else:
                    print("❌ Failed to apply discount")
            else:
                print("⚠️ Cannot apply discount with current balance")

        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
