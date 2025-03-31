#!/bin/bash
# Script to run Alembic migrations inside Docker

# Ensure Docker containers are running
if ! docker compose ps | grep -q "localai-backend"; then
    echo "Backend container is not running. Starting Docker services..."
    docker compose up -d backend postgres
    # Give some time for services to initialize
    sleep 10
fi

# Check if the container exists before proceeding
if ! docker compose ps | grep -q "localai-backend"; then
    echo "ERROR: Backend container failed to start or is not found."
    exit 1
fi

# Parse command line arguments
if [ "$1" == "revision" ]; then
    # Create a new migration (autogenerate)
    if [ -z "$2" ]; then
        echo "ERROR: Missing migration message. Usage: ./run_migrations_docker.sh revision \"Your migration message\""
        exit 1
    fi
    docker compose exec backend alembic revision --autogenerate -m "$2"
elif [ "$1" == "upgrade" ]; then
    # Default to 'head' if no specific version is provided
    TARGET=${2:-head}
    docker compose exec backend alembic upgrade $TARGET
elif [ "$1" == "downgrade" ]; then
    # Default to -1 if no specific version is provided
    TARGET=${2:--1}
    docker compose exec backend alembic downgrade $TARGET
elif [ "$1" == "history" ]; then
    # Show migration history
    docker compose exec backend alembic history
elif [ "$1" == "current" ]; then
    # Show current migration version
    docker compose exec backend alembic current
elif [ "$1" == "check" ]; then
    # Check if there are any changes to migrate
    docker compose exec backend alembic check
else
    echo "Usage:"
    echo "  ./run_migrations_docker.sh revision \"Your migration message\"  # Create a new migration"
    echo "  ./run_migrations_docker.sh upgrade [target]                     # Apply migrations (default: head)"
    echo "  ./run_migrations_docker.sh downgrade [target]                   # Revert migrations (default: -1)"
    echo "  ./run_migrations_docker.sh history                              # Show migration history"
    echo "  ./run_migrations_docker.sh current                              # Show current migration version"
    echo "  ./run_migrations_docker.sh check                                # Check for pending migrations"
    exit 1
fi

echo "Migration operation completed."
