# ./backend/app/main.py
"""
Main FastAPI application entry point for the Local AI Family Wellness Platform.

Initializes the app, includes routers, sets up middleware, and manages lifespan events
including database connection pooling and mDNS registration.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional # Added for type hinting

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool # Import the pool type
from zeroconf import ServiceInfo # Import for type hinting

# Import configuration and settings
from app.core.config import settings

# Import the main API router
from app.api.router import api_router

# Import lifespan management functions / DB setup
# Assuming init_db now CREATES and RETURNS the pool, and needs a separate close function
# Adjust paths if your files are named differently or located elsewhere
from app.db.session import create_db_pool, close_db_pool, ensure_extensions_created, ensure_tables_created
from app.tools.registry import load_tools_registry # Assuming registry.py is in app/tools/
from app.utils.zeroconf_service import register_mdns, unregister_mdns # Assuming zeroconf_service.py is in app/utils/

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    - Creates database connection pool.
    - Ensures database extensions and tables exist.
    - Loads AI tool registry.
    - Registers mDNS service.
    - Cleans up resources (DB pool, mDNS) on shutdown.
    """
    logger.info("Starting up LocalAI Family Wellness Platform...")

    db_pool: Optional[AsyncConnectionPool] = None
    service_info: Optional[ServiceInfo] = None

    try:
        # 1. Create Database Connection Pool
        db_pool = await create_db_pool() # Function returns the pool object
        app.state.db_pool = db_pool # Store pool in app state for access in requests
        logger.info("Database connection pool created.")

        # 2. Ensure Database Extensions (like vector) Exist
        await ensure_extensions_created(db_pool)
        logger.info("Database extensions checked/created.")

        # 3. Ensure Database Tables Are Created (Run migrations/create_all)
        # WARNING: ensure_tables_created uses SQLAlchemy create_all - DEV ONLY!
        # Use Alembic for production migrations. Comment out if using Alembic.
        await ensure_tables_created(db_pool)
        logger.info("Database tables checked/created (using DEV method).")

        # 4. Load the AI Tool Registry
        load_tools_registry() # Assumes sync function loading tools_config.json
        logger.info("Tool registry loaded.")

        # 5. Register the service with mDNS for local discovery
        service_info = register_mdns() # Function registers the service
        app.state.mdns_info = service_info # Store info needed for unregistering
        if service_info:
            logger.info(f"mDNS service registered as '{settings.MDNS_SERVICE_NAME}'")

    except Exception as e:
        logger.error(f"Critical error during application startup: {e}", exc_info=True)
        # Attempt cleanup if pool was partially created
        if db_pool:
            await close_db_pool(db_pool)
        raise # Stop app startup

    logger.info("Application startup complete. Ready to accept requests.")
    yield  # --- FastAPI application runs here ---
    logger.info("Shutting down LocalAI Family Wellness Platform...")

    # --- Teardown operations (run on shutdown) ---
    try:
        # 1. Unregister the mDNS service
        stored_service_info = getattr(app.state, 'mdns_info', None)
        if stored_service_info:
            unregister_mdns(stored_service_info)
            logger.info("mDNS service unregistered.")

        # 2. Close Database Connection Pool
        stored_db_pool = getattr(app.state, 'db_pool', None)
        if stored_db_pool:
            await close_db_pool(stored_db_pool)
            logger.info("Database connection pool closed.")

    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)

    logger.info("Application shutdown complete.")


# --- FastAPI App Initialization ---
# Create FastAPI app instance, passing the lifespan manager
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # Standard OpenAPI endpoint
    docs_url=f"{settings.API_V1_STR}/docs",             # Swagger UI
    redoc_url=f"{settings.API_V1_STR}/redoc",           # ReDoc UI
    lifespan=lifespan
)

# --- CORS Middleware ---
# Set up CORS middleware if origins are defined in settings
if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    logger.info(f"Configuring CORS for origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,          # List of allowed origins
        allow_credentials=True,       # Allow cookies (needed for auth flows)
        allow_methods=["*"],          # Allow all standard methods
        allow_headers=["*"],          # Allow all headers
    )
else:
    logger.warning("No CORS origins configured. Web frontends might be blocked.")


# --- Include API Routers ---
# Mount the main API router (defined in app/api/router.py)
# under the configured prefix (e.g., /api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)


# --- Root Endpoint / Health Check ---
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Basic health check endpoint to confirm the API is running.
    """
    # Future: Could add a simple DB ping here using app.state.db_pool for a deeper check
    return {"status": "healthy", "message": f"{settings.PROJECT_NAME} is running"}

# Note: Uvicorn runs this 'app' instance based on Docker CMD or direct execution command.
# Example: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload