#!/bin/bash
set -e  # Exit on error (but we catch critical sections with || true)
set -x  # Debug mode: print every command for troubleshooting

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for PostgreSQL with timeout and retries
wait_for_postgres() {
    local max_attempts=60  # Increased for better reliability
    local attempt=1
    local wait_interval=2
    
    log_info "Waiting for PostgreSQL to be ready..."
    log_info "Host: ${DB_HOST:-db}, Port: ${DB_PORT:-5432}, User: ${DB_USER:-pixelcast_signage_user}"
    # libpq defaults the DB name to the username if -d is omitted — that DB may not exist. Use maintenance DB `postgres`.
    export PGPASSWORD="${DB_PASSWORD:-}"
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-pixelcast_signage_user}" -d postgres > /dev/null 2>&1; then
            log_success "PostgreSQL is ready!"
            return 0
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            log_warning "Attempt $attempt/$max_attempts: PostgreSQL is not ready yet. Still waiting..."
        fi
        sleep $wait_interval
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL is not ready after $max_attempts attempts (${max_attempts}s)."
    log_warning "The application will continue to start, but database operations may fail."
    log_warning "This is intentional to allow the container to start even if the database is temporarily unavailable."
    return 1
}

# Function to check if database connection is actually working
check_db_connection() {
    log_info "Verifying database connection..."
    python << EOF
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Screengram.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result:
            print("Database connection verified successfully")
            sys.exit(0)
        else:
            print("Database connection failed: No result")
            sys.exit(1)
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)
EOF
}

# Function to run migrations with error handling
run_migrations() {
    log_info "Running database migrations..."
    
    if ! check_db_connection; then
        log_warning "Database connection check failed. Skipping migrations."
        return 1
    fi
    
    # Run migrations with fake-initial to handle existing tables
    if python manage.py migrate --noinput --fake-initial; then
        log_success "Database migrations completed successfully"
        return 0
    else
        log_error "Migrations failed. Attempting to continue..."
        # Try to run migrations without fake-initial as fallback
        if python manage.py migrate --noinput; then
            log_success "Migrations completed (fallback method)"
            return 0
        else
            log_error "Migrations failed completely. The application may not work correctly."
            return 1
        fi
    fi
}

# Function to collect static files
collect_static() {
    log_info "Collecting static files..."
    
    if python manage.py collectstatic --noinput --clear; then
        log_success "Static files collected successfully"
        return 0
    else
        log_warning "Static file collection had issues, but continuing..."
        # Try without --clear flag as fallback
        if python manage.py collectstatic --noinput; then
            log_success "Static files collected (fallback method)"
            return 0
        else
            log_warning "Static file collection failed. Some assets may not be available."
            return 1
        fi
    fi
}

# Get installation lock path (must match Django settings INSTALLATION_STATE_DIR)
INSTALLATION_STATE_DIR="${INSTALLATION_STATE_DIR:-/app/installation_state}"
INSTALLED_LOCK_PATH="${INSTALLATION_STATE_DIR}/installed.lock"

# Ensure installation state directory exists with proper permissions
ensure_installation_state_dir() {
    log_info "Ensuring installation state directory exists: $INSTALLATION_STATE_DIR"
    
    # Create directory if it doesn't exist
    mkdir -p "$INSTALLATION_STATE_DIR" || {
        log_error "Failed to create $INSTALLATION_STATE_DIR"
        return 1
    }
    
    # Set permissions (777 for Docker volume compatibility - app creates lock file)
    chmod 777 "$INSTALLATION_STATE_DIR" 2>/dev/null || {
        log_warning "Could not chmod 777 $INSTALLATION_STATE_DIR (may be OK if already writable)"
    }
    
    # Verify directory is writable
    if [ -w "$INSTALLATION_STATE_DIR" ]; then
        log_success "Installation state directory is writable"
        return 0
    else
        log_error "Installation state directory is NOT writable: $INSTALLATION_STATE_DIR"
        log_error "Check Docker volume permissions"
        return 1
    fi
}

# Function to verify installation lock file
check_installation() {
    if [ -f "$INSTALLED_LOCK_PATH" ]; then
        log_info "Installation lock file found. Application is installed."
        return 0
    else
        log_warning "Installation lock file not found. Installation wizard will be required."
        log_info "Lock path: $INSTALLED_LOCK_PATH"
        return 1
    fi
}

