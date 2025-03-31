#!/bin/bash
# Script to run Alembic migrations directly using the postgres container
# without requiring the backend container

# Ensure PostgreSQL container is running
if ! docker compose ps | grep -q "localai-postgres"; then
    echo "PostgreSQL container is not running. Starting it..."
    docker compose up -d postgres
    # Give some time for services to initialize
    sleep 5
fi

# Check if the container exists before proceeding
if ! docker compose ps | grep -q "localai-postgres"; then
    echo "ERROR: PostgreSQL container failed to start or is not found."
    exit 1
fi

# Ensure PostgreSQL is running and healthy
echo "Checking PostgreSQL connection..."
if ! docker compose exec postgres psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to PostgreSQL. Please check if it's running properly."
    exit 1
fi

# Check if the database exists, create if needed
echo "Ensuring database exists..."
docker compose exec postgres psql -U postgres -c "CREATE DATABASE family_wellness;" > /dev/null 2>&1 || echo "Database already exists."

# Create a temporary container to run Alembic migrations
echo "Creating temporary container for migrations..."
docker run --rm \
    --network localai-family-wellness_database-net \
    -v "$(pwd)/backend:/app" \
    -w /app \
    -e DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD:-change_this_password}@postgres:5432/family_wellness" \
    $(docker compose images backend -q) \
    alembic "$@"

echo "Migration operation completed."
