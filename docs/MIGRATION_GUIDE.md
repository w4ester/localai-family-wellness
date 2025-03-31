# Database Migration Guide

This guide explains two methods for managing database migrations for the LocalAI Family Wellness Platform:

1. **Docker-based migrations** (using `migrate.sh`)
2. **Local development migrations** (using `local_migrate.sh`)

Both approaches use Alembic under the hood but operate in different environments.

## Docker-based Migrations (Recommended for Consistency)

The `migrate.sh` script runs Alembic commands in a Docker container, ensuring consistency with your production environment.

### Prerequisites
- Docker and Docker Compose installed
- The PostgreSQL container running

### Basic Commands

```bash
# Generate a new migration
./migrate.sh generate "Description of changes"

# Apply migrations
./migrate.sh upgrade

# Check migration status
./migrate.sh status

# See migration history
./migrate.sh history

# View current migration version
./migrate.sh current
```

## Local Development Migrations (Using Poetry)

The `local_migrate.sh` script runs Alembic on your local machine using Poetry, requiring local dependencies but offering faster execution.

### Prerequisites
- Poetry installed
- PostgreSQL accessible from your local machine
- Required Python dependencies installed (`poetry install`)

### Basic Commands

```bash
# Generate a new migration
./local_migrate.sh generate "Description of changes"

# Apply migrations
./local_migrate.sh upgrade

# Check migration status
./local_migrate.sh status

# See migration history
./local_migrate.sh history

# View current migration version
./local_migrate.sh current
```

### Local Configuration

For local development, create a `.env.local` file in the `backend` directory with your database connection information:

```
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/family_wellness
```

## Common Workflow

1. Make changes to your SQLAlchemy models in `app/db/models/`
2. Generate a migration:
   ```bash
   ./migrate.sh generate "Description of your model changes"
   ```
3. Review the generated migration in `backend/alembic/versions/`
4. Apply the migration:
   ```bash
   ./migrate.sh upgrade
   ```

## Troubleshooting

### Docker Network Issues
If the Docker migration script can't connect to PostgreSQL, verify the container is running:
```bash
docker compose ps
```

### Local Connection Issues
If the local script can't connect to PostgreSQL:
1. Check if PostgreSQL port is exposed in `docker-compose.yml`
2. Verify the connection string in `.env.local`
3. Make sure your local machine can connect to the Docker container

### Migration Conflicts
If you get migration conflicts:
1. Check the current database state: `./migrate.sh current`
2. Compare with the available migrations: `./migrate.sh history`
3. Correct any discrepancies by upgrading or downgrading to a specific revision

## Initial Setup

For the initial setup of your database:

```bash
# Using Docker
./migrate.sh generate "Initial schema"
./migrate.sh upgrade

# Or using local Poetry
./local_migrate.sh generate "Initial schema"
./local_migrate.sh upgrade
```

These commands will create all database tables based on your SQLAlchemy models.
