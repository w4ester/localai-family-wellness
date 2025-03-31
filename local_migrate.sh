#!/bin/bash
# Script for local development migrations using Poetry

# Ensure proper error handling
set -e

# Command can be "generate", "upgrade", or other alembic commands
COMMAND=${1:-"status"}
# Message for migration (only used with generate command)
MESSAGE=${2:-"Migration update"}

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Set up DATABASE_URL that connects to the Docker container through localhost
# This assumes you've forwarded the PostgreSQL port in your docker-compose.yml (which we'll add separately)
export DATABASE_URL="postgresql+psycopg://postgres:change_this_password@localhost:5432/family_wellness"

# Load from .env.local if it exists
if [ -f .env.local ]; then
  source .env.local
fi

echo "Using DATABASE_URL: $DATABASE_URL"

# Run alembic command with Poetry
if [ "$COMMAND" == "generate" ]; then
  echo "Generating new migration with message: '$MESSAGE'"
  poetry run alembic revision --autogenerate -m "$MESSAGE"
  echo "Migration file created. Review it before applying."
elif [ "$COMMAND" == "upgrade" ]; then
  echo "Applying migrations to latest version..."
  poetry run alembic upgrade head
  echo "Migrations applied successfully."
elif [ "$COMMAND" == "current" ]; then
  echo "Current database revision:"
  poetry run alembic current
elif [ "$COMMAND" == "history" ]; then
  echo "Migration history:"
  poetry run alembic history
elif [ "$COMMAND" == "status" ]; then
  echo "Checking migration status..."
  poetry run alembic check || echo "Pending migrations exist"
else
  echo "Running alembic $COMMAND..."
  poetry run alembic $COMMAND
fi
