#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

import django
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3

print("🔍 Test Configurazione TeoCoin")
print("=" * 40)

try:
    service = TeoCoinService()
    print(f"✅ Connesso: {service.w3.is_connected()}")
    print(f"🔑 Admin key: {'✅' if service.admin_private_key else '❌'}")
    
    if service.admin_private_key:
        admin_account = service.w3.eth.account.from_key(service.admin_private_key)
        balance = service.w3.eth.get_balance(admin_account.address)
        matic_balance = service.w3.from_wei(balance, 'ether')
        
        print(f"👤 Admin: {admin_account.address}")
        print(f"💰 MATIC: {matic_balance}")
        
        if float(matic_balance) > 0:
            print("✅ Pronto per minting!")
        else:
            print("⚠️ Serve MATIC per gas")
            print(f"   Vai su: https://faucet.polygon.technology/")
            print(f"   Address: {admin_account.address}")
    
except Exception as e:
    print(f"❌ Errore: {e}")
