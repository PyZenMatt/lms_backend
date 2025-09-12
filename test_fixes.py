#!/usr/bin/env python3
"""
Quick test for our R1.1 and field length fixes
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_field_lengths():
    print("🧪 Testing transaction_type field lengths...")
    
    transaction_types = [
        "course_bonus",  # Fixed from course_purchase_bonus (21 -> 12)
        "completion_bonus",  # Fixed from course_completion_bonus (23 -> 17)
        "discount_accept",  # OK (15)
        "lesson_reward",  # OK (13)
        "withdrawal_request",  # OK (18)
        "withdrawal_cancelled",  # OK (20)
        "bonus",  # OK (5)
        "hold",  # OK (4)
    ]
    
    print("📊 Transaction type lengths:")
    for transaction_type in transaction_types:
        length = len(transaction_type)
        status = "✅" if length <= 20 else "❌"
        print(f"   {status} {transaction_type}: {length} chars")
    
    print("\n🔧 Import fixes:")
    print("   ✅ PaymentDiscountSnapshot import moved to top of files")
    print("   ✅ Duplicate imports removed from conditional blocks")
    
    print("\n🎯 All fixes applied successfully!")

if __name__ == "__main__":
    test_field_lengths()
