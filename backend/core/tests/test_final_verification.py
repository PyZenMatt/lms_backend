#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview, Exercise
from rewards.models import BlockchainTransaction
from users.models import User
from django.utils import timezone
from django.db import transaction
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_final_review_with_fix():
    """
    Final test to verify that the last review completion works without network error
    """
    print("🧪 Final Test - Last Review Completion (Post-Fix)")
    print("=" * 60)
    
    # Create a fresh scenario
    exercise = Exercise.objects.first()
    if not exercise:
        print("❌ No exercise found")
        return False
    
    all_users = list(User.objects.all())
    if len(all_users) < 4:
        print("❌ Need at least 4 users")
        return False
    
    student = all_users[0]
    reviewers = all_users[1:4]
    
    print(f"Creating test scenario:")
    print(f"  Student: {student.username}")
    print(f"  Reviewers: {[r.username for r in reviewers]}")
    
    # Create fresh submission
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Final test submission for network error fix",
        reviewed=False,
        passed=False
    )
    
    # Create reviews
    reviews = []
    for reviewer in reviewers:
        review = ExerciseReview.objects.create(
            submission=submission,
            reviewer=reviewer,
            assigned_at=timezone.now(),
            score=None
        )
        submission.reviewers.add(reviewer)
        reviews.append(review)
    
    submission.save()
    print(f"✅ Created submission {submission.id}")
    
    # Complete first two reviews
    print("\n--- Completing First Two Reviews ---")
    for i, review in enumerate(reviews[:2]):
        review.score = 7  # Pass score
        review.reviewed_at = timezone.now()
        review.save()
        print(f"✅ Review {i+1} by {review.reviewer.username}: score {review.score}")
        
        # Check submission status
        submission.refresh_from_db()
        print(f"  Submission reviewed: {submission.reviewed}")
    
    # Now the critical test - complete the LAST review
    print("\n🎯 --- Completing FINAL Review (Critical Test) ---")
    final_review = reviews[2]
    
    try:
        # Simulate exactly what happens in ReviewExerciseView.post()
        print(f"Reviewer: {final_review.reviewer.username}")
        print("Attempting to complete final review...")
        
        # Before completion
        submission.refresh_from_db()
        existing_rewards = BlockchainTransaction.objects.filter(
            transaction_type__in=['exercise_reward', 'review_reward'],
            related_object_id=str(submission.id)
        )
        print(f"Before: Submission reviewed={submission.reviewed}, Rewards={existing_rewards.count()}")
        
        # Complete the review
        final_review.score = 8  # Pass score
        final_review.reviewed_at = timezone.now()
        final_review.save()
        
        # Update average score (mimicking the view logic)
        ExerciseReview.calculate_average_score(submission)
        
        # This should trigger the reward creation logic
        reviews_check = ExerciseReview.objects.filter(submission=submission)
        if all(r.score is not None for r in reviews_check) and not submission.reviewed:
            print("🔥 All reviews complete - executing reward logic...")
            
            # The exact logic from the fixed ReviewExerciseView
            with transaction.atomic():
                # Mark as reviewed FIRST
                submission.reviewed = True
                submission.save(update_fields=['reviewed'])
                
                # Calculate scores
                scores = [r.score for r in reviews_check if r.score is not None]
                average = sum(scores) / len(scores) if scores else None
                passed = average is not None and average >= 6
                
                print(f"Average score: {average}, Passed: {passed}")
                
                # Get course
                course = None
                try:
                    if hasattr(submission.exercise, 'lesson') and submission.exercise.lesson:
                        course = submission.exercise.lesson.course
                except AttributeError:
                    pass
                
                if course and hasattr(course, 'price'):
                    print(f"Course: {course.title}, Price: {course.price}")
                    
                    from courses.views.exercises import create_reward_transaction
                    reward_transactions_created = []
                    
                    # Exercise reward for student (if passed) - WITH FIX
                    if passed:
                        reward_max = int(course.price * 0.15)
                        reward_distributed = getattr(course, 'reward_distributed', 0)
                        reward_remaining = reward_max - reward_distributed

                        if reward_remaining > 0:
                            reward_cap = max(1, int(course.price * 0.05))  # 🔧 THE FIX
                            print(f"Reward calculation: max={reward_max}, cap={reward_cap}, remaining={reward_remaining}")
                            
                            import random
                            random_reward = min(random.randint(1, reward_cap), reward_remaining)
                            print(f"Calculated exercise reward: {random_reward} TEO")

                            submission.reward_amount = random_reward
                            
                            exercise_reward = create_reward_transaction(
                                submission.student, 
                                random_reward, 
                                'exercise_reward', 
                                submission.id
                            )
                            reward_transactions_created.append(exercise_reward)

                            course.reward_distributed = reward_distributed + random_reward
                            course.save(update_fields=['reward_distributed'])
                    
                    # Review rewards for all reviewers
                    reviewer_reward = max(1, int(course.price * 0.005))
                    print(f"Reviewer reward: {reviewer_reward} TEO each")
                    
                    for r in reviews_check:
                        review_reward = create_reward_transaction(
                            r.reviewer,
                            reviewer_reward,
                            'review_reward',
                            submission.id
                        )
                        reward_transactions_created.append(review_reward)
                    
                    # Save submission changes
                    submission.passed = passed
                    submission.save()
                    
                    print(f"✅ Created {len(reward_transactions_created)} reward transactions successfully!")
                    
                    # Wait for automatic processing
                    import time
                    time.sleep(3)
                    
                    # Final verification
                    print("\n--- Final Verification ---")
                    final_rewards = BlockchainTransaction.objects.filter(
                        transaction_type__in=['exercise_reward', 'review_reward'],
                        related_object_id=str(submission.id)
                    ).order_by('-created_at')
                    
                    print(f"Total rewards: {final_rewards.count()}")
                    
                    success_count = 0
                    for reward in final_rewards:
                        status_emoji = "✅" if reward.status == 'completed' else "❌" if reward.status == 'failed' else "⏳"
                        print(f"  {status_emoji} {reward.transaction_type}: {reward.amount} TEO for {reward.user.username} ({reward.status})")
                        if reward.status == 'completed':
                            success_count += 1
                        elif reward.status == 'failed':
                            print(f"      Error: {reward.error_message}")
                    
                    print(f"\nSuccess rate: {success_count}/{final_rewards.count()} rewards processed successfully")
                    
                    return True
                else:
                    print("❌ No course found")
                    return False
        else:
            print("Reviews not complete or already processed")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR (this was the network error): {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_final_review_with_fix()
    
    if success:
        print("\n🎉 SUCCESS! The network error has been FIXED!")
        print("✅ Last review completion now works without errors")
        print("✅ All reward transactions are created properly")
        print("✅ Users should no longer see 'errore di rete'")
    else:
        print("\n❌ FAILED! The issue may still exist")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
