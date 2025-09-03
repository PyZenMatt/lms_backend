#!/usr/bin/env bash
set -e

# Run migrations then exec passed CMD
echo "Running migrations (if DB ready)..."
python manage.py migrate --noinput || echo "Migrations failed or DB not ready; continuing"

exec "$@"
