#!/bin/bash

set -e

echo "Starting PixelCast installer..."

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo ".env created from .env.example. Review values before running again."
    exit 1
  fi
  echo "DB_PASSWORD=PCgPxCl_X8nM4pQ7wK2vL9jH5cF3yT6sA1eB0dZgM" > .env
  echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
  echo "DB_NAME=pixelcast_signage_db" >> .env
  echo "DB_USER=pixelcast_signage_user" >> .env
  echo ".env generated. Review and run install.sh again."
  exit 1
fi

if [ ! -f "frontend/src/pages/logs/LogsReports.vue" ]; then
  echo "Required file missing: frontend/src/pages/logs/LogsReports.vue"
  exit 1
fi

docker compose down 2>/dev/null || true
docker compose build --no-cache
docker compose up -d

echo "Installation finished."
