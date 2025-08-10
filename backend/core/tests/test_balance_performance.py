"""
Test script to verify blockchain balance performance optimizations.

This script makes multiple balance requests to demonstrate the difference
between uncached (first call) and cached (subsequent calls) balance queries.
"""

import requests
import time
import sys
import os
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.contrib.auth.models import User

User = get_user_model()

def test_balance_performance():
    """Test balance endpoint performance with multiple calls"""
    # Get a test user with a wallet
    user = User.objects.filter(wallet_address__isnull=False).first()
    
    if not user:
        print("No users with wallet found. Please link a wallet first.")
        return
    
    print(f"Testing with user: {user.username}")
    
    # Create API client and authenticate
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Make multiple requests to test caching
    print("\nMaking balance requests to test caching...")
    
    for i in range(3):
        start_time = time.time()
        response = client.get('/api/v1/blockchain/balance/')
        duration = time.time() - start_time
        
        print(f"Request {i+1}: {duration:.3f} seconds - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            cached = data.get('cached', False)
            print(f"  Balance: {data.get('balance')} - Cached: {cached}")
        
        # Pause between requests
        if i < 2:
            time.sleep(1)

if __name__ == "__main__":
    test_balance_performance()
    print("\nTest completed. Check server logs for detailed performance metrics.")
