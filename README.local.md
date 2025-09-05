Local production-like setup (Docker Compose)

1) Add to /etc/hosts (requires sudo):

   127.0.0.1  schoolplatform.local
   127.0.0.1  api.schoolplatform.local

2) Build & start minimal services:

   docker compose up -d db
   sleep 3
   docker compose up --build backend frontend

3) Create superuser if needed:

   docker compose exec backend python manage.py createsuperuser

4) Basic checks (from host):

   # CORS preflight
   curl -i https://api.schoolplatform.local:8000/api/v1/token/ \
     -H "Origin: https://schoolplatform.local" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: content-type, authorization"

   # Login (POST JSON) and profile GET using returned token

Notes:
- Backend reads `backend/.env` and uses `schoolplatform.settings.prod` to emulate production (WhiteNoise + gunicorn).
- If you want local TLS for the domains, consider `mkcert` + a small nginx reverse-proxy.
