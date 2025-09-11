#!/usr/bin/env python

import os
import sys
import django
from decimal import Decimal

# Add Django path and configure settings
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from rewards.models import PaymentDiscountSnapshot
from courses.models import TeacherDiscountDecision, Course
from users.models import User
from rewards.services.transaction_services import apply_discount_and_snapshot

def test_duplicate_prevention():
    """Test che la fix previene i duplicati"""
    
    print("=== Test Prevenzione Duplicati ===")
    
    # Get test data
    student = User.objects.filter(email__contains="student").first()
    course = Course.objects.first()
    teacher = course.teacher if course else None
    
    if not all([student, course, teacher]):
        print("❌ Test data not available")
        return
    
    print(f"Student: {student.email}")
    print(f"Course: {course.title}")
    print(f"Teacher: {teacher.email}")
    
    # Count before
    snapshots_before = PaymentDiscountSnapshot.objects.filter(
        student=student,
        course=course,
        teacher=teacher
    ).count()
    
    decisions_before = TeacherDiscountDecision.objects.filter(
        student=student,
        course=course,
        teacher=teacher
    ).count()
    
    print(f"\nBefore: {snapshots_before} snapshots, {decisions_before} decisions")
    
    # Simulate two calls (like payment flow + webhook)
    try:
        print("\n--- First call (simulating payment creation) ---")
        result1 = apply_discount_and_snapshot(
            student_user_id=student.id,
            course_id=course.id,
            teacher_id=teacher.id,
            teo_cost=Decimal("15.00"),
            offered_teacher_teo=Decimal("18.75")
        )
        print(f"Result 1: {result1}")
        
        print("\n--- Second call (simulating webhook/retry) ---")
        result2 = apply_discount_and_snapshot(
            student_user_id=student.id,
            course_id=course.id,
            teacher_id=teacher.id,
            teo_cost=Decimal("15.00"),
            offered_teacher_teo=Decimal("18.75")
        )
        print(f"Result 2: {result2}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return
    
    # Count after
    snapshots_after = PaymentDiscountSnapshot.objects.filter(
        student=student,
        course=course,
        teacher=teacher
    ).count()
    
    decisions_after = TeacherDiscountDecision.objects.filter(
        student=student,
        course=course,
        teacher=teacher
    ).count()
    
    print(f"\nAfter: {snapshots_after} snapshots, {decisions_after} decisions")
    
    # Verify no duplicates created
    snapshot_delta = snapshots_after - snapshots_before
    decision_delta = decisions_after - decisions_before
    
    print(f"\n=== Results ===")
    print(f"Snapshots created: {snapshot_delta} (should be 0 or 1)")
    print(f"Decisions created: {decision_delta} (should be 1 or 2 max)")
    
    if snapshot_delta <= 1:
        print("✅ Snapshot duplication FIXED!")
    else:
        print("❌ Snapshot duplication still exists")
    
    if decision_delta <= 2:
        print("✅ Decision creation reasonable")
    else:
        print("⚠️ Too many decisions created")

if __name__ == "__main__":
    test_duplicate_prevention()
