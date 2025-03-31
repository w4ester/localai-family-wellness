# ./backend/app/crud/user_crud.py
"""
CRUD (Create, Read, Update, Delete) operations for User objects in the database.
"""
import logging
from typing import Optional, List
from uuid import UUID

import psycopg # For type hints
from psycopg.rows import class_row # To map results to Pydantic/dataclasses if needed
from pydantic import EmailStr # For type hinting if needed

# Import your DB model and Pydantic schemas
from app.db.models.user_model import User as DBUser, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

# --- Read Operations ---

async def get_user_by_id(db: psycopg.AsyncConnection, user_id: UUID) -> Optional[DBUser]:
    """Fetch a single user by their primary key ID."""
    logger.debug(f"Getting user by ID: {user_id}")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        await cur.execute(f'SELECT * FROM "{DBUser.__tablename__}" WHERE id = %s', (user_id,))
        user = await cur.fetchone()
        return user

async def get_user_by_keycloak_id(db: psycopg.AsyncConnection, keycloak_id: str) -> Optional[DBUser]:
    """Fetch a single user by their Keycloak ID."""
    logger.debug(f"Getting user by Keycloak ID: {keycloak_id}")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        await cur.execute(f'SELECT * FROM "{DBUser.__tablename__}" WHERE keycloak_id = %s', (keycloak_id,))
        user = await cur.fetchone()
        return user

async def get_user_by_email(db: psycopg.AsyncConnection, email: EmailStr) -> Optional[DBUser]:
    """Fetch a single user by their email address."""
    logger.debug(f"Getting user by email: {email}")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        await cur.execute(f'SELECT * FROM "{DBUser.__tablename__}" WHERE email = %s', (email,))
        user = await cur.fetchone()
        return user

async def get_user_by_username(db: psycopg.AsyncConnection, username: str) -> Optional[DBUser]:
    """Fetch a single user by their username."""
    logger.debug(f"Getting user by username: {username}")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        await cur.execute(f'SELECT * FROM "{DBUser.__tablename__}" WHERE username = %s', (username,))
        user = await cur.fetchone()
        return user

async def get_users_by_family(db: psycopg.AsyncConnection, family_id: UUID, skip: int = 0, limit: int = 100) -> List[DBUser]:
    """Fetch multiple users belonging to a specific family, with pagination."""
    logger.debug(f"Getting users for family ID: {family_id}, skip: {skip}, limit: {limit}")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        await cur.execute(
            f'SELECT * FROM "{DBUser.__tablename__}" WHERE family_id = %s ORDER BY created_at ASC LIMIT %s OFFSET %s',
            (family_id, limit, skip)
        )
        users = await cur.fetchall()
        return users

# --- Create Operation ---

