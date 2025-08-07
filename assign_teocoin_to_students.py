#!/usr/bin/env python3
"""
Production Script: Assign TeoCoin to All Students
Per assegnare TEO a tutti gli studenti nel database di produzione
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment - Use dev for local testing, prod for production
# Check if we're in development (has sqlite) or production (needs DATABASE_URL)
if os.getenv('DATABASE_URL'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

# Import Django modules after setup
from django.contrib.auth import get_user_model
from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from django.db import transaction
from django.db import models

def assign_teocoin_to_students(default_amount=50):
    """
    Assegna TEO a tutti gli studenti che non hanno già un balance
    
    Args:
        default_amount (int): Quantità di TEO da assegnare (default: 50)
    """
    
    print("🏦 Script Assegnazione TeoCoin agli Studenti")
    print("=" * 60)
    print(f"💰 Quantità da assegnare: {default_amount} TEO per studente")
    print("=" * 60)
    
    User = get_user_model()
    
    try:
        with transaction.atomic():
            # 1. Trova tutti gli studenti
            students = User.objects.filter(role='student')
            total_students = students.count()
            
            if total_students == 0:
                print("❌ Nessuno studente trovato nel database")
                return
            
            print(f"👥 Trovati {total_students} studenti nel database")
            print("-" * 60)
            
            # 2. Statistiche prima dell'operazione
            existing_balances = DBTeoCoinBalance.objects.filter(user__role='student')
            students_with_balance = existing_balances.count()
            
            print(f"📊 Studenti con balance esistente: {students_with_balance}")
            print(f"📊 Studenti senza balance: {total_students - students_with_balance}")
            print("-" * 60)
            
            # 3. Processa ogni studente
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for student in students:
                try:
                    # Controlla se lo studente ha già un balance
                    balance, created = DBTeoCoinBalance.objects.get_or_create(
                        user=student,
                        defaults={
                            'available_balance': Decimal(str(default_amount)),
                            'updated_at': datetime.now(timezone.utc)
                        }
                    )
                    
                    if created:
                        # Nuovo balance creato - crea transazione di credito
                        DBTeoCoinTransaction.objects.create(
                            user=student,
                            transaction_type='bonus',
                            amount=Decimal(str(default_amount)),
                            description=f'Initial TeoCoin allocation - Production Setup'
                        )
                        
                        print(f"✅ NUOVO: {student.email} - {default_amount} TEO assegnati")
                        created_count += 1
                        
                    else:
                        # Balance già esistente
                        if balance.available_balance == 0:
                            # Se il balance è 0, aggiungi i TEO
                            balance.available_balance = Decimal(str(default_amount))
                            balance.updated_at = datetime.now(timezone.utc)
                            balance.save()
                            
                            DBTeoCoinTransaction.objects.create(
                                user=student,
                                transaction_type='bonus',
                                amount=Decimal(str(default_amount)),
                                description=f'TeoCoin top-up - Production Setup'
                            )
                            
                            print(f"🔄 AGGIORNATO: {student.email} - {default_amount} TEO aggiunti (era 0)")
                            updated_count += 1
                        else:
                            print(f"⏭️  SALTATO: {student.email} - già ha {balance.available_balance} TEO")
                            skipped_count += 1
                            
                except Exception as e:
                    print(f"❌ ERRORE per {student.email}: {str(e)}")
                    continue
            
            # 4. Statistiche finali
            print("-" * 60)
            print("📈 RISULTATI FINALI:")
            print(f"✅ Nuovi balance creati: {created_count}")
            print(f"🔄 Balance aggiornati (da 0): {updated_count}")
            print(f"⏭️  Studenti saltati (già con TEO): {skipped_count}")
            print(f"📊 Totale studenti processati: {created_count + updated_count + skipped_count}")
            
            # 5. Verifica finale
            total_balances_after = DBTeoCoinBalance.objects.filter(user__role='student').count()
            total_teo_distributed = DBTeoCoinBalance.objects.filter(
                user__role='student'
            ).aggregate(total=models.Sum('available_balance'))['total'] or 0
            
            print("-" * 60)
            print("🔍 VERIFICA FINALE:")
            print(f"📊 Studenti con balance dopo l'operazione: {total_balances_after}")
            print(f"💰 Totale TEO distribuiti nel sistema: {total_teo_distributed}")
            print(f"💵 Valore teorico (studenti × {default_amount}): {total_students * default_amount}")
            print("=" * 60)
            
            if created_count > 0 or updated_count > 0:
                print("✅ OPERAZIONE COMPLETATA CON SUCCESSO!")
                print("🚀 Il sistema è pronto per la produzione!")
            else:
                print("ℹ️  Nessuna modifica necessaria - tutti gli studenti hanno già TEO")
                
    except Exception as e:
        print(f"❌ ERRORE CRITICO: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  OPERAZIONE ANNULLATA - Nessuna modifica salvata")

def preview_operation():
    """Preview dell'operazione senza modifiche al database"""
    print("👁️  PREVIEW MODE - Nessuna modifica al database")
    print("=" * 60)
    
    User = get_user_model()
    students = User.objects.filter(role='student')
    existing_balances = DBTeoCoinBalance.objects.filter(user__role='student')
    
    print(f"👥 Studenti totali: {students.count()}")
    print(f"💰 Studenti con balance: {existing_balances.count()}")
    print(f"📋 Studenti che riceverebbero TEO: {students.count() - existing_balances.count()}")
    
    print("\n📝 Lista studenti che riceverebbero TEO:")
    students_without_balance = students.exclude(
        id__in=existing_balances.values_list('user_id', flat=True)
    )
    
    for student in students_without_balance[:10]:  # Mostra solo i primi 10
        print(f"  - {student.email}")
    
    if students_without_balance.count() > 10:
        print(f"  ... e altri {students_without_balance.count() - 10} studenti")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'preview':
            preview_operation()
        elif sys.argv[1] == 'execute':
            amount = 50
            if len(sys.argv) > 2:
                try:
                    amount = int(sys.argv[2])
                except ValueError:
                    print("❌ Errore: l'amount deve essere un numero")
                    sys.exit(1)
            
            confirm = input(f"\n⚠️  Stai per assegnare {amount} TEO a tutti gli studenti senza balance.\nContinuare? (yes/no): ")
            if confirm.lower() in ['yes', 'y', 'si', 's']:
                assign_teocoin_to_students(amount)
            else:
                print("❌ Operazione annullata dall'utente")
        else:
            print("❌ Parametro non valido. Usa: 'preview' o 'execute [amount]'")
    else:
        print("📖 USO:")
        print("  python assign_teocoin_to_students.py preview")
        print("  python assign_teocoin_to_students.py execute [amount]")
        print("\nEsempi:")
        print("  python assign_teocoin_to_students.py preview")
        print("  python assign_teocoin_to_students.py execute 50")
        print("  python assign_teocoin_to_students.py execute 100")
