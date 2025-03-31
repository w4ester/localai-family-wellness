"""
Database session and connection handling.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create async engine using the DATABASE_URL from settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,  # Set to True to see SQL queries in logs
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    future=True,  # Use SQLAlchemy 2.0 style
)

# Create a session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Dependency to get a database session
async def get_db() -> AsyncSession:
    """
    Dependency for getting an async database session.
    To be used in FastAPI dependency injection.
    
    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
