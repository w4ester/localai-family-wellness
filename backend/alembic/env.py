import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.base import Base
from app.db.models.user_model import User
from app.db.models.family_model import Family
from app.db.models.screen_time_model import ScreenTimeRule, ScreenTimeUsage, ScreenTimeExtensionRequest
from app.db.models.chore_model import Chore
from app.db.models.ai_memory import AIMemory

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get the SQLAlchemy URL from environment variable or fallback to config
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    
    # Ensure URL is in the correct format for async driver
    if url and not url.startswith("postgresql+psycopg"):
        url = url.replace("postgresql", "postgresql+psycopg", 1)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the SQLAlchemy URL from environment variable or fallback to config
    url = os.getenv("DATABASE_URL")
    if not url:
        config_section = config.get_section(config.config_ini_section)
        url = config_section["sqlalchemy.url"]
    
    # Ensure URL is in the correct format for async driver
    if url and not url.startswith("postgresql+psycopg"):
        url = url.replace("postgresql", "postgresql+psycopg", 1)
    
    # Create async engine
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
