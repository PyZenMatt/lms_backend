#!/usr/bin/env python3
"""
Test semplice per verificare che il trasferimento dalla reward pool funzioni
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from eth_account import Account
from decimal import Decimal

def main():
    print("🔧 === TEST SEMPLICE REWARD POOL ===")
    
    # Inizializza il servizio
    tcs = TeoCoinService()
    
    # Verifica stato iniziale
    print("\n📊 === STATO INIZIALE ===")
    pool_balance = tcs.get_reward_pool_balance()
    pool_address = os.getenv('REWARD_POOL_ADDRESS')
    pool_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(pool_address), 'ether')
    
    print(f"💰 Reward Pool TeoCoins: {pool_balance}")
    print(f"⛽ Reward Pool MATIC: {pool_matic}")
    
    # Crea un account di test
    student = Account.create()
    print(f"\n👨‍🎓 Test Student: {student.address}")
    
    # Verifica balance iniziale studente
    student_balance_before = tcs.get_balance(student.address)
    print(f"Student TeoCoins iniziali: {student_balance_before}")
    
    # Test 1: Trasferimento semplice dalla reward pool
    print("\n🎁 === TEST TRASFERIMENTO REWARD POOL ===")
    try:
        # Testiamo con una quantità piccola
        amount = Decimal('10')
        tx_hash = tcs.transfer_from_reward_pool(student.address, amount)
        
        if tx_hash:
            print(f"✅ Trasferimento riuscito!")
            print(f"📋 Transaction hash: {tx_hash}")
            
            # Aspetta un po' per la conferma e controlla il balance
            import time
            time.sleep(3)
            
            student_balance_after = tcs.get_balance(student.address)
            pool_balance_after = tcs.get_reward_pool_balance()
            pool_matic_after = tcs.w3.from_wei(tcs.w3.eth.get_balance(pool_address), 'ether')
            
            print(f"\n💳 === BALANCE DOPO TRASFERIMENTO ===")
            print(f"Student TeoCoins: {student_balance_after} (+{student_balance_after - student_balance_before})")
            print(f"Reward Pool TeoCoins: {pool_balance_after} ({pool_balance_after - pool_balance:+})")
            print(f"Reward Pool MATIC: {pool_matic_after} ({pool_matic_after - pool_matic:+.6f})")
            
            if student_balance_after > student_balance_before:
                print("🎉 TRASFERIMENTO RIUSCITO!")
            else:
                print("❌ Il balance dello studente non è cambiato")
                
        else:
            print("❌ Trasferimento fallito - nessun hash di transazione")
            
    except Exception as e:
        print(f"❌ Errore nel trasferimento: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
