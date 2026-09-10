#!/usr/bin/env bash
set -e

echo "Starting PostgreSQL..."
service postgresql start

echo "Starting Redis..."
service redis-server start

# Wait for services to be ready
sleep 2

echo "Initializing Database..."
python3 -m app.core.init_db

echo "Handing over execution to the given command..."
exec "$@"
