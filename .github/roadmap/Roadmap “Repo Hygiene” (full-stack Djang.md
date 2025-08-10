Roadmap “Repo Hygiene” (full-stack Django + React)

Fase 0 — Freeze & mappa (oggi)

    Crea tag/branch pre-cleanup.

    Esporta lista cartelle/file “sospetti” (scripts vecchi, configs doppi, test obsoleti).

    Elenca workflow CI esistenti (se rotti, li disabilitiamo temporaneamente).

Fase 1 — Struttura & standard

    Struttura cartelle chiara:

    backend/      # Django
    frontend/     # React
    infra/        # docker, deploy, IaC
    docs/         # documentazione utente/dev
    .github/      # issue templates, workflows, instructions

    File base: CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md, CODEOWNERS, LICENSE.

    Unifica .env.example per backend e frontend.

Fase 2 — Documentazione

    README.md root (overview, architettura, comandi base).

    backend/README.md (setup, migrazioni, test, lint).

    frontend/README.md (setup, build, test, lint).

    docs/ con 4 pagine minime: Architecture, Environments, API, Release process.

Fase 3 — Test rehab (prima backend, poi frontend)

    Backend: migrazione a pytest + pytest-django (se non già), coverage, fixture pulite, marking (slow, integration, quarantine).

    Frontend: Vitest + Testing Library, separa unit/integration, Playwright E2E per 2 flow reali.

    Quarantena test rotti: non li cancelli, li marchi e li togli dal bloccare la CI finché non sono sistemati.

Fase 4 — CI/CD

    2 workflow distinti: backend-ci.yml e frontend-ci.yml (lint, typecheck, test, build).

    Artifacts: report coverage, HTML test reports, upload.

Fase 5 — Copilot & qualità continua

    .github/copilot-instructions.md (stack, regole, struttura).

    Issue templates (bug/feature/chore/refactor).

    Regole Conventional Commits + Husky/lint-staged.