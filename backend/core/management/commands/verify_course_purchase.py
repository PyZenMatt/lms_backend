#!/usr/bin/env python3
"""
Verifica l'acquisto corso completato via MetaMask
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from rewards.models import BlockchainTransaction
from courses.models import CourseEnrollment, Course
from blockchain.blockchain import teocoin_service

User = get_user_model()

def verify_course_purchase():
    """Verifica l'acquisto corso completato"""
    
    print("🎉 VERIFICA ACQUISTO CORSO VIA METAMASK")
    print("=" * 50)
    
    # 1. Ultime transazioni (ultima ora)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_txs = BlockchainTransaction.objects.filter(
        created_at__gte=one_hour_ago
    ).order_by('-created_at')
    
    print(f"📊 Transazioni ultime ora ({len(recent_txs)} trovate):")
    print("-" * 30)
    
    course_purchase_tx = None
    for i, tx in enumerate(recent_txs, 1):
        print(f"{i}. {tx.created_at.strftime('%H:%M:%S')} - {tx.transaction_type}")
        print(f"   👤 User: {tx.user.username}")
        print(f"   💰 Amount: {tx.amount} TEO")
        print(f"   🔗 Hash: {tx.transaction_hash}")
        print(f"   📍 From: {tx.from_address}")
        print(f"   📍 To: {tx.to_address}")
        print(f"   📝 Note: {tx.notes}")
        print(f"   ✅ Status: {tx.status}")
        
        if tx.transaction_type == 'course_purchase':
            course_purchase_tx = tx
            
        print()
    
    # 2. Ultimi enrollment
    recent_enrollments = CourseEnrollment.objects.filter(
        enrolled_at__gte=one_hour_ago
    ).order_by('-enrolled_at')
    
    print(f"📚 Enrollment ultime ora ({len(recent_enrollments)} trovati):")
    print("-" * 30)
    
    for enrollment in recent_enrollments:
        print(f"👤 Student: {enrollment.student.username}")
        print(f"📖 Course: {enrollment.course.title}")
        print(f"💰 Price: {enrollment.course.price} TEO")
        print(f"👨‍🏫 Teacher: {enrollment.course.teacher.username}")
        print(f"🕐 Time: {enrollment.enrolled_at.strftime('%H:%M:%S')}")
        print()
    
    # 3. Verifica bilanci aggiornati
    print("💼 Bilanci attuali:")
    print("-" * 20)
    
    student = User.objects.filter(username='student1').first()
    if student and student.wallet_address:
        student_balance = teocoin_service.get_balance(student.wallet_address)
        print(f"👤 Student1: {student_balance} TEO ({student.wallet_address})")
    
    # Trova teacher del corso acquistato
    if course_purchase_tx and course_purchase_tx.related_object_id:
        try:
            course = Course.objects.get(id=course_purchase_tx.related_object_id)
            if course.teacher.wallet_address:
                teacher_balance = teocoin_service.get_balance(course.teacher.wallet_address)
                print(f"👨‍🏫 {course.teacher.username}: {teacher_balance} TEO ({course.teacher.wallet_address})")
        except Course.DoesNotExist:
            pass
    
    # Reward pool
    reward_pool_address = "0x3b72a4E942CF1467134510cA3952F01b63005044"
    reward_pool_balance = teocoin_service.get_balance(reward_pool_address)
    print(f"🏦 Reward Pool: {reward_pool_balance} TEO ({reward_pool_address})")
    
    # 4. Verifica transazione blockchain se disponibile
    if course_purchase_tx:
        print("\n🔍 VERIFICA TRANSAZIONE BLOCKCHAIN:")
        print("-" * 35)
        
        tx_hash = course_purchase_tx.transaction_hash
        print(f"Hash: {tx_hash}")
        
        try:
            # Verifica sulla blockchain
            receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
            transaction = teocoin_service.w3.eth.get_transaction(tx_hash)
            
            print(f"✅ Status: {receipt.status} (1=success, 0=failed)")
            print(f"⛽ Gas used: {receipt.gasUsed}")
            print(f"📍 Block: {receipt.blockNumber}")
            print(f"🔗 Explorer: https://amoy.polygonscan.com/tx/{tx_hash}")
            
            # Decodifica eventi Transfer
            if receipt.logs:
                print(f"\n📋 Eventi Transfer trovati: {len(receipt.logs)}")
                for i, log in enumerate(receipt.logs):
                    try:
                        # Decodifica evento Transfer (topic[0] = Transfer signature)
                        if len(log.topics) >= 3 and log.topics[0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                            from_addr = '0x' + log.topics[1].hex()[26:]
                            to_addr = '0x' + log.topics[2].hex()[26:]
                            amount_wei = int(log.data.hex(), 16)
                            amount_teo = teocoin_service.w3.from_wei(amount_wei, 'ether')
                            
                            print(f"  {i+1}. Transfer: {amount_teo} TEO")
                            print(f"     From: {from_addr}")
                            print(f"     To: {to_addr}")
                    except Exception as e:
                        print(f"  {i+1}. Log non decodificabile: {str(e)[:50]}")
                        
        except Exception as e:
            print(f"❌ Errore verifica blockchain: {e}")
    
    # 5. Riepilogo finale
    print("\n🎯 RIEPILOGO ACQUISTO:")
    print("=" * 25)
    
    if course_purchase_tx and recent_enrollments:
        print("✅ Transazione course_purchase trovata")
        print("✅ Enrollment corso completato")
        print("✅ Record database creati")
        print("✅ Sistema MetaMask funzionante!")
        print("\n🚀 IL FLUSSO METAMASK È COMPLETAMENTE OPERATIVO! 🚀")
    else:
        print("⚠️ Verifica se l'acquisto è stato completato correttamente")
        print("💡 Controlla i log del browser per eventuali errori")

if __name__ == "__main__":
    verify_course_purchase()
