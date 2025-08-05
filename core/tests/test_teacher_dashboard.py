"""
Test script to verify the teacher dashboard API is working correctly
after fixing the teocoin_service import path.
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

def test_teacher_dashboard_api():
    """Test the teacher dashboard API endpoint"""
    # Get a test user with teacher role
    teacher = User.objects.filter(role='teacher').first()
    
    if not teacher:
        print("No teacher users found. Please create a teacher user first.")
        return
    
    print(f"Testing with teacher user: {teacher.username}")
    
    # Create API client and authenticate
    client = APIClient()
    client.force_authenticate(user=teacher)
    
    # Make request to teacher dashboard API
    print("\nMaking request to teacher dashboard API...")
    
    try:
        response = client.get('/api/v1/dashboard/teacher/')
        status_code = response.status_code
        
        print(f"Status code: {status_code}")
        
        if status_code == 200:
            data = response.json()
            print("API response received successfully!")
            print(f"Blockchain balance: {data.get('blockchain_balance')}")
            print(f"Wallet address: {data.get('wallet_address')}")
            print(f"Total courses: {data.get('stats', {}).get('total_courses')}")
            print(f"Total earnings: {data.get('stats', {}).get('total_earnings')}")
            print(f"Active students: {data.get('stats', {}).get('active_students')}")
            print(f"Courses count: {len(data.get('courses', []))}")
            print(f"Transactions count: {len(data.get('transactions', []))}")
        else:
            print(f"Error response: {response.content.decode()}")
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_teacher_dashboard_api()
    print("\nTest completed.")
