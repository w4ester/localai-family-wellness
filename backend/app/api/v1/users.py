# ./backend/app/api/v1/users.py (Implementation Example)
"""
API endpoints for user management.
"""
import logging
from typing import List, Optional
from uuid import UUID

import psycopg # For type hints
from psycopg_pool import AsyncConnectionPool # For type hints
from fastapi import APIRouter, Depends, HTTPException, status

# --- Dependency Imports ---
from app.db.session import get_db_conn
from app.auth.dependencies import get_current_active_user # Get authenticated user

# --- Schema Imports ---
from app.schemas.user_schemas import UserRead, UserUpdate, UserReadMinimal

# --- CRUD Function Imports ---
from app.crud import user_crud # Import the module

# --- DB Model Import ---
from app.db.models.user_model import User as DBUser

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: DBUser = Depends(get_current_active_user) # Use the dependency
):
    """
    Get current logged-in user details.
    The dependency already fetches and validates the user.
    FastAPI automatically converts the DBUser to UserRead based on response_model.
    """
    logger.info(f"Fetching details for current user: {current_user.username}")
    # The dependency directly returns the DBUser object
    return current_user


@router.put("/me", response_model=UserRead)
async def update_user_me(
    *, # Enforce keyword args
    user_in: UserUpdate, # Get update data from request body
    db: AsyncConnectionPool = Depends(get_db_conn), # Get DB pool (pass pool to CRUD)
    current_user: DBUser = Depends(get_current_active_user) # Get current user
):
    """
    Update current logged-in user's profile.
    """
    logger.info(f"Updating profile for user: {current_user.username}")
    # The current_user object is the one fetched from DB by the dependency
    # Pass the connection from the pool to the CRUD function
    async with db.connection() as conn:
        updated_user = await user_crud.update_user(conn, user=current_user, user_in=user_in)
    return updated_user


@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_id(
    user_id: UUID,
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: DBUser = Depends(get_current_active_user) # Use dependency for auth check
):
    """
    Get a specific user by ID.
    Requires permission check (e.g., admin or same family parent).
    """
    logger.info(f"User {current_user.username} attempting to fetch user ID: {user_id}")

    # --- Permission Check Example ---
    # Allow user to fetch their own data
    if current_user.id == user_id:
        async with pool.connection() as conn:
             user = await user_crud.get_user_by_id(conn, user_id=user_id)
    # Allow parent/admin in the same family to fetch data (adjust roles as needed)
    elif current_user.family_id and str(current_user.role) in ["parent", "admin", "caregiver"]:
        async with pool.connection() as conn:
             user = await user_crud.get_user_by_id(conn, user_id=user_id)
             # Verify the requested user is in the same family
             if not user or user.family_id != current_user.family_id:
                 user = None # Don't leak existence of users in other families
    else:
        # User is not allowed to fetch this specific user ID
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's information"
        )
    # --- End Permission Check ---

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


# --- Example: Admin Endpoint to List Users ---
@router.get("", response_model=List[UserRead], dependencies=[Depends(get_current_active_parent_or_admin)]) # Require parent/admin
async def read_users(
    pool: AsyncConnectionPool = Depends(get_db_conn),
    skip: int = 0,
    limit: int = 100,
    # current_user: DBUser = Depends(get_current_active_parent_or_admin) # Included via dependencies list above
):
    """
    Retrieve a list of users (requires admin/parent privileges).
    Provides pagination using skip and limit.
    """
    # In a multi-tenant system, you might filter by family_id based on current_user
    # For simplicity here, assuming admin sees all or filter applied in crud
    logger.info(f"Admin/Parent fetching user list: skip={skip}, limit={limit}")
    async with pool.connection() as conn:
        # Need a get_multi function in user_crud.py
        # users = await user_crud.get_multi(conn, skip=skip, limit=limit)
        # return users
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User listing not fully implemented")


# --- Implement other endpoints (DELETE etc.) similarly, always including: ---
# 1. Dependencies (get_db_conn, auth dependencies like get_current_active_user or role-specific ones)
# 2. Permission Checks
# 3. Calls to appropriate CRUD functions
# 4. Error Handling (404s, 403s, etc.)
# 5. Correct response_model