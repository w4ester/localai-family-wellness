# Database Migration with Alembic

This project supports two methods for managing database migrations:

## Quick Start

### Option 1: Using Docker (Recommended for Production)
```bash
# Make the scripts executable
chmod +x migrate.sh

# Generate the initial schema
./migrate.sh generate "Initial schema"

# Apply migrations
./migrate.sh upgrade
```

### Option 2: Local Development with Poetry
```bash
# Make the script executable
chmod +x local_migrate.sh

# Generate the initial schema
./local_migrate.sh generate "Initial schema"

# Apply migrations
./local_migrate.sh upgrade
```

## Detailed Documentation

For full details on migration workflows, configuration, and troubleshooting, see the [Migration Guide](./docs/MIGRATION_GUIDE.md).
