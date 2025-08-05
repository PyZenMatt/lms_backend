#!/usr/bin/env python3
"""
Test script to verify balance APIs are working correctly
"""

import os
import django
import requests
import json

# Setup Django
import sys
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from blockchain.models import DBTeoCoinBalance

def test_balance_apis():
    """Test both balance API endpoints"""
    
    print("🧪 Testing Balance API Endpoints")
    print("=" * 50)
    
    # Get a test user
    test_user = User.objects.first()
    if not test_user:
        print("❌ No users found in database")
        return
    
    print(f"👤 Testing with user: {test_user.email}")
    
    # Check database balance directly
    try:
        balance_obj = DBTeoCoinBalance.objects.get(user=test_user)
        print(f"\n📊 Database Balance:")
        print(f"   Available: {balance_obj.available_balance} TEO")
        print(f"   Pending: {balance_obj.pending_withdrawal} TEO")
        print(f"   Staked: {balance_obj.staked_balance} TEO")
    except DBTeoCoinBalance.DoesNotExist:
        print("❌ No balance record found for user")
        return
    
    # Test old API endpoint
    print(f"\n🔄 Testing OLD API: /api/v1/teocoin/balance/")
    try:
        response = requests.get('http://localhost:8000/api/v1/teocoin/balance/', 
                               headers={'Authorization': 'Bearer fake_token'})
        print(f"   Status: {response.status_code}")
        if response.status_code != 401:  # We expect 401 without real auth
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test new API endpoint
    print(f"\n🔄 Testing NEW API: /api/v1/teocoin/withdrawals/balance/")
    try:
        response = requests.get('http://localhost:8000/api/v1/teocoin/withdrawals/balance/', 
                               headers={'Authorization': 'Bearer fake_token'})
        print(f"   Status: {response.status_code}")
        if response.status_code != 401:  # We expect 401 without real auth
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n✅ Test completed!")
    print(f"💡 Both APIs should return 401 (authentication required)")
    print(f"💡 If you see different responses, there might be endpoint issues")

if __name__ == "__main__":
    test_balance_apis()
