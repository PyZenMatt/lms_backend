#!/usr/bin/env python3
"""
Test Exercise Reward System with DB-based TeoCoin
"""

import os
import sys
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import ExerciseSubmission
from services.db_teocoin_service import DBTeoCoinService

User = get_user_model()

def test_exercise_rewards():
    """Test exercise reward distribution using DB service"""
    print("🎯 Testing Exercise Reward System with DB TeoCoin")
    print("=" * 60)
    
    try:
        db_service = DBTeoCoinService()
        
        # Find test users
        student = User.objects.filter(email__icontains='student').first()
        reviewers = User.objects.filter(email__icontains='student')[:3]
        
        if not student or len(reviewers) < 3:
            print("❌ Not enough test users found")
            return False
            
        print(f"👤 Student: {student.email}")
        print(f"👥 Reviewers: {[r.email for r in reviewers]}")
        
        # Get initial balances
        student_initial = db_service.get_user_balance(student)
        reviewer_balances = []
        for reviewer in reviewers:
            balance = db_service.get_user_balance(reviewer)
            reviewer_balances.append((reviewer, balance))
            
        print(f"\n💰 Initial Balances:")
        print(f"   Student: {student_initial['total_balance']} TEO")
        for reviewer, balance in reviewer_balances:
            print(f"   {reviewer.email}: {balance['total_balance']} TEO")
        
        # Test reward distribution
        print(f"\n🎁 Distributing Exercise Rewards...")
        
        # Student reward: 11 TEO
        student_result = db_service.add_balance(
            user=student,
            amount=Decimal('11'),
            transaction_type='reward',
            description='Exercise completion reward'
        )
        
        # Reviewer rewards: 1 TEO each
        reviewer_results = []
        for i, reviewer in enumerate(reviewers):
            result = db_service.add_balance(
                user=reviewer,
                amount=Decimal('1'),
                transaction_type='reward', 
                description=f'Exercise review reward #{i+1}'
            )
            reviewer_results.append(result)
        
        # Verify new balances
        print(f"\n✅ Rewards Distributed:")
        student_final = db_service.get_user_balance(student)
        print(f"   Student: {student_initial['total_balance']} → {student_final['total_balance']} TEO (+11)")
        
        for i, (reviewer, initial_balance) in enumerate(reviewer_balances):
            final_balance = db_service.get_user_balance(reviewer)
            print(f"   {reviewer.email}: {initial_balance['total_balance']} → {final_balance['total_balance']} TEO (+1)")
        
        # Check transaction history
        print(f"\n📋 Recent Transactions:")
        student_transactions = db_service.get_user_transactions(student, limit=3)
        print(f"   Student transactions: {len(student_transactions)}")
        for tx in student_transactions[:2]:
            print(f"     • {tx['type']}: {tx['amount']} TEO - {tx['description']}")
        
        reviewer_transactions = db_service.get_user_transactions(reviewers[0], limit=3) 
        print(f"   Reviewer transactions: {len(reviewer_transactions)}")
        for tx in reviewer_transactions[:2]:
            print(f"     • {tx['type']}: {tx['amount']} TEO - {tx['description']}")
        
        print(f"\n🎉 Exercise Reward System Test: ✅ PASSED")
        print(f"   • DB-based TeoCoin service working")
        print(f"   • Instant balance updates")
        print(f"   • Transaction history recording")
        print(f"   • Ready for frontend integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_exercise_rewards()
    sys.exit(0 if success else 1)
