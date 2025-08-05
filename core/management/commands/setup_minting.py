#!/usr/bin/env python3
"""
Script per configurare il sistema di minting TeoCoin
"""

import os
import sys
import django
from web3 import Web3

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def generate_admin_wallet():
    """Genera un nuovo wallet admin"""
    print("🔐 GENERAZIONE WALLET ADMIN")
    print("=" * 40)
    
    # Genera nuovo account
    w3 = Web3()
    account = w3.eth.account.create()
    
    print(f"✅ Nuovo wallet generato:")
    print(f"   Address: {account.address}")
    print(f"   Private Key: {account.key.hex()}")
    
    print(f"\n📋 PASSI DA SEGUIRE:")
    print(f"1. Aggiungere al file .env:")
    print(f"   ADMIN_PRIVATE_KEY={account.key.hex()}")
    
    print(f"\n2. Aggiungere MATIC all'address:")
    print(f"   • Vai su https://faucet.polygon.technology/")
    print(f"   • Seleziona 'Amoy Testnet'")
    print(f"   • Incolla address: {account.address}")
    print(f"   • Richiedi MATIC testnet")
    
    print(f"\n3. Configurare ownership del contratto:")
    print(f"   • Se sei owner: trasferisci ownership a {account.address}")
    print(f"   • Se hai minter role: aggiungi {account.address} come minter")
    
    return account.address, account.key.hex()

def check_current_setup():
    """Verifica la configurazione attuale"""
    print("🔍 VERIFICA CONFIGURAZIONE ATTUALE")
    print("=" * 40)
    
    try:
        from blockchain.blockchain import TeoCoinService
        service = TeoCoinService()
        
        has_admin = bool(service.admin_private_key)
        print(f"Admin Key: {'✅ Configurata' if has_admin else '❌ Non configurata'}")
        
        if has_admin:
            admin_account = service.w3.eth.account.from_key(service.admin_private_key)
            balance = service.w3.eth.get_balance(admin_account.address)
            matic_balance = service.w3.from_wei(balance, 'ether')
            
            print(f"Admin Address: {admin_account.address}")
            print(f"MATIC Balance: {matic_balance}")
            
            if float(matic_balance) > 0:
                print("✅ Setup completo - pronto per minting!")
                return True
            else:
                print("⚠️ Serve MATIC per gas fees")
                return False
        else:
            print("❌ Admin key non configurata")
            return False
            
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

def create_env_template():
    """Crea template file .env"""
    env_content = """# TeoCoin Blockchain Configuration
ADMIN_PRIVATE_KEY=your_private_key_here
POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology/
TEOCOIN_CONTRACT_ADDRESS=0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8

# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
"""
    
    env_path = "/home/teo/Project/school/schoolplatform/.env"
    
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ File .env creato: {env_path}")
    else:
        print(f"⚠️ File .env già esiste: {env_path}")
    
    return env_path

def test_minting():
    """Testa il minting con la configurazione attuale"""
    print("\n🧪 TEST MINTING")
    print("=" * 40)
    
    try:
        from blockchain.blockchain import TeoCoinService
        from decimal import Decimal
        
        service = TeoCoinService()
        
        if not service.admin_private_key:
            print("❌ Admin key non configurata")
            return False
        
        # Prova minting di test (1 TEO)
        test_address = "0x742d35Cc6cF000000000000000000001"
        test_amount = Decimal('1')
        
        print(f"Tentativo minting {test_amount} TEO a {test_address}...")
        
        tx_hash = service.mint_tokens(test_address, test_amount)
        
        if tx_hash:
            print(f"✅ Minting riuscito! TX: {tx_hash}")
            return True
        else:
            print("❌ Minting fallito")
            return False
            
    except Exception as e:
        print(f"❌ Errore minting: {str(e)}")
        return False

def main():
    print("🚀 CONFIGURAZIONE SISTEMA TEOCOIN MINTING")
    print("=" * 50)
    
    # Verifica setup attuale
    is_configured = check_current_setup()
    
    if not is_configured:
        print("\n" + "="*50)
        choice = input("\nVuoi generare un nuovo wallet admin? (y/n): ").lower()
        
        if choice == 'y':
            # Genera wallet
            address, private_key = generate_admin_wallet()
            
            # Crea template .env
            env_path = create_env_template()
            
            print(f"\n🎯 CONFIGURAZIONE COMPLETATA")
            print(f"Modifica il file {env_path} con:")
            print(f"ADMIN_PRIVATE_KEY={private_key}")
            
        else:
            print("\n📋 CONFIGURAZIONE MANUALE:")
            print("1. Ottieni un private key admin")
            print("2. Aggiungi ADMIN_PRIVATE_KEY nel file .env")
            print("3. Aggiungi MATIC all'admin address")
            print("4. Riesegui questo script per testare")
    
    else:
        # Testa minting
        print("\n✅ Configurazione OK - Testing minting...")
        test_minting()
    
    print(f"\n📚 DOCUMENTAZIONE:")
    print(f"• Polygon Amoy Faucet: https://faucet.polygon.technology/")
    print(f"• Contract Explorer: https://amoy.polygonscan.com/address/0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8")

if __name__ == "__main__":
    main()
