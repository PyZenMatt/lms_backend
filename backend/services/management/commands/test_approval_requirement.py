#!/usr/bin/env python3
"""
Test the approval requirement for TeoCoin discount
"""
import os
import sys
import django

# Setup Django environment  
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.teocoin_discount_service import teocoin_discount_service
from blockchain.blockchain import TeoCoinService
from decimal import Decimal

def test_approval_requirement():
    """Test that shows why approval is needed"""
    try:
        print("🧪 Testing TEO Approval Requirement for Discount Contract")
        print("=" * 60)
        
        # Test parameters
        student_address = "0x742d35Cc6674C5532C5d48C54F4D9f16D5e10b3d"
        course_price = Decimal("99.99")  # EUR
        discount_percent = 10
        
        # Calculate TEO cost
        teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
            course_price, discount_percent
        )
        
        print(f"📚 Course Price: €{course_price}")
        print(f"💰 Discount: {discount_percent}%")
        print(f"🎓 Student: {student_address}")
        print(f"💎 TEO Cost: {teo_cost / 10**18:.4f} TEO ({teo_cost} wei)")
        
        # Get TEO service to check balances
        teo_service = TeoCoinService()
        
        # Check student TEO balance
        try:
            student_balance = teo_service.get_balance(student_address)
            print(f"👤 Student TEO Balance: {student_balance} TEO")
            
            if student_balance >= teo_cost / 10**18:
                print(f"✅ Student has sufficient TEO balance")
            else:
                print(f"❌ Student has insufficient TEO balance")
                
        except Exception as balance_error:
            print(f"⚠️ Could not check student balance: {balance_error}")
        
        # Check allowance
        try:
            discount_contract_address = teocoin_discount_service.discount_contract.address if teocoin_discount_service.discount_contract else "N/A"
            print(f"🏭 Discount Contract: {discount_contract_address}")
            
            if discount_contract_address != "N/A":
                # Try to check allowance (this will show why approval is needed)
                try:
                    allowance = teo_service.teocoin_contract.functions.allowance(
                        student_address, 
                        discount_contract_address
                    ).call()
                    
                    allowance_teo = allowance / 10**18
                    required_teo = teo_cost / 10**18
                    
                    print(f"🔓 Current Allowance: {allowance_teo:.4f} TEO")
                    print(f"🔒 Required Allowance: {required_teo:.4f} TEO")
                    
                    if allowance >= teo_cost:
                        print(f"✅ Sufficient allowance - discount request would succeed")
                        return True
                    else:
                        print(f"❌ INSUFFICIENT ALLOWANCE - this is why the transaction fails!")
                        print(f"💡 Student needs to approve {required_teo:.4f} TEO spending")
                        print(f"🔧 Frontend fix: Add approveTeoCoin() call before createDiscountRequest()")
                        return False
                        
                except Exception as allowance_error:
                    print(f"⚠️ Could not check allowance: {allowance_error}")
            else:
                print(f"⚠️ Discount contract not initialized")
                
        except Exception as contract_error:
            print(f"❌ Contract error: {contract_error}")
        
        print(f"\n💡 SOLUTION:")
        print(f"   1. Frontend calls: approveTeoCoin({teo_cost / 10**18:.4f})")
        print(f"   2. User approves spending in MetaMask")
        print(f"   3. Frontend calls: createDiscountRequest()")
        print(f"   4. Backend successfully executes transferFrom()")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_approval_requirement()
