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


## Contratti API (OpenAPI → Tipi TypeScript)

Per allineare i contratti FE ↔ BE:

1. **Export OpenAPI**
	- Backend remoto:
	  ```bash
	  BACKEND_URL="https://schoolplatform.onrender.com" ./tools/fetch_openapi.sh
	  ```
	- Backend locale:
	  ```bash
	  ./tools/fetch_openapi.sh
	  ```

2. **Genera tipi TypeScript**
	- Da root o da frontend:
	  ```bash
	  npm run openapi:gen --prefix frontend
	  ```

3. **Importa i tipi**
	- Usa `import { ... } from 'src/lib/api/schema'` nel FE.

4. **Workflow CI**
	- Vedi `.github/workflows/openapi.yml` per generazione automatica su ogni PR.

No secrets sono committati; usa i template .env.example.
