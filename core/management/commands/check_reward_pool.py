#!/usr/bin/env python
"""
Utility script per controllare il bilancio della reward pool
e trasferire fondi se necessario
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import teocoin_service


def check_reward_pool_balance():
    """
    Controlla il bilancio della reward pool
    """
    print("=" * 50)
    print("REWARD POOL STATUS CHECK")
    print("=" * 50)
    
    try:
        # Controlla la configurazione
        if not teocoin_service.reward_pool_address:
            print("❌ ERRORE: Reward pool address non configurato")
            return False
        
        if not teocoin_service.reward_pool_private_key:
            print("❌ ERRORE: Reward pool private key non configurata")
            return False
        
        print(f"🏦 Reward Pool Address: {teocoin_service.reward_pool_address}")
        
        # Controlla il bilancio
        balance = teocoin_service.get_reward_pool_balance()
        print(f"💰 Current Balance: {balance} TEO")
        
        if balance < Decimal('100'):
            print("⚠️  ATTENZIONE: Bilancio reward pool basso (< 100 TEO)")
        elif balance < Decimal('10'):
            print("🚨 CRITICO: Bilancio reward pool molto basso (< 10 TEO)")
        else:
            print("✅ Bilancio reward pool OK")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE nel controllo reward pool: {e}")
        return False


def transfer_to_reward_pool(amount_teo):
    """
    Trasferisce TEO dall'account admin alla reward pool
    
    Args:
        amount_teo: Quantità di TEO da trasferire
    """
    try:
        if not teocoin_service.admin_private_key:
            print("❌ ERRORE: Admin private key non configurata")
            return False
        
        print(f"💸 Trasferendo {amount_teo} TEO alla reward pool...")
        
        tx_hash = teocoin_service.transfer_tokens(
            from_private_key=teocoin_service.admin_private_key,
            to_address=teocoin_service.reward_pool_address,
            amount=Decimal(str(amount_teo))
        )
        
        if tx_hash:
            print(f"✅ Trasferimento completato! TX Hash: {tx_hash}")
            return True
        else:
            print("❌ Trasferimento fallito")
            return False
            
    except Exception as e:
        print(f"❌ ERRORE nel trasferimento: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestisce la reward pool TeoCoin")
    parser.add_argument('--check', action='store_true', help='Controlla il bilancio della reward pool')
    parser.add_argument('--transfer', type=float, help='Trasferisce TEO alla reward pool')
    
    args = parser.parse_args()
    
    if args.check:
        check_reward_pool_balance()
    elif args.transfer:
        if args.transfer <= 0:
            print("❌ ERRORE: Importo deve essere positivo")
            sys.exit(1)
        
        print("Controllando stato reward pool prima del trasferimento...")
        check_reward_pool_balance()
        print("\n" + "=" * 50)
        
        if transfer_to_reward_pool(args.transfer):
            print("\nControllando stato reward pool dopo il trasferimento...")
            check_reward_pool_balance()
    else:
        print("Uso: python check_reward_pool.py --check")
        print("     python check_reward_pool.py --transfer <amount>")
        check_reward_pool_balance()
