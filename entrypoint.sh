#!/bin/sh
set -e

# Wait for Postgres
until pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-postgres}; do
  echo "Waiting for postgres..."
  sleep 2
done

echo "Postgres is up - running migrations"
python manage.py migrate --noinput

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Starting Gunicorn"
exec gunicorn schoolplatform.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-3} \
  --access-logfile - \
  --error-logfile -
