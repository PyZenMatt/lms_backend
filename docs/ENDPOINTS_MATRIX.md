# ENDPOINTS_MATRIX v1 — Web3 vs Web2 (Day 1 draft)
<!-- markdownlint-disable MD013 -->

| Dominio  | Metodo | Path                                 | Canonical | Tag      | Chi lo chiama | Auth   | Risposta Web3 OFF                          | Log & metriche              | Note                               |
|----------|--------|--------------------------------------|-----------|----------|---------------|--------|--------------------------------------------|-----------------------------|------------------------------------|
| Wallet   | POST   | `/api/v1/rewards/wallet/mint/`       | ✅        | GATE/OFF | FE/Worker     | Auth   | 410/501 + feature_disabled                 | count 410/501               | [EVID-rewards-mint] (@sha:NA/NA)   |
| Wallet   | POST   | `/api/v1/rewards/wallet/burn/`       | ✅        | GATE/OFF | FE            | Auth   | 410/501 + feature_disabled                 | count 410/501               | [EVID-rewards-burn] (@sha:NA/NA)   |
| Wallet   | GET    | `/api/v1/rewards/wallet/health/`     | ✅        | KEEP     | FE            | Auth   | 200 (ok) or 401 if not auth                | availability, auth failures | [EVID-rewards-health] (@sha:NA/NA) |
| Rewards  | POST   | `/api/v1/rewards/wallet/transactions/` | ✅      | KEEP     | FE            | Auth   | 200 / DB-only behavior                     | p95, errors                 | [EVID-rewards-transactions] (@sha:NA/NA) |
| NFT      | POST   | `/api/v1/nft/mint/`                  | ✅        | GATE/OFF | FE            | Auth   | 410/501 + {"code":"feature_disabled"}      | trace NFT services          | [EVID-nft-mint] (@sha:NA/NA)       |
| TeoCoin  | GET    | `/api/v1/teocoin/balance/`           | ✅        | KEEP     | FE            | Auth   | 200 + DB fallback when Web3 off            | request rate, p95, 401      | [EVID-teocoin-balance] (@sha:NA/NA) |
| TeoCoin  | GET    | `/api/v1/teocoin/transactions/`      | ✅        | KEEP     | FE            | Auth   | 200 (DB-only if Web3 off)                  | errors, latency             | [EVID-teocoin-transactions] (@sha:NA/NA) |
| TeoCoin  | POST   | `/api/v1/teocoin/withdraw/`          | ✅        | GATE/OFF | FE            | Auth   | 410/501 + {"code":"feature_disabled"}      | count 410/501               | [EVID-teocoin-withdraw] (@sha:NA/NA) |
| TeoCoin  | POST   | `/api/v1/teocoin/withdrawals/admin/process-pending/` | ✅ | GATE/OFF | Worker/Cron | Admin | 410/501 + {"code":"feature_disabled"}      | job run counts, errors      | [EVID-teocoin-process-pending] (@sha:NA/NA) |
| TeoCoin  | POST   | `/api/v1/teocoin/withdrawals/admin/mint/` | ✅     | GATE/OFF | Admin/API     | Admin | 410/501 + {"code":"feature_disabled"}      | audit logs, admin calls     | [EVID-admin-mint] (@sha:NA/NA)     |
| Discounts | POST  | `/api/v1/rewards/discounts/preview/` | ✅        | KEEP     | FE            | Public/Auth* | 200 (simulate; DB-based preview)         | p95, error-rate             | [EVID-discounts-preview] (@sha:NA/NA) |
| Discounts | POST  | `/api/v1/rewards/discounts/confirm/` | ✅        | GATE/OFF | FE            | Auth   | 410/501 + {"code":"feature_disabled"}      | count 410/501               | [EVID-discounts-confirm] (@sha:NA/NA) |
| Discounts | GET   | `/api/v1/rewards/discounts/pending/` | ✅        | KEEP     | FE Admin      | Auth   | 200 (DB-based list)                        | pending count, age histo    | [EVID-discounts-pending] (@sha:NA/NA) |
| Services/Discounts | POST | `/api/v1/services/discount/calculate/` | ✅ | KEEP | FE / backend | Auth | 200 (DB fallback)                           | latency, errors             | [EVID-services-discount-calc] (@sha:NA/NA) |
| Staking  | GET    | `/api/v1/services/staking/info/`     | ✅        | KEEP     | FE            | Auth   | 200                                        | availability, errors        | [EVID-staking-info] (@sha:NA/NA)   |
| Staking  | POST   | `/api/v1/services/staking/stake/`    | ✅        | GATE/OFF | FE            | Auth   | 410/501 + {"code":"feature_disabled"}      | stake ops metrics           | [EVID-staking-stake] (@sha:NA/NA)  |
| Wallet Connect | POST | `/api/v1/users/me/wallet/link/`  | ✅        | KEEP     | FE            | Auth   | 200 / 400                                  | connection attempts, fails  | [EVID-wallet-link] (@sha:NA/NA)    |
| Wallet Connect | DELETE | `/api/v1/users/me/wallet/`     | ✅        | KEEP     | FE            | Auth   | 200                                        | disconnects count           | [EVID-wallet-unlink] (@sha:NA/NA)  |

Notes:

- Matrix Web3 surfaces: rewards, teocoin, discounts, staking, withdrawals, wallet connect/disconnect, NFT mint.
- Tag: `GATE/OFF` = gated con 410/501 + `{"code":"feature_disabled"}`; `KEEP` = operativo (read-only/DB); `OBSERVE` = monitora.
- Source of truth: URL backend `lms_backend/api/*` e OpenAPI `lms_backend/openapi.json`.

See also:

- `../../docs/CONTRACTS.md` — API contracts and health guidance for frontend/ops.
- `FLAGS_MATRIX.md` — deployment flags and expectations (which envs are DB-first vs chain-enabled).
- `PLAYBOOK_WEB3_OFF.md` — operational steps when Web3 features are disabled.
