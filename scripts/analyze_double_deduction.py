#!/usr/bin/env python3
"""
Simple test to verify double deduction fix by checking transaction patterns
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    exit(1)

from blockchain.models import DBTeoCoinTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

def analyze_double_deduction():
    """Analyze existing transactions for double deduction patterns"""
    
    print("🔍 Analyzing TeoCoin transactions for double deduction patterns...")
    print("=" * 60)
    
    # Look for discount transactions
    discount_transactions = DBTeoCoinTransaction.objects.filter(
        transaction_type='discount',
        amount__lt=0  # Negative = deduction
    ).order_by('-created_at')
    
    print(f"📊 Found {discount_transactions.count()} discount transactions (deductions)")
    
    if discount_transactions.count() == 0:
        print("ℹ️  No discount transactions found")
        return True
    
    # Group by user and course to find duplicates
    user_course_combinations = {}
    
    for tx in discount_transactions:
        key = f"{tx.user.id}_{tx.course_id}"
        if key not in user_course_combinations:
            user_course_combinations[key] = []
        user_course_combinations[key].append(tx)
    
    print(f"📊 Unique user-course combinations: {len(user_course_combinations)}")
    
    # Check for double deductions
    double_deductions_found = False
    
    for key, transactions in user_course_combinations.items():
        user_id, course_id = key.split('_')
        
        if len(transactions) > 1:
            print(f"\n⚠️  POTENTIAL DOUBLE DEDUCTION DETECTED:")
            print(f"   User ID: {user_id}, Course ID: {course_id}")
            print(f"   Number of discount transactions: {len(transactions)}")
            
            total_deducted = sum(abs(tx.amount) for tx in transactions)
            
            for i, tx in enumerate(transactions, 1):
                print(f"   {i}. {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {abs(tx.amount)} TEO - {tx.description}")
            
            print(f"   📉 Total TEO deducted: {total_deducted} TEO")
            double_deductions_found = True
        else:
            user = transactions[0].user
            print(f"✅ User {user.username} (Course {course_id}): Single deduction of {abs(transactions[0].amount)} TEO")
    
    if double_deductions_found:
        print(f"\n❌ DOUBLE DEDUCTION DETECTED!")
        print("The fix needs to be properly deployed.")
        return False
    else:
        print(f"\n✅ NO DOUBLE DEDUCTION FOUND!")
        print("The fix appears to be working correctly.")
        return True

def show_recent_transactions():
    """Show recent transactions for context"""
    print("\n📜 Recent Discount Transactions (last 10):")
    print("-" * 60)
    
    recent = DBTeoCoinTransaction.objects.filter(
        transaction_type='discount'
    ).order_by('-created_at')[:10]
    
    for tx in recent:
        status = "✅" if tx.amount < 0 else "⚠️"
        print(f"{status} {tx.created_at.strftime('%Y-%m-%d %H:%M')} | User: {tx.user.username} | Course: {tx.course_id} | Amount: {tx.amount} TEO")
        print(f"   Description: {tx.description}")

if __name__ == '__main__':
    try:
        success = analyze_double_deduction()
        show_recent_transactions()
        
        if success:
            print("\n🎉 DOUBLE DEDUCTION FIX VERIFICATION: PASSED")
            exit(0)
        else:
            print("\n💥 DOUBLE DEDUCTION FIX VERIFICATION: FAILED")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
