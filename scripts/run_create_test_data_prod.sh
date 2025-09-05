#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_create_test_data_prod.sh --yes-im-sure
# This script runs migrations and the create_test_data management command
# using the production Django settings. It requires an explicit --yes-im-sure
# argument to avoid accidental execution in production.

if [[ "${1:-}" != "--yes-im-sure" ]]; then
  cat <<EOF
This will run database migrations and the management command create_test_data
against the Django project using the production settings.

To proceed, re-run with the explicit confirmation flag:

  $0 --yes-im-sure

EOF
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Default to production settings unless DJANGO_SETTINGS_MODULE is already set
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-schoolplatform.settings.prod}"

echo "Using DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Running create_test_data..."
python manage.py create_test_data --settings="$DJANGO_SETTINGS_MODULE"

echo "Done: create_test_data finished."
