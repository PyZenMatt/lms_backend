#!/bin/sh
set -eu

echo "Running migrations (retry finché DB è pronto)..."
# retry loop semplice: esce appena migrate va a buon fine
i=0
until python manage.py migrate; do
  i=$((i+1))
  echo "DB non pronto o migrazioni fallite (tentativo $i). Retry tra 3s..."
  sleep 3
done

echo "Collect static..."
python manage.py collectstatic --noinput || true

echo "Starting gunicorn..."
exec gunicorn schoolplatform.wsgi:application \
  -b 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
