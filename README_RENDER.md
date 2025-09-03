Deploying the Django backend to Render (quick guide)

1) Prepare the repo
   - Root: this folder (contains `manage.py`). Push to GitHub.

2) Create a Postgres database on Render (Free plan ok).

3) Create a new Web Service on Render
   - Environment: Python
   - Root directory: this repo root (where `manage.py` lives)
    - Build command:
       mkdir -p staticfiles && pip install -r requirements.txt && python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput
   - Start command:
     gunicorn schoolplatform.wsgi:application --workers=3 --threads=2 --timeout=120

4) Environment variables (Render → Environment)
   - DJANGO_SETTINGS_MODULE=schoolplatform.settings.prod
   - SECRET_KEY (generate a strong secret)
   - DATABASE_URL (connect from the Render DB created earlier)
   - ALLOWED_HOSTS=<your-backend>.onrender.com
   - CORS_ALLOWED_ORIGINS=https://<your-frontend>.onrender.com
   - CSRF_TRUSTED_ORIGINS=https://<your-frontend>.onrender.com,https://<your-backend>.onrender.com
   - STRIPE_SECRET_KEY (if using Stripe in prod)

5) Update frontend (Render Static Site) env
   - VITE_API_BASE_URL=https://<your-backend>.onrender.com

6) Smoke test
   - Visit https://<your-backend>.onrender.com/api/health/ (add a simple view if missing)
   - Visit https://<your-backend>.onrender.com/admin/ and confirm static CSS loads

Notes & troubleshooting
 - Whitenoise is already configured in `base.py` via storage and middleware.
 - If static files 404: ensure `STATIC_ROOT` exists and `collectstatic` ran during build.
 - For CSRF errors: confirm exact origins (including https://) are in `CSRF_TRUSTED_ORIGINS`.
