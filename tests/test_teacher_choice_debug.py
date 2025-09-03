#!/usr/bin/env python3
"""
Test TEO choice endpoint directly
"""
import json
import os
import sys

import django
from api.teacher_absorption_views import TeacherMakeAbsorptionChoiceView
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

# Add the project directory to Python path
sys.path.insert(0, "/home/teo/Project/school/schoolplatform")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolplatform.settings")
django.setup()


def test_teacher_choice():
    print("🔍 Testing TEO choice endpoint...")

    User = get_user_model()

    # Find a teacher
    teacher = User.objects.filter(is_staff=True).first()
    if not teacher:
        print("❌ No teacher found in database")
        return

    print(f"✅ Found teacher: {teacher.username} (ID: {teacher.id})")

    # Create DRF request
    factory = APIRequestFactory()

    # Test TEO choice
    request_data = {"choice": "teo", "discount_amount": 10.0}

    request = factory.post(
        "/api/v1/teocoin/teacher/choice/", request_data, format="json"
    )
    request.user = teacher

    print(f"📤 Sending request: {request_data}")

    # Call the view
    view = TeacherMakeAbsorptionChoiceView()
    try:
        response = view.post(request)
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response data: {response.content.decode()}")

        # Test EUR choice too
        print("\n🔍 Testing EUR choice...")
        request_data_eur = {"choice": "eur", "discount_amount": 10.0}

        request_eur = factory.post(
            "/api/v1/teocoin/teacher/choice/",
            json.dumps(request_data_eur),
            content_type="application/json",
        )
        request_eur.user = teacher

        response_eur = view.post(request_eur)
        print(f"📥 EUR Response status: {response_eur.status_code}")
        print(f"📥 EUR Response data: {response_eur.content.decode()}")

    except Exception as e:
        print(f"❌ Error calling view: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_teacher_choice()
