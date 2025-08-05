#!/usr/bin/env python
"""
Simple test of burn deposit API without blockchain verification
"""

import os
import sys
import django
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()

def test_burn_deposit_api_simple():
    """Test burn deposit API with mock verification"""
    print("🧪 Testing burn deposit API with actual client...")
    
    try:
        # Get a test user
        user = User.objects.filter(email__contains='test').first()
        if not user:
            user = User.objects.first()
        
        if not user:
            print("❌ No users found")
            return False
        
        print(f"✅ Using user: {user.email}")
        
        # Create Django test client
        client = Client()
        
        # Login as the user (simulate authentication)
        client.force_login(user)
        
        # Test data
        test_data = {
            'transaction_hash': '0xfaketest123456789',
            'amount': '15.50',
            'metamask_address': '0x742d35Cc6634C0532925a3b8d4017d6e2b3D7567'
        }
        
        print(f"📡 Sending request to burn deposit API...")
        print(f"📄 Data: {test_data}")
        
        # Make the API call
        response = client.post(
            '/api/v1/teocoin/burn-deposit/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response content: {response.content.decode()}")
        
        # Parse response
        try:
            response_data = json.loads(response.content.decode())
            print(f"📋 Parsed response: {response_data}")
        except:
            print("❌ Could not parse JSON response")
            return False
        
        # We expect this to fail at verification (fake hash), but should see the error
        if response.status_code == 400:
            if 'Transaction not found' in str(response_data.get('error', '')):
                print("✅ API reached verification step (expected failure with fake hash)")
                return True
            else:
                print(f"❌ Unexpected verification error: {response_data.get('error')}")
                return False
        elif response.status_code == 500:
            print(f"❌ Server error: {response_data.get('error')}")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Burn Deposit API\n")
    result = test_burn_deposit_api_simple()
    print(f"\n📊 Result: {'✅ PASS' if result else '❌ FAIL'}")
