#!/usr/bin/env python3
"""
Verifica transazione blockchain per debug
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import teocoin_service
from web3 import Web3

def check_transaction(tx_hash):
    """Verifica dettagli di una transazione"""
    
    print(f"🔍 Verifica transazione: {tx_hash}")
    print("=" * 60)
    
    try:
        # Get transaction receipt
        w3 = teocoin_service.w3
        
        # Check if transaction exists
        try:
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            print(f"✅ Transazione trovata!")
            print(f"📊 Status: {tx_receipt.status} (1=success, 0=failed)")
            print(f"⛽ Gas used: {tx_receipt.gasUsed}")
            print(f"📍 Block: {tx_receipt.blockNumber}")
            print(f"🏠 From: {tx_receipt['from']}")
            print(f"🎯 To: {tx_receipt.to}")
            
            # Check transaction details
            tx = w3.eth.get_transaction(tx_hash)
            print(f"💰 Value: {Web3.from_wei(tx.value, 'ether')} MATIC")
            print(f"📝 Input data length: {len(tx.input)} bytes")
            
            if tx_receipt.status == 0:
                print("❌ TRANSAZIONE FALLITA!")
            else:
                print("✅ Transazione completata con successo")
                
        except Exception as e:
            print(f"❌ Transazione non trovata o errore: {e}")
            
        # Check allowance
        student_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
        reward_pool_address = "0x3b72a4E942CF1467134510cA3952F01b63005044"
        
        print(f"\n🔍 Verifica allowance:")
        print(f"👤 Student: {student_address}")
        print(f"🏦 Reward Pool: {reward_pool_address}")
        
        contract = teocoin_service.contract
        checksum_student = Web3.to_checksum_address(student_address)
        checksum_reward_pool = Web3.to_checksum_address(reward_pool_address)
        
        allowance_wei = contract.functions.allowance(checksum_student, checksum_reward_pool).call()
        allowance = Web3.from_wei(allowance_wei, 'ether')
        
        print(f"💳 Allowance attuale: {allowance} TEO")
        
        if float(allowance) >= 15:
            print("✅ Allowance sufficiente per il pagamento")
        else:
            print("❌ Allowance insufficiente! Serve approve() via MetaMask")
            
        # Check balances
        student_balance = teocoin_service.get_balance(student_address)
        print(f"💼 Balance studente: {student_balance} TEO")
        
    except Exception as e:
        print(f"❌ Errore nella verifica: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Hash from the test result
    tx_hash = "3114f0200efa4ae12e34328f1d8139302e7bbd5e3256cc0501a276e3f84e696e"
    check_transaction(tx_hash)
