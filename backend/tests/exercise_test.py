# =======================================
# 🎯 TEST COMPLETO SISTEMA ESERCIZI
# ========================================

print("🚀 STARTING COMPLETE EXERCISE SYSTEM TEST")
print("=" * 60)

# Setup Django
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from backend.services.db_teocoin_service import DBTeoCoinService
from users.models import User
from courses.models import Course, Lesson, Exercise, ExerciseSubmission, ExerciseReview
from backend.rewards.blockchain_rewards import BlockchainRewards, BlockchainRewardManager
from decimal import Decimal
from django.utils import timezone
import random

# Inizializza servizio
db_service = DBTeoCoinService()

print("✅ Services initialized")

# ========================================
# 1. TROVA/CREA DATI DI TEST
# ========================================

print("\n📚 1. SETTING UP TEST DATA")
print("-" * 40)

# Trova studente
student = User.objects.filter(role='student').first()
if not student:
    print("⚠️  No student found, using first available user")
    student = User.objects.first()

print(f"   📘 Student: {student.username} (ID: {student.id})")

# Trova teacher/reviewer
teacher = User.objects.filter(role='teacher').first()
if not teacher:
    teacher = User.objects.filter(is_staff=True).first()

print(f"   👨‍🏫 Teacher/Reviewer: {teacher.username if teacher else 'None found'}")

# Trova corso ed esercizio
course = Course.objects.first()
if not course:
    print("❌ No course found - cannot test exercises")
    exit()

    print(f"   📖 Course: {course.title} (Price: €{course.price_eur})")# Trova lezione
lesson = course.lessons_in_course.first()
if not lesson:
    print("❌ No lesson found in course")
    exit()

print(f"   📝 Lesson: {lesson.title}")

# Trova esercizio
exercise = lesson.exercises.first()
if not exercise:
    print("❌ No exercise found in lesson")
    exit()

print(f"   🎯 Exercise: {exercise.title}")

# ========================================
# 2. TEST CALCOLO REWARD ESERCIZIO
# ========================================

print("\n💰 2. TESTING EXERCISE REWARD CALCULATION")
print("-" * 40)

# Test calcolo reward per il corso
try:
    from backend.rewards.blockchain_rewards import BlockchainRewardCalculator
    
    # Calcola pool reward totale del corso
    total_pool = BlockchainRewardCalculator.calculate_course_reward_pool(course)
    print(f"   📊 Course total reward pool: {total_pool} TEO")
    
    # Conta esercizi nel corso
    total_exercises = 0
    for l in course.lessons_in_course.all():
        exercise_count = l.exercises.count()
        total_exercises += exercise_count
        print(f"      - Lesson '{l.title}': {exercise_count} exercises")
    
    print(f"   🔢 Total exercises in course: {total_exercises}")
    
    if total_exercises > 0:
        # Distribuisce reward tra esercizi
        exercise_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(
            course, total_exercises
        )
        print(f"   🎁 Exercise rewards distribution: {exercise_rewards}")
        
        # Trova reward per il nostro esercizio specifico
        exercise_index = 0
        current_exercise_index = 0
        for l in course.lessons_in_course.all():
            for ex in l.exercises.all():
                if ex.id == exercise.id:
                    current_exercise_index = exercise_index
                    break
                exercise_index += 1
        
        our_exercise_reward = exercise_rewards[current_exercise_index]
        print(f"   🎯 Our exercise '{exercise.title}' reward: {our_exercise_reward} TEO")
    
except Exception as e:
    print(f"   ❌ Error calculating rewards: {e}")

# ========================================
# 3. VERIFICA BALANCE INIZIALE STUDENTE
# ========================================

print("\n💳 3. CHECKING STUDENT INITIAL BALANCE")
print("-" * 40)

try:
    initial_balance = db_service.get_balance(student)
    print(f"   💰 Student initial balance: {initial_balance} TEO")
    
    # Test che get_balance funzioni (era il bug principale)
    print("   ✅ get_balance method works correctly")
    
except Exception as e:
    print(f"   ❌ Error getting student balance: {e}")
    print("   🚨 This indicates the DBTeoCoinService fix didn't work!")

# ========================================
# 4. CREA/TROVA EXERCISE SUBMISSION
# ========================================

print("\n📄 4. CREATING/FINDING EXERCISE SUBMISSION")
print("-" * 40)

# Cerca submission esistente o creane una nuova
submission = ExerciseSubmission.objects.filter(
    exercise=exercise,
    student=student
).first()

if submission:
    print(f"   📋 Found existing submission: ID {submission.id}")
    print(f"      Status: {submission.status}")
    print(f"      Submitted: {submission.submitted_at}")
    print(f"      Current reward_amount: {submission.reward_amount}")
else:
    print("   📝 Creating new exercise submission...")
    try:
        submission = ExerciseSubmission.objects.create(
            exercise=exercise,
            student=student,
            content="Test submission for exercise reward system",
            status='submitted',
            submitted_at=timezone.now()
        )
        print(f"   ✅ Created submission: ID {submission.id}")
    except Exception as e:
        print(f"   ❌ Error creating submission: {e}")

# ========================================
# 5. TEST ASSEGNAZIONE REWARD ESERCIZIO
# ========================================

print("\n🎁 5. TESTING EXERCISE REWARD ASSIGNMENT")
print("-" * 40)

if submission:
    try:
        # Verifica se già premiato
        from backend.rewards.models import BlockchainTransaction
        existing_reward = BlockchainTransaction.objects.filter(
            user=student,
            transaction_type='exercise_reward',
            related_object_id=str(submission.id)
        ).first()
        
        if existing_reward:
            print(f"   ⚠️  Exercise already rewarded (Transaction ID: {existing_reward.id})")
            print(f"      Amount: {existing_reward.amount} TEO")
            print(f"      Status: {existing_reward.status}")
        else:
            print("   🚀 Awarding exercise completion reward...")
            
            # Usa il metodo fixato
            result = BlockchainRewards.award_exercise_completion(submission)
            
            if result:
                print(f"   ✅ Exercise reward assigned successfully!")
                print(f"      Transaction ID: {result.id}")
                print(f"      Amount: {result.amount} TEO")
                print(f"      Status: {result.status}")
                
                # Verifica nuovo balance studente
                new_balance = db_service.get_balance(student)
                balance_increase = new_balance - initial_balance
                print(f"   💰 Student balance: {initial_balance} → {new_balance} TEO")
                print(f"   📈 Balance increase: +{balance_increase} TEO")
                
                # Verifica che la submission sia aggiornata
                submission.refresh_from_db()
                print(f"   📋 Submission reward_amount updated: {submission.reward_amount}")
                
            else:
                print("   ❌ Exercise reward assignment failed!")
                
    except Exception as e:
        print(f"   ❌ Error in exercise reward assignment: {e}")
        import traceback
        traceback.print_exc()

# ========================================
# 6. TEST SISTEMA REVIEW (SE DISPONIBILE)
# ========================================

print("\n🔍 6. TESTING REVIEW SYSTEM")
print("-" * 40)

if submission and teacher:
    try:
        # Cerca review esistente
        review = ExerciseReview.objects.filter(
            submission=submission,
            reviewer=teacher
        ).first()
        
        if review:
            print(f"   📝 Found existing review: ID {review.id}")
            print(f"      Status: {review.status}")
            print(f"      Score: {review.score}")
        else:
            print("   📝 Creating test review...")
            review = ExerciseReview.objects.create(
                submission=submission,
                reviewer=teacher,
                status='completed',
                score=85,
                feedback="Good work! Test review for reward system.",
                reviewed_at=timezone.now()
            )
            print(f"   ✅ Created review: ID {review.id}")
        
        # Test reviewer reward
        if review and submission.reward_amount and submission.reward_amount > 0:
            print("   🎁 Testing reviewer reward...")
            
            # Verifica se reviewer già premiato
            existing_review_reward = BlockchainTransaction.objects.filter(
                user=teacher,
                transaction_type='review_reward',
                related_object_id=str(review.id)
            ).first()
            
            if existing_review_reward:
                print(f"      ⚠️  Reviewer already rewarded: {existing_review_reward.amount} TEO")
            else:
                # Verifica balance reviewer iniziale
                reviewer_initial = db_service.get_balance(teacher)
                print(f"      💰 Reviewer initial balance: {reviewer_initial} TEO")
                
                # Assegna reward per review
                review_result = BlockchainRewards.award_review_completion(review)
                
                if review_result:
                    reviewer_new = db_service.get_balance(teacher)
                    reviewer_increase = reviewer_new - reviewer_initial
                    print(f"      ✅ Reviewer reward assigned: {review_result.amount} TEO")
                    print(f"      💰 Reviewer balance: {reviewer_initial} → {reviewer_new} TEO (+{reviewer_increase})")
                else:
                    print("      ❌ Reviewer reward assignment failed!")
        else:
            print("   ⚠️  Cannot test reviewer reward (no submission reward_amount)")
            
    except Exception as e:
        print(f"   ❌ Error in review system test: {e}")

# ========================================
# 7. VERIFICA STATO FINALE
# ========================================

print("\n📊 7. FINAL SYSTEM STATE")
print("-" * 40)

try:
    # Balance finali
    final_student_balance = db_service.get_balance(student)
    print(f"   👨‍🎓 Student final balance: {final_student_balance} TEO")
    
    if teacher:
        final_teacher_balance = db_service.get_balance(teacher)
        print(f"   👨‍🏫 Teacher final balance: {final_teacher_balance} TEO")
    
    # Transazioni nel database
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM blockchain_dbteocointransaction WHERE user_id = %s", [student.id])
        student_transactions = cursor.fetchone()[0]
        print(f"   📊 Student transactions in DB: {student_transactions}")
        
        if teacher:
            cursor.execute("SELECT COUNT(*) FROM blockchain_dbteocointransaction WHERE user_id = %s", [teacher.id])
            teacher_transactions = cursor.fetchone()[0]
            print(f"   📊 Teacher transactions in DB: {teacher_transactions}")
    
    # Reward transactions
    reward_transactions = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward']
    ).count()
    print(f"   🎁 Total reward transactions: {reward_transactions}")
    
except Exception as e:
    print(f"   ❌ Error checking final state: {e}")

print("\n" + "=" * 60)
print("🏁 EXERCISE SYSTEM TEST COMPLETED")
print("✅ Check the results above to verify everything works!")
print("=" * 60)