async def create_user(db: psycopg.AsyncConnection, user_in: UserCreate) -> DBUser:
    """Create a new user record in the database."""
    logger.info(f"Creating new user: {user_in.username} (Keycloak ID: {user_in.keycloak_id})")
    # Note: Base model provides defaults for id, created_at, updated_at
    # Role defaults to CHILD in the schema if not provided
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
        try:
            # Make sure role is passed as its value if it's an Enum
            role_value = user_in.role.value if isinstance(user_in.role, Enum) else user_in.role

            await cur.execute(
                f"""
                INSERT INTO "{DBUser.__tablename__}" (keycloak_id, username, email, first_name, last_name, role, family_id, parent_id, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    user_in.keycloak_id,
                    user_in.username,
                    user_in.email,
                    user_in.first_name,
                    user_in.last_name,
                    role_value, # Pass the string value of the enum
                    user_in.family_id,
                    user_in.parent_id,
                    user_in.is_active if user_in.is_active is not None else True # Default active if not specified
                )
            )
            created_user = await cur.fetchone()
            # Commit is handled by the connection context manager from get_db_conn usually
            # await db.commit()
            if not created_user:
                 # Should not happen with RETURNING * if insert succeeded
                 raise Exception("User creation failed unexpectedly.")
            logger.info(f"User {created_user.username} created successfully with ID: {created_user.id}")
            return created_user
        except psycopg.errors.UniqueViolation as e:
            logger.warning(f"Failed to create user. Unique constraint violation: {e}")
            await db.rollback() # Rollback the transaction
            # Determine which field caused the violation (e.g., username, email, keycloak_id)
            # You might need to parse e.diag.constraint_name or e.pgerror
            detail = "Username, email, or Keycloak ID already exists."
            if "uq_user_username" in str(e): detail = "Username already exists."
            if "uq_user_email" in str(e): detail = "Email already exists."
            if "uq_user_keycloak_id" in str(e): detail = "Keycloak ID already linked."
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from e
        except Exception as e:
            logger.error(f"Error creating user {user_in.username}: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user") from e


# --- Update Operation ---

async def update_user(db: psycopg.AsyncConnection, user: DBUser, user_in: UserUpdate) -> DBUser:
    """Update an existing user record."""
    logger.debug(f"Updating user ID: {user.id}")
    # Get fields to update from the input schema, excluding unset fields
    update_data = user_in.model_dump(exclude_unset=True)

    if not update_data:
        logger.debug("No update data provided for user {user.id}")
        return user # Return original user if no changes

    # Prepare SQL update statement dynamically (safer than f-strings for production)
    fields_to_update = []
    values_to_update = []
    i = 1 # Start parameter index at 1 for psycopg
    for key, value in update_data.items():
        # Make sure the key is a valid column in the DBUser model
        if hasattr(DBUser, key):
            fields_to_update.append(f'"{key}" = %s') # Use placeholder %s
            # Handle enums correctly
            if isinstance(value, Enum):
                 values_to_update.append(value.value)
            else:
                 values_to_update.append(value)
            i += 1

    # Add updated_at manually if not using DB trigger (Base class handles this via onupdate)
    # fields_to_update.append('"updated_at" = NOW()')

    if not fields_to_update:
        logger.warning(f"No valid fields provided for updating user {user.id}")
        return user # Return original if no valid fields were provided

    set_clause = ", ".join(fields_to_update)
    sql = f'UPDATE "{DBUser.__tablename__}" SET {set_clause} WHERE id = %s RETURNING *'
    params = values_to_update + [user.id]

    logger.debug(f"Executing update for user {user.id}: SQL='{sql}' PARAMS='{params}'")
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
         try:
            await cur.execute(sql, params)
            updated_user = await cur.fetchone()
            # await db.commit() # Handled by connection context manager
            if not updated_user:
                 raise Exception("User update failed unexpectedly (RETURNING * yielded no result).")
            logger.info(f"User {updated_user.username} (ID: {updated_user.id}) updated successfully.")
            return updated_user
         except psycopg.errors.UniqueViolation as e:
             logger.warning(f"Failed to update user {user.id}. Unique constraint violation: {e}")
             await db.rollback()
             detail = "Username or email already exists."
             if "uq_user_username" in str(e): detail = "Username already exists."
             if "uq_user_email" in str(e): detail = "Email already exists."
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from e
         except Exception as e:
             logger.error(f"Error updating user {user.id}: {e}", exc_info=True)
             await db.rollback()
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating user") from e

# --- Delete Operation ---
# Optional: Implement delete if needed, be careful with relationships/cascades
async def delete_user(db: psycopg.AsyncConnection, user_id: UUID) -> Optional[DBUser]:
    """Delete a user by ID."""
    logger.warning(f"Attempting to delete user ID: {user_id}") # Log deletion attempts
    async with db.cursor(row_factory=class_row(DBUser)) as cur:
         # Optional: Return the deleted user data
        await cur.execute(f'DELETE FROM "{DBUser.__tablename__}" WHERE id = %s RETURNING *', (user_id,))
        deleted_user = await cur.fetchone()
        # await db.commit() # Handled by connection context manager
        if deleted_user:
             logger.info(f"Successfully deleted user {deleted_user.username} (ID: {user_id})")
        else:
             logger.warning(f"User ID {user_id} not found for deletion.")
        return deleted_user