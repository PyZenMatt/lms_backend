#!/usr/bin/env python3
"""
Test Double Deduction Fix
Testa che la doppia deduzione di TeoCoin sia stata risolta
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')

django.setup()

from blockchain.models import DBTeoCoinTransaction, DBTeoCoinBalance
from users.models import User
from courses.models import Course
from django.test import Client
from django.contrib.auth import authenticate
from decimal import Decimal
import json

print("🧪 TESTING DOUBLE DEDUCTION FIX")
print("=" * 60)

# 1. Setup test data
print("\n1. 📊 Setting up test data")

# Find or create test user
test_user = User.objects.filter(email__icontains='test').first()
if not test_user:
    test_user = User.objects.create_user(
        username='test_double_deduction',
        email='test_double_deduction@test.com',
        password='testpass123',
        role='student'
    )
    print(f"   ✅ Created test user: {test_user.email}")
else:
    print(f"   ✅ Using existing test user: {test_user.email}")

# Find test course
test_course = Course.objects.first()
if not test_course:
    print("   ❌ No courses found for testing")
    exit(1)
print(f"   ✅ Using test course: {test_course.title}")

# Ensure user has sufficient TeoCoin balance
from services.db_teocoin_service import DBTeoCoinService
db_service = DBTeoCoinService()

balance_data = db_service.get_user_balance(test_user)
current_balance = balance_data.get('available_balance', 0)
print(f"   💰 Current balance: {current_balance} TEO")

if current_balance < 50:
    # Add some TeoCoin for testing
    success = db_service.add_balance(
        user=test_user,
        amount=Decimal('100'),
        transaction_type='test_credit',
        description='Test credit for double deduction test'
    )
    if success:
        balance_data = db_service.get_user_balance(test_user)
        current_balance = balance_data.get('available_balance', 0)
        print(f"   ✅ Added test credit, new balance: {current_balance} TEO")

# 2. Check transaction history before test
print(f"\n2. 📋 Transaction History Before Test")
existing_transactions = DBTeoCoinTransaction.objects.filter(
    user=test_user,
    course_id=str(test_course.pk),
    transaction_type='discount'
).count()
print(f"   Existing discount transactions for course {test_course.pk}: {existing_transactions}")

# 3. Test the apply-discount endpoint directly
print(f"\n3. 🔧 Testing apply-discount endpoint")

client = Client()

# Force login using force_login instead of credentials
from django.test import Client as TestClient
client = TestClient()
client.force_login(test_user)
print(f"   ✅ Force logged in as {test_user.username}")

# Test data for discount application
test_discount_data = {
    'course_id': test_course.pk,
    'teo_amount': 15.0,
    'discount_percentage': 15.0
}

print(f"   📤 Applying discount: {test_discount_data}")

# First call to apply-discount
response1 = client.post(
    '/api/v1/teocoin/apply-discount/',
    data=json.dumps(test_discount_data),
    content_type='application/json'
)

print(f"   📥 First call response: {response1.status_code}")
if response1.status_code == 200:
    response1_data = response1.json()
    print(f"      Success: {response1_data.get('success')}")
    print(f"      Message: {response1_data.get('message')}")
    print(f"      TEO used: {response1_data.get('teo_used')}")
    print(f"      New balance: {response1_data.get('new_balance')}")
else:
    print(f"      Error: {response1.content.decode()}")

# Check transactions after first call
transactions_after_first = DBTeoCoinTransaction.objects.filter(
    user=test_user,
    course_id=str(test_course.pk),
    transaction_type='discount'
).count()
print(f"   📊 Discount transactions after first call: {transactions_after_first}")

# Second call to apply-discount (should not deduct again)
print(f"\n   🔄 Making second call (should detect existing discount)...")
response2 = client.post(
    '/api/v1/teocoin/apply-discount/',
    data=json.dumps(test_discount_data),
    content_type='application/json'
)

print(f"   📥 Second call response: {response2.status_code}")
if response2.status_code == 200:
    response2_data = response2.json()
    print(f"      Success: {response2_data.get('success')}")
    print(f"      Message: {response2_data.get('message')}")
    print(f"      Already applied: {response2_data.get('already_applied')}")
    print(f"      TEO used: {response2_data.get('teo_used')}")
    print(f"      New balance: {response2_data.get('new_balance')}")
else:
    print(f"      Error: {response2.content.decode()}")

# Check transactions after second call
transactions_after_second = DBTeoCoinTransaction.objects.filter(
    user=test_user,
    course_id=str(test_course.pk),
    transaction_type='discount'
).count()
print(f"   📊 Discount transactions after second call: {transactions_after_second}")

# 4. Final verification
print(f"\n4. ✅ Results Summary")
print(f"   Transactions before test: {existing_transactions}")
print(f"   Transactions after first call: {transactions_after_first}")
print(f"   Transactions after second call: {transactions_after_second}")

if transactions_after_second == transactions_after_first:
    print(f"   🎉 SUCCESS: No double deduction occurred!")
    print(f"   ✅ Fix is working correctly")
else:
    print(f"   ❌ FAILURE: Double deduction still occurring")
    print(f"   📋 Expected: {transactions_after_first}, Got: {transactions_after_second}")

# Show recent transactions for this course
print(f"\n5. 📋 Recent Discount Transactions for Course {test_course.pk}")
recent_transactions = DBTeoCoinTransaction.objects.filter(
    user=test_user,
    course_id=str(test_course.pk),
    transaction_type='discount'
).order_by('-created_at')[:5]

for tx in recent_transactions:
    print(f"   {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {tx.amount} TEO | {tx.description}")

print(f"\n" + "=" * 60)
print(f"🏁 DOUBLE DEDUCTION TEST COMPLETED")
