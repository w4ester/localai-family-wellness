# ./backend/app/crud/ai_memory_crud.py
"""
CRUD operations specifically for AIMemory objects, mainly for potential
manual management or retrieval outside vector search if needed.
Vector search/storage logic is primarily in app.ai.memory.
"""
import logging
from typing import Optional, List
from uuid import UUID

import psycopg
from psycopg.rows import class_row

# Import DB model and Pydantic schemas (if needed for direct creation/update)
from app.db.models.ai_memory import AIMemory as DBAIMemory
# from app.schemas.ai_schemas import AIMemoryCreate, AIMemoryUpdate # Example schemas if needed

logger = logging.getLogger(__name__)

# NOTE: Most memory interaction (creation with embedding, vector search)
# happens in app/ai/memory.py and app/ai/service.py.
# These CRUD functions are for simpler, non-vector operations if required.

async def get_memory_by_id(db: psycopg.AsyncConnection, memory_id: UUID) -> Optional[DBAIMemory]:
    """Fetch a single AI memory record by its primary key ID."""
    logger.debug(f"Getting AI Memory by ID: {memory_id}")
    async with db.cursor(row_factory=class_row(DBAIMemory)) as cur:
        # Exclude the 'embedding' column by default unless specifically needed,
        # as fetching large vectors can be inefficient if only text/metadata is required.
        await cur.execute(
             # Explicitly list columns excluding embedding
            f'SELECT id, user_id, family_id, text, memory_type, source, metadata, importance, created_at, updated_at '
            f'FROM "{DBAIMemory.__tablename__}" WHERE id = %s',
            (memory_id,)
        )
        memory = await cur.fetchone()
        return memory

async def get_memories_by_user(
    db: psycopg.AsyncConnection,
    user_id: UUID,
    memory_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
) -> List[DBAIMemory]:
    """Fetch memories for a user, optionally filtered by type, ordered by creation time."""
    logger.debug(f"Getting memories for user {user_id}, type={memory_type}")
    base_query = f'SELECT id, user_id, family_id, text, memory_type, source, metadata, importance, created_at, updated_at FROM "{DBAIMemory.__tablename__}" WHERE user_id = %s'
    params = [user_id]
    param_index = 2

    if memory_type:
        base_query += f" AND memory_type = %s"
        params.append(memory_type)
        param_index += 1

    base_query += f" ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, skip])

    async with db.cursor(row_factory=class_row(DBAIMemory)) as cur:
        await cur.execute(base_query, tuple(params))
        memories = await cur.fetchall()
        return memories


# Direct Create/Update/Delete via CRUD might be less common for AIMemory,
# as creation involves embedding generation (handled in ai/memory.py)
# and deletion might have complex implications for AI state.

# Example Delete (Use with extreme caution!)
async def delete_memory(db: psycopg.AsyncConnection, memory_id: UUID) -> Optional[DBAIMemory]:
    """Delete an AI Memory record by ID."""
    logger.warning(f"Attempting deletion of AI Memory ID: {memory_id}")
    async with db.cursor(row_factory=class_row(DBAIMemory)) as cur:
        try:
            # Return the deleted item to confirm
            await cur.execute(f'DELETE FROM "{DBAIMemory.__tablename__}" WHERE id = %s RETURNING id, text, memory_type', (memory_id,))
            deleted_memory_info = await cur.fetchone()
            # await db.commit() # Handled by context
            if deleted_memory_info:
                 logger.info(f"Successfully deleted AI Memory ID: {memory_id}")
                 return deleted_memory_info # Return partial info
            else:
                 logger.warning(f"AI Memory ID {memory_id} not found for deletion.")
                 return None
        except Exception as e:
             logger.error(f"Error deleting AI Memory {memory_id}: {e}", exc_info=True)
             await db.rollback()
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting memory")