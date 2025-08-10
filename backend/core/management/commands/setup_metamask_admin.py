#!/usr/bin/env python3
"""
Guida per configurare la chiave privata di MetaMask come admin key
"""

import os
import sys
import django
from web3 import Web3

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

print("🔑 CONFIGURAZIONE CHIAVE PRIVATA METAMASK COME ADMIN KEY")
print("=" * 60)

print("\n📋 PASSAGGI PER ESTRARRE LA CHIAVE PRIVATA DA METAMASK:")
print("1. Apri MetaMask")
print("2. Clicca sui 3 puntini in alto a destra")
print("3. Vai su 'Account details'")
print("4. Clicca su 'Export private key'")
print("5. Inserisci la password di MetaMask")
print("6. Copia la chiave privata (64 caratteri esadecimali)")

print("\n⚠️  ATTENZIONE SICUREZZA:")
print("• NON condividere mai la tua chiave privata")
print("• NON commitarla su git")
print("• Usala solo in ambiente di sviluppo/test")
print("• Per produzione, crea un wallet dedicato")

print("\n🔧 CONFIGURAZIONE:")
print("1. Copia la chiave privata (senza 0x)")
print("2. Incollala qui sotto quando richiesta")
print("3. Verrà salvata nel file .env")

# Input della chiave privata
print("\n" + "="*60)
private_key = input("Incolla la tua chiave privata MetaMask (senza 0x): ").strip()

# Validazione
if not private_key:
    print("❌ Chiave privata vuota")
    sys.exit(1)

# Rimuovi 0x se presente
if private_key.startswith('0x'):
    private_key = private_key[2:]

# Validazione lunghezza
if len(private_key) != 64:
    print(f"❌ Chiave privata non valida. Lunghezza: {len(private_key)}, richiesta: 64")
    sys.exit(1)

# Validazione formato esadecimale
try:
    int(private_key, 16)
except ValueError:
    print("❌ Chiave privata non è in formato esadecimale valido")
    sys.exit(1)

# Ottieni address dalla chiave privata
try:
    w3 = Web3()
    account = w3.eth.account.from_key(private_key)
    admin_address = account.address
    print(f"\n✅ Chiave privata valida!")
    print(f"📍 Admin Address: {admin_address}")
except Exception as e:
    print(f"❌ Errore validazione chiave: {e}")
    sys.exit(1)

# Leggi il file .env esistente
env_file = '/home/teo/Project/school/schoolplatform/.env'
env_content = ""

if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        env_content = f.read()

# Aggiorna/aggiungi la chiave privata
lines = env_content.split('\n')
updated_lines = []
admin_key_found = False

for line in lines:
    if line.startswith('ADMIN_PRIVATE_KEY='):
        updated_lines.append(f'ADMIN_PRIVATE_KEY={private_key}')
        admin_key_found = True
        print(f"🔄 Aggiornata ADMIN_PRIVATE_KEY esistente")
    else:
        updated_lines.append(line)

if not admin_key_found:
    updated_lines.append(f'ADMIN_PRIVATE_KEY={private_key}')
    print(f"➕ Aggiunta nuova ADMIN_PRIVATE_KEY")

# Assicurati che ci siano le altre configurazioni blockchain
blockchain_configs = [
    'POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology/',
    'TEOCOIN_CONTRACT_ADDRESS=0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8'
]

for config in blockchain_configs:
    config_name = config.split('=')[0]
    config_found = any(line.startswith(f'{config_name}=') for line in updated_lines)
    
    if not config_found:
        updated_lines.append(config)
        print(f"➕ Aggiunta configurazione: {config_name}")

# Salva il file .env aggiornato
with open(env_file, 'w') as f:
    f.write('\n'.join(updated_lines))

print(f"\n✅ File .env aggiornato: {env_file}")

# Test connessione blockchain
print(f"\n🧪 TEST CONNESSIONE BLOCKCHAIN...")

try:
    from blockchain.blockchain import TeoCoinService
    
    # Ricarica le variabili d'ambiente
    from django.conf import settings
    os.environ['ADMIN_PRIVATE_KEY'] = private_key
    
    service = TeoCoinService()
    
    if service.w3.is_connected():
        print("✅ Connesso alla blockchain Polygon Amoy")
        
        # Verifica admin address
        if service.admin_private_key:
            admin_account = service.w3.eth.account.from_key(service.admin_private_key)
            print(f"✅ Admin address configurato: {admin_account.address}")
            
            # Controlla balance MATIC
            admin_balance = service.w3.eth.get_balance(admin_account.address)
            admin_matic = service.w3.from_wei(admin_balance, 'ether')
            print(f"💰 Balance MATIC: {admin_matic}")
            
            if admin_matic > 0:
                print("✅ Admin ha MATIC per gas fees")
            else:
                print("⚠️  Admin non ha MATIC per gas fees")
                print("   Aggiungi MATIC testnet dal faucet: https://faucet.polygon.technology/")
            
            # Test info contratto
            try:
                token_info = service.get_token_info()
                print(f"🪙 Token: {token_info.get('name')} ({token_info.get('symbol')})")
                print(f"📊 Total Supply: {token_info.get('total_supply')}")
            except Exception as e:
                print(f"⚠️  Errore lettura contratto: {e}")
                
        else:
            print("❌ Admin private key non caricata nel servizio")
    else:
        print("❌ Impossibile connettersi alla blockchain")
        
except Exception as e:
    print(f"❌ Errore test blockchain: {e}")

print(f"\n🎯 PROSSIMI PASSI:")
print("1. Riavvia il server Django per caricare le nuove configurazioni")
print("2. Se admin non ha MATIC, prendilo dal faucet")
print("3. Testa il minting con test_blockchain_rewards.py")
print("4. Verifica che i reward vengano mintati on-chain")

print(f"\n📋 COMANDI UTILI:")
print("# Riavvio server Django:")
print("python manage.py runserver")
print("")
print("# Test sistema reward:")
print("python test_blockchain_rewards.py")
print("")
print("# Test integrazione completa:")
print("python test_blockchain_integration.py")

print(f"\n✅ CONFIGURAZIONE COMPLETATA!")
