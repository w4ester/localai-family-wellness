# ./backend/app/db/models/chore_model.py
"""
Chore model for task management within the family wellness platform.
"""
from enum import Enum
from datetime import datetime # Keep standard datetime for type hinting
from typing import Optional, Dict, Any
from uuid import UUID # Keep standard UUID for type hinting

# Import necessary SQLAlchemy components
from sqlalchemy import String, ForeignKey, Text, Integer, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum # Import Enum type for database columns
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Use specific UUID type for column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import the Base class from your project structure
from app.db.base import Base


class ChoreStatus(str, Enum):
    """Enum defining the possible states of a chore."""
    PENDING = "pending"         # Newly created or recurring instance
    IN_PROGRESS = "in_progress" # Started by the assignee
    COMPLETED = "completed"     # Marked as done by assignee, awaiting verification
    VERIFIED = "verified"       # Confirmed as done by a parent/verifier
    OVERDUE = "overdue"         # Past due date and not completed/verified
    CANCELLED = "cancelled"     # No longer required


class ChoreRecurrence(str, Enum):
    """Enum defining how often a chore repeats."""
    ONCE = "once"               # Does not repeat
    DAILY = "daily"             # Repeats every day
    WEEKLY = "weekly"           # Repeats every week (config specifies day)
    MONTHLY = "monthly"         # Repeats every month (config specifies day/week)
    CUSTOM = "custom"           # Complex pattern defined in recurrence_config


class Chore(Base):
    """
    SQLAlchemy model representing a chore or task.
    """
    __tablename__ = "chore" # Explicit table name

    # --- Core Chore Information ---
    title: Mapped[str] = mapped_column(String, nullable=False, index=True) # Index title for searching
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Assignment & Ownership ---
    # The family this chore belongs to
    family_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("family.id"), nullable=False, index=True)
    family: Mapped["Family"] = relationship("Family", back_populates="chores") # Assumes 'chores' relationship on Family model

    # The user currently assigned to do this chore instance (can be null if unassigned)
    assignee_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True)
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assignee_id], backref="assigned_chores")

    # The user who originally created this chore template/schedule
    creator_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id], backref="created_chores")

    # --- Scheduling & Recurrence ---
    # When this specific instance of the chore is due
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # How the chore repeats
    recurrence: Mapped[ChoreRecurrence] = mapped_column(SQLEnum(ChoreRecurrence, name="chore_recurrence_enum", create_type=True), nullable=False, default=ChoreRecurrence.ONCE)

    # JSONB field to store details for complex recurrence (e.g., specific days of week/month)
    recurrence_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # --- Status & Progress Tracking ---
    # Current status of the chore instance
    status: Mapped[ChoreStatus] = mapped_column(SQLEnum(ChoreStatus, name="chore_status_enum", create_type=True), nullable=False, default=ChoreStatus.PENDING, index=True)

    # Timestamp when the assignee marked it as completed
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamp when a parent/verifier confirmed completion
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # User who verified the chore completion
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    verified_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by_id], backref="verified_chores")

    # --- Rewards ---
    # Points awarded upon verification
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Optional description of a non-point reward
    reward_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Flag indicating if the reward (points or other) has been processed/delivered
    reward_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Additional Information ---
    # Priority level (e.g., 1-5 scale)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)

    # Flexible tags for categorization (stored as JSON array of strings)
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True) # Example: ["kitchen", "cleaning", "allowance"]

    def __repr__(self):
        """String representation for debugging."""
        return f"<Chore id={self.id} title='{self.title}' status={self.status}>"</function_content>
