#!/usr/bin/env python3
"""
Invio 50 TEO         print(f"\n📊 INITIAL BALANCES:")
        
        # Admin balances
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic}, TEO: {admin_teo}")
        
        # Student1 balances  
        student1_matic_wei = service.w3.eth.get_balance(Web3.to_checksum_address(STUDENT1_ADDRESS))
        student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic}, TEO: {student1_teo}")a student1 per test completo
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
from web3 import Web3

def send_to_student1():
    """Invia 50 TEO e 0.01 MATIC a student1"""
    print("🚀 Sending 50 TEO and 0.01 MATIC to student1...")
    
    # Configurazione
    ADMIN_PRIVATE_KEY = "e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255"
    STUDENT1_ADDRESS = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Calcola l'admin address dalla private key
        admin_account = service.w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
        admin_address = admin_account.address
        
        print(f"👤 Admin address: {admin_address}")
        print(f"🎯 Student1 address: {STUDENT1_ADDRESS}")
        
        # Step 1: Controlla balances iniziali
        print("\n📊 INITIAL BALANCES:")
        
        # Admin balances
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic}, TEO: {admin_teo}")
        
        # Student1 balances  
        student1_matic_wei = service.w3.eth.get_balance(STUDENT1_ADDRESS)
        student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic}, TEO: {student1_teo}")
        
        # Step 2: Calcola costi stimati
        gas_price = service.w3.eth.gas_price
        gas_price_gwei = service.w3.from_wei(gas_price, 'gwei')
        print(f"\n⛽ Current gas price: {gas_price_gwei} Gwei")
        
        # Costo per mint TEO (gas limit: 120000)
        mint_cost = service.w3.from_wei(gas_price * 120000, 'ether')
        # Costo per transfer MATIC (gas limit: 21000)
        matic_transfer_cost = service.w3.from_wei(gas_price * 21000, 'ether')
        
        total_gas_needed = mint_cost + matic_transfer_cost
        print(f"💰 Estimated costs:")
        print(f"  - Mint 50 TEO: {mint_cost} MATIC")
        print(f"  - Send 0.01 MATIC: {matic_transfer_cost} MATIC")
        print(f"  - Total gas needed: {total_gas_needed} MATIC")
        
        # Step 3: Verifica se admin ha abbastanza MATIC
        matic_needed_for_transfer = Decimal('0.01') + Decimal(str(total_gas_needed))
        print(f"  - Total MATIC needed: {matic_needed_for_transfer} MATIC")
        
        if admin_matic < matic_needed_for_transfer:
            print(f"❌ Admin has insufficient MATIC!")
            print(f"   Available: {admin_matic}")
            print(f"   Needed: {matic_needed_for_transfer}")
            return
        
        # Step 4: Mint 50 TEO to student1
        print(f"\n🪙 Minting 50 TEO to student1...")
        mint_result = service.mint_tokens(STUDENT1_ADDRESS, Decimal('50'))
        
        if mint_result:
            print(f"✅ TEO mint successful! TX: {mint_result}")
        else:
            print(f"❌ TEO mint failed!")
            return
        
        # Step 5: Send 0.01 MATIC to student1
        print(f"\n💎 Sending 0.01 MATIC to student1...")
        
        # Prepara transazione MATIC
        matic_amount_wei = service.w3.to_wei('0.01', 'ether')
        
        matic_transaction = {
            'to': Web3.to_checksum_address(STUDENT1_ADDRESS),
            'value': matic_amount_wei,
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': service.w3.eth.get_transaction_count(admin_address),
        }
        
        # Firma e invia
        signed_matic_txn = service.w3.eth.account.sign_transaction(matic_transaction, ADMIN_PRIVATE_KEY)
        matic_tx_hash = service.w3.eth.send_raw_transaction(signed_matic_txn.raw_transaction)
        
        print(f"✅ MATIC transfer successful! TX: {matic_tx_hash.hex()}")
        
        # Step 6: Verifica balances finali
        print(f"\n📊 FINAL BALANCES:")
        
        # Aspetta un po' per la conferma
        import time
        time.sleep(5)
        
        # Admin balances
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic}, TEO: {admin_teo}")
        
        # Student1 balances  
        student1_matic_wei = service.w3.eth.get_balance(Web3.to_checksum_address(STUDENT1_ADDRESS))
        student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic}, TEO: {student1_teo}")
        
        print(f"\n🎉 SUCCESS! Student1 now has:")
        print(f"   💎 {student1_matic} MATIC (for gas)")
        print(f"   🪙 {student1_teo} TEO (for purchases)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_to_student1()
