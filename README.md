# SchoolPlatform — Repo Baseline

This repository is structured as:

- backend/ — Django backend
- frontend/ — React frontend
- infra/ — deployment and ops (Docker, reverse proxy, PaaS files)
- docs/ — documentation

Policies:

- [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [SECURITY.md](./SECURITY.md)
- [CODEOWNERS](./CODEOWNERS)
- [LICENSE](./LICENSE)

Environment:

- backend/.env.example
- frontend/.env.example

Local development:

- Backend: python backend/manage.py runserver
- Frontend: cd frontend && npm start

No secrets are committed; use the provided .env.example templates.
