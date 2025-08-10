#!/usr/bin/env bash
set -euo pipefail

echo "Repo cleanup baseline — start"

# create dirs
mkdir -p backend infra/{deploy,reverse-proxy,platform,archive} scripts/repo backend/tests

# moves (safe, only if exists)
move_if() { [ -e "$1" ] && git mv "$1" "$2" && echo "moved: $1 -> $2" || true; }

move_if manage.py backend/manage.py
move_if schoolplatform backend/schoolplatform
move_if core backend/core
move_if blockchain backend/blockchain
move_if courses backend/courses
move_if users backend/users
move_if requirements.txt backend/requirements.txt
move_if runtime.txt backend/runtime.txt
move_if db.sqlite3 backend/db.sqlite3
move_if db.sqlite3.bak backend/db.sqlite3.bak

for f in test_*.py; do move_if "$f" "backend/tests/$f"; done
move_if exercise_test.py backend/tests/exercise_test.py

move_if Dockerfile infra/deploy/Dockerfile
move_if docker-compose.prod.yml infra/deploy/docker-compose.prod.yml
move_if nginx.conf infra/reverse-proxy/nginx.conf
move_if render.yaml infra/platform/render.yaml
move_if Procfile infra/platform/Procfile

touch infra/archive/.gitkeep

echo "Repo cleanup baseline — done"
