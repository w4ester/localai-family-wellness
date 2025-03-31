A	MIGRATION_GUIDE.md
M	README.md
A	README_MIGRATIONS.md
M	backend/Dockerfile
M	backend/alembic.ini
M	backend/alembic/__pycache__/env.cpython-311.pyc
M	backend/alembic/env.py
M	backend/app/core/config.py
M	backend/app/db/models/chore_model.py
M	backend/app/db/models/screen_time_model.py
A	backend/create_tables.sql
M	backend/pyproject.toml
A	backend/requirements.txt
A	config/postgres/init-scripts/01_init_pgvector.sql
M	create_local_db.sh
M	create_migration.sh
A	direct_migrations.sh
A	docker-compose.override.yml
M	docker-compose.yml
A	docs/MIGRATION_GUIDE.md
A	docs/alembic_migrations_guide.md
A	fix_version.sh
A	local_migrate.sh
A	make_executable.sh
A	manual_migration.sh
A	migrate.sh
A	poetry_migrations.sh
A	postgres_migrations.sh
A	run_migrations_docker.sh
A	setup_database.sh
A	setup_database_complete.sh
A	setup_pgvector.sh
diff --git a/MIGRATION_GUIDE.md b/MIGRATION_GUIDE.md
new file mode 100644
index 0000000..e069f95
--- /dev/null
+++ b/MIGRATION_GUIDE.md
@@ -0,0 +1,96 @@
+# Database Migration Guide for LocalAI Family Wellness Platform
+
+This guide explains how to use Alembic for database migrations with your Docker-based environment.
+
+## Prerequisites
+
+- Docker and Docker Compose installed
+- Docker containers properly configured in docker-compose.yml
+- The .env file properly configured with database connection details
+
+## Using the Migration Script
+
+The `migrate.sh` script simplifies running Alembic migrations within your Docker containers.
+
+1. First, make the script executable:
+   ```bash
+   chmod +x migrate.sh
+   ```
+
+2. Generate a new migration:
+   ```bash
+   ./migrate.sh generate "Migration description"
+   ```
+   This will create a new migration file in `/app/alembic/versions/` inside the backend container.
+
+3. Apply all migrations:
+   ```bash
+   ./migrate.sh upgrade
+   ```
+   This will apply all migrations up to the latest version.
+
+4. Check current database state:
+   ```bash
+   ./migrate.sh current
+   ```
+   This shows the current migration version of your database.
+
+5. View migration history:
+   ```bash
+   ./migrate.sh history
+   ```
+   This displays the full migration history.
+
+6. Check migration status:
+   ```bash
+   ./migrate.sh status
+   ```
+   This verifies if there are pending migrations to be applied.
+
+## Development Workflow
+
+When you make changes to your SQLAlchemy models:
+
+1. Update your model files in `backend/app/db/models/`
+2. Generate a new migration:
+   ```bash
+   ./migrate.sh generate "Description of model changes"
+   ```
+3. Review the generated migration file
+4. Apply the migration:
+   ```bash
+   ./migrate.sh upgrade
+   ```
+
+## Initial Database Setup
+
+For the initial setup of your database:
+
+1. Ensure Docker is running
+2. Make sure your database configuration is correct in `.env`
+3. Run the migration script to create the initial schema:
+   ```bash
+   ./migrate.sh generate "Initial schema"
+   ./migrate.sh upgrade
+   ```
+
+## Notes About Your Setup
+
+- Migrations run within the Docker container, ensuring consistency with your application environment
+- The connection parameters are taken from the `DATABASE_URL` environment variable
+- All models are properly imported in `alembic/env.py`
+- The pgvector extension is handled correctly in the model definitions
+
+## Manual Intervention (if needed)
+
+If you need to manually access the database:
+
+```bash
+docker compose exec postgres psql -U postgres -d family_wellness
+```
+
+If you need to run Alembic commands directly:
+
+```bash
+docker compose exec backend alembic [command]
+```
diff --git a/README.md b/README.md
index 455ba08..4c5106a 100644
--- a/README.md
+++ b/README.md
@@ -22,17 +22,39 @@ Make sure you have the following installed:
 
 ### 3. Initial Database Migration
 
-1. Make the migration script executable:
+#### Option A: Using Docker (Recommended)
+
+1. Make the migration scripts executable:
+   ```bash
+   chmod +x create_migration.sh run_migrations_docker.sh
+   ```
+
+2. Start the services:
+   ```bash
+   docker compose up -d backend postgres
+   ```
+
+3. Run the migration script with Docker:
+   ```bash
+   ./create_migration.sh --docker -m "Initial schema"
+   ```
+
+#### Option B: Local Development
+
+1. Install PostgreSQL and pgvector extension locally
+
+2. Create the local database:
    ```bash
-   chmod +x create_migration.sh
+   chmod +x create_local_db.sh
+   ./create_local_db.sh
    ```
 
-2. Run the migration script:
+3. Create and apply migrations:
    ```bash
-   ./create_migration.sh
+   ./create_migration.sh --local -m "Initial schema"
    ```
 
-This will create and apply the initial database migration.
+See [docs/alembic_migrations_guide.md](docs/alembic_migrations_guide.md) for detailed information on working with migrations.
 
 ### 4. Running the Application
 
@@ -58,9 +80,11 @@ docker-compose up -d
 1. Make your changes
 2. Create necessary database migrations:
    ```bash
-   cd backend
-   alembic revision --autogenerate -m "Description of changes"
-   alembic upgrade head
+   # Using Docker (recommended)
+   ./create_migration.sh --docker -m "Description of changes"
+   
+   # Or locally
+   ./create_migration.sh --local -m "Description of changes"
    ```
 3. Test your changes locally
 4. Commit and push your changes
diff --git a/README_MIGRATIONS.md b/README_MIGRATIONS.md
new file mode 100644
index 0000000..d92483b
--- /dev/null
+++ b/README_MIGRATIONS.md
@@ -0,0 +1,33 @@
+# Database Migration with Alembic
+
+This project supports two methods for managing database migrations:
+
+## Quick Start
+
+### Option 1: Using Docker (Recommended for Production)
+```bash
+# Make the scripts executable
+chmod +x migrate.sh
+
+# Generate the initial schema
+./migrate.sh generate "Initial schema"
+
+# Apply migrations
+./migrate.sh upgrade
+```
+
+### Option 2: Local Development with Poetry
+```bash
+# Make the script executable
+chmod +x local_migrate.sh
+
+# Generate the initial schema
+./local_migrate.sh generate "Initial schema"
+
+# Apply migrations
+./local_migrate.sh upgrade
+```
+
+## Detailed Documentation
+
+For full details on migration workflows, configuration, and troubleshooting, see the [Migration Guide](./docs/MIGRATION_GUIDE.md).
diff --git a/backend/Dockerfile b/backend/Dockerfile
index fc89ac3..1270475 100644
--- a/backend/Dockerfile
+++ b/backend/Dockerfile
@@ -6,8 +6,8 @@
 FROM python:3.11-slim as base
 
 # Set environment variables for Python behavior and Poetry version
-ENV PYTHONDONTWRITEBYTECODE 1
-ENV PYTHONUNBUFFERED 1
+ENV PYTHONDONTWRITEBYTECODE=1
+ENV PYTHONUNBUFFERED=1
 ENV POETRY_VERSION=1.7.1
 
 # Install essential system dependencies needed for building Python packages
@@ -34,15 +34,21 @@ WORKDIR /app
 # though this example remains single-stage for simplicity with `virtualenvs.create false`.
 FROM base as builder
 
