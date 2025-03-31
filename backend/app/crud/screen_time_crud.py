# ./backend/app/crud/screen_time_crud.py
"""
CRUD operations for ScreenTimeRule, ScreenTimeUsage, and ScreenTimeExtensionRequest.
"""
import logging
import json # Needed for JSONB/Array handling if not automatic
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status

import psycopg
from psycopg.rows import class_row, dict_row

# Import DB models and Pydantic schemas
from app.db.models.screen_time_model import ScreenTimeRule as DBScreenTimeRule, \
    ScreenTimeUsage as DBScreenTimeUsage, \
    ScreenTimeExtensionRequest as DBExtensionRequest, \
    DayOfWeek, AppCategory, RequestStatus # Import Enums
from app.schemas.screen_time_schemas import ScreenTimeRuleCreate, ScreenTimeRuleUpdate, \
    ScreenTimeUsageCreate, ScreenTimeExtensionRequestCreate, ScreenTimeExtensionRequestUpdate

logger = logging.getLogger(__name__)

# === ScreenTimeRule CRUD ===

async def create_screen_time_rule(db: psycopg.AsyncConnection, rule_in: ScreenTimeRuleCreate) -> DBScreenTimeRule:
    """Create a new screen time rule."""
    logger.info(f"Creating screen time rule '{rule_in.name}' for user {rule_in.user_id}")

    # Handle JSONB/ARRAY fields - psycopg might handle lists directly for JSONB, check driver docs
    active_days_json = json.dumps([day.value for day in rule_in.active_days]) if rule_in.active_days else None
    blocked_apps_json = json.dumps(rule_in.blocked_apps) if rule_in.blocked_apps else None
    allowed_apps_json = json.dumps(rule_in.allowed_apps) if rule_in.allowed_apps else None
    blocked_categories_json = json.dumps([cat.value for cat in rule_in.blocked_categories]) if rule_in.blocked_categories else None
    allowed_categories_json = json.dumps([cat.value for cat in rule_in.allowed_categories]) if rule_in.allowed_categories else None

    sql = f"""
        INSERT INTO "{DBScreenTimeRule.__tablename__}" (
            name, description, family_id, user_id, daily_limit_minutes,
            active_days, start_time, end_time, blocked_apps, allowed_apps,
            blocked_categories, allowed_categories, is_active, can_request_extension,
            extension_limit_minutes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    params = (
        rule_in.name, rule_in.description, rule_in.family_id, rule_in.user_id, rule_in.daily_limit_minutes,
        active_days_json, rule_in.start_time, rule_in.end_time, blocked_apps_json, allowed_apps_json,
        blocked_categories_json, allowed_categories_json,
        rule_in.is_active if rule_in.is_active is not None else True,
        rule_in.can_request_extension if rule_in.can_request_extension is not None else True,
        rule_in.extension_limit_minutes
    )
    async with db.cursor(row_factory=class_row(DBScreenTimeRule)) as cur:
        try:
            await cur.execute(sql, params)
            created_rule = await cur.fetchone()
            if not created_rule: raise Exception("Rule creation failed.")
            logger.info(f"Screen time rule '{created_rule.name}' created with ID: {created_rule.id}")
            return created_rule
        except Exception as e:
            logger.error(f"Error creating screen time rule '{rule_in.name}': {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating rule")


async def get_screen_time_rule_by_id(db: psycopg.AsyncConnection, rule_id: UUID) -> Optional[DBScreenTimeRule]:
    """Fetch a single screen time rule by ID."""
    logger.debug(f"Getting screen time rule by ID: {rule_id}")
    async with db.cursor(row_factory=class_row(DBScreenTimeRule)) as cur:
        await cur.execute(f'SELECT * FROM "{DBScreenTimeRule.__tablename__}" WHERE id = %s', (rule_id,))
        rule = await cur.fetchone()
        return rule


async def get_screen_time_rules_for_user(db: psycopg.AsyncConnection, user_id: UUID) -> List[DBScreenTimeRule]:
    """Fetch all active screen time rules for a specific user."""
    logger.debug(f"Getting screen time rules for user ID: {user_id}")
    async with db.cursor(row_factory=class_row(DBScreenTimeRule)) as cur:
        await cur.execute(
            f'SELECT * FROM "{DBScreenTimeRule.__tablename__}" WHERE user_id = %s AND is_active = TRUE ORDER BY created_at',
            (user_id,)
        )
        rules = await cur.fetchall()
        return rules

# --- Implement update_screen_time_rule similar to update_chore ---
# async def update_screen_time_rule(db: psycopg.AsyncConnection, rule: DBScreenTimeRule, rule_in: ScreenTimeRuleUpdate) -> DBScreenTimeRule: ...

# --- Implement delete_screen_time_rule if needed ---
# async def delete_screen_time_rule(db: psycopg.AsyncConnection, rule_id: UUID) -> Optional[DBScreenTimeRule]: ...


# === ScreenTimeUsage CRUD ===

async def create_screen_time_usage(db: psycopg.AsyncConnection, usage_in: ScreenTimeUsageCreate) -> DBScreenTimeUsage:
    """Log a new screen time usage record."""
    # Note: Assumes device agent provides necessary data correctly
    logger.debug(f"Logging screen time usage for user {usage_in.user_id}, app '{usage_in.app_name}'")

    # Handle JSONB metadata
    metadata_json = json.dumps(usage_in.metadata) if usage_in.metadata else None

    sql = f"""
        INSERT INTO "{DBScreenTimeUsage.__tablename__}" (
            user_id, start_time, end_time, duration_seconds, device_id,
            device_name, app_identifier, app_name, app_category,
            activity_type, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    params = (
        usage_in.user_id, usage_in.start_time, usage_in.end_time, usage_in.duration_seconds, usage_in.device_id,
        usage_in.device_name, usage_in.app_identifier, usage_in.app_name, usage_in.app_category,
        usage_in.activity_type, metadata_json
    )
    async with db.cursor(row_factory=class_row(DBScreenTimeUsage)) as cur:
        try:
            await cur.execute(sql, params)
            created_usage = await cur.fetchone()
            if not created_usage: raise Exception("Usage log creation failed.")
            # No commit needed usually with 'async with pool.connection()'
            return created_usage
        except Exception as e:
            logger.error(f"Error logging screen time usage for user {usage_in.user_id}: {e}", exc_info=True)
            await db.rollback() # Explicit rollback on error might be wise here
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error logging usage")

async def get_screen_time_usage_for_user(
    db: psycopg.AsyncConnection,
    user_id: UUID,
    start_time: datetime,
    end_time: datetime,
    limit: int = 1000
) -> List[DBScreenTimeUsage]:
    """Fetch screen time usage records for a user within a time range."""
    logger.debug(f"Getting usage for user {user_id} between {start_time} and {end_time}")
    sql = f"""
        SELECT * FROM "{DBScreenTimeUsage.__tablename__}"
        WHERE user_id = %s AND start_time >= %s AND end_time <= %s
        ORDER BY start_time DESC
        LIMIT %s
        """
    params = (user_id, start_time, end_time, limit)
    async with db.cursor(row_factory=class_row(DBScreenTimeUsage)) as cur:
        await cur.execute(sql, params)
        usage_logs = await cur.fetchall()
        return usage_logs


async def update_screen_time_rule(
    db: psycopg.AsyncConnection,
    rule: DBScreenTimeRule,
    rule_in: ScreenTimeRuleUpdate
) -> DBScreenTimeRule:
    """Update an existing screen time rule."""
    logger.debug(f"Updating screen time rule ID: {rule.id}")
    # Get fields to update from the input schema, excluding unset fields
    update_data = rule_in.model_dump(exclude_unset=True)

    if not update_data:
        logger.debug(f"No update data provided for rule {rule.id}")
        return rule # Return original if no changes

    # Prepare SQL update statement dynamically
    fields_to_update = []
    values_to_update = []
    for key, value in update_data.items():
        # Ensure the key is a valid column in the ScreenTimeRule model
        if hasattr(DBScreenTimeRule, key) and key != 'id':
            fields_to_update.append(f'"{key}" = %s')
            # Handle complex types that need serialization (JSONB, potentially Enums if stored as strings)
            if key in ["active_days", "blocked_apps", "allowed_apps", "blocked_categories", "allowed_categories"] and value is not None:
                # For JSONB, ensure value is dumped to JSON string if psycopg doesn't handle dicts/lists automatically
                # For Enums stored in JSONB (like categories), dump their .value
                if key in ["blocked_categories", "allowed_categories"]:
                     values_to_update.append(json.dumps([enum_val.value for enum_val in value]))
                elif key == "active_days":
                     values_to_update.append(json.dumps([enum_val.value for enum_val in value]))
                else: # blocked_apps, allowed_apps are likely lists of strings already
                     values_to_update.append(json.dumps(value))
            elif isinstance(value, Enum): # Handle direct SQLEnum columns if any
                 values_to_update.append(value.value)
            else:
                 values_to_update.append(value)

    if not fields_to_update:
        logger.warning(f"No valid fields provided for updating rule {rule.id}")
        return rule # Return original if no valid fields were provided

    # Add updated_at automatically (handled by Base model)

    set_clause = ", ".join(fields_to_update)
    sql = f'UPDATE "{DBScreenTimeRule.__tablename__}" SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *'
    params = values_to_update + [rule.id]

    logger.debug(f"Executing update for rule {rule.id}: SQL='{sql}' PARAMS='{params}'")
    async with db.cursor(row_factory=class_row(DBScreenTimeRule)) as cur:
         try:
            await cur.execute(sql, tuple(params)) # Ensure params is a tuple
            updated_rule = await cur.fetchone()
            if not updated_rule:
                 raise Exception("Screen time rule update failed unexpectedly.")
            logger.info(f"Screen time rule '{updated_rule.name}' (ID: {updated_rule.id}) updated successfully.")
            return updated_rule
         except Exception as e:
             logger.error(f"Error updating screen time rule {rule.id}: {e}", exc_info=True)
             await db.rollback()
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating screen time rule") from e


async def delete_screen_time_rule(db: psycopg.AsyncConnection, rule_id: UUID) -> Optional[DBScreenTimeRule]:
    """Delete a screen time rule by ID."""
    # Note: Consider implications of cascade delete defined in relationships (e.g., deleting requests)
    logger.warning(f"Attempting deletion of screen time rule ID: {rule_id}")
    async with db.cursor(row_factory=class_row(DBScreenTimeRule)) as cur:
        try:
            # Return the deleted item to confirm
            await cur.execute(f'DELETE FROM "{DBScreenTimeRule.__tablename__}" WHERE id = %s RETURNING *', (rule_id,))
            deleted_rule = await cur.fetchone()
            # Commit handled by context manager
            if deleted_rule:
                 logger.info(f"Successfully deleted screen time rule '{deleted_rule.name}' (ID: {rule_id})")
            else:
                 logger.warning(f"Screen time rule ID {rule_id} not found for deletion.")
            return deleted_rule
        except Exception as e:
             logger.error(f"Error deleting screen time rule {rule_id}: {e}", exc_info=True)
             await db.rollback()
             # Could raise 404 here too if needed based on specific DB errors like ForeignKeyViolation
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting screen time rule")


# === ScreenTimeExtensionRequest CRUD ===

async def create_extension_request(db: psycopg.AsyncConnection, request_in: ScreenTimeExtensionRequestCreate) -> DBExtensionRequest:
    """Create a new screen time extension request."""
    logger.info(f"Creating extension request for user {request_in.user_id} regarding rule {request_in.rule_id}")

    sql = f"""
        INSERT INTO "{DBExtensionRequest.__tablename__}" (user_id, rule_id, requested_minutes, reason, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    params = (
        request_in.user_id, request_in.rule_id, request_in.requested_minutes, request_in.reason,
        RequestStatus.PENDING.value # Ensure default status is set
    )
    async with db.cursor(row_factory=class_row(DBExtensionRequest)) as cur:
        try:
            await cur.execute(sql, params)
            created_request = await cur.fetchone()
            if not created_request: raise Exception("Extension request creation failed.")
            logger.info(f"Extension request {created_request.id} created.")
            return created_request
        except Exception as e:
            logger.error(f"Error creating extension request for user {request_in.user_id}: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating request")

async def get_extension_request_by_id(db: psycopg.AsyncConnection, request_id: UUID) -> Optional[DBExtensionRequest]:
    """Fetch a single extension request by ID."""
    logger.debug(f"Getting extension request by ID: {request_id}")
    async with db.cursor(row_factory=class_row(DBExtensionRequest)) as cur:
        await cur.execute(f'SELECT * FROM "{DBExtensionRequest.__tablename__}" WHERE id = %s', (request_id,))
        request = await cur.fetchone()
        return request

async def update_extension_request_status(
    db: psycopg.AsyncConnection,
    request: DBExtensionRequest,
    response_in: ScreenTimeExtensionRequestUpdate,
    responder_id: UUID
) -> DBExtensionRequest:
    """Update the status and response fields of an extension request."""
    logger.info(f"Updating extension request {request.id} status to {response_in.status.value} by user {responder_id}")

    status_value = response_in.status.value # Get string value from enum
    approved_minutes_value = response_in.approved_minutes if status_value == RequestStatus.APPROVED.value else None

    sql = f"""
        UPDATE "{DBExtensionRequest.__tablename__}"
        SET status = %s,
            responded_at = NOW(),
            responded_by_id = %s,
            approved_minutes = %s,
            response_note = %s,
            updated_at = NOW()
        WHERE id = %s AND status = %s -- Prevent race conditions, only update pending
        RETURNING *
    """
    params = (
        status_value, responder_id, approved_minutes_value, response_in.response_note,
        request.id, RequestStatus.PENDING.value
    )
    async with db.cursor(row_factory=class_row(DBExtensionRequest)) as cur:
        try:
            await cur.execute(sql, params)
            updated_request = await cur.fetchone()
            if not updated_request:
                 # Could be because status wasn't PENDING or ID mismatch
                 logger.warning(f"Failed to update extension request {request.id}. May have already been actioned or ID mismatch.")
                 # Re-fetch current state to check
                 current_state = await get_extension_request_by_id(db, request.id)
                 if current_state and current_state.status != RequestStatus.PENDING:
                      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request has already been actioned.")
                 else:
                      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found or update failed.")

            logger.info(f"Extension request {updated_request.id} status updated to {updated_request.status}.")
            return updated_request
        except Exception as e:
            logger.error(f"Error updating extension request {request.id}: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating request")

async def get_extension_requests_multi(
    db: psycopg.AsyncConnection,
    current_user: Any,
    target_user_id: Optional[UUID] = None,
    status: Optional[RequestStatus] = None,
    limit: int = 50
) -> List[DBExtensionRequest]:
    """
    Get multiple extension requests with filtering based on user permissions.
    - Parents/Admins can see all requests in their family
    - Children can only see their own requests
    
    Args:
        db: Database connection
        current_user: The authenticated user making the request
        target_user_id: Optional filter for a specific user's requests
        status: Optional filter for request status
        limit: Maximum number of requests to return
        
    Returns:
        List of extension requests matching the criteria
    """
    logger.debug(f"Getting extension requests. User: {current_user.id}, Target: {target_user_id}, Status: {status}")
    
    is_parent_or_admin = str(current_user.role).lower() in ["parent", "admin", "caregiver"]
    family_id = current_user.family_id
    
    if not family_id:
        logger.warning(f"User {current_user.id} has no family_id when fetching extension requests")
        return [] # Return empty list if no family
    
    # Base query conditions
    conditions = []
    params = []
    
    # Filter by status if provided
    if status:
        conditions.append(f"status = %s")
        params.append(status.value)
    
    # Apply user-based filtering
    if is_parent_or_admin:
        # Parent/Admin: Get requests within family by joining with users table
        if target_user_id:
            # If specific user requested, verify they're in the family
            sql = f"""
                SELECT r.* 
                FROM {DBExtensionRequest.__tablename__} r
                JOIN user u ON r.user_id = u.id
                WHERE u.family_id = %s AND r.user_id = %s
            """
            params = [family_id, target_user_id] + params  # Prepend family_id and user_id
        else:
            # Get all requests from users in the family
            sql = f"""
                SELECT r.*
                FROM {DBExtensionRequest.__tablename__} r
                JOIN user u ON r.user_id = u.id
                WHERE u.family_id = %s
            """
            params = [family_id] + params  # Prepend family_id
    else:
        # Child: Only see own requests regardless of target_user_id
        sql = f'SELECT * FROM "{DBExtensionRequest.__tablename__}" WHERE user_id = %s'
        params = [current_user.id] + params  # Prepend user_id
    
    # Add status condition to SQL if needed
    if status and not is_parent_or_admin:
        sql += " AND status = %s"
    elif status and is_parent_or_admin and "WHERE" not in sql:
        sql += " WHERE status = %s"
    elif status and is_parent_or_admin:
        sql += " AND status = %s"
    
    # Add order and limit
    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    # Execute the query
    async with db.cursor(row_factory=class_row(DBExtensionRequest)) as cur:
        try:
            await cur.execute(sql, tuple(params))
            requests = await cur.fetchall()
            logger.debug(f"Found {len(requests)} extension requests matching criteria")
            return requests
        except Exception as e:
            logger.error(f"Error fetching extension requests: {e}", exc_info=True)
            # No need to rollback for a SELECT query
            return []  # Return empty list on error