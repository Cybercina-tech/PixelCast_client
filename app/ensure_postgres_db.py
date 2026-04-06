#!/usr/bin/env python3
"""
Ensure the configured PostgreSQL database exists.

Connects to the maintenance database `postgres` (not DB_NAME) so this works when
DB_NAME has not been created yet — e.g. reused Docker volume from an older init,
or DB_NAME changed after the data directory was first initialized.
"""
from __future__ import annotations

import os
import sys


def _use_sqlite() -> bool:
    v = os.environ.get("USE_SQLITE", "false").strip().lower()
    return v in ("1", "true", "yes", "on")


def main() -> int:
    if _use_sqlite():
        print("USE_SQLITE enabled — skipping PostgreSQL ensure step.")
        return 0

    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        print("ensure_postgres_db: psycopg2 not installed", file=sys.stderr)
        return 1

    db_name = os.environ.get("DB_NAME", "pixelcast_signage_db").strip()
    db_user = os.environ.get("DB_USER", "pixelcast_signage_user").strip()
    host = os.environ.get("DB_HOST", "db").strip() or "db"
    port = os.environ.get("DB_PORT", "5432").strip() or "5432"
    password = os.environ.get("DB_PASSWORD", "")

    if not db_name:
        print("ensure_postgres_db: DB_NAME is empty", file=sys.stderr)
        return 1

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=db_user,
            password=password,
            dbname="postgres",
            connect_timeout=15,
        )
    except Exception as e:
        print(f"ensure_postgres_db: cannot connect to PostgreSQL (database=postgres): {e}", file=sys.stderr)
        return 1

    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone():
                print(f"ensure_postgres_db: database {db_name!r} already exists.")
                return 0
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8'").format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user),
                )
            )
            print(f"ensure_postgres_db: created database {db_name!r} (owner {db_user!r}).")
            return 0
    except Exception as e:
        print(f"ensure_postgres_db: failed: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
