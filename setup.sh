#!/bin/bash
set -e

echo "setup.sh is kept for backward compatibility."
exec ./install.sh
#!/bin/bash

# PixelCast Signage - Fix & Setup Script (macOS, Linux)
# Run from project root: ./setup.sh

set -e

echo "🚀 Starting PixelCast Signage Fix & Setup..."

# 1. Check for .env file
if [ ! -f .env ]; then
  echo "⚠️  .env file not found!"
  if [ -f env.example ]; then
    echo "   Creating .env from env.example..."
    cp env.example .env
    echo "   Please edit .env and set DB_PASSWORD and SECRET_KEY before running again."
    echo "   Or run: export DB_PASSWORD=your-password SECRET_KEY=\$(openssl rand -hex 32)"
    exit 1
  else
    echo "   Creating minimal .env..."
    echo "DB_PASSWORD=PCgPxCl_X8nM4pQ7wK2vL9jH5cF3yT6sA1eB0dZgM" > .env
    echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
    echo "DB_NAME=pixelcast_signage_db" >> .env
    echo "DB_USER=pixelcast_signage_user" >> .env
    echo "⚠️  Please edit .env and set a secure DB_PASSWORD before running again."
    exit 1
  fi
fi

# 2. Verify required env vars (warn if missing)
if [ -z "${DB_PASSWORD}" ] && ! grep -q "^DB_PASSWORD=.\+" .env 2>/dev/null; then
  echo "⚠️  DB_PASSWORD not set in .env - build may fail. Set it in .env"
fi
if [ -z "${SECRET_KEY}" ] && ! grep -q "^SECRET_KEY=.\+" .env 2>/dev/null; then
  echo "⚠️  SECRET_KEY not set in .env - adding random one..."
  if ! grep -q "^SECRET_KEY=" .env; then
    echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
  fi
fi

# 3. Verify LogsReports.vue exists (case-sensitive for Linux/Docker)
FILE_PATH="frontend/src/pages/logs/LogsReports.vue"
if [ ! -f "$FILE_PATH" ]; then
  echo "❌ Error: $FILE_PATH not found!"
  echo "   Searching for similar files..."
  find frontend -iname "*.vue" 2>/dev/null | head -20
  exit 1
fi
echo "✓ LogsReports.vue found"

# 4. Clean Docker (avoid ARM vs x86 cache issues on Mac)
echo "🧹 Cleaning up old Docker images and cache..."
docker compose down 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# 5. Build with --no-cache for fresh dependencies
echo "🏗️  Building containers..."
docker compose build --no-cache

# 6. Start services
echo "🆙 Starting PixelCast Signage..."
docker compose up -d

echo "✅ Done! Use 'docker compose logs -f' to see the logs."
echo "   Frontend: http://localhost:5173 (set FRONTEND_HOST_PORT in .env to change host port)"
