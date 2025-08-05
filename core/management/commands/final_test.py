#!/usr/bin/env python3

print("🚀 TEST COMPLETO SISTEMA TEOCOIN")
print("=" * 50)

# Test diretto delle configurazioni
import os
from web3 import Web3

# Verifica variabili d'ambiente
print("1. 🔍 Verifica variabili d'ambiente:")
admin_key = os.getenv('ADMIN_PRIVATE_KEY')
rpc_url = os.getenv('POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
contract_addr = os.getenv('TEOCOIN_CONTRACT_ADDRESS', '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')

print(f"   ADMIN_PRIVATE_KEY: {'✅ Configurata' if admin_key else '❌ Mancante'}")
print(f"   POLYGON_AMOY_RPC_URL: {rpc_url}")
print(f"   TEOCOIN_CONTRACT_ADDRESS: {contract_addr}")

# Test connessione blockchain
print("\n2. 🌐 Test connessione blockchain:")
try:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    connected = w3.is_connected()
    print(f"   Connesso: {'✅' if connected else '❌'}")
    
    if connected:
        latest_block = w3.eth.block_number
        print(f"   Ultimo blocco: {latest_block}")
except Exception as e:
    print(f"   ❌ Errore connessione: {e}")

# Test admin wallet
print("\n3. 👤 Test admin wallet:")
if admin_key:
    try:
        admin_account = w3.eth.account.from_key(admin_key)
        admin_address = admin_account.address
        balance = w3.eth.get_balance(admin_address)
        matic_balance = w3.from_wei(balance, 'ether')
        
        print(f"   Address: {admin_address}")
        print(f"   MATIC Balance: {matic_balance}")
        
        if float(matic_balance) > 0:
            print("   ✅ Admin ha MATIC per gas fees")
        else:
            print("   ⚠️ Admin NON ha MATIC - serve per gas fees")
            print(f"   💡 Vai su: https://faucet.polygon.technology/")
            print(f"   📝 Incolla address: {admin_address}")
    except Exception as e:
        print(f"   ❌ Errore admin wallet: {e}")
else:
    print("   ❌ Admin key non configurata")

# Test contratto
print("\n4. 📄 Test contratto TeoCoin:")
try:
    from blockchain.teocoin_abi import TEOCOIN_ABI
    
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_addr),
        abi=TEOCOIN_ABI
    )
    
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    total_supply = contract.functions.totalSupply().call()
    
    print(f"   Nome: {name}")
    print(f"   Simbolo: {symbol}")
    print(f"   Total Supply: {total_supply}")
    print("   ✅ Contratto accessibile")
    
except Exception as e:
    print(f"   ❌ Errore contratto: {e}")

# Test Django integration
print("\n5. 🔧 Test integrazione Django:")
try:
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
    import django
    django.setup()
    
    from blockchain.blockchain import TeoCoinService
    
    service = TeoCoinService()
    print("   ✅ TeoCoinService inizializzato")
    print(f"   Admin key configurata: {'✅' if service.admin_private_key else '❌'}")
    
    if service.admin_private_key:
        admin_account = service.w3.eth.account.from_key(service.admin_private_key)
        balance = service.w3.eth.get_balance(admin_account.address)
        matic_balance = service.w3.from_wei(balance, 'ether')
        
        print(f"   Admin MATIC: {matic_balance}")
        
        if float(matic_balance) > 0:
            print("   🎯 SISTEMA PRONTO PER MINTING!")
        else:
            print("   ⚠️ Serve MATIC per completare setup")
    
except Exception as e:
    print(f"   ❌ Errore Django: {e}")

print("\n" + "=" * 50)
print("🎯 RIASSUNTO:")

if admin_key and float(matic_balance) > 0:
    print("✅ CONFIGURAZIONE COMPLETA!")
    print("   • Admin key configurata")
    print("   • Admin ha MATIC per gas")
    print("   • Contratto accessibile")
    print("   • Sistema pronto per minting automatico")
elif admin_key:
    print("⚠️ QUASI PRONTO!")
    print("   • Admin key configurata ✅")
    print("   • Serve MATIC per gas ⚠️")
    print(f"   • Vai su: https://faucet.polygon.technology/")
    print(f"   • Address: {admin_address}")
else:
    print("❌ CONFIGURAZIONE INCOMPLETA")
    print("   • Configura ADMIN_PRIVATE_KEY nel file .env")

print("\n🚀 PROSSIMI PASSI:")
print("1. Ottenere MATIC dal faucet per l'admin address")
print("2. Testare un minting di prova")
print("3. Verificare che i reward vengano mintati on-chain")
