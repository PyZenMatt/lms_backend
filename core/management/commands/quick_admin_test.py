#!/usr/bin/env python3
"""
Quick test del gas ottimizzato per admin wallet
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

def quick_admin_test():
    """Test rapido admin wallet con gas ottimizzato"""
    try:
        service = TeoCoinService()
        
        # Admin wallet
        admin_address = "0x3b72a4E942CF1467134510cA3952F01b63005044"
        
        # Balance MATIC
        matic_balance_wei = service.w3.eth.get_balance(service.w3.to_checksum_address(admin_address))
        matic_balance = service.w3.from_wei(matic_balance_wei, 'ether')
        
        # Balance TEO
        teo_balance_wei = service.contract.functions.balanceOf(service.w3.to_checksum_address(admin_address)).call()
        teo_balance = service.w3.from_wei(teo_balance_wei, 'ether')
        
        print(f"🔍 ADMIN WALLET CHECK")
        print(f"📍 Address: {admin_address}")
        print(f"💎 MATIC: {matic_balance}")
        print(f"🪙 TEO: {teo_balance}")
        
        # Calcolo gas ottimizzato
        gas_per_tx = 0.0008  # Gas ottimizzato
        total_users = 6  # Altri utenti (escludiamo admin)
        total_gas_needed = gas_per_tx * total_users
        
        print(f"\n📊 ANALISI GAS OTTIMIZZATO:")
        print(f"👥 Utenti da servire: {total_users}")
        print(f"⛽ Gas per TX: {gas_per_tx} MATIC")
        print(f"🔢 Gas totale necessario: {total_gas_needed:.6f} MATIC")
        print(f"💰 MATIC disponibili: {float(matic_balance):.6f}")
        
        if float(matic_balance) >= total_gas_needed:
            surplus = float(matic_balance) - total_gas_needed
            print(f"✅ SUFFICIENTE! Surplus: {surplus:.6f} MATIC")
            print(f"🚀 Possiamo procedere con la distribuzione!")
            return True
        else:
            deficit = total_gas_needed - float(matic_balance)
            print(f"❌ Deficit: {deficit:.6f} MATIC")
            return False
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    can_proceed = quick_admin_test()
    print(f"\n🎯 Risultato: {'Procedere con distribuzione' if can_proceed else 'Serve più MATIC'}")
