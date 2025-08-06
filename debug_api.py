#!/usr/bin/env python
"""
Test script for debugging API endpoints locally
"""
import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from users.models import User
from services.user_service import user_service

def test_pending_teachers():
    """Test the pending teachers endpoint"""
    print("🔍 Testing pending teachers...")
    
    try:
        # Check if there are any pending teachers
        pending_teachers = User.objects.filter(role='teacher', is_approved=False)
        print(f"📊 Raw query result: {pending_teachers.count()} pending teachers")
        
        for teacher in pending_teachers:
            print(f"  - {teacher.email} (ID: {teacher.id})")
        
        # Test the service method
        service_result = user_service.get_pending_teachers()
        print(f"📊 Service result: {len(service_result)} pending teachers")
        
        for teacher_data in service_result:
            print(f"  - {teacher_data.get('email')} (ID: {teacher_data.get('id')})")
            
    except Exception as e:
        print(f"❌ Error testing pending teachers: {e}")
        import traceback
        traceback.print_exc()

def test_pending_withdrawals():
    """Test pending withdrawals for a user"""
    print("\n🔍 Testing pending withdrawals...")
    
    try:
        from blockchain.models import TeoCoinWithdrawalRequest
        
        # Check if there are any pending withdrawals
        pending = TeoCoinWithdrawalRequest.objects.filter(status='pending')
        print(f"📊 Total pending withdrawals: {pending.count()}")
        
        for withdrawal in pending[:5]:  # Show first 5
            print(f"  - User: {withdrawal.user.email}, Amount: {withdrawal.amount}, Status: {withdrawal.status}")
            
    except Exception as e:
        print(f"❌ Error testing pending withdrawals: {e}")
        import traceback
        traceback.print_exc()

def test_wallet_addresses():
    """Test wallet address configuration"""
    print("\n🔍 Testing wallet addresses...")
    
    try:
        from django.conf import settings
        import os
        
        platform_address = getattr(settings, 'PLATFORM_WALLET_ADDRESS', 'NOT_SET')
        private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY', 'NOT_SET')
        
        print(f"📊 PLATFORM_WALLET_ADDRESS from settings: {platform_address}")
        print(f"📊 Environment PLATFORM_WALLET_ADDRESS: {os.getenv('PLATFORM_WALLET_ADDRESS', 'NOT_SET')}")
        print(f"📊 PLATFORM_PRIVATE_KEY configured: {'Yes' if private_key != 'NOT_SET' else 'No'}")
        
        if private_key != 'NOT_SET':
            try:
                from eth_account import Account
                derived_address = Account.from_key(private_key).address
                print(f"📊 Address derived from private key: {derived_address}")
                if derived_address.lower() != platform_address.lower():
                    print(f"⚠️  WARNING: Address mismatch!")
                    print(f"   Config: {platform_address}")
                    print(f"   From key: {derived_address}")
                else:
                    print("✅ Addresses match!")
            except Exception as e:
                print(f"❌ Error deriving address from key: {e}")
        
    except Exception as e:
        print(f"❌ Error testing wallet config: {e}")

if __name__ == '__main__':
    print("🚀 Starting API endpoint tests...\n")
    
    test_pending_teachers()
    test_pending_withdrawals() 
    test_wallet_addresses()
    
    print("\n✅ Tests completed!")
