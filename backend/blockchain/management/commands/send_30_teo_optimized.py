#!/usr/bin/env python3
"""
Invio 30 TEO a student1 con gas fees ottimizzate
"""

import os
import sys
import django
from decimal import Decimal
import time

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3

def check_gas_fees(service):
    """Controlla e ottimizza le gas fees"""
    print("⛽ Analizzando gas fees attuali...")
    
    # Gas price corrente dalla rete
    current_gas_price = service.w3.eth.gas_price
    current_gwei = service.w3.from_wei(current_gas_price, 'gwei')
    
    # Minimo per Polygon Amoy
    min_gas_price = service.w3.to_wei('25', 'gwei')
    min_gwei = 25
    
    # Massimo che vogliamo pagare per test
    max_gas_price = service.w3.to_wei('40', 'gwei')  # Ridotto da 50 a 40
    max_gwei = 40
    
    # Gas price ottimizzato
    if current_gas_price < min_gas_price:
        optimal_gas_price = min_gas_price
        optimal_gwei = min_gwei
        print(f"   Current: {current_gwei:.1f} Gwei (troppo basso)")
        print(f"   Using minimum: {optimal_gwei} Gwei")
    elif current_gas_price > max_gas_price:
        optimal_gas_price = max_gas_price
        optimal_gwei = max_gwei
        print(f"   Current: {current_gwei:.1f} Gwei (troppo alto)")
        print(f"   Capping at: {optimal_gwei} Gwei")
    else:
        optimal_gas_price = current_gas_price
        optimal_gwei = current_gwei
        print(f"   Current: {current_gwei:.1f} Gwei (ottimale)")
        print(f"   Using: {optimal_gwei:.1f} Gwei")
    
    return optimal_gas_price, optimal_gwei

def estimate_gas_cost(service, gas_price, gas_limit):
    """Stima il costo in MATIC"""
    cost_wei = gas_price * gas_limit
    cost_matic = service.w3.from_wei(cost_wei, 'ether')
    return cost_matic

def send_30_teo_optimized():
    """Invia 30 TEO con gas fees ottimizzate"""
    print("🚀 Sending 30 TEO to student1 (gas optimized)...")
    
    # Configurazione
    ADMIN_PRIVATE_KEY = "e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255"
    STUDENT1_ADDRESS = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Admin account
        admin_account = service.w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
        admin_address = admin_account.address
        
        print(f"👤 Admin address: {admin_address}")
        print(f"🎯 Student1 address: {STUDENT1_ADDRESS}")
        
        # Step 1: Analizza gas fees
        optimal_gas_price, optimal_gwei = check_gas_fees(service)
        
        # Step 2: Stima gas limit ottimale
        print("\\n🔍 Stimando gas limit ottimale...")
        
        # Prepara transazione per stima
        checksum_to = Web3.to_checksum_address(STUDENT1_ADDRESS)
        amount_wei = Web3.to_wei(Decimal('30'), 'ether')
        
        try:
            # Stima gas necessario per questa specifica transazione
            estimated_gas = service.contract.functions.mintTo(
                checksum_to, 
                amount_wei
            ).estimate_gas({
                'from': admin_address
            })
            
            # Aggiungi 20% di buffer per sicurezza
            gas_limit = int(estimated_gas * 1.2)
            print(f"   Estimated gas: {estimated_gas}")
            print(f"   With 20% buffer: {gas_limit}")
            
        except Exception as e:
            print(f"   ⚠️  Gas estimation failed: {e}")
            print(f"   Using conservative limit: 100000")
            gas_limit = 100000
        
        # Step 3: Calcola costo totale
        total_cost = estimate_gas_cost(service, optimal_gas_price, gas_limit)
        print(f"\\n💰 Transaction cost:")
        print(f"   Gas Price: {optimal_gwei:.1f} Gwei")
        print(f"   Gas Limit: {gas_limit}")
        print(f"   Total Cost: {total_cost:.6f} MATIC")
        
        # Step 4: Verifica bilanci
        print("\\n📊 INITIAL BALANCES:")
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic:.4f}, TEO: {admin_teo}")
        
        student1_matic_wei = service.w3.eth.get_balance(STUDENT1_ADDRESS)
        student1_matic = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic:.4f}, TEO: {student1_teo}")
        
        # Step 5: Verifica fondi sufficienti
        if admin_matic < total_cost:
            print(f"\\n❌ Fondi insufficienti!")
            print(f"   Disponibili: {admin_matic:.6f} MATIC")
            print(f"   Necessari: {total_cost:.6f} MATIC")
            return
        
        # Step 6: Conferma transazione
        print(f"\\n🔄 Proceeding with transaction...")
        print(f"   Minting 30 TEO to {STUDENT1_ADDRESS}")
        print(f"   Cost: {total_cost:.6f} MATIC ({optimal_gwei:.1f} Gwei)")
        
        # Usa il nostro gas ottimizzato invece del default del servizio
        # Dobbiamo costruire la transazione manualmente per controllo completo
        transaction = service.contract.functions.mintTo(
            checksum_to, 
            amount_wei
        ).build_transaction({
            'from': admin_address,
            'gas': gas_limit,
            'gasPrice': optimal_gas_price,
            'nonce': service.w3.eth.get_transaction_count(admin_address),
        })
        
        # Firma e invia
        signed_txn = service.w3.eth.account.sign_transaction(transaction, ADMIN_PRIVATE_KEY)
        tx_hash = service.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        print(f"✅ Transaction sent!")
        print(f"   TX Hash: {tx_hash.hex()}")
        
        # Step 7: Aspetta conferma
        print("\\n⏳ Waiting for confirmation...")
        receipt = service.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt.status == 1:
            actual_gas_used = receipt.gasUsed
            actual_cost = service.w3.from_wei(optimal_gas_price * actual_gas_used, 'ether')
            
            print(f"✅ Transaction confirmed!")
            print(f"   Gas used: {actual_gas_used} (saved {gas_limit - actual_gas_used})")
            print(f"   Actual cost: {actual_cost:.6f} MATIC")
            print(f"   Estimated cost: {total_cost:.6f} MATIC")
            print(f"   Savings: {(total_cost - actual_cost):.6f} MATIC")
        else:
            print(f"❌ Transaction failed!")
            return
        
        # Step 8: Verifica bilanci finali
        print("\\n📊 FINAL BALANCES:")
        time.sleep(2)  # Breve pausa per propagazione
        
        admin_matic_wei = service.w3.eth.get_balance(admin_address)
        admin_matic_final = service.w3.from_wei(admin_matic_wei, 'ether')
        admin_teo_final = service.get_balance(admin_address)
        print(f"Admin - MATIC: {admin_matic_final:.4f} (-{admin_matic - admin_matic_final:.6f}), TEO: {admin_teo_final}")
        
        student1_matic_wei = service.w3.eth.get_balance(STUDENT1_ADDRESS)
        student1_matic_final = service.w3.from_wei(student1_matic_wei, 'ether')
        student1_teo_final = service.get_balance(STUDENT1_ADDRESS)
        print(f"Student1 - MATIC: {student1_matic_final:.4f}, TEO: {student1_teo_final} (+{student1_teo_final - student1_teo})")
        
        print(f"\\n🎉 SUCCESS! Student1 received {student1_teo_final - student1_teo} TEO!")
        print(f"💸 Total transaction cost: {admin_matic - admin_matic_final:.6f} MATIC")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_30_teo_optimized()
