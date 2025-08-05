#!/usr/bin/env python
"""
Test per simulare e identificare i possibili punti di errore di rete
durante il processo di approvazione degli esercizi
"""

import os
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from courses.models import ExerciseSubmission, ExerciseReview
from rewards.models import BlockchainTransaction
from notifications.models import Notification
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_network_error_points():
    """
    Identifica i punti dove può avvenire un errore di rete
    """
    print("=== TEST NETWORK ERROR POINTS ===\n")
    
    try:
        # Trova l'ultimo submission di student1
        student1 = User.objects.get(username='student1')
        submission = ExerciseSubmission.objects.filter(student=student1).order_by('-submitted_at').first()
        
        if not submission:
            print("❌ Nessun submission trovato")
            return
        
        print(f"Testing submission ID: {submission.id}")
        print(f"Exercise: {submission.exercise.title}")
        print(f"Current status: reviewed={submission.reviewed}, passed={submission.passed}")
        
        # Test 1: Database connection timeout
        print("\n1. Testing database operations...")
        try:
            # Simulate slow query
            start_time = time.time()
            reviews = submission.reviews.all()
            print(f"   ✅ Retrieved {len(reviews)} reviews in {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Database error: {e}")
        
        # Test 2: Reward transaction creation
        print("\n2. Testing reward transaction creation...")
        try:
            # Simulate creating a test transaction (but don't save it)
            test_transaction = BlockchainTransaction(
                user=student1,
                amount=1.0,
                transaction_type='exercise_reward',
                related_object_id=submission.id,
                status='pending'
            )
            print("   ✅ Reward transaction object created successfully")
        except Exception as e:
            print(f"   ❌ Reward transaction error: {e}")
        
        # Test 3: Notification creation
        print("\n3. Testing notification creation...")
        try:
            # Create a test notification (but delete it immediately)
            test_notification = Notification.objects.create(
                user=student1,
                message="Test notification",
                notification_type='test'
            )
            test_notification.delete()
            print("   ✅ Notification created and deleted successfully")
        except Exception as e:
            print(f"   ❌ Notification error: {e}")
        
        # Test 4: Atomic transaction
        print("\n4. Testing atomic transaction...")
        try:
            with transaction.atomic():
                # Simulate the full process
                course = submission.exercise.lesson.course
                print(f"   Course: {course.title}")
                print(f"   Course price: {course.price}")
                print(f"   Current reward_distributed: {course.reward_distributed}")
                
                # Calculate what should happen
                reward_max = int(course.price * 0.15)
                reward_remaining = reward_max - course.reward_distributed
                print(f"   Reward max: {reward_max}, remaining: {reward_remaining}")
                
                if reward_remaining > 0:
                    reward_cap = max(1, int(course.price * 0.05))
                    print(f"   Reward cap: {reward_cap}")
                    print("   ✅ Would create exercise reward")
                else:
                    print("   ⚠️  No reward remaining - this explains the missing reward!")
                
                print("   ✅ Atomic transaction simulation completed")
        except Exception as e:
            print(f"   ❌ Atomic transaction error: {e}")
        
        # Test 5: Check for hanging connections
        print("\n5. Testing connection handling...")
        from django.db import connections
        for alias in connections:
            conn = connections[alias]
            print(f"   Connection {alias}: {conn.queries_logged} queries logged")
        
        print("\n=== POTENTIAL SOLUTIONS ===")
        print("1. Add database connection timeout settings")
        print("2. Add retry logic for failed operations")
        print("3. Split the process into smaller atomic transactions")
        print("4. Add background task processing for rewards")
        print("5. Add client-side timeout handling")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def check_missing_exercise_reward():
    """
    Controlla specificamente il reward mancante
    """
    print("\n=== MISSING EXERCISE REWARD CHECK ===")
    
    try:
        student1 = User.objects.get(username='student1')
        submission = ExerciseSubmission.objects.filter(student=student1).order_by('-submitted_at').first()
        
        course = submission.exercise.lesson.course
        print(f"Course: {course.title}")
        print(f"Course price: {course.price} TEO")
        print(f"Reward distributed: {course.reward_distributed} TEO")
        
        reward_max = int(course.price * 0.15)  # 15% of course price
        reward_remaining = reward_max - course.reward_distributed
        
        print(f"Reward max (15%): {reward_max} TEO")
        print(f"Reward remaining: {reward_remaining} TEO")
        
        if reward_remaining <= 0:
            print("🎯 FOUND THE ISSUE: No reward remaining in the pool!")
            print("This explains why no exercise reward was created.")
            
            # Find who got the rewards
            exercise_rewards = BlockchainTransaction.objects.filter(
                transaction_type='exercise_reward',
                related_object_id__in=ExerciseSubmission.objects.filter(
                    exercise__lesson__course=course
                ).values_list('id', flat=True)
            )
            
            print(f"\nExercise rewards already distributed for this course:")
            total_distributed = 0
            for reward in exercise_rewards:
                print(f"  - {reward.user.username}: {reward.amount} TEO (status: {reward.status})")
                if reward.status == 'completed':
                    total_distributed += reward.amount
            
            print(f"\nTotal actually distributed: {total_distributed} TEO")
            print(f"Course.reward_distributed: {course.reward_distributed} TEO")
            
            if total_distributed != course.reward_distributed:
                print("⚠️  INCONSISTENCY: Actual vs recorded distribution don't match!")
        else:
            print(f"✅ Reward pool has {reward_remaining} TEO available")
            print("The issue must be elsewhere in the logic.")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_network_error_points()
    check_missing_exercise_reward()
