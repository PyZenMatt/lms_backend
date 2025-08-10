#!/usr/bin/env python3
"""
Trasferisce 50 TEO da admin a student1 e riceve MATIC dal faucet
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
from web3 import Web3

def transfer_to_student1():
    """Trasferisce 50 TEO da admin a student1"""
    print("🚀 Transferring 50 TEO from admin to student1...")
    
    # Configurazione
    ADMIN_PRIVATE_KEY = "e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255"
    STUDENT1_ADDRESS = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Calcola l'admin address
        admin_account = service.w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
        admin_address = admin_account.address
        
        print(f"👤 Admin address: {admin_address}")
        print(f"🎯 Student1 address: {STUDENT1_ADDRESS}")
        
        # Controlla balances iniziali
        print(f"\n📊 INITIAL BALANCES:")
        
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic}, TEO: {admin_teo}")
        
        student1_matic_wei = service.w3.eth.get_balance(Web3.to_checksum_address(STUDENT1_ADDRESS))
        student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic}, TEO: {student1_teo}")
        
        # Calcola costo del transfer
        gas_price = service.w3.eth.gas_price
        gas_price_gwei = service.w3.from_wei(gas_price, 'gwei')
        transfer_cost = service.w3.from_wei(gas_price * 80000, 'ether')  # Gas limit per transfer TEO
        
        print(f"\n⛽ Gas price: {gas_price_gwei} Gwei")
        print(f"💰 Transfer cost: {transfer_cost} MATIC")
        
        if admin_matic < transfer_cost:
            print(f"❌ Admin has insufficient MATIC for transfer!")
            print(f"   Available: {admin_matic}")
            print(f"   Needed: {transfer_cost}")
            print(f"\n💡 Please add MATIC to admin wallet from Polygon faucet:")
            print(f"   🔗 https://faucet.polygon.technology/")
            print(f"   📍 Admin address: {admin_address}")
            return
        
        # Trasferisce 50 TEO
        print(f"\n🪙 Transferring 50 TEO to student1...")
        result = service.transfer_tokens(
            from_private_key=ADMIN_PRIVATE_KEY,
            to_address=STUDENT1_ADDRESS,
            amount=Decimal('50')
        )
        
        if result:
            print(f"✅ Transfer successful! TX: {result}")
            
            # Aspetta conferma
            import time
            time.sleep(5)
            
            # Controlla balances finali
            print(f"\n📊 FINAL BALANCES:")
            
            admin_matic_wei = service.w3.eth.get_balance(admin_address)
            admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
            admin_teo = service.get_balance(admin_address)
            print(f"Admin - MATIC: {admin_matic}, TEO: {admin_teo}")
            
            student1_matic_wei = service.w3.eth.get_balance(Web3.to_checksum_address(STUDENT1_ADDRESS))
            student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
            student1_teo = service.get_balance(STUDENT1_ADDRESS)
            print(f"Student1 - MATIC: {student1_matic}, TEO: {student1_teo}")
            
            print(f"\n🎉 SUCCESS! Student1 now has {student1_teo} TEO!")
            print(f"\n💡 Now student1 needs MATIC for gas to make purchases.")
            print(f"   You can send MATIC from faucet to: {STUDENT1_ADDRESS}")
            
        else:
            print(f"❌ Transfer failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    transfer_to_student1()
