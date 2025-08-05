#!/usr/bin/env python3
"""
Script per richiedere MATIC da faucet sulla rete Polygon Amoy
per ricaricare automaticamente la reward pool.

Faucet supportati:
1. Polygon Faucet (ufficiale)
2. Alchemy Faucet
3. QuickNode Faucet
4. Altri faucet pubblici

Utilizzo:
python faucet_matic_amoy.py [--address ADDRESS] [--amount AMOUNT]
"""
import os
import sys
import time
import requests
import json
from typing import Optional, Dict, Any

# Setup per Django (se necessario)
sys.path.append('/home/teo/Project/school/schoolplatform')
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
    django.setup()
    from blockchain.blockchain import TeoCoinService
    DJANGO_AVAILABLE = True
except:
    DJANGO_AVAILABLE = False

class MaticFaucetRequester:
    """Classe per richiedere MATIC da diversi faucet sulla rete Amoy"""
    
    def __init__(self):
        self.reward_pool_address = os.getenv('REWARD_POOL_ADDRESS')
        self.faucet_endpoints = {
            'polygon_official': 'https://faucet.polygon.technology/api/v1/faucet',
            'alchemy': 'https://polygon-amoy-faucet.alchemy.com/api/faucet',
            'quicknode': 'https://faucet.quicknode.com/polygon/amoy',
            'chainlink': 'https://faucets.chain.link/polygon-amoy'
        }
        
    def get_reward_pool_address(self) -> str:
        """Ottieni l'indirizzo della reward pool"""
        if self.reward_pool_address:
            return self.reward_pool_address
        
        # Se Django è disponibile, prova a ottenere l'indirizzo dalla configurazione
        if DJANGO_AVAILABLE:
            return self.reward_pool_address or "0x3b72a4E942CF1467134510cA3952F01b63005044"  # Fallback
        
        # Chiedi all'utente di inserire l'indirizzo
        address = input("Inserisci l'indirizzo della reward pool: ").strip()
        if not address.startswith('0x') or len(address) != 42:
            raise ValueError("Indirizzo non valido")
        return address
    
    def check_current_balance(self, address: str) -> float:
        """Controlla il balance attuale di MATIC"""
        if not DJANGO_AVAILABLE:
            print("⚠️ Django non disponibile, impossibile controllare il balance")
            return 0.0
        
        try:
            tcs = TeoCoinService()
            from web3 import Web3
            balance_wei = tcs.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_matic = tcs.w3.from_wei(balance_wei, 'ether')
            return float(balance_matic)
        except Exception as e:
            print(f"⚠️ Errore nel controllo balance: {e}")
            return 0.0
    
    def request_polygon_official_faucet(self, address: str) -> Dict[str, Any]:
        """Richiedi MATIC dal faucet ufficiale Polygon"""
        print("🔄 Tentativo con faucet ufficiale Polygon...")
        
        try:
            payload = {
                "network": "amoy",
                "address": address,
                "token": "maticToken"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            
            response = requests.post(
                self.faucet_endpoints['polygon_official'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "response": result, "faucet": "polygon_official"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def request_alchemy_faucet(self, address: str) -> Dict[str, Any]:
        """Richiedi MATIC dal faucet Alchemy"""
        print("🔄 Tentativo con faucet Alchemy...")
        
        try:
            payload = {
                "address": address,
                "network": "amoy"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            
            response = requests.post(
                self.faucet_endpoints['alchemy'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "response": result, "faucet": "alchemy"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def request_web_faucet_via_browser(self, address: str) -> Dict[str, Any]:
        """Faucet via browser (richiede interazione manuale)"""
        print("🌐 Faucet manuali disponibili:")
        print(f"1. Polygon Faucet: https://faucet.polygon.technology/")
        print(f"2. Alchemy Faucet: https://www.alchemy.com/faucets/polygon-amoy")
        print(f"3. QuickNode Faucet: https://faucet.quicknode.com/polygon/amoy")
        print(f"4. Chainlink Faucet: https://faucets.chain.link/polygon-amoy")
        print(f"\n📋 Indirizzo da usare: {address}")
        print("\n🔗 Aprendo il browser per il faucet Polygon ufficiale...")
        
        try:
            import webbrowser
            webbrowser.open(f"https://faucet.polygon.technology/")
            return {"success": True, "response": "Browser aperto", "faucet": "manual"}
        except Exception as e:
            return {"success": False, "error": f"Impossibile aprire il browser: {e}"}
    
    def request_faucet_all_methods(self, address: str) -> bool:
        """Prova tutti i metodi disponibili per richiedere MATIC"""
        print(f"🚰 === RICHIESTA FAUCET MATIC AMOY ===")
        print(f"📍 Indirizzo: {address}")
        
        # Controlla balance iniziale
        initial_balance = self.check_current_balance(address)
        print(f"💰 Balance iniziale: {initial_balance:.6f} MATIC")
        
        success = False
        
        # Metodo 1: Faucet ufficiale Polygon
        result = self.request_polygon_official_faucet(address)
        if result["success"]:
            print(f"✅ Faucet Polygon ufficiale: {result['response']}")
            success = True
        else:
            print(f"❌ Faucet Polygon ufficiale fallito: {result['error']}")
        
        # Attendi un po' prima del prossimo tentativo
        if not success:
            time.sleep(2)
        
        # Metodo 2: Faucet Alchemy
        if not success:
            result = self.request_alchemy_faucet(address)
            if result["success"]:
                print(f"✅ Faucet Alchemy: {result['response']}")
                success = True
            else:
                print(f"❌ Faucet Alchemy fallito: {result['error']}")
        
        # Metodo 3: Faucet manuali
        if not success:
            print("\n🔧 I faucet automatici non sono disponibili.")
            manual_result = self.request_web_faucet_via_browser(address)
            if manual_result["success"]:
                print("✅ Browser aperto per faucet manuali")
                
                # Attendi che l'utente completi manualmente
                input("\n⏳ Completa la richiesta nel browser e premi INVIO per continuare...")
                success = True
        
        # Controlla balance finale
        if success:
            print("\n⏳ Attendo 30 secondi per la conferma della transazione...")
            time.sleep(30)
            
            final_balance = self.check_current_balance(address)
            print(f"💰 Balance finale: {final_balance:.6f} MATIC")
            
            if final_balance > initial_balance:
                received = final_balance - initial_balance
                print(f"🎉 Ricevuti {received:.6f} MATIC!")
                return True
            else:
                print("⚠️ Il balance non è cambiato, la transazione potrebbe essere ancora in pending")
        
        return success
    
    def monitor_balance_changes(self, address: str, duration: int = 300):
        """Monitora i cambiamenti di balance per un periodo di tempo"""
        print(f"👁️ Monitoraggio balance per {duration} secondi...")
        
        initial_balance = self.check_current_balance(address)
        print(f"💰 Balance iniziale: {initial_balance:.6f} MATIC")
        
        start_time = time.time()
        last_balance = initial_balance
        
        while time.time() - start_time < duration:
            current_balance = self.check_current_balance(address)
            
            if current_balance != last_balance:
                change = current_balance - last_balance
                print(f"🔄 Balance cambiato: {current_balance:.6f} MATIC ({change:+.6f})")
                last_balance = current_balance
                
                if change > 0:
                    print(f"✅ Ricevuti {change:.6f} MATIC!")
                    return True
            
            time.sleep(10)  # Controlla ogni 10 secondi
        
        print("⏰ Timeout raggiunto")
        return False

def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Richiedi MATIC faucet per Polygon Amoy')
    parser.add_argument('--address', help='Indirizzo destinatario (default: reward pool)')
    parser.add_argument('--monitor', action='store_true', help='Monitora i cambiamenti di balance')
    parser.add_argument('--duration', type=int, default=300, help='Durata monitoraggio in secondi')
    
    args = parser.parse_args()
    
    faucet = MaticFaucetRequester()
    
    try:
        # Determina l'indirizzo destinatario
        if args.address:
            target_address = args.address
        else:
            target_address = faucet.get_reward_pool_address()
        
        print(f"🎯 Indirizzo target: {target_address}")
        
        if args.monitor:
            # Solo monitora i cambiamenti
            faucet.monitor_balance_changes(target_address, args.duration)
        else:
            # Richiedi faucet
            success = faucet.request_faucet_all_methods(target_address)
            
            if success:
                print("\n✅ === FAUCET COMPLETATO ===")
                print("🎉 MATIC ricevuti con successo!")
            else:
                print("\n❌ === FAUCET FALLITO ===")
                print("🚨 Impossibile ricevere MATIC dai faucet automatici")
                print("💡 Prova manualmente su: https://faucet.polygon.technology/")
    
    except KeyboardInterrupt:
        print("\n🛑 Operazione interrotta dall'utente")
    except Exception as e:
        print(f"❌ Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
