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
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_and_test_real_scenario():
    """
    Create a real scenario and test the actual review logic from the view
    """
    print("=== Creating Real Test Scenario ===")
    
    # Get existing submission or create new one
    exercise = Exercise.objects.first()
    if not exercise:
        print("❌ No exercise found")
        return
    
    # Find students and reviewers
    all_users = list(User.objects.all())
    if len(all_users) < 4:
        print("❌ Need at least 4 users for testing")
        return
    
    student = all_users[0]
    reviewers = all_users[1:4]  # Take 3 reviewers
    
    print(f"Student: {student.username}")
    print(f"Reviewers: {[r.username for r in reviewers]}")
    
    # Create fresh submission
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Test submission for real scenario",
        reviewed=False,
        passed=False
    )
    
    # Create reviews without scores
    for reviewer in reviewers:
        ExerciseReview.objects.create(
            submission=submission,
            reviewer=reviewer,
            assigned_at=timezone.now(),
            score=None  # No score initially
        )
        submission.reviewers.add(reviewer)
    
    submission.save()
    print(f"✅ Created submission {submission.id}")
    
    return submission, reviewers

def complete_reviews_step_by_step(submission, reviewers):
    """
    Complete reviews one by one and monitor the process
    """
    print("\n=== Completing Reviews Step by Step ===")
    
    reviews = ExerciseReview.objects.filter(submission=submission)
    
    # Complete first two reviews
    for i, review in enumerate(reviews[:2]):
        print(f"\n--- Completing Review {i+1} by {review.reviewer.username} ---")
        
        # Directly update the review (simulating what the view does)
        review.score = random.randint(6, 10)
        review.reviewed_at = timezone.now()
        review.save()
        
        print(f"Set score: {review.score}")
        
        # Update average score
        ExerciseReview.calculate_average_score(submission)
        
        # Check if all reviews are complete
        all_reviews = ExerciseReview.objects.filter(submission=submission)
        remaining_reviews = all_reviews.filter(score__isnull=True)
        
        print(f"Reviews completed: {all_reviews.count() - remaining_reviews.count()}/{all_reviews.count()}")
        
        submission.refresh_from_db()
        print(f"Submission reviewed status: {submission.reviewed}")
        
        # Check for any reward transactions
        rewards = BlockchainTransaction.objects.filter(
            transaction_type__in=['exercise_reward', 'review_reward'],
            related_object_id=str(submission.id)
        )
        print(f"Reward transactions so far: {rewards.count()}")
    
    # Now complete the FINAL review
    final_review = reviews[2]
    print(f"\n🎯 --- Completing FINAL Review by {final_review.reviewer.username} ---")
    print("This should trigger all reward creation...")
    
    # Check state before
    submission.refresh_from_db()
    print(f"Before final review - Submission reviewed: {submission.reviewed}")
    
    existing_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        related_object_id=str(submission.id)
    )
    print(f"Existing rewards before: {existing_rewards.count()}")
    
    try:
        # Complete the final review in an atomic transaction
        with transaction.atomic():
            final_review.score = random.randint(6, 10)
            final_review.reviewed_at = timezone.now()
            final_review.save()
            
            print(f"✅ Set final score: {final_review.score}")
            
            # Update average score
            ExerciseReview.calculate_average_score(submission)
            
            # This should trigger the reward logic
            # Let's manually trigger what happens in the view
            reviews = ExerciseReview.objects.filter(submission=submission)
            
            if all(r.score is not None for r in reviews) and not submission.reviewed:
                print("🎯 All reviews complete - triggering reward logic")
                
                # This mimics the logic in ReviewExerciseView.post()
                submission.reviewed = True
                submission.save(update_fields=['reviewed'])
                
                # Calculate scores and passing
                scores = [r.score for r in reviews if r.score is not None]
                average = sum(scores) / len(scores) if scores else None
                passed = average is not None and average >= 6
                
                print(f"Average score: {average}")
                print(f"Passed: {passed}")
                
                # Get course for reward calculation
                course = None
                try:
                    if hasattr(submission.exercise, 'lesson') and submission.exercise.lesson:
                        course = submission.exercise.lesson.course
                except AttributeError:
                    pass
                
                if course and hasattr(course, 'price'):
                    print(f"Course found: {course.title}, Price: {course.price}")
                    
                    # Create reward transactions manually (like in the view)
                    from courses.views.exercises import create_reward_transaction
                    
                    reward_transactions_created = []
                    
                    # Exercise reward for student (if passed)
                    if passed:
                        reward_max = int(course.price * 0.15)
                        reward_distributed = getattr(course, 'reward_distributed', 0)
                        reward_remaining = reward_max - reward_distributed

                        if reward_remaining > 0:
                            reward_cap = int(course.price * 0.05)
                            random_reward = min(random.randint(1, reward_cap), reward_remaining)

                            submission.reward_amount = random_reward
                            
                            exercise_reward = create_reward_transaction(
                                submission.student, 
                                random_reward, 
                                'exercise_reward', 
                                submission.id
                            )
                            reward_transactions_created.append(exercise_reward)
                            print(f"Created exercise reward: {random_reward} TEO for {submission.student.username}")

                            course.reward_distributed = reward_distributed + random_reward
                            course.save(update_fields=['reward_distributed'])

                    # Review rewards for all reviewers
                    reviewer_reward = max(1, int(course.price * 0.005))
                    
                    for r in reviews:
                        review_reward = create_reward_transaction(
                            r.reviewer,
                            reviewer_reward,
                            'review_reward',
                            submission.id
                        )
                        reward_transactions_created.append(review_reward)
                        print(f"Created review reward: {reviewer_reward} TEO for {r.reviewer.username}")
                    
                    # Update submission
                    submission.passed = passed
                    submission.save()
                    
                    print(f"✅ Created {len(reward_transactions_created)} reward transactions")
                    
                    # Wait for signals to process
                    import time
                    time.sleep(3)
                    
                    # Check final status
                    print("\n--- Final Status Check ---")
                    
                    final_rewards = BlockchainTransaction.objects.filter(
                        transaction_type__in=['exercise_reward', 'review_reward'],
                        related_object_id=str(submission.id)
                    ).order_by('-created_at')
                    
                    print(f"Total rewards created: {final_rewards.count()}")
                    
                    for reward in final_rewards:
                        print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username}")
                        print(f"    Status: {reward.status}, Created: {reward.created_at}")
                        if reward.status == 'failed':
                            print(f"    Error: {reward.error_message}")
                    
                    # Check if all reviewers got rewards
                    reviewer_rewards = final_rewards.filter(transaction_type='review_reward')
                    print(f"\nReview rewards: {reviewer_rewards.count()}/3 expected")
                    
                    for reviewer in reviewers:
                        reviewer_reward = reviewer_rewards.filter(user=reviewer).first()
                        if reviewer_reward:
                            print(f"  ✅ {reviewer.username}: {reviewer_reward.amount} TEO ({reviewer_reward.status})")
                        else:
                            print(f"  ❌ {reviewer.username}: NO REWARD FOUND")
                    
                    return True
                    
                else:
                    print("❌ No course found or course has no price")
                    return False
            else:
                print("Reviews not all complete or already reviewed")
                return False
                
    except Exception as e:
        print(f"❌ ERROR during final review processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Real Scenario Test - Network Error Reproduction")
    print("=" * 60)
    
    submission, reviewers = create_and_test_real_scenario()
    
    if not submission or not reviewers:
        print("❌ Failed to create test scenario")
        return
    
    success = complete_reviews_step_by_step(submission, reviewers)
    
    if success:
        print("\n✅ Test completed successfully - No network error!")
    else:
        print("\n❌ Test failed - This might reveal the issue!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
