# ./backend/app/schemas/ai_schemas.py
"""
Pydantic schemas for AI-related API requests and responses, and data representation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

# --- Schemas for /chat Endpoint ---

class AIChatRequest(BaseModel):
    """
    Schema for the request body when sending a message to the AI chat.
    """
    message: str = Field(..., description="The user's text message to the AI assistant.")
    # Optional fields you might add later for more complex context management:
    # session_id: Optional[str] = Field(None, description="An optional session identifier to maintain conversation state across requests.")
    # chat_history: Optional[List[Tuple[str, str]]] = Field(None, description="Explicitly passed chat history (list of [human, ai] tuples). If not provided, history might be inferred from memory.")


class AIChatResponse(BaseModel):
    """
    Schema for the response body returned by the AI chat endpoint.
    """
    response: str = Field(..., description="The AI assistant's textual response to the user's message.")
    # Optional fields you might add later:
    # session_id: Optional[str] = Field(None, description="Session identifier if stateful sessions are used.")
    # suggested_actions: Optional[List[str]] = Field(None, description="Optional suggested follow-up actions.")


# --- Schema for Reading AI Memory ---

class AIMemoryRead(BaseModel):
    """
    Schema for representing an AI memory record when reading from the API.
    This defines the structure returned by the /memory endpoint.
    """
    id: UUID = Field(..., description="Unique identifier of the memory record.")
    text: str = Field(..., description="The textual content of the memory.")
    memory_type: str = Field(..., description="The type classification of the memory (e.g., 'conversation', 'insight').")
    source: Optional[str] = Field(None, description="The origin of this memory (e.g., 'user_chat', 'system_summary').")
    importance: int = Field(..., description="Importance score assigned to the memory.")
    created_at: datetime = Field(..., description="Timestamp when the memory was created.")
    updated_at: datetime = Field(..., description="Timestamp when the memory was last updated.")

    # Include relevance score if provided by the search function
    score: Optional[float] = Field(None, description="Relevance score from vector similarity search (higher is typically better).")

    # Include metadata if needed by the frontend
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured metadata associated with the memory.")

    class Config:
        # Enable creating Pydantic models from ORM objects (SQLAlchemy models)
        # Requires orm_mode = True in older Pydantic, from_attributes = True in Pydantic v2+
        from_attributes = True

# --- Optional: Schema for AI Memory Feedback ---
# class AIMemoryFeedback(BaseModel):
#     rating: int = Field(..., ge=1, le=5, description="User rating (e.g., 1-5) for memory relevance/accuracy.")
#     comment: Optional[str] = Field(None, description="Optional user comment.")