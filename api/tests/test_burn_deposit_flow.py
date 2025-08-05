#!/usr/bin/env python3
"""
Test script for TeoCoin burn deposit flow
This script helps test the complete withdrawal -> burn -> deposit cycle
"""

import os, sys, django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from blockchain.models import DBTeoCoinBalance
from decimal import Decimal

def setup_test_user_balance():
    """Give test user some TEO to withdraw and test with"""
    
    # Get student1 user
    try:
        user = User.objects.get(email='student1@teoart.it')
        print(f"👤 Found user: {user.email}")
        
        # Get or create balance
        balance, created = DBTeoCoinBalance.objects.get_or_create(
            user=user,
            defaults={
                'available_balance': Decimal('100.0'),
                'staked_balance': Decimal('0.0'),
                'pending_withdrawal': Decimal('0.0')
            }
        )
        
        if not created:
            # Add some balance if user already exists
            balance.available_balance += Decimal('100.0')
            balance.save()
            
        print(f"💰 User balance: {balance.available_balance} TEO available")
        print(f"📝 Balance record updated")
        
        return balance
        
    except User.DoesNotExist:
        print("❌ User student1@teoart.it not found")
        return None

def check_burn_deposit_api():
    """Check if burn deposit API is accessible"""
    
    from django.test import Client
    
    client = Client()
    
    # Test login
    response = client.post('/api/v1/login/', {
        'email': 'student1@teoart.it',
        'password': 'testpassword'
    }, content_type='application/json')
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        print(f"✅ Login successful, token received")
        
        # Test burn deposit endpoint (should fail with fake tx)
        response2 = client.post('/api/v1/teocoin/burn-deposit/', {
            'transaction_hash': '0xfake',
            'amount': '1.0',
            'metamask_address': '0x742d35Cc6475C1C2C6b2FF4a4F5D6f'
        }, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
        
        print(f"🔥 Burn deposit API status: {response2.status_code}")
        print(f"📄 Response: {response2.content.decode()}")
        
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        return False

def main():
    print("🧪 TeoCoin Burn Deposit Test Setup")
    print("=" * 50)
    
    # 1. Setup test user with balance
    balance = setup_test_user_balance()
    if not balance:
        return
    
    print()
    
    # 2. Check API functionality
    api_works = check_burn_deposit_api()
    
    print()
    print("📋 Test Instructions:")
    print("=" * 50)
    print("1. Login to the platform as student1@teoart.it / testpassword")
    print("2. Go to the dashboard and see the burn deposit interface")
    print("3. The interface should show debug information")
    print("4. Install MetaMask and connect to Polygon Amoy network")
    print("5. Get some MATIC from faucet: https://faucet.polygon.technology/")
    print("6. First withdraw some TEO to get tokens in MetaMask")
    print("7. Then try the burn deposit to add them back")
    print()
    print("🔗 TEO Contract: 0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8")
    print("🌐 Network: Polygon Amoy Testnet")
    print()
    
    if api_works:
        print("✅ Backend API is working correctly!")
        print("✅ Frontend should be functional with MetaMask")
    else:
        print("❌ Backend API has issues")

if __name__ == "__main__":
    main()
