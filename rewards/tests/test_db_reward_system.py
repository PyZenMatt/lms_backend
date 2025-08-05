#!/usr/bin/env python
"""
Test script for the updated exercise reward system using DB-based TeoCoin service
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from services.db_teocoin_service import DBTeoCoinService
from courses.views.exercises import create_reward_transaction

User = get_user_model()

def test_db_reward_system():
    """Test the updated exercise reward system"""
    print("🧪 Testing DB-based Exercise Reward System\n")
    
    try:
        # Get test users
        test_user = User.objects.filter(email__contains='test').first()
        if not test_user:
            test_user = User.objects.first()
        
        if not test_user:
            print("❌ No users found in database")
            return False
        
        print(f"✅ Using test user: {test_user.email}")
        
        # Get initial balance
        db_service = DBTeoCoinService()
        initial_balance = db_service.get_available_balance(test_user)
        print(f"📊 Initial balance: {initial_balance} TEO")
        
        # Test 1: Create exercise reward
        print("\n🎁 Testing exercise reward creation...")
        exercise_reward = create_reward_transaction(
            user=test_user,
            amount=5,
            transaction_type='exercise_reward',
            submission_id=999
        )
        
        if exercise_reward and exercise_reward.success:
            print(f"✅ Exercise reward created: ID {exercise_reward.id}")
            new_balance = db_service.get_available_balance(test_user)
            print(f"📊 New balance: {new_balance} TEO")
            print(f"💰 Balance increased by: {new_balance - initial_balance} TEO")
        else:
            print("❌ Failed to create exercise reward")
            return False
        
        # Test 2: Create review reward
        print("\n👥 Testing review reward creation...")
        review_reward = create_reward_transaction(
            user=test_user,
            amount=1,
            transaction_type='review_reward',
            submission_id=999
        )
        
        if review_reward and review_reward.success:
            print(f"✅ Review reward created: ID {review_reward.id}")
            final_balance = db_service.get_available_balance(test_user)
            print(f"📊 Final balance: {final_balance} TEO")
            print(f"💰 Total increase: {final_balance - initial_balance} TEO")
        else:
            print("❌ Failed to create review reward")
            return False
        
        # Test 3: Check transaction history
        print("\n📜 Checking transaction history...")
        transactions = db_service.get_user_transactions(test_user, limit=5)
        
        print(f"Recent transactions ({len(transactions)}):")
        for tx in transactions[:3]:
            print(f"  - {tx['type']}: {tx['amount']} TEO - {tx['description']}")
        
        print("\n✅ All tests passed! DB-based reward system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Updated Exercise Reward System\n")
    result = test_db_reward_system()
    print(f"\n📊 Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
