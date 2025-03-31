#!/bin/bash
# Script to run Alembic migrations directly using the postgres container
# without requiring Redis or the backend container

# Check if postgres container is running
if ! docker compose ps | grep -q "localai-postgres.*running"; then
    echo "PostgreSQL container is not running. Starting it..."
    docker compose up -d postgres
    # Give PostgreSQL time to initialize
    sleep 5
fi

# Get the backend image ID to use for our temporary container
BACKEND_IMAGE=$(docker compose images backend -q)
if [ -z "$BACKEND_IMAGE" ]; then
    echo "Building backend image..."
    docker compose build backend
    BACKEND_IMAGE=$(docker compose images backend -q)
fi

# Read password from .env file
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)

# Run a temporary container using the backend image to execute Alembic commands
echo "Running Alembic migration command: $@"
docker run --rm \
    --network localai-family-wellness_database-net \
    -v "$(pwd)/backend:/app" \
    -w /app \
    -e DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@postgres:5432/family_wellness" \
    $BACKEND_IMAGE \
    bash -c "pip install alembic && alembic $*"

echo "Migration operation completed."
