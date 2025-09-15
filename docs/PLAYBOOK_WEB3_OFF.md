## PLAYBOOK — Appendice mappatura flag/health (Day 1)

DB-first vs blockchain → nome variabile reale: `TEOCOIN_SYSTEM` (alias `USE_DB_TEOCOIN_SYSTEM`)

Sotto-flag rilevati (candidati):
- `WALLET_CHAIN_RPC` — RPC URL per provider on-chain
- `ADMIN_PUBLIC_KEY`, `ADMIN_PRIVATE_KEY`, `PLATFORM_WALLET_ADDRESS` — credenziali per firma/transazioni
- `TEOCOIN_EUR_RATE` — test/dev rate override

Health key/endpoint rilevato:
- Platform health: `/api/v1/health/` (una vista aggregata: `lms_backend/core/health_check.py`).
- Wallet health (auth): `/api/v1/rewards/wallet/health/` (returns `{"ok": true}` when reachable).

Note operativo Day1:
- Per Day 1 non modifichiamo codice di runtime; appendici compilate qui sotto servono come riferimento per Day2.
- Se flag non univoci: proponiamo `TEOCOIN_SYSTEM` come canonical; se deploys use `USE_DB_TEOCOIN_SYSTEM` alias we map it during Day2.
