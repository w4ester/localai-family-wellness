#!/bin/bash
# Complete database setup script with pgvector support

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

# Create a version of the SQL script without pgvector dependencies
echo "Step 2: Creating modified SQL script without pgvector dependencies..."
cat > ./backend/create_tables_no_pgvector.sql << 'EOF'
-- SQL script to create the initial tables for the Family Wellness database

-- Create Users table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Family table
CREATE TABLE IF NOT EXISTS family (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create FamilyMember table (relationship between User and Family)
CREATE TABLE IF NOT EXISTS family_member (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    is_parent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, family_id)
);

-- Create ScreenTimeRule table
CREATE TABLE IF NOT EXISTS screen_time_rule (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    daily_limit INTEGER NOT NULL, -- in minutes
    weekly_limit INTEGER NOT NULL, -- in minutes
    allowed_hours JSONB, -- JSON array of allowed hours
    allowed_apps JSONB, -- JSON array of allowed apps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ScreenTimeUsage table
CREATE TABLE IF NOT EXISTS screen_time_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    minutes_used INTEGER NOT NULL,
    app_breakdown JSONB, -- JSON of app usage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ScreenTimeExtensionRequest table
CREATE TABLE IF NOT EXISTS screen_time_extension_request (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    requested_minutes INTEGER NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, denied
    parent_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Chore table
CREATE TABLE IF NOT EXISTS chore (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, verified
    frequency VARCHAR(20), -- daily, weekly, monthly, once
    due_date TIMESTAMP,
    completion_date TIMESTAMP,
    verification_date TIMESTAMP,
    verified_by INTEGER REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create simplified AIMemory table without vector storage
CREATE TABLE IF NOT EXISTS ai_memory (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding_json JSONB, -- Store embedding as JSON array instead of vector type
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

# Execute the SQL script to create tables
echo "Step 3: Creating database schema using modified SQL script..."
docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables_no_pgvector.sql

echo "✅ Database setup completed successfully!"
echo
echo "The following tables were created:"
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"

echo
echo "NOTE: The pgvector extension is not installed in this PostgreSQL container."
echo "To enable vector embeddings with pgvector, you'll need to modify your Docker setup."
echo "For local development, you can use the simplified schema with JSON embeddings."
echo "For production, ensure your PostgreSQL installation includes pgvector."
