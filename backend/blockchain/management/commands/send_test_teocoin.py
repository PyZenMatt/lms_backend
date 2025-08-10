#!/usr/bin/env python3
"""
Script per inviare 50 TeoCoin a un singolo studente come test
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.conf import settings
from users.models import User
from blockchain.models import UserWallet
from blockchain.blockchain import TeoCoinService

def send_test_teocoins():
    """Invia 50 TeoCoin a student1 come test"""
    
    print("💰 TEST INVIO 50 TEOCOIN A STUDENT1")
    print("=" * 50)
    
    # Configurazione
    admin_private_key = settings.ADMIN_PRIVATE_KEY
    admin_address = "0x3b72a4E942CF1467134510cA3952F01b63005044"
    amount = Decimal('50')  # 50 TeoCoin
    
    print(f"📤 Mittente: {admin_address}")
    print(f"💰 Importo: {amount} TEO")
    
    # Trova student1
    try:
        student1 = User.objects.get(username='student1')
        student1_wallet = UserWallet.objects.get(user=student1)
        recipient_address = student1_wallet.address
        print(f"📍 Destinatario: student1 ({recipient_address})")
    except User.DoesNotExist:
        print("❌ student1 non trovato!")
        return
    except Exception as e:
        print(f"❌ Errore nel trovare student1: {e}")
        return
    
    # Inizializza servizio blockchain
    try:
        teocoin_service = TeoCoinService()
        print("✅ Servizio blockchain inizializzato")
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione: {e}")
        return
    
    # Verifica balance mittente
    try:
        admin_teo_balance = teocoin_service.get_balance(admin_address)
        admin_matic_balance = teocoin_service.w3.eth.get_balance(teocoin_service.w3.to_checksum_address(admin_address))
        admin_matic = teocoin_service.w3.from_wei(admin_matic_balance, 'ether')
        
        print(f"\n📊 BALANCE MITTENTE:")
        print(f"🪙 TEO: {admin_teo_balance}")
        print(f"💎 MATIC: {admin_matic:.6f}")
        
        if admin_teo_balance < amount:
            print(f"❌ TEO insufficienti! Serve: {amount}, Disponibile: {admin_teo_balance}")
            return
            
        if float(admin_matic) < 0.012:
            print(f"⚠️  MATIC bassi ({admin_matic:.6f}), ma proviamo comunque...")
            
    except Exception as e:
        print(f"❌ Errore nel controllo balance: {e}")
        return
    
    # Verifica balance destinatario PRIMA
    try:
        recipient_balance_before = teocoin_service.get_balance(recipient_address)
        print(f"\n💰 Balance student1 PRIMA: {recipient_balance_before} TEO")
    except Exception as e:
        print(f"⚠️  Errore nel controllo balance destinatario: {e}")
        recipient_balance_before = 0
    
    # Conferma
    print(f"\n🚀 PRONTO PER INVIARE:")
    print(f"Da: Admin ({admin_address})")
    print(f"A: student1 ({recipient_address})")
    print(f"Importo: {amount} TEO")
    
    confirm = input("\nProcedere? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', 's', 'si']:
        print("❌ Operazione annullata.")
        return
    
    # Esegui trasferimento
    print("\n💸 Eseguendo trasferimento...")
    try:
        tx_hash = teocoin_service.transfer_tokens(
            from_private_key=admin_private_key,
            to_address=recipient_address,
            amount=amount
        )
        
        if tx_hash:
            print(f"✅ Trasferimento riuscito!")
            print(f"🔗 Transaction Hash: {tx_hash}")
            print(f"🌐 Visualizza su: https://amoy.polygonscan.com/tx/{tx_hash}")
            
            # Aspetta un po' e verifica il nuovo balance
            print("\n⏳ Attendendo conferma blockchain...")
            import time
            time.sleep(10)  # Aspetta 10 secondi
            
            try:
                recipient_balance_after = teocoin_service.get_balance(recipient_address)
                admin_balance_after = teocoin_service.get_balance(admin_address)
                
                print(f"\n📊 BALANCE FINALI:")
                print(f"👤 student1: {recipient_balance_before} → {recipient_balance_after} TEO")
                print(f"👑 admin: {admin_teo_balance} → {admin_balance_after} TEO")
                
                difference = recipient_balance_after - recipient_balance_before
                if difference == amount:
                    print(f"🎉 Trasferimento confermato! +{difference} TEO per student1")
                else:
                    print(f"⚠️  Differenza inaspettata: +{difference} TEO (atteso: +{amount})")
                    
            except Exception as e:
                print(f"⚠️  Errore nel controllo balance finale: {e}")
                print("💡 Controlla manualmente su Polygonscan")
        else:
            print("❌ Trasferimento fallito: nessun transaction hash restituito")
            
    except Exception as e:
        print(f"❌ Errore durante il trasferimento: {e}")
        
        # Se l'errore contiene informazioni sui gas, mostralo
        if 'insufficient funds' in str(e).lower():
            print("\n💡 PROBLEMA GAS:")
            print("Il wallet admin non ha abbastanza MATIC per le gas fees.")
            print("Vai su https://faucet.polygon.technology/ e richiedi MATIC")
            print(f"Indirizzo: {admin_address}")

if __name__ == "__main__":
    send_test_teocoins()
