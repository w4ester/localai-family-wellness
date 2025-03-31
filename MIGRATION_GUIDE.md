# Database Migration Guide for LocalAI Family Wellness Platform

This guide explains how to use Alembic for database migrations with your Docker-based environment.

## Prerequisites

- Docker and Docker Compose installed
- Docker containers properly configured in docker-compose.yml
- The .env file properly configured with database connection details

## Using the Migration Script

The `migrate.sh` script simplifies running Alembic migrations within your Docker containers.

1. First, make the script executable:
   ```bash
   chmod +x migrate.sh
   ```

2. Generate a new migration:
   ```bash
   ./migrate.sh generate "Migration description"
   ```
   This will create a new migration file in `/app/alembic/versions/` inside the backend container.

3. Apply all migrations:
   ```bash
   ./migrate.sh upgrade
   ```
   This will apply all migrations up to the latest version.

4. Check current database state:
   ```bash
   ./migrate.sh current
   ```
   This shows the current migration version of your database.

5. View migration history:
   ```bash
   ./migrate.sh history
   ```
   This displays the full migration history.

6. Check migration status:
   ```bash
   ./migrate.sh status
   ```
   This verifies if there are pending migrations to be applied.

## Development Workflow

When you make changes to your SQLAlchemy models:

1. Update your model files in `backend/app/db/models/`
2. Generate a new migration:
   ```bash
   ./migrate.sh generate "Description of model changes"
   ```
3. Review the generated migration file
4. Apply the migration:
   ```bash
   ./migrate.sh upgrade
   ```

## Initial Database Setup

For the initial setup of your database:

1. Ensure Docker is running
2. Make sure your database configuration is correct in `.env`
3. Run the migration script to create the initial schema:
   ```bash
   ./migrate.sh generate "Initial schema"
   ./migrate.sh upgrade
   ```

## Notes About Your Setup

- Migrations run within the Docker container, ensuring consistency with your application environment
- The connection parameters are taken from the `DATABASE_URL` environment variable
- All models are properly imported in `alembic/env.py`
- The pgvector extension is handled correctly in the model definitions

## Manual Intervention (if needed)

If you need to manually access the database:

```bash
docker compose exec postgres psql -U postgres -d family_wellness
```

If you need to run Alembic commands directly:

```bash
docker compose exec backend alembic [command]
```
