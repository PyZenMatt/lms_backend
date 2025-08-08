#!/usr/bin/env python3
"""
Test script per creare opportunità di assorbimento per i teacher
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment - Use the correct settings module (base/dev/prod structure)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

# Now import Django modules
from django.contrib.auth import get_user_model
from courses.models import Course
from rewards.models import TeacherDiscountAbsorption
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService

def create_test_absorption():
    """Crea una notifica di test per teacher absorption"""
    
    print("🧪 Creazione Test Teacher Absorption")
    print("=" * 50)
    
    User = get_user_model()
    
    try:
        # 1. Trova un teacher
        teacher = User.objects.filter(role='teacher').first()
        if not teacher:
            print("❌ Nessun teacher trovato nel database")
            return
        
        # 2. Trova uno student
        student = User.objects.filter(role='student').first()
        if not student:
            print("❌ Nessun student trovato nel database")
            return
            
        print(f"✅ Teacher: {teacher.username}")
        print(f"✅ Student: {student.username}")
        
        # 3. Crea un corso fittizio per il test
        # Cerchiamo un corso esistente nel database
        from courses.models import Course
        course = Course.objects.first()
        if not course:
            print("❌ Nessun corso trovato nel database")
            return
            
        print(f"✅ Corso: {course.title}")
        
        # 4. Crea absorption opportunity
        service = TeacherDiscountAbsorptionService()
        
        # Dati di discount simulati
        discount_data = {
            'discount_percentage': 15,  # 15% sconto
            'teo_used': '25.00',  # 25 TEO usati dallo student
            'discount_amount_eur': '15.00',  # €15 di sconto
            'course_price_eur': '100.00'  # Prezzo originale €100
        }
        
        absorption = service.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data=discount_data
        )
        
        if absorption:
            print(f"✅ Absorption creato con ID: {absorption.id}")
            print(f"📊 Opzione A (EUR): €{absorption.option_a_teacher_eur}")
            print(f"📊 Opzione B (TEO): {absorption.option_b_teacher_teo} TEO")
            print(f"⏰ Scade il: {absorption.expires_at}")
            print(f"👨‍� Teacher: {absorption.teacher.email}")
            print(f"👨‍🎓 Student: {absorption.student.email}")
            print("="*50)
        else:
            print("❌ Fallito nella creazione dell'absorption")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_absorption()
