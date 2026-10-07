#!/bin/sh
set -e

# ==============================================================================
# AI-Powered Fine Print Auditor - Backend Entrypoint & Startup Orchestrator
# ==============================================================================

DB_HOST="${POSTGRES_SERVER:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "[entrypoint] Waiting for PostgreSQL database at ${DB_HOST}:${DB_PORT} to accept connections..."

python -c "
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
start_time = time.time()
timeout = 60

while time.time() - start_time < timeout:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f'[entrypoint] PostgreSQL at {host}:{port} is reachable and accepting TCP connections.')
            sys.exit(0)
    except (socket.error, OSError) as err:
        print(f'[entrypoint] Database not ready yet ({err}). Retrying in 1s...')
        time.sleep(1)

print(f'[entrypoint] ERROR: Timed out after {timeout}s waiting for PostgreSQL at {host}:{port}')
sys.exit(1)
" "$DB_HOST" "$DB_PORT"

echo "[entrypoint] Executing Alembic database migrations..."
alembic upgrade head
echo "[entrypoint] Database migrations applied successfully."

echo "[entrypoint] Checking for unembedded policy clauses to re-index..."
python scripts/reindex_embeddings.py || true

echo "[entrypoint] Starting application process: $@"
exec "$@"
