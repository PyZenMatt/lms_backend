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
	default_cmd="gunicorn schoolplatform.wsgi:application --workers=3 --threads=2 --timeout=120 -b 0.0.0.0:${PORT:-8000}"
	echo "No command supplied; starting gunicorn on 0.0.0.0:${PORT:-8000}"
	echo "ENTRYPOINT: default_cmd=\"$default_cmd\""
	echo "ENTRYPOINT: PORT=\"${PORT:-}\""
	# Expand any shell-style parameter expansions (eg. ${PORT:-8000}) so the final
	# command passed to exec contains the actual port value when Render wraps
	# the Start Command (it may pass a '/bin/sh -c ...' payload). Use bash -lc
	# "echo ..." to perform expansion safely here and log the expanded command.
	expanded_default_cmd=$(bash -lc "echo $default_cmd")
	echo "ENTRYPOINT: expanded default_cmd=\"$expanded_default_cmd\""
	# Normalize: strip surrounding single/double quotes if any
	expanded_default_cmd=${expanded_default_cmd%"}
	expanded_default_cmd=${expanded_default_cmd#"}
	expanded_default_cmd=${expanded_default_cmd%\'}
	expanded_default_cmd=${expanded_default_cmd#\'}
	# If the command is wrapped like: /bin/sh -c <inner>, extract <inner>
	if [[ "$expanded_default_cmd" == /bin/sh\ -c* ]]; then
		# remove leading '/bin/sh -c ' prefix
		expanded_default_cmd=${expanded_default_cmd#/bin/sh -c }
	fi
	echo "ENTRYPOINT: normalized default_cmd=\"$expanded_default_cmd\""
	exec bash -lc "$expanded_default_cmd"
fi

# Execute provided command via bash -lc so shell-style env/parameter expansion works
cmd="$*"
echo "ENTRYPOINT: executing provided cmd: \"$cmd\""
echo "ENTRYPOINT: PORT=\"${PORT:-}\""
# Expand provided cmd to resolve any ${PORT} or other shell expansions that may
# have been left literal by the caller (Render sometimes wraps the command).
expanded_cmd=$(bash -lc "echo $cmd")
echo "ENTRYPOINT: expanded provided cmd: \"$expanded_cmd\""
# Normalize: strip surrounding quotes
expanded_cmd=${expanded_cmd%"}
expanded_cmd=${expanded_cmd#"}
expanded_cmd=${expanded_cmd%\'}
expanded_cmd=${expanded_cmd#\'}
# If wrapped as '/bin/sh -c <inner>', remove the wrapper so we exec <inner> directly
if [[ "$expanded_cmd" == /bin/sh\ -c* ]]; then
	expanded_cmd=${expanded_cmd#/bin/sh -c }
fi
echo "ENTRYPOINT: normalized provided cmd: \"$expanded_cmd\""
exec bash -lc "$expanded_cmd"
