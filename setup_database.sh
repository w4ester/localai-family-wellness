#!/bin/bash
# Script to set up the database schema manually

# Ensure PostgreSQL container is running
if ! docker compose ps | grep -q "localai-postgres.*running"; then
    echo "Starting PostgreSQL container..."
    docker compose up -d postgres
    sleep 5
fi

# Read PostgreSQL config from .env
POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)

echo "Setting up database: $POSTGRES_DB"

# Create database if it doesn't exist
echo "Step 1: Creating database if it doesn't exist..."
docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists."

# Execute the SQL script to create tables
echo "Step 2: Creating database schema using SQL script..."
docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql

echo "✅ Database setup completed successfully!"
echo
echo "The following tables were created:"
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
