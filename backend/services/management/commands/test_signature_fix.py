#!/usr/bin/env python3
"""
Quick test for TeoCoin discount signature validation fix
"""
import os
import sys
import django

# Setup Django environment  
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.teocoin_discount_service import teocoin_discount_service
from decimal import Decimal

def test_signature_generation():
    """Test signature generation with corrected token units"""
    try:
        print("🧪 Testing TeoCoin Discount Signature Generation")
        print("=" * 60)
        
        # Test parameters
        student_address = "0x742d35Cc6674C5532C5d48C54F4D9f16D5e10b3d"
        course_id = 123
        course_price = Decimal("99.99")  # EUR
        discount_percent = 10
        
        print(f"📚 Course Price: €{course_price}")
        print(f"💰 Discount: {discount_percent}%")
        print(f"🎓 Student: {student_address}")
        print(f"📖 Course ID: {course_id}")
        
        # Calculate TEO cost
        teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
            course_price, discount_percent
        )
        
        print(f"\n💎 TEO Calculations:")
        print(f"   TEO Cost (wei): {teo_cost}")
        print(f"   TEO Cost (tokens): {teo_cost / 10**18}")
        print(f"   Teacher Bonus (wei): {teacher_bonus}")
        print(f"   Teacher Bonus (tokens): {teacher_bonus / 10**18}")
        
        # Generate signature data
        signature_data = teocoin_discount_service.generate_student_signature_data(
            student_address, course_id, teo_cost
        )
        
        print(f"\n🔏 Signature Data:")
        print(f"   Message Hash: {signature_data.get('message_hash', 'N/A')}")
        print(f"   Signable Message: {signature_data.get('signable_message', 'N/A')}")
        print(f"   TEO Cost (for display): {signature_data.get('teo_cost', 'N/A')}")
        print(f"   TEO Cost (tokens for signature): {signature_data.get('teo_cost_tokens', 'N/A')}")
        
        if 'error' in signature_data:
            print(f"   ❌ Error: {signature_data['error']}")
            return False
        else:
            print(f"   ✅ Signature generation successful!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_decimal_precision():
    """Test that we're using the correct decimal precision for signature"""
    print(f"\n🔢 Testing Decimal Precision:")
    
    # Test edge cases
    test_cases = [
        (Decimal("9.99"), 10),    # €9.99 with 10% discount
        (Decimal("99.99"), 15),   # €99.99 with 15% discount  
        (Decimal("199.00"), 5),   # €199.00 with 5% discount
    ]
    
    for price, discount in test_cases:
        try:
            teo_cost, _ = teocoin_discount_service.calculate_teo_cost(price, discount)
            teo_tokens = teo_cost // 10**18
            
            print(f"   €{price} @ {discount}% → {teo_cost} wei → {teo_tokens} tokens")
            
            # Simulate what smart contract would calculate
            price_cents = int(price * 100)
            discount_value_cents = (price_cents * discount) // 100
            # Smart contract: teoCost = (discountValue * TEO_TO_EUR_RATE * 10**18) / 100
            contract_teo_cost_wei = (discount_value_cents * 10 * 10**18) // 100  # TEO_TO_EUR_RATE = 10
            contract_teo_tokens = contract_teo_cost_wei / 10**18
            
            print(f"     Contract calculation: {price_cents} cents → {discount_value_cents} discount → {contract_teo_cost_wei} wei = {contract_teo_tokens} tokens")
            
            if teo_tokens == contract_teo_tokens:
                print(f"     ✅ Match!")
            else:
                print(f"     ❌ Mismatch! Backend: {teo_tokens}, Contract: {contract_teo_tokens}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 TeoCoin Discount Signature Validation Test")
    print("🔧 Testing the fix for signature validation with correct token units")
    print()
    
    success1 = test_signature_generation()
    test_decimal_precision()
    
    print(f"\n📊 Results:")
    print(f"   Signature Generation: {'✅ PASS' if success1 else '❌ FAIL'}")
    
    if success1:
        print(f"\n🎉 Signature validation fix appears to be working!")
        print(f"💡 The frontend should now be able to create valid signatures")
    else:
        print(f"\n⚠️ Signature validation still has issues")
        
    print(f"\n💡 Next step: Test with frontend to verify signature validation works")
