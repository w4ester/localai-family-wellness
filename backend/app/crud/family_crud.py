# ./backend/app/crud/family_crud.py
"""
CRUD operations for Family objects.
"""
import logging
import secrets # For generating join codes potentially
import string # For generating join codes potentially
from typing import Optional, List
from uuid import UUID

import psycopg
from psycopg.rows import class_row, dict_row # Use dict_row if mapping to schema directly

# Import DB model and Pydantic schemas
from app.db.models.family_model import Family as DBFamily
from app.db.models.user_model import User as DBUser # Needed for owner creation logic
from app.schemas.family_schemas import FamilyCreate, FamilyUpdate
from app.crud.user_crud import update_user # To update owner's family_id
from app.schemas.user_schemas import UserUpdate # Needed for update_user call


logger = logging.getLogger(__name__)

# --- Read Operations ---

async def get_family_by_id(db: psycopg.AsyncConnection, family_id: UUID) -> Optional[DBFamily]:
    """Fetch a single family by ID."""
    logger.debug(f"Getting family by ID: {family_id}")
    async with db.cursor(row_factory=class_row(DBFamily)) as cur:
        await cur.execute(f'SELECT * FROM "{DBFamily.__tablename__}" WHERE id = %s', (family_id,))
        family = await cur.fetchone()
        return family

async def get_family_by_join_code(db: psycopg.AsyncConnection, join_code: str) -> Optional[DBFamily]:
    """Fetch a single family by its unique join code."""
    logger.debug(f"Getting family by join_code: {join_code}")
    async with db.cursor(row_factory=class_row(DBFamily)) as cur:
        await cur.execute(f'SELECT * FROM "{DBFamily.__tablename__}" WHERE join_code = %s', (join_code,))
        family = await cur.fetchone()
        return family

async def get_family_with_members(db: psycopg.AsyncConnection, family_id: UUID) -> Optional[DBFamily]:
    """
    Fetch a family and preload its members.
    NOTE: This basic version doesn't preload via SQL JOIN. It relies on SQLAlchemy's
    lazy loading OR requires separate queries if not using SQLAlchemy ORM query patterns.
    For pure psycopg, you'd typically do a separate query for members.
    Let's return the family and let the service/API layer fetch members if needed.
    """
    logger.debug(f"Getting family (members may lazy load): {family_id}")
    # For pure psycopg, just getting the family is standard. Preloading is ORM feature.
    return await get_family_by_id(db, family_id)


# --- Create Operation ---

def _generate_join_code(length: int = 8) -> str:
    """Generate a secure random alphanumeric join code."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

async def create_family_with_owner(db: psycopg.AsyncConnection, family_in: FamilyCreate, owner: DBUser) -> DBFamily:
    """Create a new family and assign the owner."""
    if owner.family_id:
        logger.warning(f"User {owner.id} attempting to create family but already belongs to {owner.family_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already belongs to a family")

    logger.info(f"Creating new family '{family_in.name}' by owner {owner.id}")

    # Generate a unique join code (add retry logic if collisions are a concern)
    join_code = _generate_join_code()
    # Consider checking if code already exists in DB if high traffic expected

    async with db.cursor(row_factory=class_row(DBFamily)) as cur:
        try:
            # Insert the new family
            await cur.execute(
                f"""
                INSERT INTO "{DBFamily.__tablename__}" (name, description, allow_screen_time_monitoring, allow_chore_management, join_code)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    family_in.name,
                    family_in.description,
                    family_in.allow_screen_time_monitoring if family_in.allow_screen_time_monitoring is not None else True,
                    family_in.allow_chore_management if family_in.allow_chore_management is not None else True,
                    join_code,
                )
            )
            created_family = await cur.fetchone()
            if not created_family:
                raise Exception("Family creation failed unexpectedly.")

            # Update the owner's family_id using the user_crud function
            owner_update = UserUpdate(family_id=created_family.id)
            await update_user(db=db, user=owner, user_in=owner_update)

            logger.info(f"Family '{created_family.name}' created with ID {created_family.id} and owner {owner.id}")
            # await db.commit() # Handled by connection context manager
            return created_family

        except psycopg.errors.UniqueViolation as e:
             logger.warning(f"Failed to create family '{family_in.name}'. Unique constraint violation (likely join_code): {e}")
             await db.rollback()
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not generate unique join code, please try again.") from e
        except Exception as e:
            logger.error(f"Error creating family '{family_in.name}': {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating family") from e


# --- Update Operation ---

async def update_family(db: psycopg.AsyncConnection, family: DBFamily, family_in: FamilyUpdate) -> DBFamily:
    """Update an existing family record."""
    logger.debug(f"Updating family ID: {family.id}")
    update_data = family_in.model_dump(exclude_unset=True)

    if not update_data:
        return family

    fields_to_update = []
    values_to_update = []
    for key, value in update_data.items():
        if hasattr(DBFamily, key) and key != 'id': # Don't allow updating ID
            fields_to_update.append(f'"{key}" = %s')
            values_to_update.append(value)

    if not fields_to_update:
        return family

    # Add updated_at manually if not using DB trigger/ORM feature
    # fields_to_update.append('"updated_at" = NOW()')

    set_clause = ", ".join(fields_to_update)
    sql = f'UPDATE "{DBFamily.__tablename__}" SET {set_clause} WHERE id = %s RETURNING *'
    params = values_to_update + [family.id]

    logger.debug(f"Executing update for family {family.id}: SQL='{sql}' PARAMS='{params}'")
    async with db.cursor(row_factory=class_row(DBFamily)) as cur:
        try:
            await cur.execute(sql, params)
            updated_family = await cur.fetchone()
            # await db.commit()
            if not updated_family:
                 raise Exception("Family update failed unexpectedly.")
            logger.info(f"Family '{updated_family.name}' (ID: {updated_family.id}) updated successfully.")
            return updated_family
        except psycopg.errors.UniqueViolation as e: # Handle join_code collision if it's updatable
             logger.warning(f"Failed to update family {family.id}. Unique constraint violation: {e}")
             await db.rollback()
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Update failed due to unique constraint (e.g., join code).") from e
        except Exception as e:
            logger.error(f"Error updating family {family.id}: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating family") from e

# --- Delete Operation ---
# Implement if needed, remember relationship cascades defined in models!
# async def delete_family(db: psycopg.AsyncConnection, family_id: UUID) -> Optional[DBFamily]: ...