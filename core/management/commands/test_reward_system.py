#!/usr/bin/env python
"""
Test script for the automated reward system
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import TestCase
from django.utils import timezone
from users.models import User
from courses.models import Course, Lesson, LessonCompletion
from rewards.automation import AutomatedRewardSystem
from rewards.models import TeoCoinTransaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_reward_system():
    """Test the automated reward system"""
    print("=== Testing Automated Reward System ===")
    print("Starting reward system test...")
    
    try:
        # Initialize reward system
        reward_system = AutomatedRewardSystem()
        print(f"✓ Reward system initialized (blockchain_enabled: {reward_system.blockchain_enabled})")
        
        # Get or create test user
        student, created = User.objects.get_or_create(
            username='test_student_reward',
            defaults={
                'email': 'teststudent@example.com',
                'role': 'student',
                'teo_coins': 0
            }
        )
        if created:
            student.set_password('testpass123')
            student.save()
        
        print(f"✓ Test student: {student.username} (TeoCoins: {student.teo_coins})")
        
        # Get first available course and lesson
        course = Course.objects.first()
        if not course:
            print("❌ No courses found in database")
            return
            
        lesson = course.lessons.first()
        if not lesson:
            print("❌ No lessons found in course")
            return
            
        print(f"✓ Using course: {course.title} (Price: ${course.price})")
        print(f"✓ Using lesson: {lesson.title}")
        
        # Test lesson completion reward
        initial_coins = student.teo_coins
        print(f"\n--- Testing Lesson Completion Reward ---")
        print(f"Initial TeoCoins: {initial_coins}")
        
        # Calculate expected reward
        expected_reward = reward_system.calculate_lesson_reward(course, lesson)
        print(f"Expected reward: {expected_reward} TeoCoins")
        
        # Award lesson completion reward
        success = reward_system.reward_lesson_completion(student, lesson, course)
        if success:
            student.refresh_from_db()
            print(f"✓ Lesson completion reward successful")
            print(f"New TeoCoins balance: {student.teo_coins}")
            print(f"Coins earned: {student.teo_coins - initial_coins}")
            
            # Create LessonCompletion record for course completion testing
            completion, created = LessonCompletion.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={'completed_at': timezone.now()}
            )
            if created:
                print(f"✓ LessonCompletion record created")
        else:
            print("❌ Lesson completion reward failed")
            
        # Test reward summary
        print(f"\n--- Testing Reward Summary ---")
        summary = reward_system.get_student_reward_summary(student, course)
        print(f"Reward summary: {summary}")
        
        # Test course completion check
        print(f"\n--- Testing Course Completion Check ---")
        completion_result = reward_system.check_and_reward_course_completion(student, course)
        print(f"Course completion check result: {completion_result}")
        
        # Show recent transactions
        print(f"\n--- Recent TeoCoin Transactions ---")
        recent_transactions = TeoCoinTransaction.objects.filter(user=student).order_by('-created_at')[:5]
        for tx in recent_transactions:
            print(f"  {tx.created_at}: {tx.amount} TeoCoins ({tx.transaction_type})")
        
        print(f"\n=== Test Completed Successfully ===")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Script starting...")
    test_reward_system()
    print("Script finished.")
