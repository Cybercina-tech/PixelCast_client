#!/usr/bin/env bash
set -euo pipefail

# Build a cPanel-ready release bundle with prebuilt frontend assets and collected static files.
# Usage:
#   ./build-cpanel-release.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_DIR="${ROOT_DIR}/app"
RELEASE_DIR="${ROOT_DIR}/release"
PACKAGE_DIR="${RELEASE_DIR}/main"

echo "[1/6] Cleaning previous release artifacts"
rm -rf "${RELEASE_DIR}"
mkdir -p "${PACKAGE_DIR}"

echo "[2/6] Building frontend bundle"
cd "${FRONTEND_DIR}"
npm ci
npm run build

echo "[3/6] Syncing repository files into release workspace"
cd "${ROOT_DIR}"
rsync -a \
  --exclude ".git" \
  --exclude ".cursor" \
  --exclude "release" \
  --exclude "frontend/node_modules" \
  --exclude "app/staticfiles" \
  --exclude "__pycache__" \
  "${ROOT_DIR}/" "${PACKAGE_DIR}/"

echo "[4/6] Embedding frontend dist into Django static source"
mkdir -p "${PACKAGE_DIR}/app/static/frontend"
rm -rf "${PACKAGE_DIR}/app/static/frontend/"*
cp -R "${FRONTEND_DIR}/dist/." "${PACKAGE_DIR}/app/static/frontend/"

echo "[5/6] Collecting static files in release workspace"
cd "${PACKAGE_DIR}/app"
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput

echo "[6/6] Creating distributable archive"
cd "${RELEASE_DIR}"
zip -r "main.zip" "main" > /dev/null

echo "Release ready: ${RELEASE_DIR}/main.zip"
