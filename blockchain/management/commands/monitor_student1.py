#!/usr/bin/env python3
"""
Monitor per verificare quando student1 riceve MATIC dal faucet
"""

import os
import sys
import django
import time

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3

def monitor_student1_matic():
    """Monitora il balance MATIC di student1"""
    print("📱 Monitoring student1 MATIC balance...")
    
    STUDENT1_ADDRESS = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
    
    try:
        service = TeoCoinService()
        student1_checksum = Web3.to_checksum_address(STUDENT1_ADDRESS)
        
        print(f"🎯 Student1 address: {STUDENT1_ADDRESS}")
        print(f"💡 Add MATIC from faucet: https://faucet.polygon.technology/")
        print(f"🔄 Checking balance every 10 seconds...\n")
        
        initial_balance = 0
        while True:
            # Controlla balance
            balance_wei = service.w3.eth.get_balance(student1_checksum)
            balance_matic = float(service.w3.from_wei(balance_wei, 'ether'))
            
            if balance_matic != initial_balance:
                print(f"💎 Balance changed: {balance_matic} MATIC")
                
                if balance_matic > 0.001:  # Soglia minima per transazioni
                    print(f"✅ Sufficient MATIC received!")
                    
                    # Controlla anche TEO
                    teo_balance = service.get_balance(STUDENT1_ADDRESS)
                    print(f"🪙 TEO balance: {teo_balance}")
                    
                    # Calcola quante transazioni può fare
                    gas_price = service.w3.eth.gas_price
                    tx_cost = service.w3.from_wei(gas_price * 80000, 'ether')
                    possible_txs = int(balance_matic / float(tx_cost))
                    
                    print(f"⛽ Gas price: {service.w3.from_wei(gas_price, 'gwei')} Gwei")
                    print(f"💰 Cost per transaction: {tx_cost} MATIC")
                    print(f"🔢 Possible transactions: {possible_txs}")
                    
                    print(f"\n🎉 Student1 is ready for blockchain testing!")
                    print(f"   💎 {balance_matic} MATIC (for gas)")
                    print(f"   🪙 {teo_balance} TEO (for purchases)")
                    break
                    
                initial_balance = balance_matic
            else:
                print(f"⏳ Current balance: {balance_matic} MATIC - waiting for faucet...")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    monitor_student1_matic()
