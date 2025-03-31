# ./backend/app/crud/chore_crud.py
"""
CRUD operations for Chore objects.
"""
import logging
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

import psycopg
from psycopg.rows import class_row, dict_row

# Import DB model and Pydantic schemas
from app.db.models.chore_model import Chore as DBChore, ChoreStatus, ChoreRecurrence # Import Enum if needed
from app.schemas.chore_schemas import ChoreCreate, ChoreUpdate

logger = logging.getLogger(__name__)

# --- Read Operations ---

async def get_chore_by_id(db: psycopg.AsyncConnection, chore_id: UUID) -> Optional[DBChore]:
    """Fetch a single chore by ID."""
    logger.debug(f"Getting chore by ID: {chore_id}")
    async with db.cursor(row_factory=class_row(DBChore)) as cur:
        await cur.execute(f'SELECT * FROM "{DBChore.__tablename__}" WHERE id = %s', (chore_id,))
        chore = await cur.fetchone()
        return chore

async def get_multi_by_family(
    db: psycopg.AsyncConnection,
    family_id: UUID,
    assignee_id: Optional[UUID] = None,
    status: Optional[str] = None, # Use string representation of ChoreStatus enum
    skip: int = 0,
    limit: int = 100
) -> List[DBChore]:
    """Fetch chores for a family, with optional filters and pagination."""
    logger.debug(f"Getting chores for family {family_id},