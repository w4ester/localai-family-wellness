#!/bin/bash
# Script to set up PostgreSQL with pgvector and initialize the database schema

echo "Step 1: Stopping existing PostgreSQL container..."
docker compose stop postgres
docker compose rm -f postgres

echo "Step 2: Starting PostgreSQL with pgvector support..."
docker compose up -d postgres
echo "Waiting for PostgreSQL to initialize..."
sleep 10

# Read PostgreSQL config from .env
POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)

echo "Step 3: Creating database if it doesn't exist..."
docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists or there was an issue creating it."

echo "Step 4: Verifying pgvector extension..."
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT * FROM pg_extension WHERE extname = 'vector';"

echo "Step 5: Creating database schema..."
docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql

echo "✅ Database setup with pgvector completed successfully!"
echo
echo "The following tables were created:"
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
