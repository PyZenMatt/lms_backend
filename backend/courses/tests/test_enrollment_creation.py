#!/usr/bin/env python3
"""
Test the complete course purchase flow with enrollment creation
"""

import os
import sys

import django
from courses.models import Course, CourseEnrollment
from django.contrib.auth import get_user_model

from blockchain.blockchain import teocoin_service

# Setup Django
sys.path.append("/home/teo/Project/school/schoolplatform")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolplatform.settings")
django.setup()


User = get_user_model()


def test_enrollment_creation():
    """Test that enrollment is created after payment"""

    print("🧪 TESTING ENROLLMENT CREATION AFTER PAYMENT")
    print("=" * 50)

    # Get student and course
    try:
        student = User.objects.get(username="student1")
        print(f"👤 Student: {student.username} ({student.wallet_address})")

        # Check available courses
        courses = Course.objects.all()
        if not courses:
            print("❌ No courses found")
            return

    course = courses.first()
    print(f"📚 Course: {course.title} - Price: {getattr(course, 'price_eur', 0)} TEO")

        # Check current enrollment
        existing_enrollment = CourseEnrollment.objects.filter(
            student=student, course=course
        ).first()

        if existing_enrollment:
            print(f"📝 Existing enrollment found: {existing_enrollment}")
            print("   Deleting for test...")
            existing_enrollment.delete()

        # Check student balance
        student_balance = teocoin_service.get_balance(student.wallet_address)
        print(f"💰 Student balance: {student_balance} TEO")

        course_price = float(getattr(course, "price_eur", 0))
        if student_balance < course_price:
            print(f"❌ Insufficient balance. Need {course_price} TEO")
            return

        print("\n🎯 Ready to test enrollment creation!")
        print("   Now you can test the purchase from the frontend.")
        print(
            "   After purchase, run this script again to verify enrollment was created."
        )

        return True

    except User.DoesNotExist:
        print("❌ Student1 not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_recent_enrollment():
    """Check for recent enrollments"""

    print("\n🔍 CHECKING RECENT ENROLLMENTS")
    print("=" * 40)

    try:
        student = User.objects.get(username="student1")

        # Get recent enrollments (last hour)
        from datetime import timedelta

        from django.utils import timezone

        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_enrollments = CourseEnrollment.objects.filter(
            student=student, enrolled_at__gte=one_hour_ago
        )

        print(f"📚 Recent enrollments found: {recent_enrollments.count()}")

        for enrollment in recent_enrollments:
            print(f"   - {enrollment.course.title}")
            print(f"     Enrolled: {enrollment.enrolled_at}")
            print(f"     Completed: {enrollment.completed}")

        # Check all enrollments for this student
        all_enrollments = CourseEnrollment.objects.filter(student=student)
        print(
            f"\n📊 Total enrollments for {student.username}: {all_enrollments.count()}"
        )

        for enrollment in all_enrollments:
            print(f"   - {enrollment.course.title} ({enrollment.enrolled_at})")

    except Exception as e:
        print(f"❌ Error checking enrollments: {e}")


if __name__ == "__main__":
    test_enrollment_creation()
    check_recent_enrollment()
