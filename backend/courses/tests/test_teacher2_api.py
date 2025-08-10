#!/usr/bin/env python
"""
Test Teacher2 API Endpoint
Simulate the exact frontend API call
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from services.db_teocoin_service import DBTeoCoinService
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_teacher2_api():
    """Test API endpoint for teacher2"""
    
    print("🧪 TESTING TEACHER2 API")
    print("=" * 50)
    
    try:
        # 1. Get teacher2
        username = 'teacher2'
        user = User.objects.get(username=username)
        print(f"✅ Teacher found: {username}")
        
        # 2. Check initial balance
        service = DBTeoCoinService()
        initial_balance_data = service.get_user_balance(user)
        initial_balance = initial_balance_data['available_balance']
        print(f"💰 Initial balance: {initial_balance:.2f} TEO")
        
        # 3. Create authenticated API client
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        print("✅ API client authenticated")
        
        # 4. Test absorption ID 10 (teacher2's pending absorption)
        url = '/api/v1/teocoin/teacher/absorptions/choose/'
        data = {
            'absorption_id': 10,
            'choice': 'absorb'
        }
        
        print(f"📡 Making API call to {url}")
        print(f"📤 Data: {data}")
        
        response = client.post(url, data, format='json')
        print(f"📈 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API call successful!")
            response_data = response.json()
            print(f"📊 Response: {response_data}")
            
            # 5. Check final balance
            final_balance_data = service.get_user_balance(user)
            final_balance = final_balance_data['available_balance']
            balance_increase = final_balance - initial_balance
            
            print(f"💰 Final balance: {final_balance:.2f} TEO")
            print(f"📈 Balance increase: +{balance_increase:.2f} TEO")
            
            if balance_increase > 0:
                print("🎉 SUCCESS! API working for teacher2!")
                return True
            else:
                print("⚠️  No balance increase detected")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_teacher2_api()
    if success:
        print("\n🏆 TEACHER2 API IS WORKING!")
    else:
        print("\n❌ Issues found with teacher2 API")
