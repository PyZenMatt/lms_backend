
import os

import django
import pytest
from courses.models import (Course, ExerciseReview, ExerciseSubmission)
from django.utils import timezone
from rewards.blockchain_rewards import BlockchainRewards
from services.db_teocoin_service import DBTeoCoinService
from users.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()


@pytest.mark.quarantine
@pytest.mark.slow
@pytest.mark.django_db
def test_complete_exercise_system():
    db_service = DBTeoCoinService()
    student = User.objects.filter(
        role='student').first() or User.objects.first()
    teacher = User.objects.filter(role='teacher').first(
    ) or User.objects.filter(is_staff=True).first()
    course = Course.objects.first()
    assert course is not None, "No course found - cannot test exercises"
    lesson = course.lessons.first()
    assert lesson is not None, "No lesson found in course"
    exercise = lesson.exercises.first()
    assert exercise is not None, "No exercise found in lesson"

    # Calcolo reward
    from rewards.blockchain_rewards import BlockchainRewardCalculator
    total_pool = BlockchainRewardCalculator.calculate_course_reward_pool(
        course)
    total_exercises = sum(l.exercises.count() for l in course.lessons.all())
    if total_exercises > 0:
        exercise_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(
            course, total_exercises)
        exercise_index = 0
        current_exercise_index = 0
        for l in course.lessons.all():
            for ex in l.exercises.all():
                if ex.pk == exercise.pk:
                    current_exercise_index = exercise_index
                    break
                exercise_index += 1
        exercise_rewards[current_exercise_index]

    initial_balance = db_service.get_balance(student)

    # Submission
    submission = ExerciseSubmission.objects.filter(
        exercise=exercise, student=student).first()
    if not submission:
        submission = ExerciseSubmission.objects.create(
            exercise=exercise,
            student=student,
            content="Test submission for exercise reward system",
            status='submitted',
            submitted_at=timezone.now()
        )

    # Assegnazione reward esercizio
    from rewards.models import BlockchainTransaction
    existing_reward = BlockchainTransaction.objects.filter(
        user=student,
        transaction_type='exercise_reward',
        related_object_id=str(submission.pk)
    ).first()
    if not existing_reward:
        result = BlockchainRewards.award_exercise_completion(submission)
        assert result is not None, "Exercise reward assignment failed!"
        new_balance = db_service.get_balance(student)
        assert new_balance > initial_balance, "Student balance did not increase after reward"
        submission.refresh_from_db()
        assert submission.reward_amount is not None, "Submission reward_amount not updated"

    # Review system
    if teacher:
        review = ExerciseReview.objects.filter(
            submission=submission, reviewer=teacher).first()
        if not review:
            review = ExerciseReview.objects.create(
                submission=submission,
                reviewer=teacher,
                status='completed',
                score=85,
                feedback="Good work! Test review for reward system.",
                reviewed_at=timezone.now()
            )
        if review and submission.reward_amount and submission.reward_amount > 0:
            existing_review_reward = BlockchainTransaction.objects.filter(
                user=teacher,
                transaction_type='review_reward',
                related_object_id=str(review.pk)
            ).first()
            if not existing_review_reward:
                reviewer_initial = db_service.get_balance(teacher)
                review_result = BlockchainRewards.award_review_completion(
                    review)
                assert review_result is not None, "Reviewer reward assignment failed!"
                reviewer_new = db_service.get_balance(teacher)
                assert reviewer_new > reviewer_initial, "Reviewer balance did not increase after reward"

    # Stato finale
    final_student_balance = db_service.get_balance(student)
    assert final_student_balance is not None, "Student final balance missing"
    if teacher:
        final_teacher_balance = db_service.get_balance(teacher)
        assert final_teacher_balance is not None, "Teacher final balance missing"
