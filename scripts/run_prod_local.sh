#!/usr/bin/env bash
# Helper to run the Django backend in production-like mode locally.
# Usage: ./scripts/run_prod_local.sh [start|migrate|collectstatic|check]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export ENVIRONMENT=${ENVIRONMENT:-production}
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-schoolplatform.settings.prod}

case "${1:-start}" in
  check)
    echo "Running 'python manage.py check --deploy' with DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
    python manage.py check --deploy
    ;;
  collectstatic)
    echo "Collecting static files to $ROOT_DIR/staticfiles (clearing first)"
    python manage.py collectstatic --noinput --clear
    ;;
  migrate)
    echo "Applying migrations"
    python manage.py migrate --noinput
    ;;
  start)
    # Start sequence: collectstatic, migrate, then gunicorn bound to localhost:8000
    echo "Starting production-like server on 127.0.0.1:8000"
    python manage.py collectstatic --noinput --clear
    python manage.py migrate --noinput
    exec gunicorn schoolplatform.wsgi:application --workers=3 --threads=2 --timeout=120 -b 127.0.0.1:8000
    ;;
  *)
    echo "Unknown command: ${1:-start}"
    echo "Usage: $0 [start|migrate|collectstatic|check]"
    exit 2
    ;;
esac
