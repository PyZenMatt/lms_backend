#!/usr/bin/env python3
"""
Manually create enrollment for the completed transaction
"""

import os
import sys

import django
from courses.models import Course, CourseEnrollment
from django.contrib.auth import get_user_model
from rewards.models import BlockchainTransaction

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()


User = get_user_model()


def create_missing_enrollment():
    """Create enrollment for the completed transaction"""

    print("🔧 CREATING MISSING ENROLLMENT")
    print("=" * 40)

    try:
        # Get the student and course from the transaction
        student = User.objects.get(username='student1')

        # Find the recent course purchase transaction
        purchase_tx = BlockchainTransaction.objects.filter(
            user=student,
            transaction_type='course_purchase',
            status='completed'
        ).order_by('-created_at').first()

        if not purchase_tx:
            print("❌ No completed purchase transaction found")
            return

        print(f"📄 Found purchase transaction: {purchase_tx.transaction_hash}")
        print(f"   Course ID: {purchase_tx.related_object_id}")
        print(f"   Amount: {purchase_tx.amount} TEO")

        # Get the course
        course = Course.objects.get(id=int(purchase_tx.related_object_id))
        print(f"📚 Course: {course.title}")

        # Check if enrollment already exists
        existing_enrollment = CourseEnrollment.objects.filter(
            student=student,
            course=course
        ).first()

        if existing_enrollment:
            print(f"✅ Enrollment already exists: {existing_enrollment}")
            return

        # Create the enrollment
        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            completed=False
        )

        print(f"✅ Created enrollment: {enrollment}")
        print(f"   Student: {enrollment.student.username}")
        print(f"   Course: {enrollment.course.title}")
        print(f"   Enrolled at: {enrollment.enrolled_at}")

        return enrollment

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    create_missing_enrollment()
