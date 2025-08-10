#!/usr/bin/env python3
"""
Script semplificato per richiedere MATIC faucet specificamente per la reward pool.
Utilizza i faucet più affidabili e fornisce istruzioni chiare.
"""
import os
import sys
import requests
import time
import webbrowser
from typing import Optional

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

try:
    import django
    django.setup()
    from blockchain.blockchain import TeoCoinService
    from web3 import Web3
    DJANGO_AVAILABLE = True
except:
    DJANGO_AVAILABLE = False
    print("⚠️ Django non disponibile, alcune funzionalità saranno limitate")

def get_reward_pool_info():
    """Ottieni informazioni sulla reward pool"""
    reward_pool_address = os.getenv('REWARD_POOL_ADDRESS', '0x3b72a4E942CF1467134510cA3952F01b63005044')
    
    if DJANGO_AVAILABLE:
        try:
            tcs = TeoCoinService()
            balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(reward_pool_address))
            balance_matic = float(tcs.w3.from_wei(balance_wei, 'ether'))
            return reward_pool_address, balance_matic
        except Exception as e:
            print(f"⚠️ Errore nel controllo balance: {e}")
            return reward_pool_address, 0.0
    
    return reward_pool_address, 0.0

def request_polygon_faucet(address: str) -> bool:
    """Richiedi MATIC dal faucet ufficiale Polygon (più affidabile)"""
    print("🔄 Richiedendo MATIC dal faucet ufficiale Polygon...")
    
    faucet_url = "https://faucet.polygon.technology/"
    api_url = "https://faucet.polygon.technology/api/faucet"
    
    # Prima prova con API diretta
    try:
        payload = {
            "network": "amoy",
            "address": address,
            "token": "maticToken"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Origin': 'https://faucet.polygon.technology',
            'Referer': 'https://faucet.polygon.technology/'
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Faucet API response: {result}")
            return True
        else:
            print(f"❌ API fallita: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Errore API: {e}")
    
    return False

def open_faucet_browser(address: str):
    """Apri i faucet nel browser per richiesta manuale"""
    print(f"\n🌐 === FAUCET MANUALI ===")
    print(f"📋 Indirizzo reward pool: {address}")
    print("\n🔗 Faucet consigliati (in ordine di affidabilità):")
    
    faucets = [
        ("Polygon Faucet (Ufficiale)", "https://faucet.polygon.technology/"),
        ("Alchemy Faucet", "https://www.alchemy.com/faucets/polygon-amoy"),
        ("QuickNode Faucet", "https://faucet.quicknode.com/polygon/amoy"),
        ("Chainlink Faucet", "https://faucets.chain.link/polygon-amoy")
    ]
    
    for i, (name, url) in enumerate(faucets, 1):
        print(f"{i}. {name}: {url}")
    
    print(f"\n📝 ISTRUZIONI:")
    print(f"1. Copia l'indirizzo: {address}")
    print(f"2. Vai su uno dei faucet sopra")
    print(f"3. Incolla l'indirizzo nel campo 'Address'")
    print(f"4. Seleziona rete 'Polygon Amoy' (se richiesto)")
    print(f"5. Completa eventuali captcha/verifiche")
    print(f"6. Clicca 'Request' o 'Send'")
    
    # Apri automaticamente il faucet ufficiale
    try:
        print(f"\n🔗 Aprendo il faucet ufficiale Polygon...")
        webbrowser.open("https://faucet.polygon.technology/")
        return True
    except Exception as e:
        print(f"⚠️ Impossibile aprire il browser: {e}")
        return False

def monitor_balance_changes(address: str, initial_balance: float, timeout: int = 180):
    """Monitora i cambiamenti di balance"""
    if not DJANGO_AVAILABLE:
        print("⚠️ Monitoraggio non disponibile senza Django")
        return False
    
    print(f"\n👁️ Monitoraggio balance per {timeout} secondi...")
    print(f"💰 Balance iniziale: {initial_balance:.6f} MATIC")
    
    tcs = TeoCoinService()
    start_time = time.time()
    last_check = time.time()
    
    while time.time() - start_time < timeout:
        # Controlla ogni 15 secondi
        if time.time() - last_check >= 15:
            try:
                balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(address))
                current_balance = float(tcs.w3.from_wei(balance_wei, 'ether'))
                
                if current_balance > initial_balance:
                    received = current_balance - initial_balance
                    print(f"🎉 SUCCESS! Ricevuti {received:.6f} MATIC!")
                    print(f"💰 Nuovo balance: {current_balance:.6f} MATIC")
                    return True
                
                print(f"⏳ Balance: {current_balance:.6f} MATIC (attesa...)")
                last_check = time.time()
                
            except Exception as e:
                print(f"⚠️ Errore nel controllo balance: {e}")
        
        time.sleep(5)
    
    print("⏰ Timeout raggiunto - la transazione potrebbe essere ancora in pending")
    return False

def main():
    print("🚰 === FAUCET MATIC AMOY PER REWARD POOL ===\n")
    
    # Ottieni informazioni reward pool
    reward_pool_address, current_balance = get_reward_pool_info()
    
    print(f"📍 Reward Pool Address: {reward_pool_address}")
    print(f"💰 Balance attuale: {current_balance:.6f} MATIC")
    
    if current_balance >= 0.01:  # Soglia minima
        print(f"✅ La reward pool ha già abbastanza MATIC ({current_balance:.6f})")
        response = input("Vuoi comunque richiedere più MATIC? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'si', 's']:
            print("👋 Operazione annullata")
            return
    
    print(f"\n🎯 Richiedendo MATIC per: {reward_pool_address}")
    
    # Prova prima con API automatica
    api_success = request_polygon_faucet(reward_pool_address)
    
    if api_success:
        print("✅ Richiesta API inviata con successo!")
        # Monitora per vedere se arrivano i fondi
        success = monitor_balance_changes(reward_pool_address, current_balance, 180)
        if success:
            print("\n🎉 === FAUCET COMPLETATO CON SUCCESSO ===")
            return
    
    # Se l'API non funziona, apri i faucet manuali
    print("\n🔧 API automatica non disponibile, usando faucet manuali...")
    browser_opened = open_faucet_browser(reward_pool_address)
    
    if browser_opened:
        # Attendi che l'utente completi la richiesta
        input("\n⏳ Completa la richiesta nel browser e premi INVIO per monitorare...")
        
        # Monitora i cambiamenti
        success = monitor_balance_changes(reward_pool_address, current_balance, 300)  # 5 minuti
        
        if success:
            print("\n🎉 === FAUCET COMPLETATO CON SUCCESSO ===")
        else:
            print("\n⚠️ === FAUCET IN ATTESA ===")
            print("La transazione potrebbe essere ancora in pending.")
            print("Controlla manualmente tra qualche minuto.")
    
    print(f"\n📊 Balance finale reward pool:")
    final_address, final_balance = get_reward_pool_info()
    print(f"💰 {final_balance:.6f} MATIC")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Operazione interrotta")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
