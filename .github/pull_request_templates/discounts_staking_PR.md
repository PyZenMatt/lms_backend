## Titolo
Feature: stabilizza discounts+staking — idempotent confirm, logs strutturati, seed idempotente, test DRF

## Breve riepilogo
Implementa l’idempotenza sicura per la conferma sconto (race-safe), standardizza i log di `discount_preview` e `discount_confirm`, aggiunge test DRF mirati e conferma che il seed per il tier Bronze è idempotente.

## Cosa include (changelog)
- Idempotent confirm flow per rewards/courses: `transaction.atomic()` + `get_or_create(order_id=...)`; `IntegrityError` catturato solo attorno a `get_or_create` e fallback a fetch + return 200.
- Log strutturati per `discount_preview`/`discount_confirm` con fields minimi: `event`, `order_id?`, `user_id`, `course_id`, `teacher_id`, `student_id`, `discount_percent`, `accept_teo`, `accept_ratio`, `tier_name`, `created?`, `snapshot_id?`.
- Migrazione `rewards/migrations/0006_...` (dedupe existing snapshots e UNIQUE on `order_id`) inclusa.
- Seed idempotente per Bronze (`rewards/management/commands/seed_staking_tiers.py` usa `update_or_create`).
- Test DRF aggiornati:
  - preview (200/422)
  - confirm: primo POST => 201, conferma ripetuta => 200
  - race: due POST paralleli => una 201 + una 200, nessun 500, 1 snapshot per `order_id`
- Allineamenti minori: `courses/views/payments.py` logging harmonized.

## Files principali toccati
- `backend/rewards/views/discount_views.py`
- `backend/courses/views/payments.py`
- `backend/courses/tests/test_payments_snapshot.py`
- `backend/rewards/management/commands/seed_staking_tiers.py`
- `backend/rewards/migrations/0006_add_unique_orderid.py`
- `backend/payments/models.py`
- `backend/schoolplatform/settings/ci.py`

## Why merge now
Feature-focused, testata localmente (dev/SQLite and CI-light with --nomigrations). Non introduce refactor DB rischiosi.

## Test plan (local / reviewer)
### Dev (sqlite)
```bash
export PYTHONPATH=$PWD/backend
export DJANGO_SETTINGS_MODULE=schoolplatform.settings.dev
python -m pytest backend/courses/tests/test_payments_snapshot.py -q --nomigrations
python -m pytest backend/rewards/tests/test_discount_views.py -q --nomigrations
# run seed
cd backend
python manage.py seed_staking_tiers
```

### Quick CI-like (Postgres) validation (no migrations)
```bash
export PYTHONPATH=$PWD
export DJANGO_SETTINGS_MODULE=schoolplatform.settings.ci
python -m pytest backend/courses/tests/test_payments_snapshot.py -q --nomigrations
```

## Definition of Done (DoD)
- [ ] Tutti i test DRF mirati passano in locale (dev settings) e in CI-light (`--nomigrations`).
- [ ] Logging formato coerente e leggibile dai sistemi di monitoring.
- [ ] Seed Bronze idempotente verificato.
- [ ] Migration `0006` inclusa in PR (codice + test per non introdurre regressioni).
- [ ] PR non cambia lo schema in modo che blocchi CI (schema cleanup separato).

## Rischi e note
- Migrazioni complete su Postgres bloccate da conflitti `related_name`/modelli duplicati — vedi Issue separata.

## Reviewer notes (quick checks)
- Controllare che `get_or_create()` sia coperto da transaction e che `IntegrityError` sia catturato solo nel blocco opportuno.
- Verificare che i log scrivano gli stessi campi minima richiesti.
- Eseguire i test DRF mirati localmente come indicato.

## Changelog breve per commit
- feat(rewards): idempotent confirm + structured logs
- test(courses): tighten snapshot confirm/race tests
- chore(rewards): seed staking bronze idempotent
- fix(settings): ensure CI imports base

