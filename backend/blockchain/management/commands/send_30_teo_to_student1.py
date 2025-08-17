#!/usr/bin/env python3
"""
Invio 30 TEO a student1 0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4
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

def send_30_teo_to_student():
    """Invia 30 TEO a student1"""
    print("🚀 Sending 30 TEO to student1...")
    
    # Configurazione
    ADMIN_PRIVATE_KEY = "e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255"
    STUDENT1_ADDRESS = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Calcola l'admin address dalla private key
        admin_account = service.w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
        admin_address = admin_account.address
        
        print(f"👤 Admin address: {admin_address}")
        print(f"🎯 Student1 address: {STUDENT1_ADDRESS}")
        
        # Step 1: Controlla balances iniziali
        print("\\n📊 INITIAL BALANCES:")
        
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
        print(f"\\n⛽ Current gas price: {gas_price_gwei} Gwei")
        
        # Costo per mint TEO (gas limit: 120000)
        mint_cost = service.w3.from_wei(gas_price * 120000, 'ether')
        print(f"💰 Estimated cost for minting 30 TEO: {mint_cost} MATIC")
        
        # Step 3: Verifica se admin ha abbastanza MATIC
        if admin_matic < mint_cost:
            print(f"❌ Admin has insufficient MATIC!")
            print(f"   Available: {admin_matic}")  
            print(f"   Needed: {mint_cost}")
            return
        
        # Step 4: Mint 30 TEO to student1
        print(f"\\n🪙 Minting 30 TEO to student1...")
        mint_result = service.mint_tokens(STUDENT1_ADDRESS, Decimal('30'))
        
        if mint_result:
            print(f"✅ TEO mint successful! TX: {mint_result}")
        else:
            print(f"❌ TEO mint failed!")
            return
        
        # Step 5: Verifica balances finali
        print(f"\\n📊 FINAL BALANCES:")
        
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
        
        print(f"\\n🎉 SUCCESS! Student1 now has {student1_teo} TEO!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_30_teo_to_student()
