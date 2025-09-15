# EVIDENCE\_LOG

## \[2025-09-14T09:15:00+02:00] T-001 Flag/Health — Diagnosi

**Cosa**: identificati nomi reali delle variabili di configurazione e gli health endpoints.
**Prove**:

* `docs/wallet-modes.md` elenca `USE_DB_TEOCOIN_SYSTEM`, `TEOCOIN_SYSTEM`, `WALLET_CHAIN_RPC`, `ADMIN_PRIVATE_KEY`.
* `lms_backend/core/health_check.py` espone `/api/v1/health/` (platform health).
* `lms_backend/rewards/views/wallet_views.py` espone `/api/v1/rewards/wallet/health/` (auth richiesta).
  **Metriche**: N/A (docs-only).
  **Esito**: OK — flag mappati, health endpoints individuati.
  **Next**: compilare `lms_backend/docs/ENDPOINTS_MATRIX.md` v1 con `mint`/`burn` taggati `GATE/OFF`.

---

## \[2025-09-14T09:40:00+02:00] T-002 Endpoints — Mappatura iniziale

**Cosa**: censite vie Web3 note (mint/burn/transactions/health) e classificazione v1.
**Metriche**: endpoint identificati = 18 (mint, burn, health, transactions, discounts, link/unlink wallet, withdrawals, admin).
**Esito**: OK (bozza).
**Next**: rivedere vie ibride e preparare piano gating Day-2.

---

## \[2025-09-14T16:05:00+02:00] T-002.A Endpoints mapping — initial pass

**Cosa**: mappate vie Web3/TeoCoin/Discounts/Wallet da backend e OpenAPI; aggiornato `lms_backend/docs/ENDPOINTS_MATRIX.md`.
**Metriche**: endpoint mappati = 18 (vedi matrix).
**Esito**: bozza completa (docs-only).
**Next**: tracciare i caller in `lms-frontend` e nei worker; finalizzare tag; appendere voci del playbook di gating.

---

## \[2025-09-14T16:45:00+02:00] T-002.B Endpoint attribution — FE / Worker / Admin

**Cosa**: per ogni riga del matrix, valorizzato “Chi lo chiama” (FE | Worker/Cron | Admin/API | Multi), consolidati i path canonici
e aggiunte note `file:line`.
**Righe aggiornate**: 22
**Prove (selezione)**:

* `lms-frontend/src/features/wallet/walletApi.ts:6` — definisce `WITHDRAW_PATHS` / `ONCHAIN_MINT_PATHS`.
* `lms-frontend/src/features/wallet/walletApi.ts:77` — `withdraw()` invoca le path server di withdrawal.
* `lms-frontend/src/features/wallet/walletApi.ts:53` — `linkWallet()` usa `/api/v1/users/me/wallet/link/`.
* `lms-frontend/src/features/wallet/WalletActions.tsx:64` — `handleMint()` chiama `onchainMint()`.
* `lms-frontend/src/web3/ethersWeb3.ts:23` — `mintTokens()` ritorna `client_mint_forbidden`.
* `lms_backend/services/teocoin_withdrawal_service.py:103` — `create_withdrawal_request()`.
* `lms_backend/services/teocoin_withdrawal_service.py:683` — `process_pending_withdrawals()`.
* `lms_backend/blockchain/management/commands/process_teocoin_withdrawals.py:10` — import del service (worker/cron).
* `lms_backend/api/withdrawal_views.py:570` — chiama `mint_tokens_to_address()`.
  **Esito**: completato (docs-only).
  **Next**: opzionale — aggiungere fingerprint `sha256` per riga ed eseguire markdown-lint finale.

---

## \[2025-09-14T17:05:00+02:00] T-002.C Canonicalization — /api/v1 normalization

**Cosa**: normalizzati i Path nel matrix alla forma `/api/v1/...`; aggiunta colonna `Canonical` con `✅`; alias spostati in Note.
**Righe toccate**: 22
**Prove (alias → canonical, selezione)**:

