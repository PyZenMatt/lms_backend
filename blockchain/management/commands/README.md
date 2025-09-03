# Blockchain Scripts

Questa cartella contiene tutti gli script utili per la gestione della blockchain e dei wallet.

## Script di Setup Wallet
- `assign_wallets.py` - Assegna wallet a tutti gli utenti
- `show_all_private_keys.py` - Mostra le chiavi private per MetaMask
- `setup_metamask_admin.py` - Setup specifico per wallet admin
- `setup_minting.py` - Setup per il minting

## Script di Gestione Fondi
- `distribute_teocoins.py` - Distribuisce TeoCoin a tutti gli utenti
- `send_test_teocoin.py` - Invia TeoCoin di test
- `send_to_student1.py` - Invia TeoCoin a student1 specificamente
- `transfer_to_student1.py` - Transfer TeoCoin a student1

## Script di Monitoraggio
- `check_wallet_balances.py` - Controlla i bilanci di tutti i wallet
- `monitor_student1.py` - Monitora specificamente student1
- `calculate_gas_costs.py` - Calcola i costi del gas

## Script di Analisi
- `analyze_contract_state.py` - Analizza lo stato del contratto
- `analyze_teocoin_contract.py` - Analizza il contratto TeoCoin

## Script di Utilità
- `alternative_faucets.py` - Lista di faucet alternativi per MATIC

## Come utilizzare gli script

```bash
# Setup iniziale dei wallet
python scripts/blockchain/assign_wallets.py

# Controllare i bilanci
python scripts/blockchain/check_wallet_balances.py

# Distribuire TeoCoin
python scripts/blockchain/distribute_teocoins.py

# Mostrare chiavi private per MetaMask
python scripts/blockchain/show_all_private_keys.py
```

## Prerequisiti
- Django environment configurato
- Connessione alla testnet Polygon Amoy
- MATIC sufficiente nel wallet admin per le transazioni

## Note di Sicurezza
- Le chiavi private sono mostrate solo per l'ambiente di sviluppo
- Mai esporre chiavi private in produzione
- Utilizzare sempre testnet per gli esperimenti
