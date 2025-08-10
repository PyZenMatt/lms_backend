#!/usr/bin/env python3
"""
Script per pulire il database mantenendo solo utenti specifici
e assegnare i corsi ai teacher 1, 2, 3
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.db import transaction
from users.models import User
from courses.models import Course, Lesson, Exercise
from blockchain.models import UserWallet

def cleanup_users_and_assign_courses():
    """Mantiene solo utenti specifici e assegna corsi ai teacher"""
    
    print("🧹 PULIZIA DATABASE E ASSEGNAZIONE CORSI")
    print("=" * 60)
    
    # Utenti da mantenere
    users_to_keep = [
        'Teo',           # admin
        'student1',      # studente
        'student4',      # studente  
        'student11',     # studente
        'teacher1',      # insegnante
        'teacher2',      # insegnante
        'teacher3'       # insegnante
    ]
    
    print(f"👥 Utenti da mantenere: {', '.join(users_to_keep)}")
    print()
    
    # Mostra stato iniziale
    total_users_before = User.objects.count()
    total_courses_before = Course.objects.count()
    
    print(f"📊 STATO INIZIALE:")
    print(f"   Utenti totali: {total_users_before}")
    print(f"   Corsi totali: {total_courses_before}")
    print()
    
    with transaction.atomic():
        # 1. Trova utenti da eliminare
        users_to_delete = User.objects.exclude(username__in=users_to_keep)
        users_to_delete_count = users_to_delete.count()
        
        print(f"🗑️  ELIMINAZIONE UTENTI:")
        print(f"   Utenti da eliminare: {users_to_delete_count}")
        
        if users_to_delete_count > 0:
            # Mostra chi verrà eliminato
            print("   Lista utenti da eliminare:")
            for user in users_to_delete:
                print(f"     • {user.username} ({user.role})")
            
            # Elimina utenti (questo eliminerà automaticamente i loro wallet)
            users_to_delete.delete()
            print(f"   ✅ Eliminati {users_to_delete_count} utenti")
        else:
            print("   ✅ Nessun utente da eliminare")
        
        print()
        
        # 2. Verifica utenti rimanenti
        remaining_users = User.objects.filter(username__in=users_to_keep).order_by('username')
        print(f"👤 UTENTI RIMANENTI ({remaining_users.count()}):")
        
        admin_user = None
        students = []
        teachers = []
        
        for user in remaining_users:
            print(f"   • {user.username} ({user.role}) - {user.email}")
            
            if user.role == 'admin':
                admin_user = user
            elif user.role == 'student':
                students.append(user)
            elif user.role == 'teacher':
                teachers.append(user)
        
        print()
        
        # 3. Ottieni i teacher specifici
        teacher1 = User.objects.filter(username='teacher1').first()
        teacher2 = User.objects.filter(username='teacher2').first()
        teacher3 = User.objects.filter(username='teacher3').first()
        
        # Verifica che esistano
        if not all([teacher1, teacher2, teacher3]):
            print("❌ Errore: Non tutti i teacher (1,2,3) sono presenti!")
            missing = []
            if not teacher1: missing.append('teacher1')
            if not teacher2: missing.append('teacher2')
            if not teacher3: missing.append('teacher3')
            print(f"   Mancanti: {', '.join(missing)}")
            return
        
        # 4. Assegna corsi ai teacher
        print(f"📚 ASSEGNAZIONE CORSI AI TEACHER:")
        
        # Ottieni tutti i corsi esistenti
        all_courses = Course.objects.all().order_by('title')
        course_list = list(all_courses)
        
        if not course_list:
            print("   ⚠️  Nessun corso trovato nel database!")
            return
        
        print(f"   Corsi totali da assegnare: {len(course_list)}")
        print()
        
        # Dividi i corsi tra i 3 teacher
        teachers_list = [teacher1, teacher2, teacher3]
        teacher_names = ['teacher1', 'teacher2', 'teacher3']
        
        for i, course in enumerate(course_list):
            # Assegna in round-robin
            assigned_teacher = teachers_list[i % 3]
            teacher_name = teacher_names[i % 3]
            
            old_teacher = course.teacher.username if course.teacher else "Nessuno"
            if assigned_teacher:  # Verifica che assigned_teacher non sia None
                course.teacher = assigned_teacher
                course.save()
                
                print(f"   📖 '{course.title[:40]}...' -> {teacher_name}")
                print(f"      (prima: {old_teacher})")
        
        print()
        
        # 5. Aggiorna anche le lezioni per essere coerenti
        print(f"📝 AGGIORNAMENTO LEZIONI:")
        lessons_updated = 0
        
        for course in Course.objects.all():
            # Usa query diretta invece del related_name
            lessons = Lesson.objects.filter(course=course)
            for lesson in lessons:
                if lesson.teacher != course.teacher:
                    lesson.teacher = course.teacher
                    lesson.save()
                    lessons_updated += 1
        
        print(f"   ✅ Aggiornate {lessons_updated} lezioni")
        print()
    
    # 6. Mostra stato finale
    print("📊 STATO FINALE:")
    final_users = User.objects.count()
    final_courses = Course.objects.count()
    final_wallets = UserWallet.objects.count()
    
    print(f"   👥 Utenti totali: {final_users}")
    print(f"   📚 Corsi totali: {final_courses}")
    print(f"   💳 Wallet totali: {final_wallets}")
    print()
    
    # 7. Riepilogo assegnazioni
    print("📋 RIEPILOGO ASSEGNAZIONI:")
    print("-" * 40)
    
    for teacher in [teacher1, teacher2, teacher3]:
        if teacher:  # Verifica che il teacher esista
            courses_assigned = Course.objects.filter(teacher=teacher)
            print(f"👨‍🏫 {teacher.username}:")
            print(f"   📚 Corsi assegnati: {courses_assigned.count()}")
            for course in courses_assigned:
                # Usa query dirette per evitare problemi con related_name
                lessons_count = Lesson.objects.filter(course=course).count()
                exercises_count = Exercise.objects.filter(lesson__course=course).count()
                print(f"      • {course.title[:30]}... ({lessons_count} lezioni, {exercises_count} esercizi)")
            print()
    
    print("=" * 60)
    print("✅ PULIZIA E ASSEGNAZIONE COMPLETATA!")
    print("=" * 60)
    
    # 8. Mostra wallet rimanenti
    print("\n💳 WALLET RIMANENTI:")
    remaining_wallets = UserWallet.objects.select_related('user').all().order_by('user__username')
    for wallet in remaining_wallets:
        print(f"   {wallet.user.username} ({wallet.user.role}) -> {wallet.address}")

if __name__ == "__main__":
    # Conferma prima di procedere
    print("⚠️  ATTENZIONE: Questo script eliminerà utenti dal database!")
    print("Utenti che verranno MANTENUTI:")
    print("• Teo (admin)")
    print("• student1, student4, student11")
    print("• teacher1, teacher2, teacher3")
    print("\nTutti gli altri utenti verranno ELIMINATI.")
    print()
    
    confirm = input("Sei sicuro di voler procedere? (scrivi 'CONFERMA' per continuare): ").strip()
    
    if confirm == 'CONFERMA':
        cleanup_users_and_assign_courses()
    else:
        print("❌ Operazione annullata.")
