#!/usr/bin/env python3
"""
Script per verificare lo status di una transazione blockchain
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import teocoin_service

def check_transaction_status(tx_hash):
    """Verifica lo stato di una transazione"""
    
    print(f"🔍 Verifica transazione: {tx_hash}")
    print("=" * 60)
    
    try:
        # Ottieni receipt della transazione
        receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
        transaction = teocoin_service.w3.eth.get_transaction(tx_hash)
        
        print("✅ Transazione trovata!")
        print(f"📊 Status: {receipt.status} (1=success, 0=failed)")
        print(f"⛽ Gas used: {receipt.gasUsed}")
        print(f"📍 Block: {receipt.blockNumber}")
        print(f"🏠 From: {transaction['from']}")
        print(f"🎯 To: {transaction['to']}")
        print(f"💰 Value: {teocoin_service.w3.from_wei(transaction['value'], 'ether')} MATIC")
        print(f"📝 Input data length: {len(transaction['input'])} bytes")
        
        if receipt.status == 1:
            print("✅ TRANSAZIONE RIUSCITA!")
            
            # Verifica i logs per eventi Transfer
            if receipt.logs:
                print(f"\n📋 Eventi trovati: {len(receipt.logs)}")
                for i, log in enumerate(receipt.logs):
                    try:
                        # Decodifica evento Transfer
                        if len(log.topics) >= 3 and log.topics[0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                            from_addr = '0x' + log.topics[1].hex()[26:]
                            to_addr = '0x' + log.topics[2].hex()[26:]
                            amount_wei = int(log.data.hex(), 16)
                            amount_teo = teocoin_service.w3.from_wei(amount_wei, 'ether')
                            
                            print(f"  🔄 Transfer #{i+1}: {amount_teo} TEO from {from_addr} to {to_addr}")
                    except Exception as e:
                        print(f"  ❓ Log #{i+1}: {log.topics[0].hex() if log.topics else 'No topics'}")
            else:
                print("📋 Nessun evento trovato")
        else:
            print("❌ TRANSAZIONE FALLITA!")
            
            # Try to get revert reason if available
            try:
                teocoin_service.w3.eth.call(transaction, receipt.blockNumber)
            except Exception as e:
                print(f"🚫 Revert reason: {str(e)}")
        
    except Exception as e:
        print(f"❌ Errore nel recupero transazione: {e}")

def check_latest_balances():
    """Verifica i bilanci più recenti"""
    
    print("\n💼 Bilanci attuali:")
    print("-" * 30)
    
    addresses = {
        "Student": "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4",
        "Teacher": "0xE2fA8AfbF1B795f5dEd1a33aa360872E9020a9A0", 
        "Reward Pool": "0x3b72a4E942CF1467134510cA3952F01b63005044"
    }
    
    for name, addr in addresses.items():
        try:
            balance = teocoin_service.get_balance(addr)
            print(f"{name}: {balance} TEO")
        except Exception as e:
            print(f"{name}: Error - {e}")

if __name__ == "__main__":
    # Verifica l'ultima transazione teacher payment
    tx_hash = "8548d94c05650923d1d07c4223547000662ce8e36ea2e3cb7743f70ed63af353"
    check_transaction_status(tx_hash)
    check_latest_balances()
