#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# Wait until PostgreSQL is ready to accept connections
# ---------------------------------------------------------------------------
echo "Waiting for PostgreSQL..."
until nc -z postgres 5432; do
  echo "  postgres is unavailable — sleeping 1s"
  sleep 1
done
echo "PostgreSQL is up."

# ---------------------------------------------------------------------------
# Run Alembic migrations
# ---------------------------------------------------------------------------
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

# ---------------------------------------------------------------------------
# Start the FastAPI application
# ---------------------------------------------------------------------------
echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
