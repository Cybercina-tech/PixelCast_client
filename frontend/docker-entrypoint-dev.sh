#!/bin/sh
# Sync container node_modules with package-lock.json. The compose file uses a
# named volume for /app/node_modules so it survives rebuilds; without this,
# adding packages on the host leaves the volume stale and Vite cannot resolve
# new imports (e.g. @fontsource/*).
set -e
cd /app

LOCK_FILE=package-lock.json
PKG_FILE=package.json
STAMP_FILE=node_modules/.install-stamp

if [ ! -f "$LOCK_FILE" ]; then
  echo "docker-entrypoint-dev: $LOCK_FILE not found" >&2
  exit 1
fi
if [ ! -f "$PKG_FILE" ]; then
  echo "docker-entrypoint-dev: $PKG_FILE not found" >&2
  exit 1
fi

# Hash both package.json and lockfile so adding a dependency (or changing either file) always triggers npm ci.
# Busybox (Alpine) provides sha256sum
DEPS_HASH=$(cat "$PKG_FILE" "$LOCK_FILE" | sha256sum | awk '{print $1}')

if [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE" 2>/dev/null)" != "$DEPS_HASH" ]; then
  echo "docker-entrypoint-dev: installing dependencies (package.json or lockfile new or changed)..."
  npm ci
  mkdir -p node_modules
  printf '%s\n' "$DEPS_HASH" > "$STAMP_FILE"
fi

exec "$@"
