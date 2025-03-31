#!/bin/bash
# Script to manually set up the database tables without using Alembic

# Ensure PostgreSQL container is running
if ! docker compose ps | grep -q "localai-postgres.*running"; then
    echo "Starting PostgreSQL container..."
    docker compose up -d postgres
    sleep 5
fi

# Read PostgreSQL password from .env
POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)

echo "Creating database if it doesn't exist..."
docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists."

echo "Creating database schema using SQL script..."

# Execute the SQL script directly in the PostgreSQL container
docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql

echo "Database schema created successfully."