# Main execution
main() {
    log_info "=========================================="
    log_info "PixelCast Signage Backend Container Starting..."
    log_info "=========================================="
    log_info "Container: $(hostname)"
    log_info "User: $(whoami)"
    log_info "Python: $(python --version)"
    
    # 0. Ensure installation state directory exists with proper permissions
    ensure_installation_state_dir || {
        log_error "CRITICAL: Cannot create/access installation state directory"
        log_error "The installation wizard will not be able to create the lock file"
        log_warning "Continuing anyway - app will start but installation may fail"
    }

    # Client distribution policy: always show setup wizard after container rebuild/restart.
    _dm=$(echo "${DEPLOYMENT_MODE:-}" | tr '[:upper:]' '[:lower:]')
    if [ "$_dm" = "client" ]; then
        [ -f "$INSTALLED_LOCK_PATH" ] && rm -f "$INSTALLED_LOCK_PATH" && log_info "Client mode: removed $INSTALLED_LOCK_PATH"
        [ -f "/app/installed.lock" ] && rm -f "/app/installed.lock" && log_info "Client mode: removed /app/installed.lock"
    fi
    
    # 1. Wait for PostgreSQL FIRST (required before migrations/installation)
    if wait_for_postgres; then
        log_success "PostgreSQL is ready"

        # Create DB_NAME if missing (e.g. Postgres data volume initialized with another name, or DB_NAME changed later).
        log_info "Ensuring application database exists..."
        if python /app/ensure_postgres_db.py; then
            log_success "PostgreSQL application database is ready"
        else
            log_warning "Could not ensure application database exists — migrations may fail (check DB_* in .env)."
        fi
        
        # Run migrations (only if database is available)
        run_migrations || log_warning "Migrations skipped or failed, but continuing..."

        # Ensure core app migrations apply (TV catalog tables); helps if a partial migrate state left gaps
        log_info "Applying core app migrations explicitly..."
        if python manage.py migrate core --noinput; then
            log_success "Core migrations OK"
        else
            log_warning "Explicit core migrate failed (check logs)."
        fi

        # Idempotent seed so Data Center has rows after fresh migrate
        log_info "Seeding TV catalog (safe to repeat)..."
        if python manage.py seed_tv_catalog; then
            log_success "TV catalog seed completed"
        else
            log_warning "TV catalog seed failed or skipped (tables may be missing)."
        fi

        # Optional: create default Developer (admin@pixelcast.com) if no user with that email exists.
        # Does not reset passwords on existing accounts. For password reset: ensure_default_developer --update
        if [ "${BOOTSTRAP_DEFAULT_ADMIN:-false}" = "true" ]; then
            log_info "BOOTSTRAP_DEFAULT_ADMIN=true: ensure_default_developer (create-if-missing)..."
            if python manage.py ensure_default_developer; then
                log_success "Default Developer bootstrap OK (or user already existed)"
            else
                log_warning "ensure_default_developer failed (non-fatal)."
            fi
        fi
    else
        log_warning "PostgreSQL is not available. Skipping database operations."
        log_warning "The container will start, but database features will not work."
    fi
    
    # 2. Check installation status (informational only - NEVER exit; app must stay alive for wizard)
    check_installation || true
    
    # 3. Collect static files (always run, doesn't require database)
    collect_static || log_warning "Static file collection had issues, but continuing..."
    
    # 3b. Optional mother platform registration (idempotent; does not fail boot)
    _mse=$(echo "${MOTHER_SYNC_ENABLED:-}" | tr '[:upper:]' '[:lower:]')
    if [ "$_mse" = "true" ] || [ "$_mse" = "1" ] || [ "$_mse" = "yes" ]; then
        if [ -n "${PURCHASE_CODE:-}" ]; then
            log_info "Mother sync: attempting one-shot registration if credentials are not stored yet..."
            python manage.py mother_register || log_warning "mother_register exited with an error (non-fatal)."
        fi
    fi
    
    # 4. Start Gunicorn with Uvicorn workers for ASGI support
    log_info "=========================================="
    log_info "Starting Gunicorn server..."
    log_info "=========================================="
    
    # Disable set -x for cleaner Gunicorn output
    set +x
    
    if [ "${ENABLE_HOT_RELOAD:-false}" = "true" ]; then
        log_info "Hot reload enabled: starting Uvicorn with ASGI (WebSockets + /ws/dashboard/)"
        exec uvicorn Screengram.asgi:application \
            --host 0.0.0.0 \
            --port 8000 \
            --reload \
            --reload-dir /app
    fi

    exec gunicorn Screengram.asgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --keep-alive ${GUNICORN_KEEPALIVE:-5} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-50} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${GUNICORN_LOG_LEVEL:-info} \
        --preload
}

# Run main function
main "$@"
