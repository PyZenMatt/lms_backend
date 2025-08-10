#!/usr/bin/env python
"""
Debug script per capire perché le submission degli esercizi non funzionano in production
"""
import os
import django


# Setup Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.prod')
django.setup()

from django.contrib.auth import get_user_model
import sys
from backend.courses.models import Exercise, ExerciseSubmission, Course, Lesson
from django.db import connection
from datetime import datetime, timedelta

User = get_user_model()

def debug_exercise_submission_production():
    print("🔍 DEBUGGING EXERCISE SUBMISSION IN PRODUCTION")
    print("=" * 60)
    
    # 1. Check database connection
    print("\n1. 📊 DATABASE CONNECTION")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_content_type")
            result = cursor.fetchone()
            print(f"✅ Database connection: OK (tables found: {result[0]})")
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return
    
    # 2. Check models availability
    print("\n2. 📋 MODELS AVAILABILITY")
    try:
        exercise_count = Exercise.objects.count()
        submission_count = ExerciseSubmission.objects.count()
        user_count = User.objects.count()
        print(f"✅ Exercises: {exercise_count}")
        print(f"✅ Submissions: {submission_count}")
        print(f"✅ Users: {user_count}")
    except Exception as e:
        print(f"❌ Models error: {e}")
        return
    
    # 3. Check recent submissions
    print("\n3. 📝 RECENT SUBMISSIONS (last 7 days)")
    try:
        recent_date = datetime.now() - timedelta(days=7)
        recent_submissions = ExerciseSubmission.objects.filter(
            created_at__gte=recent_date
        ).order_by('-created_at')[:10]
        
        if recent_submissions:
            print(f"✅ Found {recent_submissions.count()} recent submissions:")
            for sub in recent_submissions:
                print(f"  - ID: {sub.id}, Student: {sub.student.username}, Exercise: {sub.exercise.title}, Date: {sub.created_at}")
        else:
            print("❌ NO RECENT SUBMISSIONS FOUND!")
    except Exception as e:
        print(f"❌ Recent submissions error: {e}")
    
    # 4. Check users with student role
    print("\n4. 👥 USERS WITH STUDENT ROLE")
    try:
        students = User.objects.filter(role='student')[:5]
        if students:
            print(f"✅ Found {students.count()} students:")
            for student in students:
                print(f"  - {student.username} ({student.email})")
        else:
            print("❌ NO STUDENTS FOUND!")
    except Exception as e:
        print(f"❌ Students error: {e}")
    
    # 5. Check exercises available
    print("\n5. 📚 EXERCISES AVAILABLE")
    try:
        exercises = Exercise.objects.all()[:5]
        if exercises:
            print(f"✅ Found {exercises.count()} exercises:")
            for exercise in exercises:
                course = exercise.lesson.course
                print(f"  - {exercise.title} (Course: {course.title})")
        else:
            print("❌ NO EXERCISES FOUND!")
    except Exception as e:
        print(f"❌ Exercises error: {e}")
    
    # 6. Check permissions
    print("\n6. 🔐 PERMISSION CHECKS")
    try:
        # Simulate a student trying to submit
        student = User.objects.filter(role='student').first()
        if student:
            exercise = Exercise.objects.first()
            if exercise:
                course = exercise.lesson.course
                is_enrolled = course.students.filter(id=student.id).exists()
                print(f"✅ Student {student.username} enrolled in {course.title}: {is_enrolled}")
                
                # Check existing submission
                existing = ExerciseSubmission.objects.filter(exercise=exercise, student=student).exists()
                print(f"✅ Existing submission: {existing}")
            else:
                print("❌ No exercise to test")
        else:
            print("❌ No student to test")
    except Exception as e:
        print(f"❌ Permission check error: {e}")
    
    # 7. Test submission creation
    print("\n7. ✏️ TEST SUBMISSION CREATION")
    try:
        student = User.objects.filter(role='student').first()
        exercise = Exercise.objects.first()
        
        if student and exercise:
            # Check if student is enrolled
            course = exercise.lesson.course
            if not course.students.filter(id=student.id).exists():
                print(f"⚠️ Student {student.username} not enrolled in course {course.title}")
                print("   Enrolling student for test...")
                course.students.add(student)
                course.save()
            
            # Check if submission already exists
            if ExerciseSubmission.objects.filter(exercise=exercise, student=student).exists():
                print(f"⚠️ Submission already exists for this exercise")
            else:
                print(f"🧪 Creating test submission...")
                test_submission = ExerciseSubmission.objects.create(
                    student=student,
                    exercise=exercise,
                    content="Test submission from debug script"
                )
                print(f"✅ Test submission created: ID {test_submission.id}")
                
                # Clean up test submission
                test_submission.delete()
                print(f"🗑️ Test submission deleted")
        else:
            print("❌ Cannot test submission creation: missing student or exercise")
    except Exception as e:
        print(f"❌ Test submission error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_exercise_submission_production()
