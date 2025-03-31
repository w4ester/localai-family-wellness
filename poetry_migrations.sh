#!/bin/bash
# Script to run Alembic migrations using Poetry in the backend directory

# First make sure Postgres is running
if ! docker compose ps | grep -q "localai-postgres.*running"; then
    echo "Starting PostgreSQL container..."
    docker compose up -d postgres
    sleep 5
fi

# Read PostgreSQL password from .env
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)

# Change to the backend directory
cd backend

# Set up environment variables for the migration
export DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/family_wellness"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install it first."
    echo "You can install it with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Run the migration command with Poetry
echo "Running migration command: $@"
poetry run alembic "$@"

echo "Migration operation completed."
