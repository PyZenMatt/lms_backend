Deployment checklist — ensure confirm_discount enforcement

Purpose
- Ensure production backend includes the `confirm_discount` enforcement that returns 400 `INSUFFICIENT_TOKENS` when a student lacks TEO tokens, and that the frontend static build contains the Teo UI guard (no fallback to proceed to Stripe).

Quick checklist
1) Verify backend code includes enforcement
   - Confirm `lms_backend/rewards/views/discount_views.py` contains the balance check and `db_teocoin_service.deduct_balance(...)` call before returning success.

2) Run tests locally (fast smoke)
   - From repo root:

```bash
cd lms_backend
DJANGO_SETTINGS_MODULE=schoolplatform.settings.dev pytest -q rewards/tests/test_confirm_insufficient_balance.py
```

Expected: test passes and returns a dot.

3) Build & deploy backend
   - Ensure required env (DJANGO_SETTINGS_MODULE, DATABASE_URL, SECRET_KEY, etc.) are set in your deployment environment.
   - Run migrations, collectstatic, restart app server.

Example (Render / Docker hosts):
- Render: push commit and redeploy `lms-api` service. `render.yaml` already sets `VITE_API_BASE_URL` for the static site.
- Docker Compose (local parity):

```bash
# from repo root
docker compose up --build backend
# or inside backend container:
python manage.py migrate
python manage.py collectstatic --noinput
```

4) Rebuild & publish frontend static
   - Ensure `VITE_API_BASE_URL` points to the intended backend origin (example: `https://schoolplatform.onrender.com` in Render env).
   - Build and redeploy the static site:

```bash
cd lms-frontend
# ensure env: VITE_API_BASE_URL=https://your-backend.example
npm ci
npm run build
# deploy contents of dist/ to your static host
```

5) Smoke verification (browser)
   - Open the app in the browser where the issue was reported.
   - In DevTools Console run:

```js
// Shows the API base the SPA will use at runtime
window.__api_base__
```

   - Call preview/confirm manually (in console) to verify server enforces token check:

```js
// preview
fetch(`${window.__api_base__}/v1/rewards/discounts/preview/`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ price_eur: 50.0, discount_percent: 10 })
}).then(r=>r.json()).then(console.log)

// confirm
fetch(`${window.__api_base__}/v1/rewards/discounts/confirm/`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ order_id: `smoke_${Date.now()}`, price_eur: 50.0, discount_percent: 10 })
}).then(r=>r.json().then(b=>console.log(r.status,b))).catch(console.error)
```

Expected: If the logged-in user has insufficient balance, confirm returns HTTP 400 and body { error: "INSUFFICIENT_TOKENS" }.

6) Rollback plan
   - If regressions occur, roll back to the previous backend release and revert the static site to the prior build.

Notes
- The backend is authoritative: even if the frontend UI were modified, the backend confirm must always reject insufficient balances.
- CI: add `rewards/tests/test_confirm_insufficient_balance.py` to the test matrix so regressions fail early.

Contact
- If you want, I can prepare the PR (branch + commit message) and a short PR description ready for you to push and open.
