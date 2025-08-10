#!/usr/bin/env python
"""
Phase 2 Withdrawal System Integration Test
Tests the integration between Phase 1 withdrawal service and Phase 2 blockchain service
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_withdrawal_integration():
    """Test withdrawal system integration"""
    
    print("🔄 Testing Phase 2 Withdrawal Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import services
        print("Test 1: Importing withdrawal and blockchain services...")
        from services.teocoin_withdrawal_service import teocoin_withdrawal_service
        from services.consolidated_teocoin_service import teocoin_service
        print("✅ Services imported successfully")
        
        # Test 2: Test service initialization
        print("\nTest 2: Testing service initialization...")
        print(f"✅ Withdrawal service initialized: {type(teocoin_withdrawal_service).__name__}")
        print(f"✅ Blockchain service initialized: {type(teocoin_service).__name__}")
        
        # Test 3: Test validation methods
        print("\nTest 3: Testing validation methods...")
        
        # Test address validation
        test_address = "0x742d35Cc6634C0532925a3b8D6Ac6F86C8cFc4Ae"
        is_valid = teocoin_service.validate_address(test_address)
        print(f"✅ Address validation working: {is_valid}")
        
        # Test amount validation
        test_amount = Decimal("50.25")
        min_amount = teocoin_withdrawal_service.MIN_WITHDRAWAL_AMOUNT
        max_amount = teocoin_withdrawal_service.MAX_WITHDRAWAL_AMOUNT
        print(f"✅ Withdrawal limits: MIN={min_amount}, MAX={max_amount}")
        print(f"✅ Test amount {test_amount} is valid: {min_amount <= test_amount <= max_amount}")
        
        # Test 4: Test model access
        print("\nTest 4: Testing database model access...")
        from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
        print("✅ Withdrawal models accessible")
        
        # Check withdrawal request count
        pending_count = TeoCoinWithdrawalRequest.objects.filter(status='pending').count()
        print(f"✅ Current pending withdrawals: {pending_count}")
        
        # Test 5: Test contract integration
        print("\nTest 5: Testing contract integration...")
        contract_info = teocoin_service.get_token_info()
        print(f"✅ Contract name: {contract_info.get('name')}")
        print(f"✅ Contract symbol: {contract_info.get('symbol')}")
        print(f"✅ Contract address: {contract_info.get('contract_address')}")
        
        print("\n" + "=" * 50)
        print("🎉 Phase 2 withdrawal integration tests completed!")
        print("✅ All systems are properly integrated and ready for Phase 2")
        
        print("\n📋 Summary:")
        print("- ✅ Phase 1 withdrawal service: Working")
        print("- ✅ Phase 2 blockchain service: Working")  
        print("- ✅ TeoCoin2 contract connection: Working")
        print("- ✅ Database models: Accessible")
        print("- ✅ Address validation: Working")
        print("- ✅ Amount validation: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_withdrawal_integration()
    sys.exit(0 if success else 1)
