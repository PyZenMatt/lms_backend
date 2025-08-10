#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview, Exercise, Lesson, Course
from rewards.models import BlockchainTransaction
from users.models import User
from django.utils import timezone
import logging
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_scenario():
    """
    Create a test scenario with a submission that needs one more review to be completed
    """
    print("=== Creating Test Scenario ===")
    
    # Find or create a course and exercise
    course = Course.objects.filter(is_approved=True).first()
    if not course:
        print("❌ No approved course found")
        return None, None
    
    print(f"Using course: {course.title}")
    
    # Find an exercise in this course
    lesson = course.lessons.first()
    if not lesson:
        print("❌ No lesson found in course")
        return None, None
    
    exercise = lesson.exercises.first()
    if not exercise:
        print("❌ No exercise found in lesson")
        return None, None
    
    print(f"Using exercise: {exercise.title}")
    
    # Find a student enrolled in the course
    student = course.students.first()
    if not student:
        print("❌ No student enrolled in course")
        return None, None
    
    print(f"Using student: {student.username}")
    
    # Check if submission already exists
    submission = ExerciseSubmission.objects.filter(
        exercise=exercise,
        student=student
    ).first()
    
    if submission:
        print(f"Found existing submission: {submission.id}")
    else:
        # Create new submission
        submission = ExerciseSubmission.objects.create(
            exercise=exercise,
            student=student,
            content="Test submission for network error debugging"
        )
        
        # Assign reviewers
        other_users = User.objects.exclude(id=student.id)[:3]
        for reviewer in other_users:
            review, created = ExerciseReview.objects.get_or_create(
                submission=submission,
                reviewer=reviewer,
                defaults={'assigned_at': timezone.now()}
            )
            if created:
                submission.reviewers.add(reviewer)
        
        submission.save()
        print(f"Created new submission: {submission.id}")
    
    # Check review status
    reviews = ExerciseReview.objects.filter(submission=submission)
    print(f"Reviews for submission: {reviews.count()}")
    
    for review in reviews:
        print(f"  - {review.reviewer.username}: Score={review.score}")
    
    # Make sure we have at least one incomplete review
    incomplete_reviews = reviews.filter(score__isnull=True)
    if incomplete_reviews.count() == 0:
        # Reset one review to be incomplete
        last_review = reviews.last()
        last_review.score = None
        last_review.reviewed_at = None
        last_review.save()
        print(f"Reset review by {last_review.reviewer.username} to incomplete")
        
        incomplete_reviews = reviews.filter(score__isnull=True)
    
    print(f"Incomplete reviews: {incomplete_reviews.count()}")
    
    return submission, incomplete_reviews.first()

def simulate_review_completion(submission, review_to_complete):
    """
    Simulate completing the last review and monitor for network errors
    """
    print("\n=== Simulating Review Completion ===")
    
    print(f"About to complete review by {review_to_complete.reviewer.username}")
    print(f"Submission {submission.id} reviewed status: {submission.reviewed}")
    
    # Check existing reward transactions
    existing_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        related_object_id=str(submission.id)
    )
    print(f"Existing reward transactions: {existing_rewards.count()}")
    
    # Simulate what happens in ReviewExerciseView
    try:
        # Complete the review
        review_to_complete.score = random.randint(6, 10)  # Pass score
        review_to_complete.reviewed_at = timezone.now()
        review_to_complete.save()
        
        print(f"✅ Review completed with score {review_to_complete.score}")
        
        # Wait a moment for signals to process
        import time
        time.sleep(2)
        
        # Check if submission was marked as reviewed
        submission.refresh_from_db()
        print(f"Submission reviewed status after: {submission.reviewed}")
        print(f"Submission passed status: {submission.passed}")
        
        # Check reward transactions
        new_rewards = BlockchainTransaction.objects.filter(
            transaction_type__in=['exercise_reward', 'review_reward'],
            related_object_id=str(submission.id)
        )
        print(f"Total reward transactions after: {new_rewards.count()}")
        
        for reward in new_rewards.order_by('-created_at')[:5]:
            print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username} - Status: {reward.status}")
            if reward.status == 'failed':
                print(f"    Error: {reward.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during review completion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_review_flow():
    """
    Test the complete review flow that triggers when last reviewer submits
    """
    print("=== Testing Full Review Flow ===")
    
    submission, review_to_complete = create_test_scenario()
    
    if not submission or not review_to_complete:
        print("❌ Could not create test scenario")
        return
    
    success = simulate_review_completion(submission, review_to_complete)
    
    if success:
        print("✅ Review flow simulation completed successfully")
    else:
        print("❌ Review flow simulation failed")

if __name__ == "__main__":
    try:
        test_full_review_flow()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
