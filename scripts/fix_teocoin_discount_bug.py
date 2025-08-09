#!/usr/bin/env python3
"""
Fix TeoCoin Discount Bug: Add saldo deduction to course purchase flow

Bug: When purchasing a course with TeoCoin discount, the discount is applied 
to the price but the student's TeoCoin balance is never decremented.

Solution: Add proper TeoCoin balance deduction in both payment flows.

Usage: python manage.py shell < scripts/fix_teocoin_discount_bug.py
"""

from decimal import Decimal
from services.db_teocoin_service import db_teocoin_service
from django.contrib.auth import get_user_model

User = get_user_model()

def test_deduction_logic():
    """Test the TeoCoin balance deduction logic"""
    print("🧪 Testing TeoCoin balance deduction logic...")
    
    # Create test user if doesn't exist
    test_user, created = User.objects.get_or_create(
        email='test_student@example.com',
        defaults={
            'username': 'test_student',
            'role': 'student',
            'wallet_address': '0x1234567890123456789012345678901234567890'
        }
    )
    
    if created:
        print(f"✅ Created test user: {test_user.email}")
    else:
        print(f"✅ Using existing test user: {test_user.email}")
    
    # Add some balance for testing
    initial_balance = Decimal('100.00')
    db_teocoin_service.add_balance(
        user=test_user,
        amount=initial_balance,
        transaction_type='test_credit',
        description='Test balance for discount bug fix'
    )
    
    balance_before = db_teocoin_service.get_available_balance(test_user)
    print(f"   Balance before: {balance_before} TEO")
    
    # Test discount deduction
    course_price = Decimal('50.00')  # €50 course
    discount_percent = 15  # 15% discount
    discount_amount_eur = course_price * discount_percent / 100  # €7.50
    teo_required = discount_amount_eur  # 1 EUR = 1 TEO for discount
    
    print(f"   Course price: €{course_price}")
    print(f"   Discount: {discount_percent}% = €{discount_amount_eur}")
    print(f"   TEO required: {teo_required} TEO")
    
    # Deduct balance
    success = db_teocoin_service.deduct_balance(
        user=test_user,
        amount=teo_required,
        transaction_type='course_discount',
        description=f'Test discount for €{course_price} course',
        course_id='test_course_123'
    )
    
    balance_after = db_teocoin_service.get_available_balance(test_user)
    expected_balance = balance_before - teo_required
    
    print(f"   Deduction success: {success}")
    print(f"   Balance after: {balance_after} TEO")
    print(f"   Expected balance: {expected_balance} TEO")
    print(f"   Balance correct: {balance_after == expected_balance}")
    
    if success and balance_after == expected_balance:
        print("✅ TeoCoin deduction logic works correctly!")
        return True
    else:
        print("❌ TeoCoin deduction logic failed!")
        return False

def analyze_payment_flows():
    """Analyze the current payment flows to identify where to add deduction"""
    print("\n🔍 Analyzing payment flows...")
    
    print("\n📁 Payment Flow Files:")
    print("   1. services/payment_service.py (legacy system)")
    print("   2. courses/utils/teocoin_discount_payment.py (new system)")
    print("   3. courses/utils/payment_helpers.py (helper functions)")
    
    print("\n🔧 Required Changes:")
    print("   1. Add TeoCoin deduction in payment_service.py when processing TeoCoin discount")
    print("   2. Add TeoCoin deduction in teocoin_discount_payment.py after enrollment")
    print("   3. Ensure deduction happens only once per successful payment")
    print("   4. Add proper error handling and rollback on failure")
    
    print("\n⚠️  Important Considerations:")
    print("   - Deduction should happen AFTER payment confirmation")
    print("   - Must be atomic with enrollment creation")
    print("   - Should handle insufficient balance gracefully")
    print("   - Must prevent double-deduction")

def create_fix_plan():
    """Create a detailed plan to fix the bug"""
    print("\n📋 Fix Implementation Plan:")
    
    print("\n🎯 Step 1: Fix payment_service.py")
    print("   - Locate the TeoCoin discount processing section")
    print("   - Add db_teocoin_service.deduct_balance() call")
    print("   - Wrap in try/catch for error handling")
    print("   - Add transaction ID to enrollment record")
    
    print("\n🎯 Step 2: Fix teocoin_discount_payment.py")
    print("   - Add deduction after successful enrollment creation")
    print("   - Use @transaction.atomic to ensure atomicity")
    print("   - Rollback enrollment if deduction fails")
    
    print("\n🎯 Step 3: Add tests")
    print("   - Test successful discount and deduction")
    print("   - Test insufficient balance handling")
    print("   - Test double-deduction prevention")
    
    print("\n🎯 Step 4: Update enrollment model")
    print("   - Add field to track TeoCoin deduction status")
    print("   - Add TeoCoin transaction reference")

def main():
    """Main function to run the bug fix analysis and test"""
    print("🔥 TeoCoin Discount Bug Fix Script")
    print("=" * 50)
    
    # Test the deduction logic
    test_success = test_deduction_logic()
    
    # Analyze current flows
    analyze_payment_flows()
    
    # Create fix plan
    create_fix_plan()
    
    print("\n" + "=" * 50)
    if test_success:
        print("✅ Ready to implement TeoCoin discount bug fix!")
        print("   The deduction logic works - now we need to integrate it into payment flows")
    else:
        print("❌ TeoCoin deduction logic has issues - fix this first!")
    
    print("\n🚀 Next Steps:")
    print("   1. Review the generated fix plan")
    print("   2. Implement changes in payment flows")
    print("   3. Add comprehensive tests")
    print("   4. Deploy and monitor")

if __name__ == "__main__":
    main()
