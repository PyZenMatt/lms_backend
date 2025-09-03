#!/usr/bin/env bash
set -euo pipefail

# Ensure runtime directories exist (prevents logging FileNotFoundError in prod)
APP_DIR="${APP_DIR:-/app}"
LOG_DIR="$APP_DIR/logs"
echo "Ensuring log directory exists: $LOG_DIR"
mkdir -p "$LOG_DIR"
chmod 0755 "$LOG_DIR" || true

echo "Running migrations (if DB ready)..."
# Run migrations but do not fail the container startup if DB not ready
if ! python manage.py migrate --noinput; then
	echo "Migrations failed or DB not ready; continuing"
fi

# If no command supplied, default to starting gunicorn on $PORT (with fallback)
if [ "$#" -eq 0 ]; then
	echo "No command supplied; starting gunicorn on 0.0.0.0:${PORT:-8000}"
	exec bash -lc "gunicorn schoolplatform.wsgi:application --workers=3 --threads=2 --timeout=120 -b 0.0.0.0:${PORT:-8000}"
fi

# Execute provided command via bash -lc so shell-style env/parameter expansion works
cmd="$*"
exec bash -lc "$cmd"
