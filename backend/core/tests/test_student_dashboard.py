"""
Test script to verify the student dashboard API is working correctly.

This script makes a request to the student dashboard API endpoint and
prints the response or error message.
"""

import requests
import sys
import os
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

def test_student_dashboard_api():
    """Test the student dashboard API endpoint"""
    # Get a test user with student role
    user = User.objects.filter(role='student').first()
    
    if not user:
        print("No student users found. Please create a student user first.")
        return
    
    print(f"Testing with student user: {user.username}")
    
    # Create API client and authenticate
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Make request to student dashboard API
    print("\nMaking request to student dashboard API...")
    
    try:
        response = client.get('/api/v1/dashboard/student/')
        status_code = response.status_code
        
        print(f"Status code: {status_code}")
        
        if status_code == 200:
            data = response.json()
            print("API response received successfully!")
            print(f"Username: {data.get('username')}")
            print(f"Blockchain balance: {data.get('blockchain_balance')}")
            print(f"Wallet address: {data.get('wallet_address')}")
            print(f"Courses count: {len(data.get('courses', []))}")
            print(f"Transactions count: {len(data.get('recent_transactions', []))}")
        else:
            print(f"Error response: {response.content.decode()}")
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_student_dashboard_api()
