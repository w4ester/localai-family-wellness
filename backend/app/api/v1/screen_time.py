# ./backend/app/api/v1/screen_time.py
"""
API endpoints for screen time rules, usage logs, and extension requests.
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

import psycopg # For type hints
from psycopg_pool import AsyncConnectionPool # For type hints
from fastapi import APIRouter, Depends, HTTPException, status, Query # Added Query

# --- Dependency Imports ---
from app.db.session import get_db_conn
from app.auth.dependencies import ( # Import auth dependencies
    get_current_active_user,
    get_current_active_parent_or_admin, # Use for restricted actions
)

# --- Schema Imports ---
# Import all necessary schemas from the dedicated file
from app.schemas.screen_time_schemas import (
    ScreenTimeRuleRead, ScreenTimeRuleCreate, ScreenTimeRuleUpdate,
    ScreenTimeUsageRead, ScreenTimeUsageCreate,
    ScreenTimeExtensionRequestRead, ScreenTimeExtensionRequestCreate, ScreenTimeExtensionRequestUpdate,
)
# Import user schema for type hinting current_user
from app.schemas.user_schemas import UserReadMinimal # Or use DBUser if preferred internally

# --- CRUD Function Imports ---
# Import the CRUD operations modules
from app.crud import screen_time_crud, user_crud

# --- DB Model Import (Optional, mainly for type hints if needed) ---
from app.db.models.user_model import User as DBUser

# --- Router Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()


# === Screen Time Rules Endpoints ===

@router.post(
    "/rules",
    response_model=ScreenTimeRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Screen Time Rule",
    dependencies=[Depends(get_current_active_parent_or_admin)] # Require Parent/Admin
)
async def create_screen_time_rule_endpoint(
    *, # Enforce keyword arguments
    rule_in: ScreenTimeRuleCreate,
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_parent_or_admin) # Get authed user
):
    """
    Create a new screen time rule for a child.
    Requires Parent/Admin privileges.
    The `family_id` in the request body must match the creator's family.
    """
    # Permission Check: Ensure the rule is being created within the parent's own family
    if rule_in.family_id != current_user.family_id:
        logger.warning(f"User {current_user.id} attempted to create rule for different family {rule_in.family_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create rules for another family."
        )
    # Optional Check: Ensure the target user_id exists and is in the same family
    # (Could be done here or within the CRUD function)

    logger.info(f"User {current_user.id} creating screen time rule '{rule_in.name}' for user {rule_in.user_id}")
    async with pool.connection() as conn:
        # CRUD function handles the DB interaction
        rule = await screen_time_crud.create_screen_time_rule(db=conn, rule_in=rule_in)
        # No need to commit here, handled by context manager in CRUD/session
    return rule


@router.get("/rules", response_model=List[ScreenTimeRuleRead], summary="List Screen Time Rules")
async def read_screen_time_rules_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter rules applied to a specific user ID (child)."),
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_user) # Any logged-in user
):
    """
    Get screen time rules.
    - If `user_id` is provided and matches the current user, returns rules for that user.
    - If the current user is a Parent/Admin, they can provide a `user_id` for any child in their family.
    - If `user_id` is not provided:
        - Parents/Admins see all rules for their family.
        - Children see only rules applied directly to them.
    """
    if not current_user.family_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a family.")

    logger.info(f"User {current_user.id} fetching screen time rules. Filter user_id: {user_id}")

    async with pool.connection() as conn:
        # --- Permission Logic ---
        if user_id:
            # If filtering by user_id, check permissions
            is_parent_or_admin = str(current_user.role) in ["parent", "admin", "caregiver"]
            if current_user.id == user_id:
                # User requesting their own rules
                rules = await screen_time_crud.get_screen_time_rules_for_user(db=conn, user_id=user_id)
            elif is_parent_or_admin:
                # Parent/Admin requesting rules for a specific user - verify user is in their family
                target_user = await user_crud.get_user_by_id(db=conn, user_id=user_id) # Need user_crud import
                if not target_user or target_user.family_id != current_user.family_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found in your family.")
                rules = await screen_time_crud.get_screen_time_rules_for_user(db=conn, user_id=user_id)
            else:
                # Child trying to see someone else's rules
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these rules.")
        else:
            # No user_id filter provided
            if str(current_user.role) in ["parent", "admin", "caregiver"]:
                # Parent/Admin sees all rules for the family (Need CRUD function for this)
                # rules = await screen_time_crud.get_screen_time_rules_for_family(db=conn, family_id=current_user.family_id)
                logger.warning("Fetching all family rules not implemented yet in CRUD.")
                raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Fetching all family rules not implemented.")
            else:
                # Child sees only their own rules
                rules = await screen_time_crud.get_screen_time_rules_for_user(db=conn, user_id=current_user.id)
        # --- End Permission Logic ---

    return rules


@router.put(
    "/rules/{rule_id}",
    response_model=ScreenTimeRuleRead,
    summary="Update Screen Time Rule",
    dependencies=[Depends(get_current_active_parent_or_admin)] # Require Parent/Admin
)
async def update_screen_time_rule_endpoint(
    *,
    rule_id: UUID,
    rule_in: ScreenTimeRuleUpdate, # Schema with optional fields
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_parent_or_admin)
):
    """
    Update an existing screen time rule. Requires Parent/Admin privileges.
    """
    logger.info(f"User {current_user.id} attempting to update rule {rule_id}")
    async with pool.connection() as conn:
        rule_db = await screen_time_crud.get_screen_time_rule_by_id(db=conn, rule_id=rule_id)
        if not rule_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screen time rule not found")

        # Permission Check: Ensure rule belongs to the current user's family
        if rule_db.family_id != current_user.family_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this rule.")

        # Perform the update using CRUD function
        updated_rule = await screen_time_crud.update_screen_time_rule(db=conn, rule=rule_db, rule_in=rule_in)
    return updated_rule


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Screen Time Rule",
    dependencies=[Depends(get_current_active_parent_or_admin)] # Require Parent/Admin
)
async def delete_screen_time_rule_endpoint(
    *,
    rule_id: UUID,
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_parent_or_admin)
):
    """
    Delete a screen time rule. Requires Parent/Admin privileges.
    """
    logger.info(f"User {current_user.id} attempting to delete rule {rule_id}")
    async with pool.connection() as conn:
        rule_db = await screen_time_crud.get_screen_time_rule_by_id(db=conn, rule_id=rule_id)
        if not rule_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screen time rule not found")

        # Permission Check: Ensure rule belongs to the current user's family
        if rule_db.family_id != current_user.family_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this rule.")

        # Perform the delete using CRUD function
        await screen_time_crud.delete_screen_time_rule(db=conn, rule_id=rule_id)
        # No response body needed for 204
    return None # Return None explicitly for 204


# === Screen Time Usage Endpoints ===

@router.post(
    "/usage",
    response_model=ScreenTimeUsageRead, # Return the created record
    status_code=status.HTTP_201_CREATED,
    summary="Log Screen Time Usage"
)
async def log_screen_time_usage_endpoint(
    *,
    usage_in: ScreenTimeUsageCreate, # Usage data from agent
    pool: AsyncConnectionPool = Depends(get_db_conn),
    # Auth for agent: This is complex. Needs a secure method.
    # Example: Using API Key dependency (implement get_api_key_user)
    # agent_user: UserReadMinimal = Depends(get_agent_user_via_api_key)
    # For now, we'll skip agent auth and assume data is trusted if it arrives
    # WARNING: THIS IS INSECURE FOR PRODUCTION - IMPLEMENT AGENT AUTH
):
    """
    Endpoint for device agents to log screen time usage sessions.
    **WARNING:** Needs proper authentication/authorization for the agent.
    """
    # TODO: Implement agent authentication/authorization mechanism
    logger.info(f"Received screen time usage log for user {usage_in.user_id}")
    # Basic validation: maybe check if user_id exists?
    async with pool.connection() as conn:
        # user = await user_crud.get_user_by_id(conn, usage_in.user_id) # Need user_crud import
        # if not user:
        #     raise HTTPException(status_code=400, detail="Invalid user ID provided in usage log")
        usage = await screen_time_crud.create_screen_time_usage(db=conn, usage_in=usage_in)
    # Optional: Trigger Celery task for real-time limit checks here
    return usage


@router.get("/usage", response_model=List[ScreenTimeUsageRead], summary="Get Screen Time Usage Logs")
async def read_screen_time_usage_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter usage logs for a specific user ID."),
    start_time: datetime = Query(..., description="Start timestamp for the query range (ISO format)."),
    end_time: datetime = Query(..., description="End timestamp for the query range (ISO format)."),
    limit: int = Query(1000, description="Maximum number of usage records to return.", ge=1, le=5000),
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_user)
):
    """
    Get screen time usage logs within a specified time range.
    - Parents/Admins can view logs for any user in their family by providing `user_id`.
    - Children can only view their own logs (if `user_id` is provided, it must match theirs).
    """
    if not current_user.family_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a family.")

    target_user_id = user_id # The user whose logs we want to fetch

    # --- Permission Logic ---
    is_parent_or_admin = str(current_user.role) in ["parent", "admin", "caregiver"]

    if target_user_id:
        # If specific user requested, check permissions
        if current_user.id != target_user_id and not is_parent_or_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user's usage.")
        # Parent/Admin needs check if target_user is in their family
        if is_parent_or_admin and current_user.id != target_user_id:
             async with pool.connection() as conn:
                 target_user = await user_crud.get_user_by_id(conn, target_user_id) # Need user_crud import
                 if not target_user or target_user.family_id != current_user.family_id:
                     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found in your family.")
    else:
        # If no specific user requested, default to current user if child,
        # or require parent/admin to specify user_id (or implement family-wide view)
        if not is_parent_or_admin:
            target_user_id = current_user.id # Child sees own data
        else:
            # Maybe allow parent/admin to see all family usage? Needs specific CRUD.
            # For now, require user_id for parents viewing specific child.
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please specify a user ID to view usage logs.")

    # --- End Permission Logic ---

    logger.info(f"User {current_user.id} fetching usage logs for user {target_user_id} between {start_time} and {end_time}")

    async with pool.connection() as conn:
        usage_logs = await screen_time_crud.get_screen_time_usage_for_user(
            db=conn,
            user_id=target_user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    return usage_logs


# === Screen Time Extension Request Endpoints ===

@router.post(
    "/requests",
    response_model=ScreenTimeExtensionRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Request Screen Time Extension"
)
async def create_extension_request_endpoint(
    *,
    request_in: ScreenTimeExtensionRequestCreate,
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_user) # Child usually initiates
):
    """
    Create a request for additional screen time (typically initiated by a child).
    The request body must specify the user ID (which must match the current user)
    and the rule ID the request pertains to.
    """
    # Permission/Validation: Ensure user is requesting for themselves
    if request_in.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot request extension for another user.")

    # Validation: Check if rule exists and belongs to the user/family
    async with pool.connection() as conn:
        rule = await screen_time_crud.get_screen_time_rule_by_id(db=conn, rule_id=request_in.rule_id)
        if not rule or rule.user_id != current_user.id:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated screen time rule not found or does not apply.")
        # Check if the rule allows extension requests
        if not rule.can_request_extension:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension requests are not allowed for this rule.")

        logger.info(f"User {current_user.id} creating screen time extension request for rule {request_in.rule_id}")
        new_request = await screen_time_crud.create_extension_request(db=conn, request_in=request_in)

    # Optional: Trigger notification to parent(s) via Celery/ntfy
    # Example: trigger_notification.delay(target_role='parent', family_id=current_user.family_id, message=...)

    return new_request


@router.put(
    "/requests/{request_id}/respond", # Changed path slightly for clarity
    response_model=ScreenTimeExtensionRequestRead,
    summary="Respond to Screen Time Extension Request",
    dependencies=[Depends(get_current_active_parent_or_admin)] # Require Parent/Admin
)
async def respond_extension_request_endpoint(
    *,
    request_id: UUID,
    response_in: ScreenTimeExtensionRequestUpdate, # Input: status, approved_minutes?, note?
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_parent_or_admin) # Responder
):
    """
    Approve or deny a screen time extension request (Parent/Admin action).
    """
    logger.info(f"User {current_user.id} responding to extension request {request_id} with status {response_in.status}")

    async with pool.connection() as conn:
        # Fetch the request to verify ownership and status
        request_db = await screen_time_crud.get_extension_request_by_id(db=conn, request_id=request_id)
        if not request_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extension request not found.")

        # Permission Check: Ensure the request belongs to the responder's family
        # Need to fetch the requesting user to check family ID
        requesting_user = await user_crud.get_user_by_id(conn, request_db.user_id) # Need user_crud import
        if not requesting_user or requesting_user.family_id != current_user.family_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to respond to this request.")

        # Check if request is still pending (handled partly by CRUD update WHERE clause)
        if request_db.status != RequestStatus.PENDING:
              raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request has already been actioned.")

        # Optional: Validate approved_minutes against rule's extension_limit_minutes
        if response_in.status == RequestStatus.APPROVED:
             rule = await screen_time_crud.get_screen_time_rule_by_id(db=conn, rule_id=request_db.rule_id)
             if rule and rule.extension_limit_minutes is not None:
                  if response_in.approved_minutes > rule.extension_limit_minutes:
                       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Approved minutes exceed limit ({rule.extension_limit_minutes}) for this rule.")

        # Perform the update using CRUD function
        updated_request = await screen_time_crud.update_extension_request_status(
            db=conn,
            request=request_db,
            response_in=response_in,
            responder_id=current_user.id
        )

    # Optional: Notify child of the response via Celery/ntfy

    return updated_request


@router.get("/requests", response_model=List[ScreenTimeExtensionRequestRead], summary="List Screen Time Extension Requests")
async def read_extension_requests_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter requests made by a specific user ID."),
    status: Optional[RequestStatus] = Query(None, description="Filter requests by status (pending, approved, denied)."),
    limit: int = Query(50, ge=1, le=200),
    pool: AsyncConnectionPool = Depends(get_db_conn),
    current_user: UserReadMinimal = Depends(get_current_active_user)
):
    """
    Get screen time extension requests.
    - Parents/Admins see all requests for their family.
    - Children see only their own requests.
    """
    if not current_user.family_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a family.")

    logger.info(f"User {current_user.id} fetching extension requests. Filter user_id: {user_id}, status: {status}")

    # Use the implemented CRUD function to get requests
    async with pool.connection() as conn:
        requests = await screen_time_crud.get_extension_requests_multi(
            db=conn,
            current_user=current_user, # Pass user for permission checks inside CRUD
            target_user_id=user_id,
            status=status,
            limit=limit
        )
    return requests