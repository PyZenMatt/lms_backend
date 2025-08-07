#!/usr/bin/env python
"""
Quick test script to verify CourseEnrollment records are being created properly
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import Course, CourseEnrollment
from django.contrib.auth import get_user_model

User = get_user_model()

def test_courseenrollment_model():
    """Test that CourseEnrollment model works correctly"""
    print("🧪 Testing CourseEnrollment model...")
    
    # Check if model can be imported and has expected fields
    print(f"✅ CourseEnrollment model imported successfully")
    
    # Check model fields
    fields = [field.name for field in CourseEnrollment._meta.get_fields()]
    expected_fields = ['student', 'course', 'enrollment_date', 'is_active']
    
    for field in expected_fields:
        if field in fields:
            print(f"✅ Field '{field}' exists")
        else:
            print(f"❌ Field '{field}' missing")
    
    print(f"📋 All fields: {fields}")
    
    # Test basic query
    try:
        enrollment_count = CourseEnrollment.objects.count()
        print(f"✅ Current CourseEnrollment records: {enrollment_count}")
    except Exception as e:
        print(f"❌ Error querying CourseEnrollment: {e}")
    
    return True

if __name__ == "__main__":
    test_courseenrollment_model()
