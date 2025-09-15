# T-003 Reviewer checklist

- [ ] `python3 -m py_compile scripts/t003g_*.py` OK
- [ ] `PYTHONPATH=./ lms_backend pytest -q lms_backend/core/tests/test_web3_gate*` PASS
- [ ] Coverage T-003.G: only `OK / OK_COMPOSED / SKIP / NO_ACTION` statuses
- [ ] `docs/ENDPOINTS_MATRIX.md` coherent (NFT mint = `NO_ACTION (N/A)`)
- [ ] No DB migrations, no FE/SEO changes
- [ ] Evidence T-003.H included (runtime probe output, expected 410 for GATE/OFF)
- [ ] Rollback plan present: `lms_backend/ROLLBACK_PLAN.md` T-003 section (decorator-only)

Notes:

- The PR is intentionally small and decorator-only; the probe script and coverage checks are included as docs/evidence tools.