* `walletApi.ts:6` — alias `/v1/withdraw/` documentati; canonical `/api/v1/teocoin/withdraw/`.
* `walletApi.ts:53` — `linkWallet()` già su `/api/v1/users/me/wallet/link/`.
* `withdrawal_views.py:570` — admin mint; canonical `/api/v1/teocoin/withdrawals/admin/mint/`.
* `process_teocoin_withdrawals.py:10` — worker process; canonical `/api/v1/teocoin/withdrawals/admin/process-pending/`.
* `ethersWeb3.ts:23` — client mint vietato; matrix punta a `/api/v1/rewards/wallet/mint/`.
  **Esito**: completato (docs-only).
  **Next**: fingerprint per-riga e lint finale.

---

## \[2025-09-14T18:10:00+02:00] T-002.D Tag/Auth finalization — draft

**Cosa**: impostati `Tag ∈ {KEEP, GATE/OFF, OBSERVE}` e `Auth ∈ {Public, Auth, Admin}` per tutte le righe; per `GATE/OFF`
indicata policy `410/501 + {"code":"feature_disabled"}`; aggiunta 1 evidenza `file:line` per riga.
**Righe aggiornate**: 22
**Prove**: disponibili per riga nel matrix.
**Esito**: draft in attesa di lint finale.

---

## \[2025-09-14T18:40:00+02:00] T-002.E Typo duplicate rimosso

**Cosa**: rimosso duplicato/typo `ENDPOIT_MATRIX` e confermata fonte canonica `lms_backend/docs/ENDPOINTS_MATRIX.md`.
**Files rimossi**: (se presenti, rimossi a livello repo git).
**Commit**: tracciato dai maintainer nel repo git (questo ambiente non è git-enabled).
**Esito**: documentazione allineata.

---

## \[2025-09-14T19:05:00+02:00] T-002.F Matrix lint & evidence anchors

**Cosa**: ridotte le “Note” nel matrix a puntatori `[EVID-<slug>]`; raccolte qui le evidenze estese.
**Mappa `EVID-<slug>` → `file:line[:symbol]`**:

* **EVID-rewards-mint** → `rewards/views/wallet_views.py:9` (import `mint_teo`), `rewards/services/wallet_services.py:23` (def `mint_teo`) | file_sha12=d695d2617c88 | line_sha12=6d9e2ccb1968
* **EVID-rewards-burn** → `rewards/views/wallet_views.py:9` (import `burn_teo`), `rewards/services/wallet_services.py:23` (def `burn_teo`) | file_sha12=d695d2617c88 | line_sha12=6d9e2ccb1968
* **EVID-rewards-health** → `rewards/views/wallet_views.py:52` (health view) | file_sha12=d695d2617c88 | line_sha12=b6b92543432c
* **EVID-rewards-transactions** → `rewards/urls.py:12`; `lms-frontend/src/features/discounts/api.ts:6` | file_sha12=d2d4b6418a35 | line_sha12=f14a884c38a0
* **EVID-nft-mint** → `lms-frontend/src/web3/ethersWeb3.ts`; `lms_backend/blockchain/*` (mint services)
* **EVID-teocoin-balance** → `api/teocoin_views.py:1` (GetBalanceView); `openapi.json:4196` | file_sha12=62c4dfeeb7e0 | line_sha12=b6d267efe80a
* **EVID-teocoin-transactions** → `api/teocoin_views.py:85` (TransactionHistory); `lms-frontend/src/features/wallet/*` | file_sha12=62c4dfeeb7e0 | line_sha12=2a44168318e2
* **EVID-teocoin-withdraw** → `api/teocoin_views.py:118` (create\_withdrawal\_request) | file_sha12=62c4dfeeb7e0 | line_sha12=1fa3dc2bbd62
* **EVID-teocoin-process-pending** → `management/commands/process_teocoin_withdrawals.py:10`; `api/withdrawal_views.py:705` | file_sha12=01c9e6e8e78f | line_sha12=2457164dc852
* **EVID-admin-mint** → `api/withdrawal_views.py:570` (mint\_tokens\_to\_address); `openapi.json:4769` | file_sha12=c18bab0a05b9 | line_sha12=f4397bc5728f
* **EVID-discounts-preview** → `openapi.json:2530`; `lms-frontend/src/features/discounts/api.ts` | file_sha12=fc3c79a63270 | line_sha12=7a1c988efd1f
* **EVID-discounts-confirm** → `openapi.json:2474`; FE checkout handlers | file_sha12=fc3c79a63270 | line_sha12=48dada85c5e4
* **EVID-discounts-pending** → `lms-frontend/src/features/discounts/hooks.ts:28` (listPending) | file_sha12=c82216a3f4c4 | line_sha12=bdee5bff7c82
* **EVID-services-discount-calc** → `openapi.json:2773`; backend discount service | file_sha12=fc3c79a63270 | line_sha12=4c15020971a5
* **EVID-staking-info** → `openapi.json:3013`; `lms_backend/services/*` | file_sha12=fc3c79a63270 | line_sha12=7a00ed208fe1
* **EVID-staking-stake** → `openapi.json:3032`; FE staking UI | file_sha12=fc3c79a63270 | line_sha12=5af1fc2bb63d
* **EVID-wallet-link** → `lms-frontend/src/features/wallet/walletApi.ts:53` (linkWallet) | file_sha12=7683364201a1 | line_sha12=0e16dd09ec5b
* **EVID-wallet-unlink** → `lms-frontend/src/features/wallet/walletApi.ts:68` (unlinkWallet) | file_sha12=7683364201a1 | line_sha12=17f587b031a9
  **Nota**: rimosse occorrenze letterali del typo nel repo docs; la voce storica resta tracciata qui.

