# Issue-04 — Webhook ⇒ SETTLE idempotente (Stripe)

Status: proposal / ready for implementation

Goal
----
When a Stripe webhook event indicates a successful payment (e.g. `payment_intent.succeeded` or `checkout.session.completed`), capture (SETTLE) a previously-created HOLD for an applied discount snapshot. This must be idempotent so replayed webhooks do not duplicate ledger mutations.

Requirements
------------
- Webhook handler must accept Stripe events and map them to a `PaymentDiscountSnapshot` in status `pending` (lookup by `order_id` == `checkout_session_id`, fallback to payment_intent metadata if available).
- Use a `PaymentEvents` (or similar) record keyed by provider event id (`stripe:evt_...`) to guard idempotent processing.
- On first processing of a matching event: call wallet settle (capture) → update ledger and set snapshot.status=`confirmed` and record `external_txn_id`.
- On replay (same provider_event_id): no-op, return 200.
- Unknown events (no mapped snapshot): return 200 no-op.

Acceptance criteria (DoD)
------------------------
- Webhook endpoint implemented and wired (e.g. `/api/v1/payments/stripe/webhook/`).
- Replay-safe via provider event id persistence.
- Unit/integration tests:
  - `test_webhook_settle_happy_path` — pending snapshot moved to confirmed and ledger shows deduction only once.
  - `test_webhook_replay_idempotent` — duplicate event does not change ledger/snapshot twice.
  - `test_webhook_unknown_order_noop` — event with no matching snapshot returns 200 and no changes.
- At most 3 files changed (view/service/tests), ~120 LOC.

Dev commands (local)
--------------------
Run unit/integration tests (Postgres recommended):

```bash
cd lms_backend
pytest -q rewards/tests/test_webhook_settle.py -q
```

Manual testing with stripe-cli:

```bash
stripe listen --forward-to http://127.0.0.1:8000/api/v1/payments/stripe/webhook/ \
  -e payment_intent.succeeded -e checkout.session.completed
```

Notes
-----
- Idempotency: primary guard is persisting `provider_event_id` on the first processing and checking it on subsequent attempts.
- Correlation: snapshots should store `order_id` (checkout session id) and optionally payment intent id in metadata to enable lookups.
- Security: if webhook signature verification is enabled, test environment may need to bypass/disable signature checking or use stripe-cli with the signing secret.

Implementation hints
--------------------
- Create `rewards/services/webhook_settle_service.py` with a `process_stripe_event(event)` function that encapsulates lookup, idempotency check, settle, and snapshot update.
- Create `rewards/views/webhook.py` with a small Django view that verifies signature (configurable) and calls service.
- Keep the handler idempotent and fast; side effects must be persisted within a DB transaction.
