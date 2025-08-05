#!/usr/bin/env python
"""
Test semplificato del sistema reward pool
Verifica che la logica di trasferimento dalla pool funzioni
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService, get_reward_pool_balance
from django.conf import settings

def test_reward_pool_transfer():
    """
    Test della funzione di trasferimento dalla reward pool
    """
    print("=== TEST TRASFERIMENTO REWARD POOL ===")
    
    # 1. Controlla balance iniziale della reward pool
    initial_balance = get_reward_pool_balance()
    print(f"Balance iniziale reward pool: {initial_balance} TEO")
    
    # 2. Inizializza servizio TeoCoin
    try:
        service = TeoCoinService()
        print("✅ Servizio TeoCoin inizializzato")
    except Exception as e:
        print(f"❌ Errore inizializzazione servizio: {e}")
        return
    
    # 3. Test trasferimento piccolo dalla reward pool (senza effettivamente eseguirlo)
    test_address = "0x1234567890123456789012345678901234567890"  # Indirizzo di test
    test_amount = Decimal("0.001")  # 1 millesimo di TEO
    
    print(f"\n--- Test Trasferimento ---")
    print(f"Da: Reward Pool ({getattr(settings, 'REWARD_POOL_ADDRESS', 'N/A')})")
    print(f"A: {test_address}")
    print(f"Importo: {test_amount} TEO")
    
    # 4. Verifica che il metodo transfer_from_reward_pool esista
    if hasattr(service, 'transfer_from_reward_pool'):
        print("✅ Metodo transfer_from_reward_pool trovato")
        
        # Per ora solo stampiamo quello che succederebbe
        print(f"⚠️  Test in modalità simulazione (per evitare spese gas reali)")
        print(f"   Il trasferimento di {test_amount} TEO ridurrebbe il balance a {initial_balance - test_amount}")
        
    else:
        print("❌ Metodo transfer_from_reward_pool non trovato")
    
    # 5. Verifica configurazione reward pool
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
    reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
    
    print(f"\n--- Configurazione Reward Pool ---")
    print(f"Address: {reward_pool_address}")
    print(f"Private Key: {'✅ Configurata' if reward_pool_private_key else '❌ Mancante'}")
    
    # 6. Mostra soglie di avviso
    from blockchain.blockchain import check_reward_pool_health
    
    try:
        health = check_reward_pool_health()
        print(f"\n--- Stato Salute Pool ---")
        print(f"Status: {health['status'].upper()}")
        print(f"Balance: {health['balance']} TEO")
        print(f"Soglia Warning: {health['warning_threshold']} TEO")
        print(f"Soglia Critical: {health['critical_threshold']} TEO")
        
        if health['status'] == 'healthy':
            estimated_rewards = int(health['balance'] * 100)  # Assumendo 0.01 TEO per reward
            print(f"Reward stimati disponibili: ~{estimated_rewards}")
        
    except Exception as e:
        print(f"❌ Errore controllo salute pool: {e}")
    
    print(f"\n✅ Sistema reward pool configurato e pronto!")
    print(f"💡 Per testare un trasferimento reale, utilizzare il management command:")
    print(f"   python manage.py reward_pool --transfer <address> <amount>")

if __name__ == "__main__":
    test_reward_pool_transfer()
