#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import Exercise, ExerciseSubmission, ExerciseReview
from rewards.models import BlockchainTransaction
from users.models import User

def test_reward_logic_directly():
    """
    Test the reward logic directly by simulating what happens in the view
    """
    print("🔬 TESTING REWARD LOGIC DIRECTLY")
    print("=" * 50)
    
    try:
        # Get submission 59 (the one we just created)
        submission = ExerciseSubmission.objects.get(id=59)
        print(f"📝 Testing submission: {submission.id}")
        print(f"👤 Student: {submission.student.username}")
        
        # Get all reviews for this submission
        reviews = ExerciseReview.objects.filter(submission=submission)
        print(f"👥 Reviews found: {reviews.count()}")
        
        for i, review in enumerate(reviews, 1):
            print(f"  {i}. {review.reviewer.username}: score={review.score}, reviewed_at={review.reviewed_at}")
        
        # Let's manually run the reward logic that should happen in the view
        print(f"\n🔄 RUNNING REWARD LOGIC MANUALLY")
        
        # Check if all reviews have scores
        all_have_scores = all(r.score is not None for r in reviews)
        print(f"All reviews have scores: {all_have_scores}")
        print(f"Submission already reviewed: {submission.reviewed}")
        
        if all_have_scores and not submission.reviewed:
            print("✅ Conditions met for reward processing")
            
            # Calculate average
            scores = [r.score for r in reviews if r.score is not None]
            if scores:
                average = sum(scores) / len(scores)
            else:
                average = None
            
            passed = average is not None and average >= 6
            print(f"📊 Average: {average}, Passed: {passed}")
            
            # Get course
            course = None
            try:
                if hasattr(submission.exercise, 'lesson') and submission.exercise.lesson:
                    course = submission.exercise.lesson.course
                print(f"🎓 Course found: {course.title if course else 'None'}")
            except Exception as e:
                print(f"❌ Error getting course: {e}")
            
            # Mark as reviewed first
            submission.reviewed = True
            submission.passed = passed
            submission.average_score = average
            submission.save()
            print(f"✅ Submission marked as reviewed")
            
            # Process rewards if course found
            if course and hasattr(course, 'price'):
                print(f"💰 Course price: {course.price} TEO")
                
                # Exercise reward for student (if passed)
                if passed:
                    reward_cap = int(course.price * 0.05)
                    random_reward = max(1, reward_cap // 2)  # Fixed for testing
                    
                    print(f"🎁 Creating exercise reward: {random_reward} TEO")
                    
                    exercise_reward = BlockchainTransaction.objects.create(
                        user=submission.student,
                        transaction_type='exercise_reward',
                        amount=random_reward,
                        related_object_id=str(submission.id),
                        notes=f'Exercise reward for submission {submission.id}',
                        status='pending'
                    )
                    
                    submission.reward_amount = random_reward
                    submission.save()
                    print(f"✅ Exercise reward created: {exercise_reward.id}")
                
                # Review rewards for all reviewers
                reviewer_reward = max(1, int(course.price * 0.005))
                print(f"👥 Creating review rewards: {reviewer_reward} TEO each")
                
                for i, r in enumerate(reviews, 1):
                    review_reward = BlockchainTransaction.objects.create(
                        user=r.reviewer,
                        transaction_type='review_reward',
                        amount=reviewer_reward,
                        related_object_id=str(submission.id),
                        notes=f'Review reward for submission {submission.id}',
                        status='pending'
                    )
                    print(f"  {i}. Review reward for {r.reviewer.username}: {review_reward.id}")
            
            print(f"\n🎉 REWARD PROCESSING COMPLETE!")
        else:
            print("❌ Conditions not met for reward processing")
        
        # Final verification
        print(f"\n📊 FINAL VERIFICATION")
        final_rewards = BlockchainTransaction.objects.filter(
            related_object_id=str(submission.id)
        ).order_by('-created_at')
        
        print(f"Total rewards: {final_rewards.count()}")
        for reward in final_rewards:
            print(f"  - {reward.user.username}: {reward.amount} TEO ({reward.transaction_type}) - {reward.status}")
        
        # Check submission state
        submission.refresh_from_db()
        print(f"\nSubmission final state:")
        print(f"  - Reviewed: {submission.reviewed}")
        print(f"  - Passed: {submission.passed}")
        print(f"  - Average: {submission.average_score}")
        print(f"  - Reward amount: {submission.reward_amount}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_reward_logic_directly()
