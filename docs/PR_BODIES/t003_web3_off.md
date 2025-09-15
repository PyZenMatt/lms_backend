Scopo
- Disattiva in sicurezza le vie Web3 di scrittura (410) quando `TEOCOIN_SYSTEM="database"`.
- Mantiene operative le vie KEEP (health/letture/transactions).
- Nessuna migrazione DB, nessun cambio FE/SEO.

Cosa include
- Gate su vie GATE/OFF (FBV/CBV con method_decorator/dispatch).
- Coverage T-003.G: OK/OK_COMPOSED per tutte le GATE/OFF; KEEP→SKIP; N/A→NO_ACTION.
- Test no-DB: `discounts/confirm` (410 OFF, non-410 ON).
- Evidenze aggiornate: grep, py_compile, pytest, coverage finale.

Definition of Done
- `py_compile` OK sugli script.
- `pytest -q lms_backend/core/tests/test_web3_gate*` PASS.
- `docs/ENDPOINTS_MATRIX.md` coerente con T-003.*.
- Diff piccolo, build verde, nessuna migrazione DB.

Rollback
- Rimuovere soltanto le righe di decorator nelle view annotate (FBV) o l’annotazione `@method_decorator/...` (CBV). Vedi `ROLLBACK_PLAN.md`.

Note
- Vie composte (mint/burn/withdraw/admin/*) classificate come OK_COMPOSED via hint-map (urls/namespace).

--
Auto-generated: T-003 epic PR body template