-# Copy only the dependency definition files first.
-# If these files haven't changed, Docker reuses the cached layer below.
-COPY pyproject.toml poetry.lock* /app/
+# Copy both dependency definition files
+COPY pyproject.toml poetry.lock* requirements.txt* /app/
 
-# Install only production dependencies defined in pyproject.toml/poetry.lock
-# --no-root: Don't install the project itself as editable here.
-# --sync: Ensures the environment exactly matches the lock file.
-# --no-interaction / --no-ansi: For cleaner CI/scripted builds.
-RUN poetry install --no-interaction --no-ansi --no-root --sync
+# Try to install with Poetry first, if not use pip with requirements.txt
+RUN if [ -f pyproject.toml ]; then \
+        echo "Installing with Poetry" && \
+        poetry install --no-interaction --no-ansi --no-root --sync || \
+        (echo "Poetry install failed, falling back to pip" && \
+         pip install --no-cache-dir -r requirements.txt && \
+         touch /app/INSTALLED_WITH_PIP); \
+    else \
+        echo "No pyproject.toml found, using pip" && \
+        pip install --no-cache-dir -r requirements.txt && \
+        touch /app/INSTALLED_WITH_PIP; \
+    fi
 
 # --- Final Runtime Stage ---
 # Start fresh from the base to potentially have a smaller final image,
@@ -55,7 +61,8 @@ FROM base as final
 # We need to determine the exact path. A common path is /usr/local/lib/python3.11/site-packages
 # This step might be optional if just copying the whole app directory below is sufficient,
 # but explicit copying can sometimes be cleaner. Let's simplify for now.
-# COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
+COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
+COPY --from=builder /app/INSTALLED_WITH_PIP* /app/
 
 # Copy the application code from the build context's current directory (.)
 # into the container's /app directory. Respects .dockerignore.
@@ -63,6 +70,13 @@ FROM base as final
 # Since WORKDIR is /app, '.' copies into /app.
 COPY . /app/
 
+# Display which installation method was used
+RUN if [ -f /app/INSTALLED_WITH_PIP ]; then \
+        echo "Dependencies were installed with pip"; \
+    else \
+        echo "Dependencies were installed with Poetry"; \
+    fi
+
 # Inform Docker that the container listens on port 8000 at runtime.
 EXPOSE 8000
 
@@ -70,9 +84,9 @@ EXPOSE 8000
 # This is suitable for DEVELOPMENT due to `--reload`.
 # Override this command in production (e.g., via docker-compose.override.yml or separate prod Dockerfile/stage).
 # It correctly references 'app.main:app' based on your backend/app/main.py structure.
-CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
+CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
 
 # --- Example Production CMD (Commented out) ---
 # For production, remove '--reload' and potentially add '--workers'.
 # The number of workers depends on your server resources (often 2*CPU cores + 1).
-# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
\ No newline at end of file
+# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
\ No newline at end of file
diff --git a/backend/alembic.ini b/backend/alembic.ini
index 6756e35..1fed4ba 100644
--- a/backend/alembic.ini
+++ b/backend/alembic.ini
@@ -51,10 +51,10 @@ version_path_separator = os  # Use os.pathsep. Default configuration used for ne
 # output_encoding = utf-8
 
 # For local development using localhost
-sqlalchemy.url = postgresql+psycopg://postgres:password@localhost:5432/family_wellness
+# sqlalchemy.url = postgresql+psycopg://postgres_master:MVsD@m,eKW/*,XTjxe)@@localhost:5432/family_wellness
 
 # For Docker Compose (comment out the above line and uncomment this one when running with Docker)
-# sqlalchemy.url = postgresql+psycopg://postgres:postgres@postgres/family_wellness
+sqlalchemy.url = postgresql+psycopg://postgres:YOUR_STRONG_POSTGRES_PASSWORD_HERE@postgres/localai_family
 
 
 [post_write_hooks]
diff --git a/backend/alembic/__pycache__/env.cpython-311.pyc b/backend/alembic/__pycache__/env.cpython-311.pyc
index 579ee90..236c95f 100644
Binary files a/backend/alembic/__pycache__/env.cpython-311.pyc and b/backend/alembic/__pycache__/env.cpython-311.pyc differ
diff --git a/backend/alembic/env.py b/backend/alembic/env.py
index 84d6a15..10a7bec 100644
--- a/backend/alembic/env.py
+++ b/backend/alembic/env.py
@@ -1,4 +1,5 @@
 import asyncio
+import os
 from logging.config import fileConfig
 
 from sqlalchemy import engine_from_config, pool
@@ -47,7 +48,12 @@ def run_migrations_offline() -> None:
     script output.
 
     """
-    url = config.get_main_option("sqlalchemy.url")
+    # Get the SQLAlchemy URL from environment variable or fallback to config
+    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
+    
+    # Ensure URL is in the correct format for async driver
+    if url and not url.startswith("postgresql+psycopg"):
+        url = url.replace("postgresql", "postgresql+psycopg", 1)
     context.configure(
         url=url,
         target_metadata=target_metadata,
@@ -73,9 +79,15 @@ async def run_migrations_online() -> None:
     and associate a connection with the context.
 
     """
-    # Get the SQLAlchemy URL from config
-    config_section = config.get_section(config.config_ini_section)
-    url = config_section["sqlalchemy.url"]
+    # Get the SQLAlchemy URL from environment variable or fallback to config
+    url = os.getenv("DATABASE_URL")
+    if not url:
+        config_section = config.get_section(config.config_ini_section)
+        url = config_section["sqlalchemy.url"]
+    
+    # Ensure URL is in the correct format for async driver
+    if url and not url.startswith("postgresql+psycopg"):
+        url = url.replace("postgresql", "postgresql+psycopg", 1)
     
     # Create async engine
     connectable = create_async_engine(url, poolclass=pool.NullPool)
diff --git a/backend/app/core/config.py b/backend/app/core/config.py
index 65ba259..65eb6b9 100644
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -48,8 +48,16 @@ class Settings(BaseSettings):
     @classmethod
     def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
         if isinstance(v, str):
-             # If DATABASE_URL is explicitly set in env, use it
+            # Convert string manually if it's from environment variable
+            if v.startswith('postgresql+psycopg://'):
+                parts = v.split('@')
+                if len(parts) == 2:
+                    auth, server = parts
+                    prefix = auth.split('://')[0] + '://'
+                    user_pass = auth.split('://')[1]
+                    return prefix + user_pass + '@' + server
             return v
