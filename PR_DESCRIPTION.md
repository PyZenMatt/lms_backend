PR: Enforce TeoCoin confirm and add integration test

What
- Ensure `confirm_discount` enforces token availability and returns HTTP 400 with `{"error": "INSUFFICIENT_TOKENS"}` when the user balance is insufficient.
- Add `rewards/tests/test_confirm_insufficient_balance.py` integration test to prevent regressions.

Why
- Prevent users from applying discounts or paying via Stripe when they lack the required TeoCoin tokens.

Notes for reviewer
- The backend is authoritative; frontend guard changes are also present in the frontend repo and should be deployed together if you control both sides.
- The test is an integration-style test and may initialize TeoCoin services that log or make RPC calls. Consider mocking `db_teocoin_service` in CI to avoid flakiness.

How to verify locally
- From repo root:

```bash
cd lms_backend
DJANGO_SETTINGS_MODULE=schoolplatform.settings.dev pytest -q rewards/tests/test_confirm_insufficient_balance.py::TestConfirmInsufficientBalance::test_confirm_rejects_on_insufficient_balance -q -s
```

Expected: test passes and logs an attempt where confirm returns 400 `INSUFFICIENT_TOKENS`.

Backport: If you need this fix on a maintenance branch, cherry-pick the enforcement commit and the test.
