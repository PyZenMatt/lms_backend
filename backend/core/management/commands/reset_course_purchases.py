#!/usr/bin/env python
"""
Script per resettare gli acquisti dei corsi
- Rimuove studenti dai corsi
- Cancella transazioni blockchain correlate
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Course
from rewards.models import BlockchainTransaction
from users.models import User

def reset_course_purchases():
    print("=== RESET ACQUISTI CORSI ===")
    
    # 1. Mostra stato attuale
    print("Stato attuale:")
    courses = Course.objects.all()
    for course in courses:
        students = course.students.all()
        print(f"  Corso: {course.title} (ID: {course.id})")
        if students:
            print(f"    Studenti iscritti: {[s.username for s in students]}")
        else:
            print(f"    Nessuno studente iscritto")
    
    # 2. Rimuovi tutti gli studenti dai corsi
    print("\nRimuovendo studenti dai corsi...")
    total_removed = 0
    for course in courses:
        count = course.students.count()
        course.students.clear()
        total_removed += count
        print(f"  Rimossi {count} studenti da '{course.title}'")
    
    print(f"Totale studenti rimossi: {total_removed}")
    
    # 3. Cancella transazioni blockchain correlate ai corsi
    print("\nCancellando transazioni blockchain...")
    course_purchase_txs = BlockchainTransaction.objects.filter(
        transaction_type__in=['course_purchase', 'course_earned', 'platform_commission']
    )
    
    count_before = course_purchase_txs.count()
    print(f"Trovate {count_before} transazioni da cancellare:")
    
    for tx in course_purchase_txs:
        print(f"  - {tx.user.username}: {tx.transaction_type} ({tx.amount} TEO)")
    
    course_purchase_txs.delete()
    print(f"Cancellate {count_before} transazioni")
    
    # 4. Verifica stato finale
    print("\n=== STATO FINALE ===")
    for course in Course.objects.all():
        students = course.students.all()
        print(f"Corso: {course.title}")
        if students:
            print(f"  Studenti iscritti: {[s.username for s in students]}")
        else:
            print(f"  Nessuno studente iscritto ✓")
    
    remaining_txs = BlockchainTransaction.objects.filter(
        transaction_type__in=['course_purchase', 'course_earned', 'platform_commission']
    ).count()
    print(f"Transazioni correlate rimaste: {remaining_txs} ✓")
    
    print("\n✅ Reset completato!")

if __name__ == "__main__":
    reset_course_purchases()