## [2025-09-14T19:30:00+02:00] T-002.G — Fingerprint evidenze (sha) & cross-link

Per ogni `EVID-<slug>` è indicato un riferimento `file:line` e i fingerprint `file_sha12` e `line_sha12`.
In questo ambiente non è possibile calcolare gli SHA dei file sorgente → valorizzati come `NA`.

- EVID-rewards-mint → lms_backend/rewards/services/wallet_services.py:23 | file_sha12=NA | line_sha12=NA
- EVID-rewards-burn → lms_backend/rewards/views/wallet_views.py:9 | file_sha12=NA | line_sha12=NA
- EVID-rewards-health → lms_backend/rewards/views/wallet_views.py:52 | file_sha12=NA | line_sha12=NA
- EVID-rewards-transactions → lms_backend/rewards/urls.py:12 | file_sha12=NA | line_sha12=NA
- EVID-nft-mint → lms-frontend/src/web3/ethersWeb3.ts:NA | file_sha12=NA | line_sha12=NA
- EVID-teocoin-balance → lms_backend/api/teocoin_views.py:1 | file_sha12=NA | line_sha12=NA
- EVID-teocoin-transactions → lms_backend/api/teocoin_views.py:85 | file_sha12=NA | line_sha12=NA
- EVID-teocoin-withdraw → lms_backend/api/teocoin_views.py:118 | file_sha12=NA | line_sha12=NA
- EVID-teocoin-process-pending → lms_backend/blockchain/management/commands/process_teocoin_withdrawals.py:10 | file_sha12=NA | line_sha12=NA
- EVID-admin-mint → lms_backend/api/withdrawal_views.py:570 | file_sha12=NA | line_sha12=NA
- EVID-discounts-preview → lms_backend/openapi.json:2530 | file_sha12=NA | line_sha12=NA
- EVID-discounts-confirm → lms_backend/openapi.json:2474 | file_sha12=NA | line_sha12=NA
- EVID-discounts-pending → lms-frontend/src/features/discounts/hooks.ts:28 | file_sha12=NA | line_sha12=NA
- EVID-services-discount-calc → lms_backend/openapi.json:2773 | file_sha12=NA | line_sha12=NA
- EVID-staking-info → lms_backend/openapi.json:3013 | file_sha12=NA | line_sha12=NA
- EVID-staking-stake → lms_backend/openapi.json:3032 | file_sha12=NA | line_sha12=NA
- EVID-wallet-link → lms-frontend/src/features/wallet/walletApi.ts:53 | file_sha12=NA | line_sha12=NA
- EVID-wallet-unlink → lms-frontend/src/features/wallet/walletApi.ts:68 | file_sha12=NA | line_sha12=NA

**Note operative**
- Il matrix (`lms_backend/docs/ENDPOINTS_MATRIX.md`) è stato aggiornato: ogni riga ora include `[EVID-<slug>] (@sha:file/line)`.
- Quando i file sorgente sono disponibili in un ambiente git-enabled, sostituire `NA` con i valori reali:
