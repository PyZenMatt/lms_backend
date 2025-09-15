# ENDPOINTS_MATRIX v1 — Web3 vs Web2 (Day 1 draft)
<!-- markdownlint-disable MD013 -->

| Dominio  | Metodo | Path                        | Canonical | Tag      | Chi lo chiama     | Auth   | Risposta Web3 OFF      | Log & metriche      | Note |
|----------|--------|-----------------------------|-----------|----------|-------------------|--------|------------------------|---------------------|------|

| Wallet   | POST   | `/api/v1/rewards/wallet/mint/` | ✅ | GATE/OFF | FE/Worker | Auth | 410/501 + feature_disabled | count 410/501 | [EVID-rewards-mint] |
| Wallet   | POST   | `/api/v1/rewards/wallet/burn/` | ✅ | GATE/OFF | FE | Auth | 410/501 + feature_disabled | count 410/501 | [EVID-rewards-burn] |
| Wallet   | GET    | `/api/v1/rewards/wallet/health/` | ✅ | KEEP | FE | Auth | 200 (ok) or 401 if not auth | availability, auth failure rate | [EVID-rewards-health] |
| Rewards  | POST   | `/api/v1/rewards/wallet/transactions/` | ✅ | KEEP | FE | Auth | 200 / DB-only behavior | p95, errors | [EVID-rewards-transactions] |
| NFT      | POST   | `/api/v1/nft/mint/` | ✅ | GATE/OFF | FE | Auth | 410/501 + {"code":"feature_disabled"} | trace NFT services | [EVID-nft-mint] |
| TeoCoin | GET | `/api/v1/teocoin/balance/` | ✅ | KEEP | FE | Auth | 200 + DB fallback when Web3 off | request rate, p95, 401 | [EVID-teocoin-balance] |
| TeoCoin | GET | `/api/v1/teocoin/transactions/` | ✅ | KEEP | FE | Auth | 200 (DB-only if Web3 off) | errors, latency | [EVID-teocoin-transactions] |
| TeoCoin | POST | `/api/v1/teocoin/withdraw/` | ✅ | GATE/OFF | FE | Auth | 410/501 + {"code":"feature_disabled"} | count 410/501, withdraw failures | [EVID-teocoin-withdraw] |
| TeoCoin | POST | `/api/v1/teocoin/withdrawals/admin/process-pending/` | ✅ | GATE/OFF | Worker/Cron | Admin | 410/501 + {"code":"feature_disabled"} | job run counts, errors | [EVID-teocoin-process-pending] |
| TeoCoin | POST | `/api/v1/teocoin/withdrawals/admin/mint/` | ✅ | GATE/OFF | Admin/API | Admin | 410/501 + {"code":"feature_disabled"} | audit logs, admin calls | [EVID-admin-mint] |
| Discounts | POST | `/api/v1/rewards/discounts/preview/` | ✅ | KEEP | FE | Public/Auth* | 200 (simulate; returns DB-based preview when Web3 off) | p95, error-rate | [EVID-discounts-preview] |
| Discounts | POST | `/api/v1/rewards/discounts/confirm/` | ✅ | GATE/OFF | FE | Auth | 410/501 + {"code":"feature_disabled"} | count 410/501, confirm errors | [EVID-discounts-confirm] |
| Discounts | GET | `/api/v1/rewards/discounts/pending/` | ✅ | KEEP | FE Admin | Auth | 200 (DB-based list) | pending count, age histogram | [EVID-discounts-pending] |
| Services/Discounts | POST | `/api/v1/services/discount/calculate/` | ✅ | KEEP | FE / backend | Auth | 200 (DB fallback) | latency, errors | [EVID-services-discount-calc] |
| Staking | GET | `/api/v1/services/staking/info/` | ✅ | KEEP | FE | Auth | 200 | availability, errors | [EVID-staking-info] |
| Staking | POST | `/api/v1/services/staking/stake/` | ✅ | GATE/OFF | FE | Auth | 410/501 + {"code":"feature_disabled"} | stake ops metrics | [EVID-staking-stake] |
| Wallet Connect | POST | `/api/v1/users/me/wallet/link/` | ✅ | KEEP | FE | Auth | 200 / 400 | connection attempts, failures | [EVID-wallet-link] |
| Wallet Connect | DELETE | `/api/v1/users/me/wallet/` | ✅ | KEEP | FE | Auth | 200 | disconnects count | [EVID-wallet-unlink] |

Notes:

- This matrix focuses on Web3-related surfaces: rewards, teocoin, discounts, staking, withdrawals, wallet connect/disconnect and NFT minting.

- Tag guidance: `GATE/OFF` = requires feature-flag gating and an HTTP error body when Web3 functionality is disabled: e.g. 410 or 501 with JSON {"code":"feature_disabled","message":"Web3 features disabled"}.

- `KEEP` = keep operational (read-only or DB-backed fallback).

- `OBSERVE` = monitor usage and errors before deciding a gate.

- Source of truth: backend URL declarations under `lms_backend/api/*` and full OpenAPI in `lms_backend/openapi.json`.

Notes:

- Many endpoints live under `lms_backend/rewards/urls.py` (mint/burn/health/transactions).

- For Day1 we tag obvious wallet mint/burn as `GATE/OFF`. Any mixed endpoints should be `OBSERVE` and reviewed on Day2.
