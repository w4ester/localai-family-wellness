# Alembic Migrations Guide for LocalAI Family Wellness Platform

This guide explains how to use Alembic for database migrations in both local development and Docker environments.

## Overview

Alembic is used to manage database schema changes. It allows you to:

1. Create migrations based on changes to your SQLAlchemy models
2. Apply migrations to update your database schema
3. Revert migrations when needed
4. Track migration history

## Setup

The project has been configured to work with Alembic in two ways:

1. **Within Docker**: Run Alembic commands inside the backend container
2. **Locally**: Run Alembic commands directly on your development machine

## Option A: Running Migrations in Docker (Recommended)

This is the preferred method as it ensures consistency with your Docker environment.

### Prerequisites

1. Docker and Docker Compose installed
2. Docker services started: `docker compose up -d backend postgres`

### Running Migrations

We've created a script to simplify running Alembic commands in Docker:

```bash
# Create a new migration
./run_migrations_docker.sh revision "Your migration message"

# Apply all pending migrations
./run_migrations_docker.sh upgrade

# Revert the last migration
./run_migrations_docker.sh downgrade

# Show migration history
./run_migrations_docker.sh history

# Show current migration version
./run_migrations_docker.sh current

# Check for pending migrations
./run_migrations_docker.sh check
```

## Option B: Running Migrations Locally

This approach is useful for local development without Docker.

### Prerequisites

1. Local PostgreSQL with pgvector installed
2. Local database created: `./create_local_db.sh`
3. Poetry installed for dependency management

### Setup Local Environment

1. Ensure PostgreSQL is running on your local machine
2. Run `./create_local_db.sh` to set up the local database
3. Make sure `backend/.env` has the correct database credentials

### Running Migrations Locally

```bash
# Navigate to the backend directory
cd backend

# Create a new migration
poetry run alembic revision --autogenerate -m "Your migration message"

# Apply all pending migrations
poetry run alembic upgrade head

# Revert the last migration
poetry run alembic downgrade -1
```

## Migration File Structure

Migrations are stored in `backend/alembic/versions/`. Each migration file contains:

- `upgrade()`: Changes to apply when migrating forward
- `downgrade()`: Changes to apply when reverting the migration

## Best Practices

1. **Always review auto-generated migrations** before applying them. Alembic can miss certain changes or generate incorrect SQL.

2. **Add migrations to version control** to ensure consistent database schema across development environments.

3. **Test migrations** before applying them to production.

4. **Backup your database** before applying migrations in production.

## Troubleshooting

### Connection Issues

- **When using Docker**: Make sure the backend container can connect to the postgres service.
- **When running locally**: Verify your local PostgreSQL server is running and accessible.

### Alembic Configuration

The key files for Alembic configuration are:

- `backend/alembic.ini`: Contains the base configuration for Alembic
- `backend/alembic/env.py`: Contains the Python environment for Alembic, including database connection logic

### Dependency Errors

If you encounter dependency errors when running Alembic locally, ensure you've installed all dependencies:

```bash
cd backend
poetry install
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
