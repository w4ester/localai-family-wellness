# ./backend/app/api/v1/ai.py
"""
API endpoints for interacting with the AI core (chat, memory search).
"""
import logging
from typing import List, Optional, Dict, Any # Keep necessary typing imports
from uuid import UUID
from datetime import datetime # Keep datetime if used in schemas below

import psycopg # For DB connection type hint
from psycopg_pool import AsyncConnectionPool # Import pool type for hinting
from fastapi import APIRouter, Depends, HTTPException, status, Body # Added Body

# --- Dependency Imports ---
from app.db.session import get_db_conn # Dependency for DB connection pool
# !!! Placeholder: Implement this dependency to get validated user from token !!!
from app.auth.dependencies import get_current_active_user
# !!! Placeholder: Import the actual user schema returned by the dependency !!!
from app.schemas.user_schemas import UserReadMinimal # Assuming UserReadMinimal is defined here

# --- Schema Imports ---
# Import the schemas for request/response validation from their dedicated file
from app.schemas.ai_schemas import AIChatRequest, AIChatResponse, AIMemoryRead


# --- Service Function Import ---
# Import the main chat processing logic
from app.ai.service import process_chat_message_hybrid
# Import memory search function
from app.ai.memory import search_relevant_memories


# --- Router Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()


# --- API Endpoints ---

@router.post("/chat", response_model=AIChatResponse, summary="Send message to AI Chat")
async def handle_chat_message(
    # Use AIChatRequest schema imported from ai_schemas.py
    request_body: AIChatRequest = Body(...),
    # Dependency to get database pool connection wrapper
    pool: AsyncConnectionPool = Depends(get_db_conn),
    # Dependency to get the authenticated and active user making the request
    # Ensure get_current_active_user returns an object compatible with UserReadMinimal
    current_user: UserReadMinimal = Depends(get_current_active_user)
):
    """
    Receives a user's chat message, processes it using the stateful AI service
    (which handles memory, potential tool use, and LLM interaction), and returns
    the AI's final conversational response.
    """
    if not current_user.family_id:
        logger.warning(f"User {current_user.id} attempted chat without being in a family.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a family to use the AI chat."
        )

    # Prepare user info dictionary needed by the service function
    user_info = {
        "id": current_user.id,
        "name": current_user.first_name or current_user.username, # Use first name if available
        "role": current_user.role, # Pass the user's role
        "family_id": current_user.family_id,
        # Optional: Add family_name if easily available from dependency or another query
        # "family_name": current_user.family_name
    }

    logger.info(f"Received chat request from user {current_user.id} in family {current_user.family_id}")

    try:
        # Call the core AI processing function from the service layer
        ai_response_text = await process_chat_message_hybrid(
            pool=pool,
            user_info=user_info,
            message=request_body.message,
            # Pass chat_history=request_body.chat_history if managing history here
        )
        # Use AIChatResponse schema imported from ai_schemas.py
        return AIChatResponse(response=ai_response_text)

    # Catch potential exceptions from the AI service/tool client/db
    # Including HTTPExceptions raised by execute_tool
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        # Log unexpected errors and return a generic 500 response
        logger.error(f"Unexpected error processing chat for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your message."
        )


@router.get("/memory", response_model=List[AIMemoryRead], summary="Search AI Memory")
async def search_ai_memory(
    query: str, # Search query string
    limit: int = 10, # Max number of results
    # Dependency to get database pool connection wrapper
    pool: AsyncConnectionPool = Depends(get_db_conn),
    # Dependency to get the authenticated and active user making the request
    current_user: UserReadMinimal = Depends(get_current_active_user)
):
    """
    Searches the AI's memory using vector similarity for entries relevant
    to the provided query and pertaining to the current user's family context.

    Requires authentication. Returns a list of relevant memories.
    """
    if not current_user.family_id:
        logger.warning(f"User {current_user.id} attempted memory search without being in a family.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a family to search AI memory."
        )

    logger.info(f"User {current_user.id} searching memory with query: '{query[:50]}...'")

    try:
        # Call the memory search function from the memory module
        memories_data: List[Dict] = await search_relevant_memories(
            query_text=query,
            user_id=current_user.id,
            family_id=current_user.family_id,
            k=limit
            # Optionally pass a score_threshold here if desired
        )

        # FastAPI will automatically validate the returned list of dictionaries
        # against the List[AIMemoryRead] response_model.
        # Ensure the keys/types in the dictionaries returned by search_relevant_memories
        # match the fields defined in the AIMemoryRead schema.
        return memories_data

    except Exception as e:
        logger.error(f"Error during memory search for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while searching memory."
        )

# Add other AI-related endpoints as needed (e.g., managing specific memories, getting insights)