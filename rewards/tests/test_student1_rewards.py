#!/usr/bin/env python
"""
Test per verificare l'ultimo exercise submission dello studente 1
e controllare che tutti i reward siano stati pagati correttamente.
"""

import os
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from courses.models import ExerciseSubmission, Course, Exercise
from rewards.models import BlockchainTransaction
from django.utils import timezone
from datetime import timedelta

def test_student1_latest_submission():
    """
    Test dell'ultimo submission dello studente 1 e verifica dei reward
    """
    print("=== TEST STUDENT 1 LATEST SUBMISSION ===\n")
    
    try:
        # Trova lo studente 1
        student1 = User.objects.get(username='student1')
        print(f"✓ Student1 trovato: {student1.username} ({student1.email})")
        
        # Trova l'ultimo submission dello studente 1
        latest_submission = ExerciseSubmission.objects.filter(
            student=student1
        ).order_by('-submitted_at').first()
        
        if not latest_submission:
            print("❌ Nessun submission trovato per student1")
            return
            
        print(f"\n--- ULTIMO SUBMISSION ---")
        print(f"ID: {latest_submission.id}")
        print(f"Exercise: {latest_submission.exercise.title}")
        print(f"Course: {latest_submission.exercise.lesson.course.title}")
        print(f"Status: {latest_submission.status}")
        print(f"Submitted: {latest_submission.submitted_at}")
        print(f"Grade: {latest_submission.grade}")
        print(f"Is Approved: {latest_submission.is_approved}")
        
        # Conta quante review sono necessarie
        course = latest_submission.exercise.lesson.course
        required_reviews = max(1, int(course.price * 0.05))
        print(f"Required reviews: {required_reviews}")
        
        # Trova tutte le review per questo submission
        reviews = ExerciseSubmission.objects.filter(
            reviewed_submission=latest_submission,
            status='approved'
        ).order_by('submitted_at')
        
        print(f"\n--- REVIEWS ({len(reviews)}/{required_reviews}) ---")
        for i, review in enumerate(reviews, 1):
            print(f"Review {i}:")
            print(f"  - Reviewer: {review.student.username}")
            print(f"  - Submitted: {review.submitted_at}")
            print(f"  - Grade: {review.grade}")
        
        # Verifica i reward transactions per questo submission
        print(f"\n--- REWARD TRANSACTIONS ---")
        
        # Exercise reward per lo studente che ha fatto il submission
        exercise_reward = BlockchainTransaction.objects.filter(
            user=student1,
            transaction_type='exercise_reward',
            related_object_id=latest_submission.id
        ).first()
        
        if exercise_reward:
            print(f"✓ Exercise reward trovato:")
            print(f"  - ID: {exercise_reward.id}")
            print(f"  - Amount: {exercise_reward.amount} TEO")
            print(f"  - Status: {exercise_reward.status}")
            print(f"  - Created: {exercise_reward.created_at}")
            if exercise_reward.tx_hash:
                print(f"  - TX Hash: {exercise_reward.tx_hash}")
            if exercise_reward.error_message:
                print(f"  - Error: {exercise_reward.error_message}")
        else:
            print("❌ Exercise reward NON trovato")
        
        # Review rewards per i reviewer
        print(f"\n--- REVIEW REWARDS ---")
        review_rewards = BlockchainTransaction.objects.filter(
            transaction_type='review_reward',
            related_object_id=latest_submission.id
        ).order_by('created_at')
        
        print(f"Found {len(review_rewards)} review reward transactions:")
        for i, reward in enumerate(review_rewards, 1):
            print(f"Review reward {i}:")
            print(f"  - ID: {reward.id}")
            print(f"  - User: {reward.user.username}")
            print(f"  - Amount: {reward.amount} TEO")
            print(f"  - Status: {reward.status}")
            print(f"  - Created: {reward.created_at}")
            if reward.tx_hash:
                print(f"  - TX Hash: {reward.tx_hash}")
            if reward.error_message:
                print(f"  - Error: {reward.error_message}")
        
        # Verifica che tutti i reward siano stati creati
        print(f"\n--- VERIFICA COMPLETEZZA ---")
        expected_reviews = len(reviews)
        found_review_rewards = len(review_rewards)
        
        print(f"Reviews completate: {expected_reviews}")
        print(f"Review rewards creati: {found_review_rewards}")
        print(f"Exercise reward creato: {'✓' if exercise_reward else '❌'}")
        
        if exercise_reward and found_review_rewards == expected_reviews:
            print("✅ TUTTI I REWARD SONO STATI CREATI CORRETTAMENTE")
        else:
            print("⚠️  MANCANO ALCUNI REWARD")
        
        # Verifica lo status dei reward
        print(f"\n--- STATUS PROCESSING ---")
        all_rewards = list(review_rewards)
        if exercise_reward:
            all_rewards.append(exercise_reward)
        
        completed_rewards = [r for r in all_rewards if r.status == 'completed']
        pending_rewards = [r for r in all_rewards if r.status == 'pending']
        failed_rewards = [r for r in all_rewards if r.status == 'failed']
        
        print(f"Completed: {len(completed_rewards)}/{len(all_rewards)}")
        print(f"Pending: {len(pending_rewards)}")
        print(f"Failed: {len(failed_rewards)}")
        
        if len(completed_rewards) == len(all_rewards):
            print("✅ TUTTI I REWARD SONO STATI PROCESSATI CON SUCCESSO")
        elif len(failed_rewards) > 0:
            print("❌ CI SONO REWARD FALLITI")
            for reward in failed_rewards:
                print(f"  - {reward.transaction_type} (ID: {reward.id}): {reward.error_message}")
        elif len(pending_rewards) > 0:
            print("⏳ CI SONO REWARD IN ATTESA DI PROCESSING")
        
        # Mostra il balance totale ricevuto
        print(f"\n--- BALANCE SUMMARY ---")
        total_received = sum(r.amount for r in completed_rewards if r.user == student1)
        print(f"Student1 total received from this submission: {total_received} TEO")
        
        for review in reviews:
            reviewer_rewards = [r for r in completed_rewards if r.user == review.student and r.transaction_type == 'review_reward']
            reviewer_total = sum(r.amount for r in reviewer_rewards)
            print(f"{review.student.username} total received: {reviewer_total} TEO")
        
    except User.DoesNotExist:
        print("❌ Student1 non trovato nel database")
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_student1_latest_submission()
