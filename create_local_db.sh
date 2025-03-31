#!/bin/bash

# This script creates the family_wellness database in your local PostgreSQL instance
# Make sure PostgreSQL is running and you have the proper permissions

echo "Creating family_wellness database in your local PostgreSQL..."

# Create the database if it doesn't exist
psql -U postgres -h localhost -c "CREATE DATABASE family_wellness;" || echo "Database may already exist, continuing..."

# Install pgvector extension (required for AI memory vectors)
psql -U postgres -h localhost -d family_wellness -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "Failed to create vector extension. Please ensure pgvector is installed in your PostgreSQL instance."

echo "Database setup complete. Now you can run the migration script."
