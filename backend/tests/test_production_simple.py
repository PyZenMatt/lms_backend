#!/usr/bin/env python3
"""
🚀 SIMPLE PRODUCTION TEST
Test basic functionality in production environment
"""

def test_basic_functionality():
    """Test basic TeoCoin functionality"""
    print("🧪 BASIC PRODUCTION FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Test 1: Import check
    try:
        from services.db_teocoin_service import DBTeoCoinService
        print("✅ 1. DBTeoCoinService import: SUCCESS")
    except Exception as e:
        print(f"❌ 1. DBTeoCoinService import: FAILED - {e}")
        return False
    
    # Test 2: Service initialization
    try:
        db_service = DBTeoCoinService()
        print("✅ 2. Service initialization: SUCCESS")
    except Exception as e:
        print(f"❌ 2. Service initialization: FAILED - {e}")
        return False
    
    # Test 3: Database connectivity
    try:
        from users.models import User
        teacher_count = User.objects.filter(role='teacher').count()
        student_count = User.objects.filter(role='student').count()
        print(f"✅ 3. Database connectivity: SUCCESS")
        print(f"   📊 Teachers: {teacher_count}, Students: {student_count}")
    except Exception as e:
        print(f"❌ 3. Database connectivity: FAILED - {e}")
        return False
    
    # Test 4: Find test teacher
    try:
        teacher = User.objects.filter(role='teacher').first()
        if teacher:
            print(f"✅ 4. Test teacher found: {teacher.username} (ID: {teacher.id})")
        else:
            teacher = User.objects.filter(is_staff=True).first()
            if teacher:
                print(f"✅ 4. Test teacher (staff) found: {teacher.username} (ID: {teacher.id})")
            else:
                print("❌ 4. No test teacher found")
                return False
    except Exception as e:
        print(f"❌ 4. Teacher lookup: FAILED - {e}")
        return False
    
    # Test 5: TeoCoin balance check
    try:
        balance = db_service.get_balance(teacher)
        print(f"✅ 5. Balance check: SUCCESS - {balance} TEO")
    except Exception as e:
        print(f"❌ 5. Balance check: FAILED - {e}")
        return False
    
    # Test 6: TeoCoin credit test
    try:
        from decimal import Decimal
        initial_balance = db_service.get_balance(teacher)
        test_amount = Decimal('1.0')
        
        result = db_service.add_balance(
            teacher, 
            test_amount, 
            'test_production', 
            'Production test credit'
        )
        
        if result:
            new_balance = db_service.get_balance(teacher)
            print(f"✅ 6. TeoCoin credit: SUCCESS")
            print(f"   💰 Balance: {initial_balance} → {new_balance} TEO (+{test_amount})")
        else:
            print("❌ 6. TeoCoin credit: FAILED - add_balance returned False")
            return False
    except Exception as e:
        print(f"❌ 6. TeoCoin credit: FAILED - {e}")
        return False
    
    print("\n🎉 ALL BASIC TESTS PASSED!")
    print("✅ Production TeoCoin system is functional")
    return True

if __name__ == '__main__':
    success = test_basic_functionality()
    exit(0 if success else 1)
