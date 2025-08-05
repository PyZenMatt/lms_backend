#!/usr/bin/env python3
"""
Script di emergenza per trasferire MATIC dall'admin wallet alla reward pool
quando i faucet non sono disponibili.
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

def emergency_fund_reward_pool():
    """Trasferisce MATIC dall'admin alla reward pool in caso di emergenza"""
    print("🚨 === FINANZIAMENTO EMERGENZA REWARD POOL ===")
    
    tcs = TeoCoinService()
    
    # Indirizzi
    admin_address = os.getenv('ADMIN_WALLET_ADDRESS')
    reward_pool_address = os.getenv('REWARD_POOL_ADDRESS')
    admin_private_key = os.getenv('ADMIN_PRIVATE_KEY')
    
    if not all([admin_address, reward_pool_address, admin_private_key]):
        print("❌ Variabili d'ambiente mancanti (ADMIN_WALLET_ADDRESS, REWARD_POOL_ADDRESS, ADMIN_PRIVATE_KEY)")
        return False
    
    print(f"👤 Admin: {admin_address}")
    print(f"🏦 Reward Pool: {reward_pool_address}")
    
    # Controlla balance attuali
    try:
        admin_balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(admin_address))
        admin_balance = float(tcs.w3.from_wei(admin_balance_wei, 'ether'))
        
        pool_balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(reward_pool_address))
        pool_balance = float(tcs.w3.from_wei(pool_balance_wei, 'ether'))
        
        print(f"💰 Admin MATIC: {admin_balance:.6f}")
        print(f"💰 Reward Pool MATIC: {pool_balance:.6f}")
        
    except Exception as e:
        print(f"❌ Errore nel controllo balance: {e}")
        return False
    
    # Determina quanto trasferire
    min_required = 0.01  # Minimo necessario per reward pool
    transfer_amount = 0.02  # Trasferisci 0.02 MATIC
    
    if pool_balance >= min_required:
        print(f"✅ Reward pool ha già abbastanza MATIC ({pool_balance:.6f} >= {min_required})")
        return True
    
    if admin_balance < transfer_amount + 0.01:  # Lascia almeno 0.01 per gas
        print(f"❌ Admin non ha abbastanza MATIC per il trasferimento")
        print(f"   Necessari: {transfer_amount + 0.01:.6f}, Disponibili: {admin_balance:.6f}")
        return False
    
    print(f"\n🔄 Trasferimento di {transfer_amount} MATIC...")
    
    try:
        # Prepara transazione
        admin_checksum = Web3.to_checksum_address(admin_address)
        pool_checksum = Web3.to_checksum_address(reward_pool_address)
        
        nonce = tcs.w3.eth.get_transaction_count(admin_checksum)
        gas_price = tcs.get_optimized_gas_price()
        
        tx = {
            'to': pool_checksum,
            'value': Web3.to_wei(transfer_amount, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 80002  # Polygon Amoy
        }
        
        # Firma e invia
        signed_tx = tcs.w3.eth.account.sign_transaction(tx, admin_private_key)
        tx_hash = tcs.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"✅ Transazione inviata: {tx_hash.hex()}")
        
        # Attendi conferma
        print("⏳ Attendo conferma...")
        receipt = tcs.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"🎉 Trasferimento completato!")
            print(f"📋 Block: {receipt['blockNumber']}")
            print(f"⛽ Gas usato: {receipt['gasUsed']}")
            
            # Verifica balance finali
            new_admin_balance = float(tcs.w3.from_wei(
                tcs.w3.eth.get_balance(admin_checksum), 'ether'
            ))
            new_pool_balance = float(tcs.w3.from_wei(
                tcs.w3.eth.get_balance(pool_checksum), 'ether'
            ))
            
            print(f"\n💳 === BALANCE FINALI ===")
            print(f"👤 Admin: {new_admin_balance:.6f} MATIC (era {admin_balance:.6f})")
            print(f"🏦 Reward Pool: {new_pool_balance:.6f} MATIC (era {pool_balance:.6f})")
            
            return True
        else:
            print("❌ Transazione fallita")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel trasferimento: {e}")
        return False

def check_all_balances():
    """Controlla i balance di tutti gli wallet principali"""
    print("📊 === CHECK BALANCE COMPLETO ===")
    
    tcs = TeoCoinService()
    
    wallets = {
        'Admin': os.getenv('ADMIN_WALLET_ADDRESS'),
        'Reward Pool': os.getenv('REWARD_POOL_ADDRESS'),
        'Minter': os.getenv('MINTER_ADDRESS')
    }
    
    for name, address in wallets.items():
        if address:
            try:
                # MATIC balance
                balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(address))
                matic_balance = float(tcs.w3.from_wei(balance_wei, 'ether'))
                
                # TeoCoins balance
                teo_balance = tcs.get_balance(address)
                
                print(f"{name:12} ({address})")
                print(f"  MATIC: {matic_balance:.6f}")
                print(f"  TEO:   {teo_balance}")
                print()
                
            except Exception as e:
                print(f"{name:12} - Errore: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestione emergenza fondi reward pool')
    parser.add_argument('--check', action='store_true', help='Solo controlla i balance')
    parser.add_argument('--force', action='store_true', help='Forza il trasferimento anche se non necessario')
    
    args = parser.parse_args()
    
    if args.check:
        check_all_balances()
        return
    
    success = emergency_fund_reward_pool()
    
    if success:
        print("\n✅ === OPERAZIONE COMPLETATA ===")
        print("🎉 Reward pool ora ha fondi sufficienti!")
    else:
        print("\n❌ === OPERAZIONE FALLITA ===")
        print("🚨 Reward pool necessita ancora fondi")
        print("💡 Prova a usare i faucet manuali:")
        print("   https://faucet.polygon.technology/")

if __name__ == "__main__":
    main()
