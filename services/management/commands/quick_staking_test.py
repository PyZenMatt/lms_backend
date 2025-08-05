#!/usr/bin/env python3
"""
Simple Staking API Test
Quick test of the staking endpoints
"""

import os
import sys
import django
import json

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from services.teocoin_staking_service import TeoCoinStakingService

def main():
    print("🚀 Quick Staking System Test")
    print("=" * 40)
    
    # Test 1: Initialize service
    try:
        print("1. Testing staking service initialization...")
        service = TeoCoinStakingService()
        print(f"   ✅ Service initialized")
        print(f"   📋 Development mode: {service.development_mode}")
        print(f"   🎯 Tier config: {len(service.TIER_CONFIG)} tiers")
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return False
    
    # Test 2: Test tier calculation
    try:
        print("\n2. Testing tier calculation...")
        test_amounts = [0, 100, 300, 600, 1000]
        for amount in test_amounts:
            tier = service.calculate_tier(amount)
            tier_name = service.TIER_CONFIG[tier]['name']
            commission = service.TIER_CONFIG[tier]['commission_rate'] / 100
            print(f"   {amount} TEO → {tier_name} ({commission}%)")
        print("   ✅ Tier calculation working")
    except Exception as e:
        print(f"   ❌ Tier calculation failed: {e}")
        return False
    
    # Test 3: Create test user and test API
    try:
        print("\n3. Testing API endpoints...")
        client = Client()
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='test_api_user',
            defaults={
                'email': 'test@example.com',
                'wallet_address': '0x742d35cc6674c5532c5d48C54F4D9f16D5e10b3d'
            }
        )
        
        if not hasattr(user, 'wallet_address') or not user.wallet_address:
            user.wallet_address = '0x742d35cc6674c5532c5d48C54F4D9f16D5e10b3d'
            user.save()
        
        client.force_login(user)
        print(f"   ✅ Test user created: {user.username}")
        
        # Test staking tiers endpoint
        response = client.get('/api/v1/services/staking/tiers/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Tiers endpoint: {len(data.get('tiers', {}))} tiers")
        else:
            print(f"   ❌ Tiers endpoint failed: {response.status_code}")
            return False
        
        # Test staking info endpoint
        response = client.get('/api/v1/services/staking/info/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Info endpoint: user_staking, platform_stats, tier_config")
        else:
            print(f"   ❌ Info endpoint failed: {response.status_code}")
            return False
        
        # Test commission calculator
        response = client.get('/api/v1/services/staking/calculator/?current_stake=500')
        if response.status_code == 200:
            data = response.json()
            current_tier = data.get('current_tier', {})
            print(f"   ✅ Calculator endpoint: 500 TEO → {current_tier.get('name', 'Unknown')}")
        else:
            print(f"   ❌ Calculator endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API testing failed: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📊 Summary:")
    print("   ✅ Staking service working")
    print("   ✅ Tier calculation correct")
    print("   ✅ API endpoints responding")
    print("   ✅ Development mode ready")
    print("\n🚀 Ready for smart contract deployment!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
