| Ambiente | Intento (DB-first vs chain) | Variabile reale | Valori attesi | Fonte (settings/env) | Note |
|----------|------------------------------|-----------------|---------------|----------------------|------|
| DEV      | DB-first baseline            | `USE_DB_TEOCOIN_SYSTEM` / `TEOCOIN_SYSTEM` | `True` / `database` | `apps/settings` README, `docs/wallet-modes.md` | default local/dev behaviour |
| STAGING  | Web3 OFF (DB-first)         | `USE_DB_TEOCOIN_SYSTEM` / `TEOCOIN_SYSTEM` | `True` / `database` (or explicit off) | env / deploy settings | expect wallet on-chain features disabled |
| PROD     | Web3 OFF (DB-first)         | `USE_DB_TEOCOIN_SYSTEM` / `TEOCOIN_SYSTEM` | `True` / `database` | deploy env / secrets | prefer DB-first, on-chain sync async if used |

Health: platform root health is `/api/v1/health/` (see `lms_backend/core/health_check.py`).
Wallet-specific health endpoint exists at `/api/v1/rewards/wallet/health/` (requires auth) and currently returns `{"ok": true}` when reachable (see `lms_backend/rewards/views/wallet_views.py`).

Variabili addizionali identificate nel repo:

- `TEOCOIN_SYSTEM` — values: `database` | `blockchain` (docs/wallet-modes.md)
- `USE_DB_TEOCOIN_SYSTEM` — boolean alias (apps/settings README, apps/wallet)
- `WALLET_CHAIN_RPC` — RPC URL when onchain enabled
- `ADMIN_PUBLIC_KEY`, `ADMIN_PRIVATE_KEY`, `PLATFORM_WALLET_ADDRESS` — on-chain creds (secrets)

Criteri di scelta/Note:
- Use `TEOCOIN_SYSTEM` as canonical semantic flag; `USE_DB_TEOCOIN_SYSTEM` is an alias used in docs and README.
- `/api/v1/rewards/wallet/health/` is authenticated; for Day-1 evidence we will capture repo references and curl to platform health (`/api/v1/health/`) and list wallet URLs.
