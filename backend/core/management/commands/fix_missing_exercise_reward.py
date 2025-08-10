#!/usr/bin/env python
"""
Script per creare manualmente l'exercise reward mancante per student1
dopo il network error durante l'approvazione finale.
"""

import os
import django
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from courses.models import ExerciseSubmission
from rewards.models import BlockchainTransaction
from decimal import Decimal

def create_missing_exercise_reward():
    """
    Crea l'exercise reward mancante per student1 submission ID 70
    """
    print("=== CREAZIONE EXERCISE REWARD MANCANTE ===\n")
    
    try:
        # Trova student1 e il submission
        student1 = User.objects.get(username='student1')
        submission = ExerciseSubmission.objects.get(id=70)
        
        print(f"Student: {student1.username}")
        print(f"Submission ID: {submission.id}")
        print(f"Exercise: {submission.exercise.title}")
        print(f"Course: {submission.exercise.lesson.course.title}")
        print(f"Is approved: {submission.is_approved}")
        print(f"Average score: {submission.average_score}")
        
        # Verifica che non esista già un exercise reward
        existing_reward = BlockchainTransaction.objects.filter(
            user=student1,
            transaction_type='exercise_reward',
            related_object_id=submission.id
        ).first()
        
        if existing_reward:
            print(f"\n❌ Exercise reward già esistente (ID: {existing_reward.id})")
            return
        
        # Calcola l'ammonto del reward
        course = submission.exercise.lesson.course
        reward_amount = Decimal('1.5')  # Reward standard per exercise completion
        
        # Verifica che il reward pool abbia fondi sufficienti
        pool_balance = course.get_reward_pool_balance()
        print(f"\nReward pool balance: {pool_balance} TEO")
        print(f"Reward amount needed: {reward_amount} TEO")
        
        if pool_balance < reward_amount:
            print("❌ Fondi insufficienti nel reward pool")
            return
        
        # Crea la transazione reward
        with transaction.atomic():
            reward_transaction = BlockchainTransaction.objects.create(
                user=student1,
                transaction_type='exercise_reward',
                amount=reward_amount,
                related_object_id=submission.id,
                notes=f"Exercise completion reward per '{submission.exercise.title}' - Created manually after network error"
            )
            
            print(f"\n✅ Exercise reward creato:")
            print(f"  - Transaction ID: {reward_transaction.id}")
            print(f"  - Amount: {reward_transaction.amount} TEO")
            print(f"  - Status: {reward_transaction.status}")
            print(f"  - Created: {reward_transaction.created_at}")
        
        print(f"\n🎯 Exercise reward creato con successo!")
        print(f"Il reward verrà processato automaticamente dal sistema.")
        
    except User.DoesNotExist:
        print("❌ Student1 non trovato")
    except ExerciseSubmission.DoesNotExist:
        print("❌ Submission 70 non trovato")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_missing_exercise_reward()
