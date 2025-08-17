#!/usr/bin/env python3
"""
🔍 SUBMISSION REWARD DEBUG TEST
Debug the exact point where exercise submission rewards fail
"""


def test_submission_reward_debug():
    """Debug exercise submission reward step by step"""
    print("🔍 SUBMISSION REWARD DEBUG TEST")
    print("=" * 50)

    try:
        # Imports
        from decimal import Decimal

        from blockchain.models import BlockchainTransaction
        from courses.models import ExerciseSubmission
        from rewards.blockchain_rewards import BlockchainRewards
        from services.db_teocoin_service import DBTeoCoinService
        print("✅ Imports successful")

        # Get services
        db_service = DBTeoCoinService()
        reward_system = BlockchainRewards()
        print("✅ Services initialized")

        # Find a submission to test with
        submission = ExerciseSubmission.objects.filter(
            status='submitted').first()
        if not submission:
            submission = ExerciseSubmission.objects.first()

        if not submission:
            print("❌ No submissions found in database")
            return False

        student = submission.student
        exercise = submission.exercise

        print(f"✅ Test submission found:")
        print(f"   📝 Submission ID: {submission.id}")
        print(f"   👨‍🎓 Student: {student.username}")
        print(f"   📚 Exercise: {exercise.title}")
        print(f"   🏆 Exercise reward: {exercise.teocoin_reward} TEO")

        # Step 1: Check if already rewarded
        print("\n🔍 STEP 1: Check existing reward")
        existing_reward = BlockchainTransaction.objects.filter(
            user=student,
            transaction_type='exercise_completion',
            related_object_id=str(submission.id)
        ).first()

        if existing_reward:
            print(
                f"   ⚠️  Already rewarded: Transaction {existing_reward.id}, Amount: {existing_reward.amount}")
        else:
            print("   ✅ No existing reward found")

        # Step 2: Check initial balance
        print("\n🔍 STEP 2: Check student balance")
        initial_balance = db_service.get_balance(student)
        print(f"   💰 Initial balance: {initial_balance} TEO")

        # Step 3: Test reward calculation
        print("\n🔍 STEP 3: Test reward calculation")
        expected_reward = exercise.teocoin_reward
        print(f"   🎯 Expected reward: {expected_reward} TEO")

        # Step 4: Test the reward system method
        print("\n🔍 STEP 4: Call reward system")
        print(f"   🎯 Calling reward_system.award_exercise_completion(submission)")

        try:
            result = reward_system.award_exercise_completion(submission)
            print(f"   📤 Reward system result: {result}")

            if result:
                print("   ✅ Reward system returned True")
            else:
                print("   ❌ Reward system returned False")

        except Exception as e:
            print(f"   ❌ Reward system exception: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Step 5: Check balance after
        print("\n🔍 STEP 5: Check balance after reward")
        final_balance = db_service.get_balance(student)
        balance_change = final_balance - initial_balance
        print(f"   💰 Final balance: {final_balance} TEO")
        print(
            f"   📈 Balance change: {'+' if balance_change >= 0 else ''}{balance_change} TEO")

        # Step 6: Check transaction created
        print("\n🔍 STEP 6: Check transaction record")
        new_transaction = BlockchainTransaction.objects.filter(
            user=student,
            transaction_type='exercise_completion',
            related_object_id=str(submission.id)
        ).order_by('-created_at').first()

        if new_transaction:
            print(f"   ✅ Transaction found: ID {new_transaction.id}")
            print(f"   💰 Amount: {new_transaction.amount} TEO")
            print(f"   📅 Created: {new_transaction.created_at}")
            print(f"   📝 Description: {new_transaction.description}")
        else:
            print("   ❌ No transaction record found")

        # Step 7: Debug the DBTeoCoinService directly
        print("\n🔍 STEP 7: Test DBTeoCoinService directly")
        try:
            test_amount = Decimal('1.0')
            direct_result = db_service.add_balance(
                student,
                test_amount,
                'test_direct',
                'Direct test of add_balance method'
            )

            if direct_result:
                print(f"   ✅ Direct add_balance works: +{test_amount} TEO")

                # Check balance
                test_balance = db_service.get_balance(student)
                print(f"   💰 Balance after direct test: {test_balance} TEO")
            else:
                print("   ❌ Direct add_balance failed")

        except Exception as e:
            print(f"   ❌ Direct add_balance exception: {e}")

        # Step 8: Check database configuration
        print("\n🔍 STEP 8: Check TeoCoin system configuration")
        try:
            from django.conf import settings
            use_db_teocoin = getattr(settings, 'USE_DB_TEOCOIN_SYSTEM', False)
            teocoin_system = getattr(settings, 'TEOCOIN_SYSTEM', 'unknown')

            print(f"   ⚙️  USE_DB_TEOCOIN_SYSTEM: {use_db_teocoin}")
            print(f"   ⚙️  TEOCOIN_SYSTEM: {teocoin_system}")

        except Exception as e:
            print(f"   ❌ Configuration check failed: {e}")

        print("\n🎉 DEBUG TEST COMPLETED!")
        print("🔍 Check the steps above to identify where the reward system fails")

        return True

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_submission_reward_debug()
    exit(0 if success else 1)
