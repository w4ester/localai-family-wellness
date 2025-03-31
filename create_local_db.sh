#!/bin/bash

# This script creates the family_wellness database in your local PostgreSQL instance
# Make sure PostgreSQL is running and you have the proper permissions

echo "Creating family_wellness database in your local PostgreSQL..."

# Check for a master user first, then fall back to system username
PG_USER="willf"
PG_PASSWORD=""

# Try to read credentials from .pgpass if it exists
PGPASS_FILE="/Users/willf/smartIndex/postgresPSQL/credentials/.pgpass"
if [ -f "$PGPASS_FILE" ]; then
    echo "Reading credentials from $PGPASS_FILE"
    MASTER_USER=$(grep "postgres_master" "$PGPASS_FILE" | cut -d: -f4)
    MASTER_PASSWORD=$(grep "postgres_master" "$PGPASS_FILE" | cut -d: -f5)
    if [ -n "$MASTER_USER" ] && [ -n "$MASTER_PASSWORD" ]; then
        PG_USER="$MASTER_USER"
        PG_PASSWORD="$MASTER_PASSWORD"
        echo "Using master PostgreSQL user '$PG_USER'"
        export PGPASSWORD="$PG_PASSWORD"
    fi
else
    echo "Using system username '$PG_USER' for PostgreSQL."
    
    # Prompt for password if needed
    if [ -z "$PGPASSWORD" ]; then
        read -sp "Enter your PostgreSQL password for user '$PG_USER' (press Enter for no password): " PGPASS
        echo ""
        export PGPASSWORD="$PGPASS"
        PG_PASSWORD="$PGPASS"
    fi
fi

# Create the database if it doesn't exist
psql -U "$PG_USER" -h localhost -c "CREATE DATABASE family_wellness;" || echo "Database may already exist, continuing..."

# Install pgvector extension (required for AI memory vectors)
psql -U "$PG_USER" -h localhost -d family_wellness -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "Failed to create vector extension. Please ensure pgvector is installed in your PostgreSQL instance."

# Update the backend/.env file with the password and username if it exists
if [ -f "./backend/.env" ]; then
    # Write a new .env file with the correct credentials
    echo "# Local development environment variables for backend" > ./backend/.env
    echo "# This file is used when running Alembic commands directly on your host machine" >> ./backend/.env
    echo "" >> ./backend/.env
    echo "# Database connection for local development" >> ./backend/.env
    echo "DATABASE_URL=postgresql+psycopg://$PG_USER:$PG_PASSWORD@localhost:5432/family_wellness" >> ./backend/.env
    echo "Updated backend/.env with your database credentials."
fi

# Update alembic.ini to use the correct username for local development
sed -i.bak "s|sqlalchemy.url = postgresql+psycopg://postgres:password@localhost:5432/family_wellness|sqlalchemy.url = postgresql+psycopg://$PG_USER:$PG_PASSWORD@localhost:5432/family_wellness|" ./backend/alembic.ini && rm ./backend/alembic.ini.bak

echo "Database setup complete. Now you can run the migration script."
echo "To run migrations locally, cd into the backend directory and run: poetry run alembic upgrade head"
echo "To run migrations in Docker, use: ./run_migrations_docker.sh upgrade"

# Clear the password from environment for security
unset PGPASSWORD
