#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[entrypoint] $*"
}

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-pixelcast_signage_user}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"

wait_for_postgres() {
  local max_attempts=60
  local attempt=1

  export PGPASSWORD="${DB_PASSWORD:-}"
  log "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."
  until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres >/dev/null 2>&1; do
    if [ "${attempt}" -ge "${max_attempts}" ]; then
      log "PostgreSQL did not become ready in time; continuing startup."
      return 1
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  log "PostgreSQL is ready."
}

run_migrations() {
  if python manage.py migrate --noinput --fake-initial; then
    log "Migrations applied."
  else
    log "Fake-initial migrate failed, retrying normal migrate..."
    python manage.py migrate --noinput || log "Migrations failed; continuing."
  fi
}

collect_static() {
  python manage.py collectstatic --noinput --clear || python manage.py collectstatic --noinput || true
}

main() {
  log "Booting PixelCast backend..."

  wait_for_postgres || true

  if python /app/ensure_postgres_db.py; then
    log "Application database ready."
  else
    log "Could not ensure application database; continuing."
  fi

  run_migrations
  python manage.py migrate core --noinput || true
  python manage.py seed_tv_catalog || true

  # docker-compose.yml sets BOOTSTRAP_DEFAULT_ADMIN=true — creates admin@pixelcast.com / adminadmin if missing.
  if [ "${BOOTSTRAP_DEFAULT_ADMIN:-false}" = "true" ]; then
    log "BOOTSTRAP_DEFAULT_ADMIN=true — ensuring default Developer account..."
    python manage.py ensure_default_developer || log "ensure_default_developer failed (non-fatal)."
  fi

  collect_static

  if [ "${ENABLE_HOT_RELOAD:-false}" = "true" ]; then
    log "Starting uvicorn with reload..."
    exec uvicorn Screengram.asgi:application --host 0.0.0.0 --port 8000 --reload --reload-dir /app
  fi

  log "Starting gunicorn..."
  exec gunicorn Screengram.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --keep-alive "${GUNICORN_KEEPALIVE:-5}" \
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-50}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${GUNICORN_LOG_LEVEL:-info}" \
    --preload
}

main "$@"
