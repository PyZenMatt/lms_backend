# Wallet modes: DB-first vs Blockchain

SchoolPlatform supporta due modalità di wallet per TeoCoin:

## 1) DB-first (default)
- **Cosa fa:** gestisce saldo, sconti e flusso hold→settle **nel database**.  
- **Perché:** semplicità, performance, test deterministici, nessuna gestione chiavi.  
- **Quando usarla:** sviluppo, staging, produzione iniziale senza requisiti crypto.
- **Flag:**
  - `USE_DB_TEOCOIN_SYSTEM=True`
  - `TEOCOIN_SYSTEM=database`
  - `TEOCOIN_EUR_RATE=1` (solo test/dev)

**Flow tipico:**  
Checkout Stripe → webhook “succeeded” → settle degli hold nel DB → aggiornamento saldi/earning/commissioni → (opz.) notifica FE.

## 2) Blockchain (opt-in)
- **Cosa fa:** invoca operazioni on-chain (mint/transfer/withdraw) **in aggiunta** o **in alternativa** al DB.  
- **Requisiti:** RPC affidabile, gestione chiavi sicura, policy di firma, stime GAS/preventivo costi.  
- **Rischi:** leak di `ADMIN_PRIVATE_KEY`, nonce management, race conditions, costi variabili, latenza, fork/rollback di chain.
- **Flag:**
  - `USE_DB_TEOCOIN_SYSTEM=False` *(se vuoi esclusione DB)*  
  - `TEOCOIN_SYSTEM=blockchain`
  - `WALLET_CHAIN_RPC=<rpc-url>`
  - `ADMIN_PUBLIC_KEY`, `ADMIN_PRIVATE_KEY`, `PLATFORM_WALLET_ADDRESS`

> **Nota:** in molte architetture “prod” conviene mantenere **DB come source of truth** e fare **sync on-chain** asincrona (con retry e reconciliation) per evitare blocchi su percorso critico di checkout.

## Payout ai docenti
- **Stato attuale:** earning/commissioni sono **tracciate a livello dati**; l’erogazione reale (SEPA/Stripe Connect) **non è automatizzata** nel MVP.  
- **Prossimo step:** integrazione Stripe Connect (Transfers/Payouts) **fuori dal percorso del checkout studenti**.

## Sicurezza (minimi)
1. **Niente chiavi in repo**: usa `.env` o secret manager; ruota periodicamente.  
2. **Principio del minimo privilegio**: la chiave di firma deve avere scope limitato.  
3. **Audit log** per operazioni on-chain e per modifiche manuali di saldo DB.  
4. **Idempotenza**: tutti i webhook e le operazioni di settle/mint devono poter essere ri-eseguite senza effetti collaterali.

## Troubleshooting rapido
- “Saldo non si aggiorna”: verifica webhook Stripe e la logica di settle DB.  
- “Sync on-chain fallita”: controlla RPC/nonce e riprova asincrono; non bloccare il checkout.  
- “Firma fallita”: chiave errata o non caricata, o formato non supportato dal provider.
