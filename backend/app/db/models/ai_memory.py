# ./backend/app/db/models/ai_memory.py
"""
AI Memory model for storing vector embeddings and context for stateful AI.

IMPORTANT: The `Vector` dimension in the `embedding` column below MUST match
           the output dimension of the embedding model specified in
           `settings.OLLAMA_EMBEDDING_MODEL` (defined in app/core/config.py).
           Check the model documentation (e.g., on Ollama Hub/Hugging Face)
           for the correct dimension (e.g., 768 for nomic-embed-text, 384 for all-minilm).
"""
from enum import Enum
from typing import Optional, TYPE_CHECKING # Added TYPE_CHECKING for hints
from uuid import UUID # Keep standard UUID import for type hinting

from sqlalchemy import Column, String, ForeignKey, Text, Integer
# Import necessary types from SQLAlchemy and PostgreSQL dialect
from sqlalchemy import Enum as SQLEnum # Import Enum type for database
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Use specific UUID type for column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# Import the Vector type from the pgvector SQLAlchemy integration library
from pgvector.sqlalchemy import Vector

# Import the Base class from your project structure
from app.db.base import Base

# Type checking import for User relationship hint
if TYPE_CHECKING:
    from .user_model import User # noqa: F401


class MemoryType(str, Enum):
    """Enum for classifying different types of AI memories."""
    CONVERSATION = "conversation" # Record of a user interaction
    INSIGHT = "insight"         # AI-generated observation or learning
    PREFERENCE = "preference"     # User-stated preference
    BEHAVIOR = "behavior"       # Observed user behavior pattern
    RULE = "rule"             # Explicit family rule or guideline
    SUMMARY = "summary"         # AI-generated summary of events/conversations
    GOAL = "goal"             # A user or family goal
    FACT = "fact"             # A factual piece of information


class AIMemory(Base):
    """
    AI Memory model for storing vector embeddings and associated context.
    Uses pgvector for efficient vector similarity search, enabling stateful AI.
    Each record represents a piece of knowledge or memory the AI has.
    """
    __tablename__ = "ai_memory" # Explicit table name

    # --- Relationships ---
    # Link to the user this memory primarily relates to (e.g., who said it, who it's about)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    # Defines the relationship to the User model. SQLAlchemy will automatically add a
    # collection (like 'aimemory_collection') to User instances unless 'backref' or
    # 'back_populates' is defined on the User model's side.
    user: "User" = relationship("User")

    # Link to the family this memory belongs to (for scoping)
    family_id = Column(PG_UUID(as_uuid=True), ForeignKey("family.id"), nullable=False, index=True)
    # No direct relationship object to Family needed by default unless frequently navigating Family -> Memory

    # --- Core Content ---
    # The textual content of the memory
    text = Column(Text, nullable=False)

    # --- Metadata & Classification ---
    # Type of memory, using the database Enum type for integrity
    memory_type = Column(SQLEnum(MemoryType, name="memory_type_enum", create_type=True), nullable=False, index=True)

    # Where did this memory originate? (e.g., 'user_chat', 'system_summary', 'rule_entry')
    source = Column(String, nullable=True, index=True)

    # Flexible JSONB field for additional structured metadata
    # (e.g., {'related_chore_id': '...', 'timestamp_range': '...'})
    metadata = Column(JSONB, nullable=True)

    # --- Retrieval Information ---
    # Importance score assigned by the system or user (higher = more important)
    importance = Column(Integer, nullable=False, default=1, index=True)

    # Vector embedding for similarity search (using pgvector)
    # See IMPORTANT note at the top of the file regarding the dimension!
    # Make sure this number (e.g., 768) matches your embedding model's output dimension.
    embedding = Column(Vector(768), nullable=False) # <-- ADJUST DIMENSION HERE

    def __repr__(self):
        """String representation for debugging."""
        return f"<AIMemory id={self.id} type={self.memory_type} importance={self.importance} text='{self.text[:50]}...'>"