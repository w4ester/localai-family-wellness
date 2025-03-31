-- SQL script to create the initial tables for the Family Wellness database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

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

-- Create AIMemory table for vector storage
CREATE TABLE IF NOT EXISTS ai_memory (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- Assuming 1536-dimensional embeddings
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on vector column for similarity search
CREATE INDEX IF NOT EXISTS ai_memory_embedding_idx ON ai_memory USING ivfflat (embedding vector_l2_ops);
