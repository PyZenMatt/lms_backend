#!/usr/bin/env python3
"""
🎯 SIMPLE EXERCISE SYSTEM TEST
Test exercise submission and reward system step by step
"""


def test_exercise_system():
    """Test exercise submission and TeoCoin reward system"""
    print("🎯 SIMPLE EXERCISE SYSTEM TEST")
    print("=" * 50)

    # Test 1: Import dependencies
    try:
        pass

        from courses.models import Course, ExerciseSubmission
        from rewards.blockchain_rewards import BlockchainRewards
        from services.db_teocoin_service import DBTeoCoinService
        from users.models import User

        print("✅ 1. Imports: SUCCESS")
    except Exception as e:
        print(f"❌ 1. Imports: FAILED - {e}")
        return False

    # Test 2: Setup services
    try:
        db_service = DBTeoCoinService()
        reward_system = BlockchainRewards()
        print("✅ 2. Service initialization: SUCCESS")
    except Exception as e:
        print(f"❌ 2. Service initialization: FAILED - {e}")
        return False

    # Test 3: Find test data
    try:
        # Find a student
        student = User.objects.filter(role="student").first()
        if not student:
            print("❌ 3. No student found")
            return False

        # Find a teacher/reviewer
        teacher = User.objects.filter(role="teacher").first()
        if not teacher:
            teacher = User.objects.filter(is_staff=True).first()
        if not teacher:
            print("❌ 3. No teacher found")
            return False

        # Find a course with exercises
        course = Course.objects.filter(
            lessons_in_course__exercises__isnull=False
        ).first()
        if not course:
            print("❌ 3. No course with exercises found")
            return False

        # Find an exercise
        lesson = course.lessons_in_course.filter(exercises__isnull=False).first()
        if not lesson:
            print("❌ 3. No lesson with exercises found")
            return False

        exercise = lesson.exercises.first()
        if not exercise:
            print("❌ 3. No exercise found")
            return False

        print(f"✅ 3. Test data found:")
        print(f"   👨‍🎓 Student: {student.username}")
        print(f"   👨‍🏫 Teacher: {teacher.username}")
        print(f"   📚 Course: {course.title}")
        print(f"   📖 Lesson: {lesson.title}")
        print(f"   📝 Exercise: {exercise.title}")

    except Exception as e:
        print(f"❌ 3. Test data lookup: FAILED - {e}")
        return False

    # Test 4: Check initial balances
    try:
        student_initial_balance = db_service.get_balance(student)
        teacher_initial_balance = db_service.get_balance(teacher)
        print(f"✅ 4. Initial balances:")
        print(f"   👨‍🎓 Student: {student_initial_balance} TEO")
        print(f"   👨‍🏫 Teacher: {teacher_initial_balance} TEO")
    except Exception as e:
        print(f"❌ 4. Balance check: FAILED - {e}")
        return False

    # Test 5: Check existing submission
    try:
        existing_submission = ExerciseSubmission.objects.filter(
            exercise=exercise, student=student
        ).first()

        if existing_submission:
            print(
                f"✅ 5. Found existing submission: ID {existing_submission.id}, Status: {existing_submission.status}"
            )
            submission = existing_submission
        else:
            print("✅ 5. No existing submission found - will create new one")
            submission = None

    except Exception as e:
        print(f"❌ 5. Submission check: FAILED - {e}")
        return False

    # Test 6: Create submission if needed
    if not submission:
        try:
            submission = ExerciseSubmission.objects.create(
                exercise=exercise,
                student=student,
                content="Test submission content for production debugging",
                status="submitted",
            )
            print(f"✅ 6. Created new submission: ID {submission.id}")
        except Exception as e:
            print(f"❌ 6. Submission creation: FAILED - {e}")
            return False
    else:
        print("✅ 6. Using existing submission")

    # Test 7: Test exercise completion reward
    try:
        print("🎯 7. Testing exercise completion reward...")

        # Check if already rewarded
        from blockchain.models import BlockchainTransaction

        existing_reward = BlockchainTransaction.objects.filter(
            user=student,
            transaction_type="exercise_completion",
            related_object_id=str(submission.id),
        ).first()

        if existing_reward:
            print(
                f"   ⚠️  Exercise already rewarded (Transaction ID: {existing_reward.id})"
            )
            print(f"   💰 Reward amount: {existing_reward.amount} TEO")
        else:
            print("   🎯 No existing reward found - testing reward system...")

            # Call the reward system
            result = reward_system.award_exercise_completion(submission)

            if result:
                print("   ✅ Reward system returned success")

                # Check balance change
                student_new_balance = db_service.get_balance(student)
                balance_change = student_new_balance - student_initial_balance
                print(
                    f"   💰 Student balance: {student_initial_balance} → {student_new_balance} TEO ({'+' if balance_change >= 0 else ''}{balance_change})"
                )

                # Check if transaction was created
                new_reward = BlockchainTransaction.objects.filter(
                    user=student,
                    transaction_type="exercise_completion",
                    related_object_id=str(submission.id),
                ).first()

                if new_reward:
                    print(
                        f"   ✅ Transaction created: ID {new_reward.id}, Amount: {new_reward.amount} TEO"
                    )
                else:
                    print("   ⚠️  No transaction record found")

            else:
                print("   ❌ Reward system returned failure")

        print("✅ 7. Exercise reward test: COMPLETED")

    except Exception as e:
        print(f"❌ 7. Exercise reward test: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 8: Test review reward (if teacher/reviewer exists)
    try:
        print("🎯 8. Testing review reward system...")

        # Check if submission has reviews
        from courses.models import ExerciseReview

        existing_review = ExerciseReview.objects.filter(
            submission=submission, reviewer=teacher
        ).first()

        if existing_review:
            print(
                f"   📝 Found existing review: ID {existing_review.id}, Status: {existing_review.status}"
            )
            review = existing_review
        else:
            print("   📝 Creating test review...")
            review = ExerciseReview.objects.create(
                submission=submission,
                reviewer=teacher,
                content="Test review for production debugging",
                rating=5,
                status="completed",
            )
            print(f"   ✅ Created review: ID {review.id}")

        # Test review reward
        existing_review_reward = BlockchainTransaction.objects.filter(
            user=teacher,
            transaction_type="review_completion",
            related_object_id=str(review.id),
        ).first()

        if existing_review_reward:
            print(
                f"   ⚠️  Review already rewarded (Transaction ID: {existing_review_reward.id})"
            )
            print(f"   💰 Reward amount: {existing_review_reward.amount} TEO")
        else:
            print("   🎯 No existing review reward - testing review reward...")

            result = reward_system.award_review_completion(review)

            if result:
                print("   ✅ Review reward system returned success")

                # Check teacher balance change
                teacher_new_balance = db_service.get_balance(teacher)
                teacher_balance_change = teacher_new_balance - teacher_initial_balance
                print(
                    f"   💰 Teacher balance: {teacher_initial_balance} → {teacher_new_balance} TEO ({'+' if teacher_balance_change >= 0 else ''}{teacher_balance_change})"
                )

                # Check transaction
                new_review_reward = BlockchainTransaction.objects.filter(
                    user=teacher,
                    transaction_type="review_completion",
                    related_object_id=str(review.id),
                ).first()

                if new_review_reward:
                    print(
                        f"   ✅ Review transaction created: ID {new_review_reward.id}, Amount: {new_review_reward.amount} TEO"
                    )
                else:
                    print("   ⚠️  No review transaction record found")

            else:
                print("   ❌ Review reward system returned failure")

        print("✅ 8. Review reward test: COMPLETED")

    except Exception as e:
        print(f"❌ 8. Review reward test: FAILED - {e}")
        import traceback

        traceback.print_exc()
        # Non-critical, continue

    # Test 9: Summary and database state
    try:
        print("📊 9. FINAL STATE SUMMARY:")

        # Final balances
        student_final_balance = db_service.get_balance(student)
        teacher_final_balance = db_service.get_balance(teacher)

        student_total_change = student_final_balance - student_initial_balance
        teacher_total_change = teacher_final_balance - teacher_initial_balance

        print(
            f"   👨‍🎓 Student: {student_initial_balance} → {student_final_balance} TEO ({'+' if student_total_change >= 0 else ''}{student_total_change})"
        )
        print(
            f"   👨‍🏫 Teacher: {teacher_initial_balance} → {teacher_final_balance} TEO ({'+' if teacher_total_change >= 0 else ''}{teacher_total_change})"
        )

        # Transaction count
        student_transactions = BlockchainTransaction.objects.filter(
            user=student
        ).count()
        teacher_transactions = BlockchainTransaction.objects.filter(
            user=teacher
        ).count()

        print(f"   📊 Student transactions: {student_transactions}")
        print(f"   📊 Teacher transactions: {teacher_transactions}")

        print("✅ 9. Summary: COMPLETED")

    except Exception as e:
        print(f"❌ 9. Summary: FAILED - {e}")
        return False

    print("\n🎉 EXERCISE SYSTEM TEST COMPLETED!")
    print("✅ Check the output above for any issues in the exercise reward flow")
    return True


if __name__ == "__main__":
    success = test_exercise_system()
    exit(0 if success else 1)
