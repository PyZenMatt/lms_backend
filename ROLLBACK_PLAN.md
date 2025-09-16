# Rollback Plan — lms_backend

## T-003 — Web3 write gate (decorator-only rollback)

- Symptom: endpoints marked as GATE/OFF return HTTP 410 when `TEOCOIN_SYSTEM="database"`.
- Goal: rollback in minimal, low-risk way that does not touch DB migrations or FE code.

Rollback steps (minimal)

1. Checkout the branch containing the gate changes (or create a short-lived patch):

   ```bash
   git switch epic/web3-off
   # or edit files directly on main if emergency rollback required
   ```

2. Remove only the decorator lines from the annotated views:

   - For FBV: remove the `@require_web3_enabled` line immediately above the view def.
   - For CBV: remove `@method_decorator(require_web3_enabled, name='post')` or the decorator applied to `dispatch`.

3. Commit the minimal change and push:

   ```bash
   git add <changed_files>
   git commit -m "revert: remove web3 gate decorators (rollback T-003)"
   git push origin <branch>
   ```

4. Deploy and sanity-check:

   - Curl the previously gated endpoints; expect non-410 responses.
   - Keep KEEP endpoints unaffected.

Notes

- This rollback targets behavior only and is safe because it does not alter models or DB schema.
- Record the rollback incident in the change log and link the PR that performed the rollback.
