# ./backend/app/db/session.py (Recommended new name)
"""
Database connection pool management and dependency injection.
"""
import logging
from typing import AsyncGenerator, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[AsyncConnectionPool] = None

async def create_db_pool() -> AsyncConnectionPool:
    """
    Creates the asynchronous database connection pool.
    This should be called once during application startup (lifespan).
    """
    global _pool
    if _pool is not None:
        logger.warning("Database pool already exists.")
        return _pool

    logger.info("Creating database connection pool...")
    try:
        conninfo = str(settings.DATABASE_URL)
        logger.debug(f"Connecting to DB with conninfo: {conninfo[:conninfo.find('PASSWORD=')+9]}********") # Log safely

        _pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=settings.DATABASE_POOL_SIZE, # Use configured pool size
            max_size=settings.DATABASE_POOL_SIZE + settings.DATABASE_MAX_OVERFLOW, # Max connections
            # max_waiting=settings.DATABASE_MAX_OVERFLOW, # Controls wait queue size
            # timeout=10, # Timeout for getting a connection
            # max_lifetime=3600, # Max connection age in seconds
            # max_idle=300, # Max idle time before closing connection
            kwargs={"row_factory": dict_row}, # Get results as dictionaries
            open=True # Validate connection on creation
        )
        # Perform a simple query to ensure the pool is working
        async with _pool.connection() as conn:
             async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                if result and result.get('?column?') == 1: # Check column name based on dict_row
                    logger.info("Database connection pool validated successfully.")
                else:
                     raise ConnectionError("Database pool validation failed.")
        return _pool
    except (psycopg.OperationalError, ConnectionError) as e:
        logger.error(f"Failed to create or validate database connection pool: {e}", exc_info=True)
        _pool = None # Ensure pool is None if creation failed
        raise # Re-raise the exception to signal startup failure

async def close_db_pool(pool: Optional[AsyncConnectionPool] = None):
    """
    Closes the database connection pool gracefully.
    This should be called once during application shutdown (lifespan).
    """
    global _pool
    p = pool or _pool # Use passed pool or global one
    if p:
        logger.info("Closing database connection pool...")
        await p.close()
        _pool = None # Clear global reference
        logger.info("Database connection pool closed.")
    else:
        logger.warning("Attempted to close a non-existent database pool.")


async def get_db_conn() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """
    FastAPI dependency that yields a connection from the pool.
    Ensures the connection is returned to the pool even if errors occur.
    """
    global _pool
    if _pool is None:
        logger.error("Database pool is not initialized.")
        raise RuntimeError("Database pool is not available.")

    async with _pool.connection() as conn:
        try:
            yield conn
        except psycopg.Error as e:
            logger.error(f"Database error during request: {e}", exc_info=True)
            # Decide whether to rollback or let context manager handle
            # await conn.rollback() # Often handled by context exit on error
            raise # Re-raise exception to let FastAPI handle it


# --- Table/Extension Creation (Separate Logic) ---

async def ensure_extensions_created(pool: AsyncConnectionPool):
    """
    Ensures necessary PostgreSQL extensions (like vector) are created.
    Should be idempotent. Called once during startup.
    TimescaleDB is usually handled by the Docker image itself.
    """
    logger.info("Ensuring database extensions exist...")
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                # DO NOT typically create timescaledb here if using Timescale Docker image
                # await cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                await conn.commit()
                logger.info("Database extensions checked/created.")
    except Exception as e:
        logger.error(f"Error ensuring database extensions: {e}", exc_info=True)
        # Depending on severity, might want to raise to stop startup
        raise


async def ensure_tables_created(pool: AsyncConnectionPool):
    """
    Ensures database tables exist based on SQLAlchemy models.
    WARNING: This uses SQLAlchemy's create_all and is NOT suitable for production
    migrations. Use Alembic for production database schema management.
    This function is provided for initial development setup only.
    """
    logger.warning("Attempting to ensure tables exist using SQLAlchemy create_all (DEV ONLY!)")
    logger.warning("Use Alembic for production migrations.")

    # Need SQLAlchemy engine for create_all
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.db.base import Base # Import your SQLAlchemy Base
    # Import all models here so they are registered with Base.metadata
    from app.db.models.user_model import User
    from app.db.models.family_model import Family
    from app.db.models.screen_time_model import ScreenTimeRule, ScreenTimeUsage, ScreenTimeExtensionRequest
    from app.db.models.chore_model import Chore, ChoreCompletion  # If these models exist
    from app.db.models.ai_memory import AIMemory  # If this model exists

    # Create an SQLAlchemy async engine using the DATABASE_URL from settings
    # Make sure DATABASE_URL uses an async compatible dialect if using SQLAlchemy engine directly
    # Example: postgresql+asyncpg - Requires installing asyncpg
    # NOTE: This creates a SEPARATE connection mechanism from the psycopg_pool used elsewhere!
    # Consider if this is acceptable or if migrations should be run externally.
    try:
        # Adjust the URL format if needed for SQLAlchemy's async engine
        # Example using asyncpg:
        # sqlalchemy_url = str(settings.DATABASE_URL).replace("postgresql+psycopg://", "postgresql+asyncpg://")
        # engine = create_async_engine(sqlalchemy_url)

        # --- Alternative (if not using SQLAlchemy engine directly) ---
        # You would need to run migrations externally using Alembic
        logger.info("Skipping table creation via SQLAlchemy. Use Alembic externally.")
        return
        # --------------------------------------------------------------

        # async with engine.begin() as conn:
        #     # Create tables defined in Base.metadata
        #     # await conn.run_sync(Base.metadata.create_all) # Runs synchronously in thread pool
        #     pass # Replace pass with the line above if using SQLAlchemy engine

        # logger.info("SQLAlchemy Base.metadata.create_all execution complete (DEV ONLY).")

    except Exception as e:
        logger.error(f"Error during SQLAlchemy table creation: {e}", exc_info=True)
        raise
    # finally:
        # if 'engine' in locals():
        #     await engine.dispose() # Dispose the temporary engine