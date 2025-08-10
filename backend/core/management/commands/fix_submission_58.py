#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview
from rewards.models import BlockchainTransaction
from users.models import User

def create_reward_transaction(user, amount, transaction_type, submission_id):
    """
    Create a reward transaction for a user
    """
    transaction = BlockchainTransaction.objects.create(
        user=user,
        transaction_type=transaction_type,
        amount=amount,
        related_object_id=str(submission_id),
        notes=f"{transaction_type.replace('_', ' ').title()} for submission {submission_id}",
        status='pending'
    )
    return transaction

def fix_submission_58():
    """
    Fix submission 58 by manually distributing missing rewards
    """
    print("🔧 FIXING SUBMISSION 58 REWARDS")
    print("=" * 50)
    
    try:
        # Get submission 58
        submission = ExerciseSubmission.objects.get(id=58)
        print(f"📝 Found submission: {submission.exercise.title}")
        print(f"👤 Student: {submission.student.username}")
        print(f"⭐ Score: {submission.average_score}")
        print(f"✅ Approved: {submission.is_approved}")
        print(f"📋 Currently reviewed: {submission.reviewed}")
        
        # Get all reviews
        reviews = ExerciseReview.objects.filter(submission=submission)
        print(f"\n👥 Reviews: {reviews.count()}")
        for i, review in enumerate(reviews, 1):
            print(f"  {i}. {review.reviewer.username}: {review.score}")
        
        # Get course
        course = submission.exercise.lesson.course
        print(f"\n🎓 Course: {course.title}")
        print(f"💰 Course price: {course.price} TEO")
        
        # Check existing rewards
        existing_rewards = BlockchainTransaction.objects.filter(
            related_object_id=str(submission.id)
        )
        print(f"\n💎 Existing rewards: {existing_rewards.count()}")
        existing_users = set()
        for reward in existing_rewards:
            print(f"  - {reward.user.username}: {reward.amount} TEO ({reward.transaction_type})")
            existing_users.add((reward.user.id, reward.transaction_type))
        
        # Calculate missing rewards
        print(f"\n🔍 CHECKING MISSING REWARDS")
        
        # 1. Exercise reward for student (if passed)
        passed = submission.average_score >= 6
        if passed:
            student_has_exercise_reward = (submission.student.id, 'exercise_reward') in existing_users
            if not student_has_exercise_reward:
                print(f"❌ Missing exercise_reward for {submission.student.username}")
                
                # Calculate reward
                reward_cap = int(course.price * 0.05)
                reward_amount = max(1, reward_cap // 2)  # At least 1 TEO
                
                print(f"💰 Creating exercise_reward: {reward_amount} TEO")
                create_reward_transaction(
                    submission.student,
                    reward_amount,
                    'exercise_reward',
                    submission.id
                )
                submission.reward_amount = reward_amount
                submission.save()
                print(f"✅ Exercise reward created!")
            else:
                print(f"✅ Exercise reward already exists for {submission.student.username}")
        else:
            print(f"❌ Student didn't pass (score: {submission.average_score}), no exercise reward")
        
        # 2. Review rewards for all reviewers
        reviewer_reward = max(1, int(course.price * 0.005))
        print(f"\n👥 Review reward amount: {reviewer_reward} TEO")
        
        for review in reviews:
            reviewer_has_reward = (review.reviewer.id, 'review_reward') in existing_users
            if not reviewer_has_reward:
                print(f"❌ Missing review_reward for {review.reviewer.username}")
                print(f"💰 Creating review_reward: {reviewer_reward} TEO")
                create_reward_transaction(
                    review.reviewer,
                    reviewer_reward,
                    'review_reward',
                    submission.id
                )
                print(f"✅ Review reward created!")
            else:
                print(f"✅ Review reward already exists for {review.reviewer.username}")
        
        # Mark submission as reviewed
        if not submission.reviewed:
            submission.reviewed = True
            submission.passed = passed
            submission.save()
            print(f"\n✅ Submission marked as reviewed: {submission.reviewed}")
        
        print(f"\n🎉 SUBMISSION 58 FIXED!")
        
        # Final verification
        print(f"\n📊 FINAL VERIFICATION")
        final_rewards = BlockchainTransaction.objects.filter(
            related_object_id=str(submission.id)
        ).order_by('-created_at')
        
        print(f"Total rewards now: {final_rewards.count()}")
        for reward in final_rewards:
            print(f"  - {reward.user.username}: {reward.amount} TEO ({reward.transaction_type}) - {reward.status}")
        
        return True
        
    except ExerciseSubmission.DoesNotExist:
        print("❌ Submission 58 not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_submission_58()
