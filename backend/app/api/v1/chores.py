# ./backend/app/api/v1/chores.py
"""
API endpoints for chore management.
"""
import logging
from typing import List
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

# --- Dependency Imports ---
from app.db.session import get_db_conn
# from app.auth.dependencies import get_current_active_user

# --- Placeholder Imports ---
# from app.schemas.chore import ChoreRead, ChoreCreate, ChoreUpdate # Example schemas
# from app.crud.chore import crud_chore # Example CRUD
# from app.models.user_model import User as DBUser # Example DB model
# ---------------------------

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ChoreRead, status_code=status.HTTP_201_CREATED)
async def create_chore(
    *,
    db: psycopg.AsyncConnection = Depends(get_db_conn),
    chore_in: ChoreCreate, # Example create schema
    # current_user: DBUser = Depends(get_current_active_user)
):
    """
    Create a new chore.
    (Implement permission check: only parent/caregiver can create?)
    """
    logger.info(f"User {current_user.id} creating chore: {chore_in.title}")
    # Check permissions
    # new_chore = await crud_chore.create(db=db, obj_in=chore_in, creator_id=current_user.id, family_id=current_user.family_id)
    # return new_chore
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.get("/", response_model=List[ChoreRead])
async def read_chores(
    db: psycopg.AsyncConnection = Depends(get_db_conn),
    # current_user: DBUser = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    assignee_id: Optional[UUID] = None, # Filter by assignee
    status: Optional[str] = None, # Filter by status
):
    """
    Retrieve chores for the current user's family, with optional filters.
    """
    logger.info(f"User {current_user.id} fetching chores for family {current_user.family_id}")
    # chores = await crud_chore.get_multi_by_family(
    #     db=db,
    #     family_id=current_user.family_id,
    #     assignee_id=assignee_id,
    #     status=status,
    #     skip=skip,
    #     limit=limit
    # )
    # return chores
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.put("/{chore_id}", response_model=ChoreRead)
async def update_chore(
    *,
    db: psycopg.AsyncConnection = Depends(get_db_conn),
    chore_id: UUID,
    chore_in: ChoreUpdate, # Example update schema
    # current_user: DBUser = Depends(get_current_active_user)
):
    """
    Update a chore (e.g., mark complete, verify, change details).
    (Implement permission checks: assignee can complete, parent can verify/edit etc.)
    """
    logger.info(f"User {current_user.id} updating chore {chore_id}")
    # chore = await crud_chore.get(db=db, id=chore_id)
    # if not chore or chore.family_id != current_user.family_id:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chore not found")
    # Check permissions based on chore_in data (e.g., status change)
    # updated_chore = await crud_chore.update(db=db, db_obj=chore, obj_in=chore_in)
    # # Handle side effects (e.g., awarding points via Celery task)
    # return updated_chore
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

# Add other endpoints like:
# GET /{chore_id} (get specific chore details)
# DELETE /{chore_id} (delete chore - permissions needed)
