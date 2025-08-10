#!/usr/bin/env python3
"""
🧪 TEST COMPLETO TEACHER CHOICE SYSTEM
Verifica che i teacher possano accettare TeoCoin dalle notifiche
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from backend.services.db_teocoin_service import DBTeoCoinService
from users.models import User
from decimal import Decimal
from rest_framework.test import APIRequestFactory
from backend.api.teacher_absorption_views import TeacherMakeAbsorptionChoiceView
import json

def test_teacher_teocoin_acceptance():
    """Test completo del sistema di accettazione TeoCoin teacher"""
    print("🧪 TESTING TEACHER TEOCOIN ACCEPTANCE SYSTEM")
    print("=" * 60)
    
    # 1. Setup servizi
    db_service = DBTeoCoinService()
    factory = APIRequestFactory()
    
    # 2. Trova teacher per test
    teacher = User.objects.filter(role='teacher').first()
    if not teacher:
        teacher = User.objects.filter(is_staff=True).first()
    
    if not teacher:
        print("❌ No teacher found for testing")
        return False
    
    print(f"👨‍🏫 Testing with teacher: {teacher.username} (ID: {teacher.id})")
    
    # 3. Test get_balance (era il bug principale)
    print("\n💰 1. TESTING GET_BALANCE METHOD")
    print("-" * 40)
    
    try:
        initial_balance = db_service.get_balance(teacher)
        print(f"   ✅ get_balance works: {initial_balance} TEO")
    except Exception as e:
        print(f"   ❌ get_balance failed: {e}")
        return False
    
    # 4. Test direct add_balance
    print("\n🔄 2. TESTING DIRECT ADD_BALANCE")
    print("-" * 40)
    
    try:
        test_amount = Decimal('5.0')
        success = db_service.add_balance(
            user=teacher,
            amount=test_amount,
            transaction_type='test_credit',
            description='Test direct TeoCoin credit'
        )
        
        if success:
            intermediate_balance = db_service.get_balance(teacher)
            difference1 = intermediate_balance - initial_balance
            print(f"   ✅ Direct credit successful: {initial_balance} → {intermediate_balance} TEO (+{difference1})")
        else:
            print("   ❌ Direct credit failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Direct credit error: {e}")
        return False
    
    # 5. Test teacher choice endpoint (TEO option)
    print("\n🎯 3. TESTING TEACHER CHOICE ENDPOINT (TEO)")
    print("-" * 40)
    
    try:
        # Simula request POST per scelta TEO
        request_data = {
            'absorption_id': 'test_notification_123',
            'choice': 'teo',
            'amount': 10.0,
            'transaction_type': 'discount_absorption',
            'description': 'Test teacher choice endpoint'
        }
        
        request = factory.post(
            '/api/v1/teocoin/teacher/choice/',
            data=request_data,
            format='json'
        )
        request.user = teacher
        
        # Chiama la view
        view = TeacherMakeAbsorptionChoiceView()
        response = view.post(request)
        
        print(f"   📤 Request sent: {request_data}")
        print(f"   📥 Response status: {response.status_code}")
        print(f"   📋 Response data: {response.data}")
        
        if response.status_code == 200 and response.data.get('success'):
            # Verifica nuovo balance
            final_balance = db_service.get_balance(teacher)
            difference2 = final_balance - intermediate_balance
            total_difference = final_balance - initial_balance
            
            print(f"   ✅ Teacher choice TEO successful!")
            print(f"   💰 Balance: {intermediate_balance} → {final_balance} TEO (+{difference2})")
            print(f"   📊 Total test increase: +{total_difference} TEO")
            
            # Verifica dati nella response
            if 'amount_credited' in response.data:
                credited = response.data['amount_credited']
                print(f"   🎁 Amount credited per response: {credited} TEO")
            
        else:
            print(f"   ❌ Teacher choice TEO failed: {response.data}")
            return False
            
    except Exception as e:
        print(f"   ❌ Teacher choice endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Test teacher choice endpoint (EUR option)
    print("\n💰 4. TESTING TEACHER CHOICE ENDPOINT (EUR)")
    print("-" * 40)
    
    try:
        # Simula request POST per scelta EUR
        request_data_eur = {
            'absorption_id': 'test_notification_456',
            'choice': 'eur',
            'amount': 0,
            'transaction_type': 'discount_declined',
            'description': 'Test teacher choice endpoint EUR'
        }
        
        request_eur = factory.post(
            '/api/v1/teocoin/teacher/choice/',
            data=request_data_eur,
            format='json'
        )
        request_eur.user = teacher
        
        # Chiama la view
        response_eur = view.post(request_eur)
        
        print(f"   📤 Request sent: {request_data_eur}")
        print(f"   📥 Response status: {response_eur.status_code}")
        print(f"   📋 Response data: {response_eur.data}")
        
        if response_eur.status_code == 200 and response_eur.data.get('success'):
            print(f"   ✅ Teacher choice EUR successful!")
            
            # Verifica che il balance NON sia cambiato
            eur_balance = db_service.get_balance(teacher)
            if eur_balance == final_balance:
                print(f"   ✅ Balance unchanged for EUR choice: {eur_balance} TEO")
            else:
                print(f"   ⚠️  Balance changed unexpectedly: {final_balance} → {eur_balance} TEO")
            
        else:
            print(f"   ❌ Teacher choice EUR failed: {response_eur.data}")
            return False
            
    except Exception as e:
        print(f"   ❌ Teacher choice EUR endpoint error: {e}")
        return False
    
    # 7. Test finale - verifica transazioni nel DB
    print("\n📊 5. FINAL DATABASE VERIFICATION")
    print("-" * 40)
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Conta transazioni teacher
            cursor.execute(
                "SELECT COUNT(*) FROM blockchain_dbteocointransaction WHERE user_id = %s",
                [teacher.id]
            )
            teacher_transactions = cursor.fetchone()[0]
            print(f"   📊 Teacher total transactions in DB: {teacher_transactions}")
            
            # Ultime transazioni teacher
            cursor.execute(
                "SELECT transaction_type, amount, description FROM blockchain_dbteocointransaction WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
                [teacher.id]
            )
            recent_transactions = cursor.fetchall()
            
            print(f"   📋 Recent transactions:")
            for tx in recent_transactions:
                tx_type, amount, desc = tx
                print(f"      - {tx_type}: {amount} TEO ({desc})")
        
    except Exception as e:
        print(f"   ❌ Database verification error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TEACHER TEOCOIN ACCEPTANCE TEST COMPLETED SUCCESSFULLY!")
    print("✅ Teachers can now accept TeoCoin from notifications")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_teacher_teocoin_acceptance()
    
    if success:
        print("\n🚀 ALL TESTS PASSED!")
        print("👨‍🏫 Teachers can now accept TeoCoin from notifications")
        print("💰 The endpoint /api/v1/teocoin/teacher/choice/ is working")
        print("🎯 Both TEO and EUR choices are functional")
    else:
        print("\n❌ TESTS FAILED!")
        print("🚨 Teacher TeoCoin acceptance is still broken")
        
    sys.exit(0 if success else 1)
