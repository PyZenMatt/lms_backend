#!/usr/bin/env python
"""
Test the teacher choice API endpoint
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rewards.models import TeacherDiscountAbsorption
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_teacher_choice_api():
    print("🧪 TESTING TEACHER CHOICE API")
    print("=" * 50)
    
    User = get_user_model()
    
    # Get teacher and pending absorption
    teacher = User.objects.filter(username='test_teacher_notifications').first()
    if not teacher:
        print("❌ Teacher not found")
        return
    
    absorption = TeacherDiscountAbsorption.objects.filter(
        teacher=teacher,
        status='pending'
    ).first()
    
    if not absorption:
        print("❌ No pending absorption found")
        return
    
    print(f"✅ Teacher: {teacher.username}")
    print(f"✅ Absorption ID: {absorption.pk}")
    print(f"✅ Current status: {absorption.status}")
    
    # Create API client
    client = APIClient()
    
    # Generate JWT token for teacher
    refresh = RefreshToken.for_user(teacher)
    access_token = str(refresh.access_token)
    
    # Set authentication header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test the API endpoint
    url = '/api/v1/teocoin/teacher/choice/'
    data = {
        'absorption_id': absorption.pk,
        'choice': 'absorb'
    }
    
    print(f"\n🔗 Testing URL: {url}")
    print(f"📤 Request data: {data}")
    
    response = client.post(url, data, format='json')
    
    print(f"\n📡 Response:")
    print(f"   Status: {response.status_code}")
    print(f"   Content: {response.content.decode()}")
    
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('success'):
            print("✅ API endpoint working correctly!")
        else:
            print(f"❌ API returned error: {response_data.get('error')}")
    else:
        print("❌ API endpoint failed")
    
    # Check if absorption was updated
    absorption.refresh_from_db()
    print(f"\n📊 Absorption after API call:")
    print(f"   Status: {absorption.status}")
    print(f"   Final TEO: {absorption.final_teacher_teo}")

if __name__ == "__main__":
    test_teacher_choice_api()
