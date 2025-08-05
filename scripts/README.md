# Scripts SchoolPlatform

Questa cartella contiene tutti gli script di utilità, setup e deployment della piattaforma, ora riorganizzati per categoria.

## 📁 Struttura Riorganizzata

### 📂 `/blockchain/`
Script specifici per la gestione blockchain e TeoCoin:
- Analisi contratti e stato blockchain
- Calcolo gas fees e distribuzione token
- Gestione wallet e faucet

### 📂 `/data/`
Script per gestione dati e setup iniziale:
- Creazione dati di test e approvazioni
- Pulizia e reset database
- Gestione utenti e assegnazioni

### 📂 `/debug/`
Script per debugging e risoluzione problemi:
- Debug transazioni e mint failures
- Fix per inconsistenze dati
- Risoluzione errori sistema

### 📂 `/verification/`
Script per verifica stato sistema:
- Check bilanci e reward pool
- Verifica transazioni e acquisti
- Validazione frontend e API

### 📂 `/setup/`
Script di configurazione e setup iniziale (esistenti):
- Setup art school e minting
- Configurazione MetaMask e admin
- Test performance e reward system
- **Monitoraggio**: Controllo bilanci e stato blockchain
- **Analisi**: Script per analizzare contratti e performance

[📖 Documentazione completa](blockchain/README.md)

### 📂 `/setup/`
Script per setup iniziale e creazione dati di test:
- **Dati di Test**: Creazione utenti, corsi, achievements
- **Performance**: Test delle performance del sistema
- **Configurazione**: Validazione setup

[📖 Documentazione completa](setup/README.md)

### 📂 `/` (Root)
Script di deployment e build:
- `analyze_build.sh` - Analisi del build
- `deploy.sh` - Deployment della piattaforma
- `validate_deployment.sh` - Validazione deployment
- `dev-setup.sh` - Setup ambiente di sviluppo
- `test-runner.sh` - Esecuzione test automatici

## 🚀 Quick Start

### Setup Completo Iniziale
```bash
# 1. Setup ambiente di sviluppo
./scripts/dev-setup.sh

# 2. Creare dati di test
python scripts/setup/create_test_data.py

# 3. Setup blockchain e wallet
python scripts/blockchain/assign_wallets.py

# 4. Verificare setup
python scripts/setup/final_test.py
```

### Deployment
```bash
# Build e analisi
./scripts/analyze_build.sh

# Deploy
./scripts/deploy.sh

# Validazione
./scripts/validate_deployment.sh
```

### Blockchain Management
```bash
# Controllare bilanci
python scripts/blockchain/check_wallet_balances.py

# Distribuire TeoCoin
python scripts/blockchain/distribute_teocoins.py

# Monitoraggio
python scripts/blockchain/monitor_student1.py
```

## 📋 Ordine di Esecuzione Raccomandato

1. **Setup base**: `dev-setup.sh`
2. **Dati di test**: `setup/create_test_data.py`
3. **Blockchain setup**: `blockchain/assign_wallets.py`
4. **Verifiche**: `setup/final_test.py`
5. **Deploy**: `deploy.sh`

## ⚠️ Note Importanti

- Eseguire sempre in ambiente virtuale Python
- Verificare variabili d'ambiente prima dell'esecuzione
- Backup del database prima di script di setup massivi
- Scripts blockchain richiedono MATIC per transazioni

## 🔧 Troubleshooting

- **Errori Web3**: Verificare connessione Polygon Amoy
- **Errori Database**: Controllare migrazioni Django
- **Errori Gas**: Consultare `blockchain/alternative_faucets.py`

---
Per documentazione dettagliata, consultare i README nelle sottocartelle.
