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

def test_new_review_system():
    """
    Test the new review and reward system by creating a new submission and reviews
    """
    print("🧪 TESTING NEW REVIEW SYSTEM")
    print("=" * 50)
    
    try:
        # Find an exercise to test with
        exercises = Exercise.objects.all()[:5]
        print(f"Available exercises: {exercises.count()}")
        for ex in exercises:
            print(f"  - {ex.id}: {ex.title}")
        
        if not exercises:
            print("❌ No exercises found")
            return False
        
        # Use the first exercise
        exercise = exercises[0]
        print(f"\n📝 Using exercise: {exercise.title}")
        
        # Get users for testing
        students = User.objects.filter(role='student')[:2]
        teachers = User.objects.filter(role='teacher')[:2] 
        
        print(f"👥 Available students: {[s.username for s in students]}")
        print(f"👥 Available teachers: {[t.username for t in teachers]}")
        
        if len(students) < 1:
            print("❌ Need at least 1 student")
            return False
        
        if len(teachers) < 2:
            print("❌ Need at least 2 teachers for review")
            return False
        
        # Create a new submission
        student = students[0]
        submission = ExerciseSubmission.objects.create(
            exercise=exercise,
            student=student,
            content="Test submission content for testing reward system"
        )
        
        print(f"\n✅ Created submission {submission.id} by {student.username}")
        
        # Assign reviewers
        reviewers = [teachers[0], teachers[1]]
        if len(students) > 1:
            reviewers.append(students[1])  # Add a second student as reviewer
        
        submission.reviewers.set(reviewers)
        print(f"👥 Assigned reviewers: {[r.username for r in reviewers]}")
        
        # Create reviews 
        scores = [7, 8, 6]  # Good scores to ensure passing
        for i, reviewer in enumerate(reviewers):
            review = ExerciseReview.objects.create(
                submission=submission,
                reviewer=reviewer,
                score=scores[i] if i < len(scores) else 7
            )
            review.reviewed_at = review.created_at
            review.save()
            print(f"✅ Review {i+1}: {reviewer.username} gave score {review.score}")
        
        # Check if rewards were created automatically
        print(f"\n🔍 CHECKING AUTOMATIC REWARD CREATION")
        
        # Refresh submission
        submission.refresh_from_db()
        print(f"Submission reviewed: {submission.reviewed}")
        print(f"Submission passed: {submission.passed}")
        print(f"Average score: {submission.average_score}")
        
        # Check for reward transactions
        rewards = BlockchainTransaction.objects.filter(
            related_object_id=str(submission.id)
        ).order_by('-created_at')
        
        print(f"\n💰 REWARD TRANSACTIONS: {rewards.count()}")
        
        if rewards.count() > 0:
            for reward in rewards:
                print(f"  - {reward.user.username}: {reward.amount} TEO ({reward.transaction_type}) - {reward.status}")
            print("✅ Rewards were created automatically!")
        else:
            print("❌ No rewards found - system needs debugging")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_new_review_system()
