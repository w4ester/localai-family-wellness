# Markdown Files in LocalAI Family Wellness Project

This document lists all markdown files in the project, ordered from most recently created to oldest, with a brief description of each file's purpose.

## Most Recent Files

### 1. compareBranch_Main.md (2025-03-31)
Generated diff file showing changes between branches, focusing on files related to database migrations, Docker configuration, and PostgreSQL setup.

### 2. README_MIGRATIONS.md (2025-03-31)
Quick-start guide for database migrations offering two options: Docker-based method and local development with Poetry, with links to detailed documentation.

### 3. docs/MIGRATION_GUIDE.md (2025-03-31)
Detailed guide covering two migration methods (Docker-based and local development), with commands, prerequisites, workflow instructions, and troubleshooting tips for each approach.

### 4. MIGRATION_GUIDE.md (2025-03-31)
Guide explaining how to use the migrate.sh script to run Alembic migrations within Docker containers, with step-by-step instructions for different migration tasks.

### 5. README.md (2025-03-31)
Project introduction and setup instructions for the LocalAI Family Wellness Platform, covering environment configuration, database migration, running the application, and development workflow.

### 6. docs/alembic_migrations_guide.md (2025-03-31)
Comprehensive guide for using Alembic for database migrations in both Docker and local development environments, including commands, best practices, and troubleshooting tips.

## Recent Files

### 7. whatSTEPSNEXT.md (2025-03-30)
Detailed roadmap outlining next steps for project completion, organized into phases covering backend completion, tool server implementation, background tasks, frontend development, testing, and deployment.

### 8. backend/model_upgrade_notes.md (2025-03-30)
Step-by-step guide for updating remaining models to SQLAlchemy 2.0, with examples for different column types and relationships.

### 9. backend/SQLALCHEMY_UPGRADE.md (2025-03-30)
Guide explaining the changes made to upgrade models to SQLAlchemy 2.0 style, including base class updates, model definitions, and how to work with the new type annotations.

### 10. backend/app/AUTHENTICATION_AND_MIGRATION_SETUP.md (2025-03-30)
Summary of changes made to implement authentication and database migrations, including token schema updates, auth endpoints, and Alembic configuration.

### 11. backend/app/auth/README.md (2025-03-30)
Documentation of the authentication system that uses Keycloak with OAuth2, describing the architecture, components, setup requirements, and security considerations.

## Older Files

### 12. backend/app/backendFixes.md (2025-03-30)
Summary of fixes implemented to address naming and structural issues in the backend codebase, including database connection management, SQLAlchemy Base class, and missing CRUD implementations.

### 13. backend/app/backendRecentNamingFixes.md (2025-03-30)
List of critical naming issues found in the codebase with specific fixes required, including file renames, missing imports, and typo corrections.

### 14. backend/filesNEEDINGalignment.md (2025-03-30)
Document detailing files that need naming convention alignment, particularly between AI service.py, tool_models.py, and tools_config.json, with recommendations for standardization.

### 15. backendNotes.md (2025-03-30)
Analysis of the current state of backend implementation focusing on AI components, identifying inconsistencies between tool models and providing recommendations for standardization.

### 16. older_ultimateREADME.md (2025-03-30)
Comprehensive overview of the project's structure and components, including detailed descriptions of key backend files, workflow, and implementation tasks with next steps for development.

### 17. backend/app/api/v1/README_v1.md (2025-03-30)
Documentation file explaining the API endpoints for version 1, providing implementation guidelines for API routers related to auth, users, families, AI, chores, and screen time.