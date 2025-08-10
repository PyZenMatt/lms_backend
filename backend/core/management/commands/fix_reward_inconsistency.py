#!/usr/bin/env python
"""
Script per correggere l'inconsistenza nel reward_distributed del corso
e creare il reward mancante per student1
"""

import os
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from courses.models import ExerciseSubmission, Course
from rewards.models import BlockchainTransaction

def fix_reward_inconsistency():
    """
    Corregge l'inconsistenza tra reward_distributed e actual rewards
    """
    print("=== FIXING REWARD INCONSISTENCY ===\n")
    
    try:
        # Trova il corso con il problema
        student1 = User.objects.get(username='student1')
        submission = ExerciseSubmission.objects.filter(student=student1).order_by('-submitted_at').first()
        course = submission.exercise.lesson.course
        
        print(f"Course: {course.title}")
        print(f"Course price: {course.price} TEO")
        print(f"Current reward_distributed: {course.reward_distributed} TEO")
        
        # Trova tutti i reward reali per questo corso
        all_submissions = ExerciseSubmission.objects.filter(
            exercise__lesson__course=course
        )
        submission_ids = [s.id for s in all_submissions]
        
        exercise_rewards = BlockchainTransaction.objects.filter(
            transaction_type='exercise_reward',
            related_object_id__in=submission_ids
        )
        
        print(f"\nSubmissions for this course: {len(all_submissions)}")
        print(f"Exercise rewards found: {len(exercise_rewards)}")
        
        # Calcola il totale realmente distribuito
        total_distributed = sum(r.amount for r in exercise_rewards if r.status == 'completed')
        print(f"Total actually distributed: {total_distributed} TEO")
        print(f"Recorded in course: {course.reward_distributed} TEO")
        print(f"Difference: {course.reward_distributed - total_distributed} TEO")
        
        if total_distributed != course.reward_distributed:
            print("\n🔧 FIXING INCONSISTENCY...")
            
            with transaction.atomic():
                # Reset reward_distributed to actual amount
                course.reward_distributed = total_distributed
                course.save(update_fields=['reward_distributed'])
                print(f"✅ Reset course.reward_distributed to {total_distributed} TEO")
                
                # Now there should be room for new rewards
                reward_max = int(course.price * 0.15)
                reward_remaining = reward_max - total_distributed
                print(f"Reward max: {reward_max} TEO")
                print(f"New reward remaining: {reward_remaining} TEO")
                
                if reward_remaining > 0:
                    print(f"✅ Now there are {reward_remaining} TEO available for new rewards!")
                    
                    # Check if student1's submission deserves a reward
                    if submission.passed and submission.is_approved:
                        reward_cap = max(1, int(course.price * 0.05))
                        reward_amount = min(1, reward_remaining)  # Give 1 TEO or what's left
                        
                        print(f"\n🎁 Creating missing exercise reward for student1...")
                        print(f"Amount: {reward_amount} TEO")
                        
                        # Create the reward transaction
                        from rewards.utils import create_reward_transaction
                        exercise_reward = create_reward_transaction(
                            submission.student,
                            reward_amount,
                            'exercise_reward',
                            submission.id
                        )
                        
                        # Update the course and submission
                        course.reward_distributed = total_distributed + reward_amount
                        course.save(update_fields=['reward_distributed'])
                        
                        submission.reward_amount = reward_amount
                        submission.save(update_fields=['reward_amount'])
                        
                        print(f"✅ Exercise reward created: ID {exercise_reward.id}")
                        print(f"✅ Course reward_distributed updated to: {course.reward_distributed} TEO")
                        print(f"✅ Submission reward_amount set to: {submission.reward_amount} TEO")
                    else:
                        print("⚠️  Student1's submission doesn't qualify for reward (not passed or approved)")
                else:
                    print("⚠️  No reward remaining even after correction")
        else:
            print("✅ No inconsistency found - values match")
        
        print("\n=== FINAL STATUS ===")
        course.refresh_from_db()
        print(f"Course reward_distributed: {course.reward_distributed} TEO")
        
        # Count final rewards
        final_rewards = BlockchainTransaction.objects.filter(
            transaction_type='exercise_reward',
            related_object_id__in=submission_ids
        )
        final_total = sum(r.amount for r in final_rewards if r.status in ['completed', 'pending'])
        print(f"Total exercise rewards: {final_total} TEO")
        print(f"Status: {'✅ CONSISTENT' if final_total == course.reward_distributed else '❌ STILL INCONSISTENT'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_reward_inconsistency()
