#!/usr/bin/env python3
"""
Test Script to Verify No Double TeoCoin Deduction
Tests both payment creation and discount application endpoints
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from decimal import Decimal
import json

from courses.models import Course
from blockchain.models import DBTeoCoinTransaction
from services.db_teocoin_service import DBTeoCoinService

User = get_user_model()

def test_no_double_deduction():
    """Test that TEO is not deducted twice when using both endpoints"""
    
    print("🧪 Testing No Double TeoCoin Deduction")
    print("=" * 50)
    
    # Setup test data
    try:
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='testuser',
            email='test@example.com',
            defaults={'password': 'testpass123'}
        )
        if created:
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Create or get test course
        course, created = Course.objects.get_or_create(
            title='Test Course for Double Deduction',
            defaults={
                'description': 'Test course',
                'price_eur': Decimal('100.00'),
                'teocoin_discount_percent': 15
            }
        )
        if created:
            print(f"✅ Created test course: {course.title}")
        else:
            print(f"✅ Using existing test course: {course.title}")
        
        # Setup initial TEO balance
        db_service = DBTeoCoinService()
        
        # Clear any existing transactions for clean test
        DBTeoCoinTransaction.objects.filter(user=user, course_id=str(course.id)).delete()
        print("🧹 Cleared existing test transactions")
        
        # Add initial TEO balance
        initial_balance = Decimal('50.0')
        db_service.add_balance(
            user=user,
            amount=initial_balance,
            transaction_type='test_setup',
            description='Initial balance for double deduction test'
        )
        
        balance_before = db_service.get_user_balance(user)
        print(f"💰 Initial TEO balance: {balance_before['available_balance']} TEO")
        
        # Calculate expected values
        discount_percent = 15
        teo_cost = Decimal('15.0')  # 15% of 100 EUR = 15 EUR = 15 TEO
        expected_balance_after = initial_balance - teo_cost
        
        print(f"🎯 Expected TEO cost: {teo_cost} TEO")
        print(f"🎯 Expected balance after: {expected_balance_after} TEO")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    # Test 1: Create Payment Intent (should NOT deduct TEO)
    print("\n📝 Test 1: CreatePaymentIntentView (should NOT deduct TEO)")
    try:
        client = APIClient()
        client.force_authenticate(user=user)
        
        payment_data = {
            'use_teocoin_discount': True,
            'discount_percent': discount_percent,
            'student_address': '0x123...',
            'student_signature': '0x456...'
        }
        
        response = client.post(
            f'/api/v1/courses/{course.id}/payment/create-intent/',
            data=payment_data,
            format='json'
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 201:
            print("✅ Payment intent created successfully")
            balance_after_payment = db_service.get_user_balance(user)
            print(f"💰 Balance after payment intent: {balance_after_payment['available_balance']} TEO")
            
            if balance_after_payment['available_balance'] == initial_balance:
                print("✅ CORRECT: No TEO deducted by payment intent")
            else:
                print(f"❌ ERROR: TEO was deducted by payment intent! Expected {initial_balance}, got {balance_after_payment['available_balance']}")
                return False
        else:
            print(f"❌ Payment intent failed: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Payment intent test failed: {e}")
        return False
    
    # Test 2: Apply Discount (should deduct TEO once)
    print("\n📝 Test 2: ApplyDiscountView (should deduct TEO once)")
    try:
        discount_data = {
            'course_id': course.id,
            'teo_amount': float(teo_cost),
            'discount_percentage': discount_percent
        }
        
        response = client.post(
            '/api/v1/teocoin/apply-discount/',
            data=discount_data,
            format='json'
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Discount applied successfully")
            balance_after_discount = db_service.get_user_balance(user)
            print(f"💰 Balance after discount: {balance_after_discount['available_balance']} TEO")
            
            if balance_after_discount['available_balance'] == expected_balance_after:
                print("✅ CORRECT: TEO deducted correctly by apply discount")
            else:
                print(f"❌ ERROR: Wrong balance after discount! Expected {expected_balance_after}, got {balance_after_discount['available_balance']}")
                return False
        else:
            print(f"❌ Apply discount failed: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Apply discount test failed: {e}")
        return False
    
    # Test 3: Try to apply discount again (should not deduct again)
    print("\n📝 Test 3: ApplyDiscountView again (should NOT deduct again)")
    try:
        response = client.post(
            '/api/v1/teocoin/apply-discount/',
            data=discount_data,
            format='json'
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            balance_after_second = db_service.get_user_balance(user)
            print(f"💰 Balance after second discount attempt: {balance_after_second['available_balance']} TEO")
            
            if balance_after_second['available_balance'] == expected_balance_after:
                print("✅ CORRECT: No double deduction - balance unchanged")
                if response.data.get('already_applied'):
                    print("✅ CORRECT: API indicated discount was already applied")
                else:
                    print("⚠️  WARNING: API should indicate discount was already applied")
            else:
                print(f"❌ ERROR: Double deduction occurred! Expected {expected_balance_after}, got {balance_after_second['available_balance']}")
                return False
        else:
            print(f"❌ Second discount call failed: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Second discount test failed: {e}")
        return False
    
    # Check transaction history
    print("\n📊 Transaction History Analysis")
    try:
        transactions = DBTeoCoinTransaction.objects.filter(
            user=user,
            course_id=str(course.id)
        ).order_by('created_at')
        
        print(f"📜 Total transactions for course {course.id}: {transactions.count()}")
        
        discount_transactions = [t for t in transactions if t.transaction_type == 'discount' and t.amount < 0]
        print(f"📜 Discount transactions (negative amounts): {len(discount_transactions)}")
        
        for i, tx in enumerate(discount_transactions, 1):
            print(f"  {i}. Amount: {tx.amount} TEO, Description: {tx.description}")
        
        if len(discount_transactions) == 1:
            print("✅ CORRECT: Only one discount transaction found")
        elif len(discount_transactions) == 0:
            print("❌ ERROR: No discount transactions found")
            return False
        else:
            print(f"❌ ERROR: Multiple discount transactions found ({len(discount_transactions)})")
            return False
            
    except Exception as e:
        print(f"❌ Transaction analysis failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED! No double deduction detected.")
    return True

if __name__ == '__main__':
    success = test_no_double_deduction()
    if success:
        print("\n✅ DOUBLE DEDUCTION FIX VERIFIED")
        exit(0)
    else:
        print("\n❌ DOUBLE DEDUCTION STILL EXISTS")
        exit(1)
