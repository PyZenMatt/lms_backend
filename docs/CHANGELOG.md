# Changelog

## 2025-09-15 — T-003 Web3 OFF gate

- Implemented a docs-first Web3 write gate that returns HTTP 410 for TeoCoin write endpoints when `TEOCOIN_SYSTEM` is configured for DB-only.
- Files: `core/decorators/web3_gate.py`, `scripts/t003g_coverage.py`, `scripts/t003g_hints.py`, `scripts/t003h_probe.sh`.
- Tests: no-DB unit tests for gate behavior (`core/tests/test_web3_gate_*`).
- Evidence: `docs/T-003-GATE-COVERAGE.txt`, `docs/EVIDENCE_LOG.md` (probe/runtime evidence to be appended separately).
