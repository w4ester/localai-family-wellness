# LocalAI Family Wellness Platform

A local, safe, and free stateful AI family wellness platform.

## Getting Started

### 1. Setting Up the Development Environment

Make sure you have the following installed:
- Python 3.11+
- Docker and Docker Compose
- Node.js (for frontend development)

### 2. Environment Configuration

1. Create a `.env` file in the project root based on the `.env.example`:
   ```bash
   cp backend/.env.example .env
   ```

2. Update the `.env` file with appropriate values for your local development.

### 3. Initial Database Migration

1. Make the migration script executable:
   ```bash
   chmod +x create_migration.sh
   ```

2. Run the migration script:
   ```bash
   ./create_migration.sh
   ```

This will create and apply the initial database migration.

### 4. Running the Application

Start the application using Docker Compose:
```bash
docker-compose up -d
```

## Project Structure

- `backend/`: FastAPI backend application
  - `app/`: Main application code
    - `api/`: API endpoints
    - `db/`: Database models and session management
    - `schemas/`: Pydantic schemas for API validation
    - `crud/`: CRUD operations for database models
    - `ai/`: AI integration with Ollama
    - `tools/`: Tool definitions for AI assistance
- `docker-compose.yml`: Docker Compose configuration for development

## Development Workflow

1. Make your changes
2. Create necessary database migrations:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Description of changes"
   alembic upgrade head
   ```
3. Test your changes locally
4. Commit and push your changes

## Features

- Family management with parent and child accounts
- Screen time monitoring and management
- Chore tracking and verification
- Stateful AI assistance using local models
- Secure authentication and privacy-focused

## Next Steps

See [whatSTEPSNEXT.md](whatSTEPSNEXT.md) for the detailed development roadmap.
