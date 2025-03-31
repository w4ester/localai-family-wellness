#!/bin/bash

# Script to manage database migrations using Alembic, executed
# inside the running backend Docker container via 'docker compose exec'.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# Service names defined in your docker-compose.yml
DB_CONTAINER_NAME="localai-postgres"
BACKEND_CONTAINER_NAME="localai-backend"
# Read DB name/user from .env file (ensure .env exists in project root)
# Source the .env file to load variables into the script's environment
if [ -f .env ]; then
    set -a
    . .env
    set +a
else
    echo "Error: .env file not found in project root!"
    exit 1
fi
DB_NAME="${POSTGRES_DB:-localai_family}" # Use value from .env or default
DB_USER="${POSTGRES_USER:-postgres}"

# --- Command Handling ---
# Default command is 'status' if no argument provided
COMMAND=${1:-"status"}
# Migration message (only used for 'generate'/'revision' command)
MESSAGE=${2:-"Alembic migration"}

# --- Pre-checks ---
echo "--> Checking if required Docker services are running..."
# Check if Postgres container is running and healthy
if ! docker compose ps -q --filter "name=$DB_CONTAINER_NAME" --filter "health=healthy" | grep -q .; then
    echo "PostgreSQL container ($DB_CONTAINER_NAME) is not running or not healthy."
    echo "Attempting to start required services..."
    docker compose up -d postgres backend # Start both DB and Backend
    echo "Waiting for services to potentially become healthy..."
    sleep 15 # Give services time to start and potentially pass healthchecks
    # Re-check health after waiting
    if ! docker compose ps -q --filter "name=$DB_CONTAINER_NAME" --filter "health=healthy" | grep -q .; then
        echo "Error: PostgreSQL container ($DB_CONTAINER_NAME) did not become healthy after starting."
        echo "Check Docker logs:"
        docker compose logs "$DB_CONTAINER_NAME"
        exit 1
    fi
else
    echo "PostgreSQL container is healthy."
fi

# Check if Backend container is running (needed for exec)
if ! docker compose ps -q --filter "name=$BACKEND_CONTAINER_NAME" --filter "status=running" | grep -q .; then
     echo "Error: Backend container ($BACKEND_CONTAINER_NAME) is not running. Cannot execute Alembic."
     echo "Attempt to start it with 'docker compose up -d backend'"
     exit 1
fi
echo "Backend container is running."


# --- Ensure pgvector Extension ---
# Although the init script should handle this, an explicit check here adds robustness.
echo "--> Ensuring pgvector extension exists in database '$DB_NAME'..."
docker compose exec -T "$DB_CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
if [ $? -ne 0 ]; then echo "Error: Failed command to ensure pgvector extension exists."; exit 1; fi
echo "pgvector extension check/creation successful."


# --- Execute Alembic Command ---
echo "--> Running 'alembic $COMMAND' inside container '$BACKEND_CONTAINER_NAME'..."

# Prepare Alembic command arguments
ALEMBIC_CMD="alembic"

if [ "$COMMAND" == "generate" ] || [ "$COMMAND" == "revision" ]; then
    # Use 'revision --autogenerate' for generation
    ALEMBIC_CMD="$ALEMBIC_CMD revision --autogenerate -m \"$MESSAGE\""
elif [ "$COMMAND" == "upgrade" ] || [ "$COMMAND" == "downgrade" ]; then
    # Append revision target (e.g., 'head', 'base', specific revision ID) if provided
    REVISION_TARGET=${2:-"head"} # Default to 'head' for upgrade if no target specified
    ALEMBIC_CMD="$ALEMBIC_CMD $COMMAND $REVISION_TARGET"
else
    # For other commands like status, current, history, just pass them through
    ALEMBIC_CMD="$ALEMBIC_CMD $COMMAND"
fi

# Execute the assembled Alembic command inside the backend container
docker compose exec "$BACKEND_CONTAINER_NAME" $ALEMBIC_CMD

# Check exit status
if [ $? -ne 0 ]; then
    echo "Error: Alembic command '$ALEMBIC_CMD' failed."
    echo "Check output above and backend container logs if necessary:"
    # docker compose logs "$BACKEND_CONTAINER_NAME" # Uncomment to see logs on failure
    exit 1
fi

echo "✅ Alembic command '$ALEMBIC_CMD' executed successfully!"
exit 0