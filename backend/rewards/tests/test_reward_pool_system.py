#!/usr/bin/env python
"""
Test del nuovo sistema di reward pool
Testa che i reward vengano trasferiti dalla pool invece di essere mintati
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, Exercise, ExerciseSubmission, ExerciseReview
from rewards.models import TeoCoinTransaction, BlockchainTransaction
from rewards.blockchain_rewards import BlockchainRewardManager
from blockchain.blockchain import get_reward_pool_balance

User = get_user_model()

def test_reward_pool_system():
    """
    Test completo del sistema di reward pool
    """
    print("=== TEST SISTEMA REWARD POOL ===")
    
    # 1. Controlla balance iniziale della reward pool
    initial_balance = get_reward_pool_balance()
    print(f"Balance iniziale reward pool: {initial_balance} TEO")
    
    # 2. Crea utenti di test (se non esistono)
    try:
        student = User.objects.get(email='student_test@example.com')
        print("Utente studente trovato")
    except User.DoesNotExist:
        student = User.objects.create_user(
            email='student_test@example.com',
            password='testpass123',
            role='student'
        )
        # Aggiorna wallet address direttamente nel modello User
        student.wallet_address = '0x1234567890123456789012345678901234567890'
        student.save()
        print("Utente studente creato")
    
    try:
        teacher = User.objects.get(email='teacher_test@example.com')
        print("Utente teacher trovato")
    except User.DoesNotExist:
        teacher = User.objects.create_user(
            email='teacher_test@example.com',
            password='testpass123',
            role='teacher'
        )
        teacher.wallet_address = '0x9876543210987654321098765432109876543210'
        teacher.save()
        print("Utente teacher creato")
    
    # 3. Crea corso di test
    course, created = Course.objects.get_or_create(
        title="Test Course Reward Pool",
        defaults={
            'description': 'Corso per testare il sistema reward pool',
            'instructor': teacher,
            'price': Decimal('10.00')
        }
    )
    if created:
        print("Corso di test creato")
    else:
        print("Corso di test già esistente")
    
    # 4. Crea lezione di test
    lesson, created = Lesson.objects.get_or_create(
        title="Test Lesson",
        course=course,
        defaults={
            'description': 'Lezione di test',
            'order': 1
        }
    )
    if created:
        print("Lezione di test creata")
    
    # 5. Crea esercizio di test
    exercise, created = Exercise.objects.get_or_create(
        title="Test Exercise",
        lesson=lesson,
        defaults={
            'description': 'Esercizio di test per reward pool',
            'question': 'Domanda di test'
        }
    )
    if created:
        print("Esercizio di test creato")
    
    # 6. Simula submission di esercizio
    submission, created = ExerciseSubmission.objects.get_or_create(
        exercise=exercise,
        student=student,
        defaults={
            'answer': 'Risposta di test',
            'is_correct': True
        }
    )
    if created:
        print("Submission di test creata")
    
    # 7. Testa reward per completamento esercizio
    print("\n--- Test Reward Esercizio ---")
    try:
        # Elimina eventuali transazioni precedenti per questo test
        TeoCoinTransaction.objects.filter(
            user=student,
            transaction_type='exercise_reward',
            related_object_id=submission.id
        ).delete()
        
        blockchain_tx = BlockchainRewardManager.award_exercise_completion(submission)
        
        if blockchain_tx:
            print(f"✅ Reward esercizio assegnato con successo!")
            print(f"   TX Hash: {blockchain_tx.tx_hash}")
            print(f"   Amount: {blockchain_tx.amount} TEO")
            print(f"   Status: {blockchain_tx.status}")
        else:
            print("❌ Errore nell'assegnazione reward esercizio")
            
    except Exception as e:
        print(f"❌ Errore nel test reward esercizio: {e}")
    
    # 8. Testa reward per review
    print("\n--- Test Reward Review ---")
    try:
        # Crea una review di test
        review, created = ExerciseReview.objects.get_or_create(
            submission=submission,
            reviewer=teacher,
            defaults={
                'is_approved': True,
                'feedback': 'Ottimo lavoro!'
            }
        )
        
        if created:
            print("Review di test creata")
        
        # Elimina eventuali transazioni precedenti per questo test
        TeoCoinTransaction.objects.filter(
            user=teacher,
            transaction_type='review_reward',
            related_object_id=review.id
        ).delete()
        
        blockchain_tx = BlockchainRewardManager.award_review_completion(review)
        
        if blockchain_tx:
            print(f"✅ Reward review assegnato con successo!")
            print(f"   TX Hash: {blockchain_tx.tx_hash}")
            print(f"   Amount: {blockchain_tx.amount} TEO")
            print(f"   Status: {blockchain_tx.status}")
        else:
            print("❌ Errore nell'assegnazione reward review")
            
    except Exception as e:
        print(f"❌ Errore nel test reward review: {e}")
    
    # 9. Controlla balance finale della reward pool
    final_balance = get_reward_pool_balance()
    print(f"\n--- Risultati Finali ---")
    print(f"Balance finale reward pool: {final_balance} TEO")
    
    if final_balance < initial_balance:
        difference = initial_balance - final_balance
        print(f"✅ TEO trasferiti dalla pool: {difference}")
        print("✅ Sistema reward pool funziona correttamente!")
    else:
        print("⚠️  Nessun cambiamento nel balance della pool")
    
    # 10. Mostra transazioni create
    print("\n--- Transazioni Create ---")
    student_transactions = TeoCoinTransaction.objects.filter(user=student)
    teacher_transactions = TeoCoinTransaction.objects.filter(user=teacher)
    
    print(f"Transazioni studente: {student_transactions.count()}")
    for tx in student_transactions.order_by('-created_at')[:3]:
        print(f"  - {tx.transaction_type}: {tx.amount/1000} TEO")
    
    print(f"Transazioni teacher: {teacher_transactions.count()}")
    for tx in teacher_transactions.order_by('-created_at')[:3]:
        print(f"  - {tx.transaction_type}: {tx.amount/1000} TEO")

if __name__ == "__main__":
    test_reward_pool_system()