+        
         # Otherwise, assemble it from components
         values = info.data
         return PostgresDsn.build(
diff --git a/backend/app/db/models/chore_model.py b/backend/app/db/models/chore_model.py
index ae633c9..e133259 100644
--- a/backend/app/db/models/chore_model.py
+++ b/backend/app/db/models/chore_model.py
@@ -103,4 +103,4 @@ class Chore(Base):
 
     def __repr__(self):
         """String representation for debugging."""
-        return f"<Chore id={self.id} title='{self.title}' status={self.status}>"</function_content>
+        return f"<Chore id={self.id} title='{self.title}' status={self.status}>"
diff --git a/backend/app/db/models/screen_time_model.py b/backend/app/db/models/screen_time_model.py
index eb5371c..125c181 100644
--- a/backend/app/db/models/screen_time_model.py
+++ b/backend/app/db/models/screen_time_model.py
@@ -157,7 +157,7 @@ class ScreenTimeUsage(Base):
     # Type of activity if detectable (e.g., "browsing", "watching", "gaming") (optional)
     activity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
     # Flexible JSONB for any other relevant context data (optional)
-    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
+    usage_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
 
     def __repr__(self):
         return f"<ScreenTimeUsage user={self.user_id} app='{self.app_name}' duration={self.duration_seconds}s start={self.start_time}>"
@@ -205,6 +205,8 @@ class ScreenTimeExtensionRequest(Base):
     # Optional note from the responder
     response_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
 
+    # Inside the ScreenTimeExtensionRequest class
+
     def __repr__(self):
-        return f"<ScreenTimeExtensionRequest id={self.id} user={self.user_id} status={self.status} requested={self.requested_minutes}min>"</function_content>
-</invoke>
\ No newline at end of file
+        """String representation for debugging."""
+        return f"<ScreenTimeExtensionRequest id={self.id} user={self.user_id} status={self.status} requested={self.requested_minutes}min>"
\ No newline at end of file
diff --git a/backend/create_tables.sql b/backend/create_tables.sql
new file mode 100644
index 0000000..aee256d
--- /dev/null
+++ b/backend/create_tables.sql
@@ -0,0 +1,104 @@
+-- SQL script to create the initial tables for the Family Wellness database
+
+-- Enable pgvector extension
+CREATE EXTENSION IF NOT EXISTS vector;
+
+-- Create Users table
+CREATE TABLE IF NOT EXISTS "user" (
+    id SERIAL PRIMARY KEY,
+    username VARCHAR(50) UNIQUE NOT NULL,
+    email VARCHAR(100) UNIQUE NOT NULL,
+    hashed_password VARCHAR(100) NOT NULL,
+    is_active BOOLEAN DEFAULT TRUE,
+    is_superuser BOOLEAN DEFAULT FALSE,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create Family table
+CREATE TABLE IF NOT EXISTS family (
+    id SERIAL PRIMARY KEY,
+    name VARCHAR(100) NOT NULL,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create FamilyMember table (relationship between User and Family)
+CREATE TABLE IF NOT EXISTS family_member (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    is_parent BOOLEAN DEFAULT FALSE,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    UNIQUE(user_id, family_id)
+);
+
+-- Create ScreenTimeRule table
+CREATE TABLE IF NOT EXISTS screen_time_rule (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    daily_limit INTEGER NOT NULL, -- in minutes
+    weekly_limit INTEGER NOT NULL, -- in minutes
+    allowed_hours JSONB, -- JSON array of allowed hours
+    allowed_apps JSONB, -- JSON array of allowed apps
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create ScreenTimeUsage table
+CREATE TABLE IF NOT EXISTS screen_time_usage (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    date DATE NOT NULL,
+    minutes_used INTEGER NOT NULL,
+    app_breakdown JSONB, -- JSON of app usage
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create ScreenTimeExtensionRequest table
+CREATE TABLE IF NOT EXISTS screen_time_extension_request (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    requested_minutes INTEGER NOT NULL,
+    reason TEXT,
+    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, denied
+    parent_notes TEXT,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create Chore table
+CREATE TABLE IF NOT EXISTS chore (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    title VARCHAR(100) NOT NULL,
+    description TEXT,
+    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, verified
+    frequency VARCHAR(20), -- daily, weekly, monthly, once
+    due_date TIMESTAMP,
+    completion_date TIMESTAMP,
+    verification_date TIMESTAMP,
+    verified_by INTEGER REFERENCES "user"(id),
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create AIMemory table for vector storage
+CREATE TABLE IF NOT EXISTS ai_memory (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    content TEXT NOT NULL,
+    embedding VECTOR(1536), -- Assuming 1536-dimensional embeddings
+    metadata JSONB,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create index on vector column for similarity search
+CREATE INDEX IF NOT EXISTS ai_memory_embedding_idx ON ai_memory USING ivfflat (embedding vector_l2_ops);
diff --git a/backend/pyproject.toml b/backend/pyproject.toml
index 6a455d2..2311159 100644
--- a/backend/pyproject.toml
+++ b/backend/pyproject.toml
@@ -63,8 +63,9 @@ httpx = "^0.26.0" # Re-listed here as it's also useful for testing APIs
 # Development Workflow
 pre-commit = "^3.6.0"
 
-# Optional: Database Migrations (Highly Recommended for Production)
-# alembic = "^1.13.1"
+# Database Migrations (Required for Production)
+alembic = "^1.15.2"
+pgvector = "^0.2.5" # Python pgvector integration for SQLAlchemy
 
 
 [build-system]
diff --git a/backend/requirements.txt b/backend/requirements.txt
new file mode 100644
index 0000000..848a8a7
--- /dev/null
+++ b/backend/requirements.txt
@@ -0,0 +1,21 @@
+fastapi==0.109.0
+uvicorn[standard]==0.27.0
+strawberry-graphql[fastapi]==0.217.0
+python-multipart==0.0.6
+psycopg[binary,pool]==3.1.16
+sqlalchemy==2.0.25
+langchain==0.1.0
+langchain-community==0.0.13
+httpx==0.26.0
+redis==5.0.1
+celery[redis]==5.3.6
+python-jose[cryptography]==3.3.0
+boto3==1.34.32
+emails==0.6
+pydantic==2.5.3
+pydantic-settings==2.1.0
+zeroconf==0.131.0
+prometheus-client==0.19.0
+circuitbreaker==1.4.0
+alembic==1.15.2
+pgvector==0.2.5
\ No newline at end of file
diff --git a/config/postgres/init-scripts/01_init_pgvector.sql b/config/postgres/init-scripts/01_init_pgvector.sql
new file mode 100644
index 0000000..7e4a1e8
--- /dev/null
+++ b/config/postgres/init-scripts/01_init_pgvector.sql
@@ -0,0 +1,5 @@
+-- Enable pgvector extension
+CREATE EXTENSION IF NOT EXISTS vector;
+
+-- Verify the extension is installed
+SELECT * FROM pg_extension WHERE extname = 'vector';
diff --git a/create_local_db.sh b/create_local_db.sh
old mode 100644
new mode 100755
index 4837df3..9a7a4f7
--- a/create_local_db.sh
+++ b/create_local_db.sh
@@ -5,10 +5,57 @@
 
 echo "Creating family_wellness database in your local PostgreSQL..."
 
+# Check for a master user first, then fall back to system username
+PG_USER="willf"
+PG_PASSWORD=""
+
+# Try to read credentials from .pgpass if it exists
+PGPASS_FILE="/Users/willf/smartIndex/postgresPSQL/credentials/.pgpass"
+if [ -f "$PGPASS_FILE" ]; then
+    echo "Reading credentials from $PGPASS_FILE"
+    MASTER_USER=$(grep "postgres_master" "$PGPASS_FILE" | cut -d: -f4)
+    MASTER_PASSWORD=$(grep "postgres_master" "$PGPASS_FILE" | cut -d: -f5)
+    if [ -n "$MASTER_USER" ] && [ -n "$MASTER_PASSWORD" ]; then
+        PG_USER="$MASTER_USER"
+        PG_PASSWORD="$MASTER_PASSWORD"
+        echo "Using master PostgreSQL user '$PG_USER'"
+        export PGPASSWORD="$PG_PASSWORD"
+    fi
+else
+    echo "Using system username '$PG_USER' for PostgreSQL."
+    
+    # Prompt for password if needed
+    if [ -z "$PGPASSWORD" ]; then
+        read -sp "Enter your PostgreSQL password for user '$PG_USER' (press Enter for no password): " PGPASS
+        echo ""
+        export PGPASSWORD="$PGPASS"
+        PG_PASSWORD="$PGPASS"
+    fi
+fi
+
 # Create the database if it doesn't exist
-psql -U postgres -h localhost -c "CREATE DATABASE family_wellness;" || echo "Database may already exist, continuing..."
+psql -U "$PG_USER" -h localhost -c "CREATE DATABASE family_wellness;" || echo "Database may already exist, continuing..."
 
 # Install pgvector extension (required for AI memory vectors)
-psql -U postgres -h localhost -d family_wellness -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "Failed to create vector extension. Please ensure pgvector is installed in your PostgreSQL instance."
+psql -U "$PG_USER" -h localhost -d family_wellness -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "Failed to create vector extension. Please ensure pgvector is installed in your PostgreSQL instance."
+
+# Update the backend/.env file with the password and username if it exists
+if [ -f "./backend/.env" ]; then
+    # Write a new .env file with the correct credentials
+    echo "# Local development environment variables for backend" > ./backend/.env
+    echo "# This file is used when running Alembic commands directly on your host machine" >> ./backend/.env
+    echo "" >> ./backend/.env
+    echo "# Database connection for local development" >> ./backend/.env
+    echo "DATABASE_URL=postgresql+psycopg://$PG_USER:$PG_PASSWORD@localhost:5432/family_wellness" >> ./backend/.env
+    echo "Updated backend/.env with your database credentials."
+fi
+
+# Update alembic.ini to use the correct username for local development
+sed -i.bak "s|sqlalchemy.url = postgresql+psycopg://postgres:password@localhost:5432/family_wellness|sqlalchemy.url = postgresql+psycopg://$PG_USER:$PG_PASSWORD@localhost:5432/family_wellness|" ./backend/alembic.ini && rm ./backend/alembic.ini.bak
 
 echo "Database setup complete. Now you can run the migration script."
+echo "To run migrations locally, cd into the backend directory and run: poetry run alembic upgrade head"
+echo "To run migrations in Docker, use: ./run_migrations_docker.sh upgrade"
+
+# Clear the password from environment for security
+unset PGPASSWORD
diff --git a/create_migration.sh b/create_migration.sh
index 3396269..80a68d3 100755
--- a/create_migration.sh
+++ b/create_migration.sh
@@ -1,16 +1,71 @@
 #!/bin/bash
 
-# Change to the backend directory
-cd /Users/willf/smartIndex/epicforesters/localai-family-wellness/backend
+# Script to create a new migration either locally or with Docker
 
-# Generate the initial migration
-alembic revision --autogenerate -m "Initial schema"
+# Default migration message
+MIGRATION_MSG="Schema update"
 
-# If the previous command succeeded, apply the migration
-if [ $? -eq 0 ]; then
-    echo "Migration created successfully. Now applying migration..."
-    alembic upgrade head
-    echo "Database migration complete."
+# Parse command line arguments
+USE_DOCKER=false
+
+while [[ $# -gt 0 ]]; do
+  case $1 in
+    -m|--message)
+      MIGRATION_MSG="$2"
+      shift 2
+      ;;
+    -d|--docker)
+      USE_DOCKER=true
+      shift
+      ;;
+    -l|--local)
+      USE_DOCKER=false
+      shift
+      ;;
+    -h|--help)
+      echo "Usage: $0 [options]"
+      echo "Options:"
+      echo "  -m, --message MESSAGE  Set migration message (default: 'Schema update')"
+      echo "  -d, --docker           Run with Docker (recommended)"
+      echo "  -l, --local            Run locally"
+      echo "  -h, --help             Show this help message"
+      exit 0
+      ;;
+    *)
+      echo "Unknown option: $1"
+      exit 1
+      ;;
+  esac
+done
+
+if [ "$USE_DOCKER" = true ]; then
+    echo "Creating migration with Docker: \"$MIGRATION_MSG\""
+    ./run_migrations_docker.sh revision "$MIGRATION_MSG"
+    
+    echo "Apply this migration? [y/N]"
+    read -r APPLY
+    if [[ $APPLY =~ ^[Yy]$ ]]; then
+        ./run_migrations_docker.sh upgrade
+    fi
 else
-    echo "Failed to create migration. Check the error messages above."
+    # Change to the backend directory
+    cd "$(dirname "$0")/backend" || exit 1
+    
+    echo "Creating local migration: \"$MIGRATION_MSG\""
+    poetry run alembic revision --autogenerate -m "$MIGRATION_MSG"
+    
+    # If the previous command succeeded, ask to apply the migration
+    if [ $? -eq 0 ]; then
+        echo "Migration created successfully."
+        echo "Apply this migration? [y/N]"
+        read -r APPLY
+        if [[ $APPLY =~ ^[Yy]$ ]]; then
+            poetry run alembic upgrade head
+            echo "Database migration applied."
+        else
+            echo "Migration created but not applied."
+        fi
+    else
+        echo "Failed to create migration. Check the error messages above."
+    fi
 fi
diff --git a/direct_migrations.sh b/direct_migrations.sh
new file mode 100755
index 0000000..2e8665e
--- /dev/null
+++ b/direct_migrations.sh
@@ -0,0 +1,34 @@
+#!/bin/bash
+# Script to run Alembic migrations directly using the postgres container
+# without requiring Redis or the backend container
+
+# Check if postgres container is running
+if ! docker compose ps | grep -q "localai-postgres.*running"; then
+    echo "PostgreSQL container is not running. Starting it..."
+    docker compose up -d postgres
+    # Give PostgreSQL time to initialize
+    sleep 5
+fi
+
+# Get the backend image ID to use for our temporary container
+BACKEND_IMAGE=$(docker compose images backend -q)
+if [ -z "$BACKEND_IMAGE" ]; then
+    echo "Building backend image..."
+    docker compose build backend
+    BACKEND_IMAGE=$(docker compose images backend -q)
+fi
+
+# Read password from .env file
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+
+# Run a temporary container using the backend image to execute Alembic commands
+echo "Running Alembic migration command: $@"
+docker run --rm \
+    --network localai-family-wellness_database-net \
+    -v "$(pwd)/backend:/app" \
+    -w /app \
+    -e DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@postgres:5432/family_wellness" \
+    $BACKEND_IMAGE \
+    bash -c "pip install alembic && alembic $*"
+
+echo "Migration operation completed."
diff --git a/docker-compose.override.yml b/docker-compose.override.yml
new file mode 100644
index 0000000..d90e512
--- /dev/null
+++ b/docker-compose.override.yml
@@ -0,0 +1,7 @@
+# Override file for docker-compose.yml
+# This file adds port forwarding for PostgreSQL to enable local development
+
+services:
+  postgres:
+    ports:
+      - "5432:5432"  # Forward PostgreSQL port to host
diff --git a/docker-compose.yml b/docker-compose.yml
index 9c8ee22..efa3aec 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -1,5 +1,4 @@
 # docker-compose.yml (Version 1.1 - Enhanced Security - COMPLETE FILE)
-version: '3.8'
 
 # Define networks for service isolation
 networks:
@@ -29,8 +28,9 @@ volumes:
 services:
   # Database: PostgreSQL with pgvector and TimescaleDB extensions
   postgres:
-    # Using Timescale image. Assumes init script in volume below will create pgvector.
-    image: timescale/timescaledb-ha:pg15-latest
+    # Use a PostgreSQL image with pgvector pre-installed
+    image: pgvector/pgvector:pg15
+    platform: linux/arm64
     container_name: localai-postgres
     restart: unless-stopped
     environment:
@@ -40,13 +40,12 @@ services:
     volumes:
       - postgres-data:/var/lib/postgresql/data
       # Mounts local init script(s) into the container's initialization directory.
-      # User MUST create ./config/postgres/init-scripts/init-pgvector.sql with CREATE EXTENSION command.
       - ./config/postgres/init-scripts:/docker-entrypoint-initdb.d
     networks:
       - database-net
     healthcheck:
-      # Use $$ to escape $ for shell evaluation inside docker-compose
-      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
+      # Use $ to escape $ for shell evaluation inside docker-compose
+      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
       interval: 10s
       timeout: 5s
       retries: 5
@@ -130,15 +129,16 @@ services:
     image: redis:alpine
     container_name: localai-redis
     restart: unless-stopped
+    platform: linux/arm64
     # Added password requirement
-    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} # Defined in .env
+    command: redis-server --appendonly yes --requirepass "${REDIS_PASSWORD}"
     volumes:
       - redis-data:/data
     networks:
       - backend-net
     healthcheck:
-      # Added password to healthcheck ping
-      test: ["CMD", "redis-cli", "-a", "$${REDIS_PASSWORD}", "ping"] # Use $$ to escape $
+      # Include authentication for healthcheck
+      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
       interval: 10s
       timeout: 5s
       retries: 3
@@ -317,60 +317,3 @@ services:
         condition: service_healthy
       # backend: # Only if it DIRECTLY calls the backend API, often not needed
       #   condition: service_started
-
-  # --- Add other tool server definitions here following the pattern above ---
-  # --- Example structure: ---
-  # communication-tool:
-  #   build:
-  #     context: ./tool-servers/communication-tool
-  #     dockerfile: Dockerfile
-  #   container_name: localai-comm-tool
-  #   restart: unless-stopped
-  #   environment:
-  #     # Add necessary env vars from .env (e.g., SMTP details, NTFY details)
-  #     NTFY_URL: http://ntfy
-  #     SMTP_HOST: ${SMTP_HOST}
-  #     SMTP_PORT: ${SMTP_PORT}
-  #     SMTP_USER: ${SMTP_USER}
-  #     SMTP_PASSWORD: ${SMTP_PASSWORD}
-  #     SMTP_SENDER_EMAIL: ${SMTP_SENDER_EMAIL}
-  #   volumes:
-  #     - ./tool-servers/communication-tool:/app
-  #   networks:
-  #     - backend-net
-  #   depends_on:
-  #     - ntfy
-
-  # file-tool:
-  #   build:
-  #     context: ./tool-servers/file-tool
-  #     dockerfile: Dockerfile
-  #   container_name: localai-file-tool
-  #   restart: unless-stopped
-  #   environment:
-  #     MINIO_ENDPOINT: minio:9000
-  #     MINIO_USE_SSL: "false"
-  #     MINIO_ACCESS_KEY: ${MINIO_APP_ACCESS_KEY} # Uses App Key
-  #     MINIO_SECRET_KEY: ${MINIO_APP_SECRET_KEY} # Uses App Key
-  #   volumes:
-  #     - ./tool-servers/file-tool:/app
-  #   networks:
-  #     - backend-net
-  #   depends_on:
-  #     - minio
-
-  # chore-tool:
-  #   build:
-  #     context: ./tool-servers/chore-tool
-  #     dockerfile: Dockerfile
-  #   container_name: localai-chore-tool
-  #   restart: unless-stopped
-  #   environment:
-  #     DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
-  #   volumes:
-  #     - ./tool-servers/chore-tool:/app
-  #   networks:
-  #     - backend-net
-  #     - database-net
-  #   depends_on:
-  #     - postgres
\ No newline at end of file
diff --git a/docs/MIGRATION_GUIDE.md b/docs/MIGRATION_GUIDE.md
new file mode 100644
index 0000000..a201e1f
--- /dev/null
+++ b/docs/MIGRATION_GUIDE.md
@@ -0,0 +1,120 @@
+# Database Migration Guide
+
+This guide explains two methods for managing database migrations for the LocalAI Family Wellness Platform:
+
+1. **Docker-based migrations** (using `migrate.sh`)
+2. **Local development migrations** (using `local_migrate.sh`)
+
+Both approaches use Alembic under the hood but operate in different environments.
+
+## Docker-based Migrations (Recommended for Consistency)
+
+The `migrate.sh` script runs Alembic commands in a Docker container, ensuring consistency with your production environment.
+
+### Prerequisites
+- Docker and Docker Compose installed
+- The PostgreSQL container running
+
+### Basic Commands
+
+```bash
+# Generate a new migration
+./migrate.sh generate "Description of changes"
+
+# Apply migrations
+./migrate.sh upgrade
+
+# Check migration status
+./migrate.sh status
+
+# See migration history
+./migrate.sh history
+
+# View current migration version
+./migrate.sh current
+```
+
+## Local Development Migrations (Using Poetry)
+
+The `local_migrate.sh` script runs Alembic on your local machine using Poetry, requiring local dependencies but offering faster execution.
+
+### Prerequisites
+- Poetry installed
+- PostgreSQL accessible from your local machine
+- Required Python dependencies installed (`poetry install`)
+
+### Basic Commands
+
+```bash
+# Generate a new migration
+./local_migrate.sh generate "Description of changes"
+
+# Apply migrations
+./local_migrate.sh upgrade
+
+# Check migration status
+./local_migrate.sh status
+
+# See migration history
+./local_migrate.sh history
+
+# View current migration version
+./local_migrate.sh current
+```
+
+### Local Configuration
+
+For local development, create a `.env.local` file in the `backend` directory with your database connection information:
+
+```
+DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/family_wellness
+```
+
+## Common Workflow
+
+1. Make changes to your SQLAlchemy models in `app/db/models/`
+2. Generate a migration:
+   ```bash
+   ./migrate.sh generate "Description of your model changes"
+   ```
+3. Review the generated migration in `backend/alembic/versions/`
+4. Apply the migration:
+   ```bash
+   ./migrate.sh upgrade
+   ```
+
+## Troubleshooting
+
+### Docker Network Issues
+If the Docker migration script can't connect to PostgreSQL, verify the container is running:
+```bash
+docker compose ps
+```
+
+### Local Connection Issues
+If the local script can't connect to PostgreSQL:
+1. Check if PostgreSQL port is exposed in `docker-compose.yml`
+2. Verify the connection string in `.env.local`
+3. Make sure your local machine can connect to the Docker container
+
+### Migration Conflicts
+If you get migration conflicts:
+1. Check the current database state: `./migrate.sh current`
+2. Compare with the available migrations: `./migrate.sh history`
+3. Correct any discrepancies by upgrading or downgrading to a specific revision
+
+## Initial Setup
+
+For the initial setup of your database:
+
+```bash
+# Using Docker
+./migrate.sh generate "Initial schema"
+./migrate.sh upgrade
+
+# Or using local Poetry
+./local_migrate.sh generate "Initial schema"
+./local_migrate.sh upgrade
+```
+
+These commands will create all database tables based on your SQLAlchemy models.
diff --git a/docs/alembic_migrations_guide.md b/docs/alembic_migrations_guide.md
new file mode 100644
index 0000000..c45fc50
--- /dev/null
+++ b/docs/alembic_migrations_guide.md
@@ -0,0 +1,129 @@
+# Alembic Migrations Guide for LocalAI Family Wellness Platform
+
+This guide explains how to use Alembic for database migrations in both local development and Docker environments.
+
+## Overview
+
+Alembic is used to manage database schema changes. It allows you to:
+
+1. Create migrations based on changes to your SQLAlchemy models
+2. Apply migrations to update your database schema
+3. Revert migrations when needed
+4. Track migration history
+
+## Setup
+
+The project has been configured to work with Alembic in two ways:
+
+1. **Within Docker**: Run Alembic commands inside the backend container
+2. **Locally**: Run Alembic commands directly on your development machine
+
+## Option A: Running Migrations in Docker (Recommended)
+
+This is the preferred method as it ensures consistency with your Docker environment.
+
+### Prerequisites
+
+1. Docker and Docker Compose installed
+2. Docker services started: `docker compose up -d backend postgres`
+
+### Running Migrations
+
+We've created a script to simplify running Alembic commands in Docker:
+
+```bash
+# Create a new migration
+./run_migrations_docker.sh revision "Your migration message"
+
+# Apply all pending migrations
+./run_migrations_docker.sh upgrade
+
+# Revert the last migration
+./run_migrations_docker.sh downgrade
+
+# Show migration history
+./run_migrations_docker.sh history
+
+# Show current migration version
+./run_migrations_docker.sh current
+
+# Check for pending migrations
+./run_migrations_docker.sh check
+```
+
+## Option B: Running Migrations Locally
+
+This approach is useful for local development without Docker.
+
+### Prerequisites
+
+1. Local PostgreSQL with pgvector installed
+2. Local database created: `./create_local_db.sh`
+3. Poetry installed for dependency management
+
+### Setup Local Environment
+
+1. Ensure PostgreSQL is running on your local machine
+2. Run `./create_local_db.sh` to set up the local database
+3. Make sure `backend/.env` has the correct database credentials
+
+### Running Migrations Locally
+
+```bash
+# Navigate to the backend directory
+cd backend
+
+# Create a new migration
+poetry run alembic revision --autogenerate -m "Your migration message"
+
+# Apply all pending migrations
+poetry run alembic upgrade head
+
+# Revert the last migration
+poetry run alembic downgrade -1
+```
+
+## Migration File Structure
+
+Migrations are stored in `backend/alembic/versions/`. Each migration file contains:
+
+- `upgrade()`: Changes to apply when migrating forward
+- `downgrade()`: Changes to apply when reverting the migration
+
+## Best Practices
+
+1. **Always review auto-generated migrations** before applying them. Alembic can miss certain changes or generate incorrect SQL.
+
+2. **Add migrations to version control** to ensure consistent database schema across development environments.
+
+3. **Test migrations** before applying them to production.
+
+4. **Backup your database** before applying migrations in production.
+
+## Troubleshooting
+
+### Connection Issues
+
+- **When using Docker**: Make sure the backend container can connect to the postgres service.
+- **When running locally**: Verify your local PostgreSQL server is running and accessible.
+
+### Alembic Configuration
+
+The key files for Alembic configuration are:
+
+- `backend/alembic.ini`: Contains the base configuration for Alembic
+- `backend/alembic/env.py`: Contains the Python environment for Alembic, including database connection logic
+
+### Dependency Errors
+
+If you encounter dependency errors when running Alembic locally, ensure you've installed all dependencies:
+
+```bash
+cd backend
+poetry install
+```
+
+## Additional Resources
+
+- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
+- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
diff --git a/fix_version.sh b/fix_version.sh
new file mode 100755
index 0000000..e859093
--- /dev/null
+++ b/fix_version.sh
@@ -0,0 +1,7 @@
+#!/bin/bash
+# Script to fix the version line in docker-compose.yml
+
+# Remove the 'version' line from docker-compose.yml
+sed -i.bak '/^version:/d' docker-compose.yml && rm docker-compose.yml.bak
+
+echo "Removed 'version:' line from docker-compose.yml"
diff --git a/local_migrate.sh b/local_migrate.sh
new file mode 100755
index 0000000..227aba7
--- /dev/null
+++ b/local_migrate.sh
@@ -0,0 +1,47 @@
+#!/bin/bash
+# Script for local development migrations using Poetry
+
+# Ensure proper error handling
+set -e
+
+# Command can be "generate", "upgrade", or other alembic commands
+COMMAND=${1:-"status"}
+# Message for migration (only used with generate command)
+MESSAGE=${2:-"Migration update"}
+
+# Navigate to backend directory
+cd "$(dirname "$0")/backend"
+
+# Set up DATABASE_URL that connects to the Docker container through localhost
+# This assumes you've forwarded the PostgreSQL port in your docker-compose.yml (which we'll add separately)
+export DATABASE_URL="postgresql+psycopg://postgres:change_this_password@localhost:5432/family_wellness"
+
+# Load from .env.local if it exists
+if [ -f .env.local ]; then
+  source .env.local
+fi
+
+echo "Using DATABASE_URL: $DATABASE_URL"
+
+# Run alembic command with Poetry
+if [ "$COMMAND" == "generate" ]; then
+  echo "Generating new migration with message: '$MESSAGE'"
+  poetry run alembic revision --autogenerate -m "$MESSAGE"
+  echo "Migration file created. Review it before applying."
+elif [ "$COMMAND" == "upgrade" ]; then
+  echo "Applying migrations to latest version..."
+  poetry run alembic upgrade head
+  echo "Migrations applied successfully."
+elif [ "$COMMAND" == "current" ]; then
+  echo "Current database revision:"
+  poetry run alembic current
+elif [ "$COMMAND" == "history" ]; then
+  echo "Migration history:"
+  poetry run alembic history
+elif [ "$COMMAND" == "status" ]; then
+  echo "Checking migration status..."
+  poetry run alembic check || echo "Pending migrations exist"
+else
+  echo "Running alembic $COMMAND..."
+  poetry run alembic $COMMAND
+fi
diff --git a/make_executable.sh b/make_executable.sh
new file mode 100755
index 0000000..4d9f696
--- /dev/null
+++ b/make_executable.sh
@@ -0,0 +1,4 @@
+#!/bin/bash
+# Make migration script executable
+chmod +x migrate.sh
+echo "Made migrate.sh executable"
diff --git a/manual_migration.sh b/manual_migration.sh
new file mode 100755
index 0000000..7646240
--- /dev/null
+++ b/manual_migration.sh
@@ -0,0 +1,24 @@
+#!/bin/bash
+# Script to manually set up the database tables without using Alembic
+
+# Ensure PostgreSQL container is running
+if ! docker compose ps | grep -q "localai-postgres.*running"; then
+    echo "Starting PostgreSQL container..."
+    docker compose up -d postgres
+    sleep 5
+fi
+
+# Read PostgreSQL password from .env
+POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)
+
+echo "Creating database if it doesn't exist..."
+docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists."
+
+echo "Creating database schema using SQL script..."
+
+# Execute the SQL script directly in the PostgreSQL container
+docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql
+
+echo "Database schema created successfully."
diff --git a/migrate.sh b/migrate.sh
new file mode 100755
index 0000000..7c11c48
--- /dev/null
+++ b/migrate.sh
@@ -0,0 +1,98 @@
+#!/bin/bash
+
+# Script to manage database migrations using Alembic, executed
+# inside the running backend Docker container via 'docker compose exec'.
+
+set -e # Exit immediately if a command exits with a non-zero status.
+
+# --- Configuration ---
+# Service names defined in your docker-compose.yml
+DB_CONTAINER_NAME="localai-postgres"
+BACKEND_CONTAINER_NAME="localai-backend"
+# Read DB name/user from .env file (ensure .env exists in project root)
+# Source the .env file to load variables into the script's environment
+if [ -f .env ]; then
+    set -a
+    . .env
+    set +a
+else
+    echo "Error: .env file not found in project root!"
+    exit 1
+fi
+DB_NAME="${POSTGRES_DB:-localai_family}" # Use value from .env or default
+DB_USER="${POSTGRES_USER:-postgres}"
+
+# --- Command Handling ---
+# Default command is 'status' if no argument provided
+COMMAND=${1:-"status"}
+# Migration message (only used for 'generate'/'revision' command)
+MESSAGE=${2:-"Alembic migration"}
+
+# --- Pre-checks ---
+echo "--> Checking if required Docker services are running..."
+# Check if Postgres container is running and healthy
+if ! docker compose ps -q --filter "name=$DB_CONTAINER_NAME" --filter "health=healthy" | grep -q .; then
+    echo "PostgreSQL container ($DB_CONTAINER_NAME) is not running or not healthy."
+    echo "Attempting to start required services..."
+    docker compose up -d postgres backend # Start both DB and Backend
+    echo "Waiting for services to potentially become healthy..."
+    sleep 15 # Give services time to start and potentially pass healthchecks
+    # Re-check health after waiting
+    if ! docker compose ps -q --filter "name=$DB_CONTAINER_NAME" --filter "health=healthy" | grep -q .; then
+        echo "Error: PostgreSQL container ($DB_CONTAINER_NAME) did not become healthy after starting."
+        echo "Check Docker logs:"
+        docker compose logs "$DB_CONTAINER_NAME"
+        exit 1
+    fi
+else
+    echo "PostgreSQL container is healthy."
+fi
+
+# Check if Backend container is running (needed for exec)
+if ! docker compose ps -q --filter "name=$BACKEND_CONTAINER_NAME" --filter "status=running" | grep -q .; then
+     echo "Error: Backend container ($BACKEND_CONTAINER_NAME) is not running. Cannot execute Alembic."
+     echo "Attempt to start it with 'docker compose up -d backend'"
+     exit 1
+fi
+echo "Backend container is running."
+
+
+# --- Ensure pgvector Extension ---
+# Although the init script should handle this, an explicit check here adds robustness.
+echo "--> Ensuring pgvector extension exists in database '$DB_NAME'..."
+docker compose exec -T "$DB_CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
+if [ $? -ne 0 ]; then echo "Error: Failed command to ensure pgvector extension exists."; exit 1; fi
+echo "pgvector extension check/creation successful."
+
+
+# --- Execute Alembic Command ---
+echo "--> Running 'alembic $COMMAND' inside container '$BACKEND_CONTAINER_NAME'..."
+
+# Prepare Alembic command arguments
+ALEMBIC_CMD="alembic"
+
+if [ "$COMMAND" == "generate" ] || [ "$COMMAND" == "revision" ]; then
+    # Use 'revision --autogenerate' for generation
+    ALEMBIC_CMD="$ALEMBIC_CMD revision --autogenerate -m \"$MESSAGE\""
+elif [ "$COMMAND" == "upgrade" ] || [ "$COMMAND" == "downgrade" ]; then
+    # Append revision target (e.g., 'head', 'base', specific revision ID) if provided
+    REVISION_TARGET=${2:-"head"} # Default to 'head' for upgrade if no target specified
+    ALEMBIC_CMD="$ALEMBIC_CMD $COMMAND $REVISION_TARGET"
+else
+    # For other commands like status, current, history, just pass them through
+    ALEMBIC_CMD="$ALEMBIC_CMD $COMMAND"
+fi
+
+# Execute the assembled Alembic command inside the backend container
+docker compose exec "$BACKEND_CONTAINER_NAME" $ALEMBIC_CMD
+
+# Check exit status
+if [ $? -ne 0 ]; then
+    echo "Error: Alembic command '$ALEMBIC_CMD' failed."
+    echo "Check output above and backend container logs if necessary:"
+    # docker compose logs "$BACKEND_CONTAINER_NAME" # Uncomment to see logs on failure
+    exit 1
+fi
+
+echo "✅ Alembic command '$ALEMBIC_CMD' executed successfully!"
+exit 0
\ No newline at end of file
diff --git a/poetry_migrations.sh b/poetry_migrations.sh
new file mode 100755
index 0000000..863ade7
--- /dev/null
+++ b/poetry_migrations.sh
@@ -0,0 +1,31 @@
+#!/bin/bash
+# Script to run Alembic migrations using Poetry in the backend directory
+
+# First make sure Postgres is running
+if ! docker compose ps | grep -q "localai-postgres.*running"; then
+    echo "Starting PostgreSQL container..."
+    docker compose up -d postgres
+    sleep 5
+fi
+
+# Read PostgreSQL password from .env
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+
+# Change to the backend directory
+cd backend
+
+# Set up environment variables for the migration
+export DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/family_wellness"
+
+# Check if Poetry is installed
+if ! command -v poetry &> /dev/null; then
+    echo "Poetry is not installed. Please install it first."
+    echo "You can install it with: curl -sSL https://install.python-poetry.org | python3 -"
+    exit 1
+fi
+
+# Run the migration command with Poetry
+echo "Running migration command: $@"
+poetry run alembic "$@"
+
+echo "Migration operation completed."
diff --git a/postgres_migrations.sh b/postgres_migrations.sh
new file mode 100644
index 0000000..084c5c4
--- /dev/null
+++ b/postgres_migrations.sh
@@ -0,0 +1,40 @@
+#!/bin/bash
+# Script to run Alembic migrations directly using the postgres container
+# without requiring the backend container
+
+# Ensure PostgreSQL container is running
+if ! docker compose ps | grep -q "localai-postgres"; then
+    echo "PostgreSQL container is not running. Starting it..."
+    docker compose up -d postgres
+    # Give some time for services to initialize
+    sleep 5
+fi
+
+# Check if the container exists before proceeding
+if ! docker compose ps | grep -q "localai-postgres"; then
+    echo "ERROR: PostgreSQL container failed to start or is not found."
+    exit 1
+fi
+
+# Ensure PostgreSQL is running and healthy
+echo "Checking PostgreSQL connection..."
+if ! docker compose exec postgres psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
+    echo "ERROR: Cannot connect to PostgreSQL. Please check if it's running properly."
+    exit 1
+fi
+
+# Check if the database exists, create if needed
+echo "Ensuring database exists..."
+docker compose exec postgres psql -U postgres -c "CREATE DATABASE family_wellness;" > /dev/null 2>&1 || echo "Database already exists."
+
+# Create a temporary container to run Alembic migrations
+echo "Creating temporary container for migrations..."
+docker run --rm \
+    --network localai-family-wellness_database-net \
+    -v "$(pwd)/backend:/app" \
+    -w /app \
+    -e DATABASE_URL="postgresql+psycopg://postgres:${POSTGRES_PASSWORD:-change_this_password}@postgres:5432/family_wellness" \
+    $(docker compose images backend -q) \
+    alembic "$@"
+
+echo "Migration operation completed."
diff --git a/run_migrations_docker.sh b/run_migrations_docker.sh
new file mode 100755
index 0000000..dbd7c10
--- /dev/null
+++ b/run_migrations_docker.sh
@@ -0,0 +1,54 @@
+#!/bin/bash
+# Script to run Alembic migrations inside Docker
+
+# Ensure Docker containers are running
+if ! docker compose ps | grep -q "localai-backend"; then
+    echo "Backend container is not running. Starting Docker services..."
+    docker compose up -d backend postgres
+    # Give some time for services to initialize
+    sleep 10
+fi
+
+# Check if the container exists before proceeding
+if ! docker compose ps | grep -q "localai-backend"; then
+    echo "ERROR: Backend container failed to start or is not found."
+    exit 1
+fi
+
+# Parse command line arguments
+if [ "$1" == "revision" ]; then
+    # Create a new migration (autogenerate)
+    if [ -z "$2" ]; then
+        echo "ERROR: Missing migration message. Usage: ./run_migrations_docker.sh revision \"Your migration message\""
+        exit 1
+    fi
+    docker compose exec backend alembic revision --autogenerate -m "$2"
+elif [ "$1" == "upgrade" ]; then
+    # Default to 'head' if no specific version is provided
+    TARGET=${2:-head}
+    docker compose exec backend alembic upgrade $TARGET
+elif [ "$1" == "downgrade" ]; then
+    # Default to -1 if no specific version is provided
+    TARGET=${2:--1}
+    docker compose exec backend alembic downgrade $TARGET
+elif [ "$1" == "history" ]; then
+    # Show migration history
+    docker compose exec backend alembic history
+elif [ "$1" == "current" ]; then
+    # Show current migration version
+    docker compose exec backend alembic current
+elif [ "$1" == "check" ]; then
+    # Check if there are any changes to migrate
+    docker compose exec backend alembic check
+else
+    echo "Usage:"
+    echo "  ./run_migrations_docker.sh revision \"Your migration message\"  # Create a new migration"
+    echo "  ./run_migrations_docker.sh upgrade [target]                     # Apply migrations (default: head)"
+    echo "  ./run_migrations_docker.sh downgrade [target]                   # Revert migrations (default: -1)"
+    echo "  ./run_migrations_docker.sh history                              # Show migration history"
+    echo "  ./run_migrations_docker.sh current                              # Show current migration version"
+    echo "  ./run_migrations_docker.sh check                                # Check for pending migrations"
+    exit 1
+fi
+
+echo "Migration operation completed."
diff --git a/setup_database.sh b/setup_database.sh
new file mode 100755
index 0000000..0257e76
--- /dev/null
+++ b/setup_database.sh
@@ -0,0 +1,29 @@
+#!/bin/bash
+# Script to set up the database schema manually
+
+# Ensure PostgreSQL container is running
+if ! docker compose ps | grep -q "localai-postgres.*running"; then
+    echo "Starting PostgreSQL container..."
+    docker compose up -d postgres
+    sleep 5
+fi
+
+# Read PostgreSQL config from .env
+POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)
+
+echo "Setting up database: $POSTGRES_DB"
+
+# Create database if it doesn't exist
+echo "Step 1: Creating database if it doesn't exist..."
+docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists."
+
+# Execute the SQL script to create tables
+echo "Step 2: Creating database schema using SQL script..."
+docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql
+
+echo "✅ Database setup completed successfully!"
+echo
+echo "The following tables were created:"
+docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
diff --git a/setup_database_complete.sh b/setup_database_complete.sh
new file mode 100644
index 0000000..5a8de3e
--- /dev/null
+++ b/setup_database_complete.sh
@@ -0,0 +1,138 @@
+#!/bin/bash
+# Complete database setup script with pgvector support
+
+# Ensure PostgreSQL container is running
+if ! docker compose ps | grep -q "localai-postgres.*running"; then
+    echo "Starting PostgreSQL container..."
+    docker compose up -d postgres
+    sleep 5
+fi
+
+# Read PostgreSQL config from .env
+POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)
+
+echo "Setting up database: $POSTGRES_DB"
+
+# Create database if it doesn't exist
+echo "Step 1: Creating database if it doesn't exist..."
+docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists."
+
+# Create a version of the SQL script without pgvector dependencies
+echo "Step 2: Creating modified SQL script without pgvector dependencies..."
+cat > ./backend/create_tables_no_pgvector.sql << 'EOF'
+-- SQL script to create the initial tables for the Family Wellness database
+
+-- Create Users table
+CREATE TABLE IF NOT EXISTS "user" (
+    id SERIAL PRIMARY KEY,
+    username VARCHAR(50) UNIQUE NOT NULL,
+    email VARCHAR(100) UNIQUE NOT NULL,
+    hashed_password VARCHAR(100) NOT NULL,
+    is_active BOOLEAN DEFAULT TRUE,
+    is_superuser BOOLEAN DEFAULT FALSE,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create Family table
+CREATE TABLE IF NOT EXISTS family (
+    id SERIAL PRIMARY KEY,
+    name VARCHAR(100) NOT NULL,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create FamilyMember table (relationship between User and Family)
+CREATE TABLE IF NOT EXISTS family_member (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    is_parent BOOLEAN DEFAULT FALSE,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    UNIQUE(user_id, family_id)
+);
+
+-- Create ScreenTimeRule table
+CREATE TABLE IF NOT EXISTS screen_time_rule (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    daily_limit INTEGER NOT NULL, -- in minutes
+    weekly_limit INTEGER NOT NULL, -- in minutes
+    allowed_hours JSONB, -- JSON array of allowed hours
+    allowed_apps JSONB, -- JSON array of allowed apps
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create ScreenTimeUsage table
+CREATE TABLE IF NOT EXISTS screen_time_usage (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    date DATE NOT NULL,
+    minutes_used INTEGER NOT NULL,
+    app_breakdown JSONB, -- JSON of app usage
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create ScreenTimeExtensionRequest table
+CREATE TABLE IF NOT EXISTS screen_time_extension_request (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    requested_minutes INTEGER NOT NULL,
+    reason TEXT,
+    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, denied
+    parent_notes TEXT,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create Chore table
+CREATE TABLE IF NOT EXISTS chore (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    title VARCHAR(100) NOT NULL,
+    description TEXT,
+    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, verified
+    frequency VARCHAR(20), -- daily, weekly, monthly, once
+    due_date TIMESTAMP,
+    completion_date TIMESTAMP,
+    verification_date TIMESTAMP,
+    verified_by INTEGER REFERENCES "user"(id),
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Create simplified AIMemory table without vector storage
+CREATE TABLE IF NOT EXISTS ai_memory (
+    id SERIAL PRIMARY KEY,
+    family_id INTEGER REFERENCES family(id) ON DELETE CASCADE,
+    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
+    content TEXT NOT NULL,
+    embedding_json JSONB, -- Store embedding as JSON array instead of vector type
+    metadata JSONB,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+EOF
+
+# Execute the SQL script to create tables
+echo "Step 3: Creating database schema using modified SQL script..."
+docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables_no_pgvector.sql
+
+echo "✅ Database setup completed successfully!"
+echo
+echo "The following tables were created:"
+docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
+
+echo
+echo "NOTE: The pgvector extension is not installed in this PostgreSQL container."
+echo "To enable vector embeddings with pgvector, you'll need to modify your Docker setup."
+echo "For local development, you can use the simplified schema with JSON embeddings."
+echo "For production, ensure your PostgreSQL installation includes pgvector."
diff --git a/setup_pgvector.sh b/setup_pgvector.sh
new file mode 100755
index 0000000..57a953e
--- /dev/null
+++ b/setup_pgvector.sh
@@ -0,0 +1,30 @@
+#!/bin/bash
+# Script to set up PostgreSQL with pgvector and initialize the database schema
+
+echo "Step 1: Stopping existing PostgreSQL container..."
+docker compose stop postgres
+docker compose rm -f postgres
+
+echo "Step 2: Starting PostgreSQL with pgvector support..."
+docker compose up -d postgres
+echo "Waiting for PostgreSQL to initialize..."
+sleep 10
+
+# Read PostgreSQL config from .env
+POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2)
+POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2)
+POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2)
+
+echo "Step 3: Creating database if it doesn't exist..."
+docker compose exec postgres psql -U ${POSTGRES_USER} -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database already exists or there was an issue creating it."
+
+echo "Step 4: Verifying pgvector extension..."
+docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT * FROM pg_extension WHERE extname = 'vector';"
+
+echo "Step 5: Creating database schema..."
+docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < ./backend/create_tables.sql
+
+echo "✅ Database setup with pgvector completed successfully!"
+echo
+echo "The following tables were created:"
+docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
