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

exec "$@"
