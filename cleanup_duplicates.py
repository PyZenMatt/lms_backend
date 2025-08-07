#!/usr/bin/env python3
"""
Script di pulizia per rimuovere le doppie transazioni esistenti
ATTENZIONE: Usare solo in modalità dev!
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

from django.db.models import Count, Min
from rewards.models import TeacherDiscountAbsorption
from notifications.models import Notification

def cleanup_duplicate_absorptions():
    """Rimuove gli assorbimenti duplicati mantenendo il più vecchio"""
    
    print("🧹 Cleaning up duplicate absorptions...")
    print("ATTENZIONE: Questo script modifica il database!")
    
    response = input("Continuare? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operazione annullata.")
        return
    
    # Trova gruppi duplicati
    duplicates = TeacherDiscountAbsorption.objects.values(
        'teacher', 'student', 'course'
    ).annotate(
        count=Count('id'),
        first_id=Min('id')
    ).filter(count__gt=1)
    
    total_deleted = 0
    
    for dup_group in duplicates:
        # Mantieni solo il primo (più vecchio) di ogni gruppo
        teacher_id = dup_group['teacher']
        student_id = dup_group['student'] 
        course_id = dup_group['course']
        first_id = dup_group['first_id']
        count = dup_group['count']
        
        # Trova tutti gli assorbimenti di questo gruppo
        absorptions = TeacherDiscountAbsorption.objects.filter(
            teacher_id=teacher_id,
            student_id=student_id,
            course_id=course_id
        ).order_by('id')
        
        # Elimina tutti tranne il primo
        to_delete = absorptions.exclude(id=first_id)
        deleted_count = to_delete.count()
        
        if deleted_count > 0:
            print(f"🗑️  Gruppo Teacher{teacher_id}/Student{student_id}/Course{course_id}: "
                  f"mantengo ID {first_id}, elimino {deleted_count} duplicati")
            
            # Elimina anche le notifiche correlate
            for absorption in to_delete:
                Notification.objects.filter(
                    related_object_id=absorption.pk,
                    notification_type='teocoin_discount_pending'
                ).delete()
            
            to_delete.delete()
            total_deleted += deleted_count
    
    print(f"\n✅ Pulizia completata!")
    print(f"🗑️  Eliminati {total_deleted} assorbimenti duplicati")
    
    # Verifica finale
    remaining_duplicates = TeacherDiscountAbsorption.objects.values(
        'teacher', 'student', 'course'
    ).annotate(count=Count('id')).filter(count__gt=1)
    
    if remaining_duplicates.exists():
        print(f"⚠️  Rimangono {remaining_duplicates.count()} gruppi con duplicati")
    else:
        print(f"✅ Nessun duplicato rimanente!")

if __name__ == "__main__":
    cleanup_duplicate_absorptions()
