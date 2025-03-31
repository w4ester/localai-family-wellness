#!/bin/bash

# Script to create a new migration either locally or with Docker

# Default migration message
MIGRATION_MSG="Schema update"

# Parse command line arguments
USE_DOCKER=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -m|--message)
      MIGRATION_MSG="$2"
      shift 2
      ;;
    -d|--docker)
      USE_DOCKER=true
      shift
      ;;
    -l|--local)
      USE_DOCKER=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -m, --message MESSAGE  Set migration message (default: 'Schema update')"
      echo "  -d, --docker           Run with Docker (recommended)"
      echo "  -l, --local            Run locally"
      echo "  -h, --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [ "$USE_DOCKER" = true ]; then
    echo "Creating migration with Docker: \"$MIGRATION_MSG\""
    ./run_migrations_docker.sh revision "$MIGRATION_MSG"
    
    echo "Apply this migration? [y/N]"
    read -r APPLY
    if [[ $APPLY =~ ^[Yy]$ ]]; then
        ./run_migrations_docker.sh upgrade
    fi
else
    # Change to the backend directory
    cd "$(dirname "$0")/backend" || exit 1
    
    echo "Creating local migration: \"$MIGRATION_MSG\""
    poetry run alembic revision --autogenerate -m "$MIGRATION_MSG"
    
    # If the previous command succeeded, ask to apply the migration
    if [ $? -eq 0 ]; then
        echo "Migration created successfully."
        echo "Apply this migration? [y/N]"
        read -r APPLY
        if [[ $APPLY =~ ^[Yy]$ ]]; then
            poetry run alembic upgrade head
            echo "Database migration applied."
        else
            echo "Migration created but not applied."
        fi
    else
        echo "Failed to create migration. Check the error messages above."
    fi
fi
