#!/usr/bin/env python3
"""
Test completo per Student1 - Invio TEO e MATIC
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from blockchain.models import UserWallet
from users.models import User

def test_student1_setup():
    """Test completo per student1 - TEO e MATIC"""
    print("🎯 Setting up Student1 for complete testing...")
    
    # Indirizzo target per student1
    student1_address = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Trova admin wallet
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("❌ Admin user not found")
            return
            
        admin_wallet = UserWallet.objects.filter(user=admin_user).first()
        if not admin_wallet:
            print("❌ Admin wallet not found")
            return
            
        print(f"👤 Admin wallet: {admin_wallet.address}")
        
        # Controlla balance admin
        admin_balance_wei = service.w3.eth.get_balance(service.w3.to_checksum_address(admin_wallet.address))
        admin_balance_matic = service.w3.from_wei(admin_balance_wei, 'ether')
        print(f"💳 Admin MATIC balance: {admin_balance_matic}")
        
        admin_teo_balance = service.get_balance(admin_wallet.address)
        print(f"🪙 Admin TEO balance: {admin_teo_balance}")
        
        # Verifica indirizzo student1
        student1_checksum = service.w3.to_checksum_address(student1_address)
        print(f"🎯 Target student1 address: {student1_checksum}")
        
        # Controlla balance student1 (prima)
        student1_balance_wei = service.w3.eth.get_balance(student1_checksum)
        student1_balance_matic = service.w3.from_wei(student1_balance_wei, 'ether')
        student1_teo_balance = service.get_balance(student1_address)
        
        print(f"\n📊 STUDENT1 BALANCE (BEFORE):")
        print(f"💳 MATIC: {student1_balance_matic}")
        print(f"🪙 TEO: {student1_teo_balance}")
        
        # Step 1: Invia 50 TEO a student1
        print(f"\n🚀 Step 1: Sending 50 TEO to student1...")
        teo_tx = service.transfer_tokens(
            from_private_key=admin_wallet.private_key,
            to_address=student1_address,
            amount=Decimal('50.0')
        )
        
        if teo_tx:
            print(f"✅ TEO transfer successful! TX: {teo_tx}")
        else:
            print(f"❌ TEO transfer failed")
            return
        
        # Step 2: Invia 0.01 MATIC a student1
        print(f"\n🚀 Step 2: Sending 0.01 MATIC to student1...")
        
        # Prepara transazione MATIC
        from_account = service.w3.eth.account.from_key(admin_wallet.private_key)
        
        # Ottieni gas price ottimizzato
        try:
            gas_price = service.w3.eth.gas_price
            min_gas_price = service.w3.to_wei('30', 'gwei')
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            max_gas_price = service.w3.to_wei('50', 'gwei')
            if gas_price > max_gas_price:
                gas_price = max_gas_price
        except:
            gas_price = service.w3.to_wei('30', 'gwei')
        
        # Transazione MATIC nativa
        matic_tx = {
            'to': student1_checksum,
            'value': service.w3.to_wei('0.01', 'ether'),
            'gas': 21000,  # Gas standard per transfer MATIC
            'gasPrice': gas_price,
            'nonce': service.w3.eth.get_transaction_count(from_account.address),
        }
        
        # Firma e invia transazione MATIC
        signed_matic_tx = service.w3.eth.account.sign_transaction(matic_tx, admin_wallet.private_key)
        matic_tx_hash = service.w3.eth.send_raw_transaction(signed_matic_tx.raw_transaction)
        
        print(f"✅ MATIC transfer successful! TX: {matic_tx_hash.hex()}")
        
        # Aspetta un po' per conferme
        print(f"\n⏳ Waiting for transaction confirmations...")
        import time
        time.sleep(10)
        
        # Controlla balance student1 (dopo)
        student1_balance_wei_after = service.w3.eth.get_balance(student1_checksum)
        student1_balance_matic_after = service.w3.from_wei(student1_balance_wei_after, 'ether')
        student1_teo_balance_after = service.get_balance(student1_address)
        
        print(f"\n📊 STUDENT1 BALANCE (AFTER):")
        print(f"💳 MATIC: {student1_balance_matic_after} (was {student1_balance_matic})")
        print(f"🪙 TEO: {student1_teo_balance_after} (was {student1_teo_balance})")
        
        # Verifica successo
        matic_received = float(student1_balance_matic_after) - float(student1_balance_matic)
        teo_received = float(student1_teo_balance_after) - float(student1_teo_balance)
        
        print(f"\n✅ SUMMARY:")
        print(f"💳 MATIC received: +{matic_received:.6f}")
        print(f"🪙 TEO received: +{teo_received:.1f}")
        
        if matic_received >= 0.009 and teo_received >= 49:  # Allowing for gas costs
            print(f"🎉 Student1 setup completed successfully!")
            print(f"🧪 Ready for full blockchain testing!")
        else:
            print(f"⚠️ Setup may have issues - check balances")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_student1_setup()
