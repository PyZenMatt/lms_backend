#!/usr/bin/env python3
"""
Test the student dashboard API and enrollment data
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import Course, CourseEnrollment
import json

User = get_user_model()

def test_student_dashboard_api():
    """Test the student dashboard API endpoint"""
    
    print("🧪 TESTING STUDENT DASHBOARD API")
    print("=" * 50)
    
    client = Client()
    
    try:
        # Get student and token
        user = User.objects.get(username='student1')
        token = RefreshToken.for_user(user).access_token
        
        print(f"👤 Testing for user: {user.username}")
        
        # Check enrollments directly
        enrollments = CourseEnrollment.objects.filter(student=user)
        print(f"📚 Direct DB enrollments: {enrollments.count()}")
        for enrollment in enrollments:
            print(f"   - Course: {enrollment.course.title} (ID: {enrollment.course.id})")
            
        # Test API endpoint
        response = client.get(
            '/api/v1/dashboard/student/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        print(f"\n🔍 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 API Response Data:")
            print(f"   - Username: {data.get('username')}")
            print(f"   - Wallet: {data.get('wallet_address')}")
            print(f"   - Balance: {data.get('blockchain_balance')}")
            print(f"   - Courses: {len(data.get('courses', []))}")
            
            for course in data.get('courses', []):
                print(f"     * {course.get('title')} (ID: {course.get('id')})")
                print(f"       Teacher: {course.get('teacher', {}).get('username', 'N/A')}")
                print(f"       Price: {course.get('price', 'N/A')}")
                
            print(f"   - Transactions: {len(data.get('recent_transactions', []))}")
            print(f"   - Notifications: {len(data.get('notifications', []))}")
            
            # Pretty print the full response for debugging
            print(f"\n📋 Full API Response:")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"❌ API Error: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def check_course_data():
    """Check the course data structure"""
    
    print("\n📖 CHECKING COURSE DATA STRUCTURE")
    print("=" * 40)
    
    try:
        course = Course.objects.get(id=81)
        print(f"📚 Course: {course.title}")
        print(f"   - ID: {course.id}")
        print(f"   - Teacher: {course.teacher.username}")
        print(f"   - Price: {course.price}")
        print(f"   - Approved: {course.is_approved}")
        print(f"   - Created: {course.created_at}")
        
        # Check enrollments for this course
        enrollments = course.enrollments.all()
        print(f"   - Enrollments: {enrollments.count()}")
        for enrollment in enrollments:
            print(f"     * Student: {enrollment.student.username}")
            print(f"       Enrolled: {enrollment.enrolled_at}")
            
    except Course.DoesNotExist:
        print("❌ Course ID 81 not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_student_dashboard_api()
    check_course_data()
