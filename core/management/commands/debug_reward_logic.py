#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import ExerciseSubmission, ExerciseReview, Course
from rewards.models import BlockchainTransaction

User = get_user_model()

def debug_submission_reward_logic():
    print("=== DEBUG SUBMISSION REWARD LOGIC ===")
    
    # Get student1
    try:
        student1 = User.objects.get(username='student1')
        print(f"Student1: {student1.username}")
    except User.DoesNotExist:
        print("❌ Student1 not found")
        return
    
    # Get last submission
    submission = ExerciseSubmission.objects.filter(student=student1).order_by('-submitted_at').first()
    
    if not submission:
        print("❌ No submissions found for student1")
        return
    
    print(f"\nSubmission details:")
    print(f"  ID: {submission.id}")
    print(f"  Exercise: {submission.exercise.title}")
    print(f"  Passed: {submission.passed}")
    print(f"  Reviewed: {submission.reviewed}")
    print(f"  Reward amount: {getattr(submission, 'reward_amount', 'N/A')}")
    
    # Check reviews
    reviews = ExerciseReview.objects.filter(submission=submission)
    print(f"\nReviews ({len(reviews)}):")
    scores = []
    for review in reviews:
        print(f"  - {review.reviewer.username}: score={review.score}")
        if review.score is not None:
            scores.append(review.score)
    
    if scores:
        average = sum(scores) / len(scores)
        passed_calculated = average >= 6
        print(f"\nCalculated average: {average}")
        print(f"Should pass (>= 6): {passed_calculated}")
    
    # Check course and pricing
    course = None
    try:
        if hasattr(submission.exercise, 'lesson') and submission.exercise.lesson:
            course = submission.exercise.lesson.course
        elif hasattr(submission.exercise, 'course') and submission.exercise.course:
            course = submission.exercise.course
    except AttributeError:
        pass
    
    if course:
        print(f"\nCourse details:")
        print(f"  Title: {course.title}")
        print(f"  Price: {course.price}")
        print(f"  Reward distributed: {getattr(course, 'reward_distributed', 'N/A')}")
        
        # Calculate expected rewards
        reward_max = int(course.price * 0.15)
        reward_distributed = getattr(course, 'reward_distributed', 0)
        reward_remaining = reward_max - reward_distributed
        reward_cap = max(1, int(course.price * 0.05))
        
        print(f"  Reward max (15%): {reward_max}")
        print(f"  Reward distributed: {reward_distributed}")
        print(f"  Reward remaining: {reward_remaining}")
        print(f"  Reward cap (5%): {reward_cap}")
        
        if passed_calculated and reward_remaining > 0:
            print(f"  ✅ Should create exercise reward")
        else:
            print(f"  ❌ Should NOT create exercise reward (passed={passed_calculated}, remaining={reward_remaining})")
    else:
        print(f"\n❌ No course found for submission")
    
    # Check existing rewards
    exercise_rewards = BlockchainTransaction.objects.filter(
        user=student1,
        transaction_type='exercise_reward',
        related_object_id=submission.id
    )
    
    review_rewards = BlockchainTransaction.objects.filter(
        transaction_type='review_reward',
        related_object_id=submission.id
    )
    
    print(f"\nExisting rewards:")
    print(f"  Exercise rewards for student1: {exercise_rewards.count()}")
    for reward in exercise_rewards:
        print(f"    - Amount: {reward.amount}, Status: {reward.status}, Created: {reward.created_at}")
    
    print(f"  Review rewards: {review_rewards.count()}")
    for reward in review_rewards:
        print(f"    - User: {reward.user.username}, Amount: {reward.amount}, Status: {reward.status}")

if __name__ == "__main__":
    debug_submission_reward_logic()
