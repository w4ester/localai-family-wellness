# ./backend/app/db/models/screen_time_model.py
"""
Screen time models for digital wellness tracking, rules, usage, and extension requests.
"""
from enum import Enum
from datetime import datetime, time # Keep standard datetime/time for type hinting
from typing import Optional, List, TYPE_CHECKING # Import List/TYPE_CHECKING for hints

from sqlalchemy import Column, String, ForeignKey, Text, Integer, Boolean, DateTime, Time
# Import necessary SQLAlchemy/PostgreSQL types
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
# Removed ARRAY as JSONB is used for lists in this version for simplicity
from sqlalchemy.orm import relationship

# Corrected import for the Base class
from app.db.base import Base

# Type checking imports to prevent runtime circular dependencies
if TYPE_CHECKING:
    from .user_model import User # noqa: F401
    from .family_model import Family # noqa: F401


class DayOfWeek(str, Enum):
    """Enum for days of the week."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AppCategory(str, Enum):
    """Enum for classifying application types."""
    SOCIAL_MEDIA = "social_media"
    GAMES = "games"
    EDUCATION = "education"
    PRODUCTIVITY = "productivity"
    ENTERTAINMENT = "entertainment"
    COMMUNICATION = "communication"
    UTILITY = "utility"
    OTHER = "other"


class RequestStatus(str, Enum):
    """Enum defining the status of an extension request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


# --- Screen Time Rule Model ---
class ScreenTimeRule(Base):
    """
    Screen time rules set by parents for specific children within a family.
    """
    __tablename__ = "screen_time_rule" # Explicit table name for clarity

    # --- Rule Information ---
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # --- Associations ---
    # Link to the family this rule belongs to
    family_id = Column(PG_UUID(as_uuid=True), ForeignKey("family.id"), nullable=False, index=True)
    family: "Family" = relationship("Family", back_populates="screen_time_rules") # Assumes 'screen_time_rules' on Family

    # Link to the specific user (child) this rule applies to
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    user: "User" = relationship("User", backref="screen_time_rules") # Using backref for simplicity

    # --- Time Limits & Scheduling ---
    # Optional overall daily limit in minutes for apps/categories covered by this rule
    daily_limit_minutes = Column(Integer, nullable=True)

    # Which days this rule is active (stored as JSON array of DayOfWeek strings)
    # Example: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    active_days = Column(JSONB, nullable=True, index=True) # Index for querying active rules today

    # Optional time window during which screen time is allowed under this rule
    start_time = Column(Time, nullable=True) # Timezone naive - interpreted in user's local context
    end_time = Column(Time, nullable=True)   # Timezone naive

    # --- Application & Content Rules (Using JSONB for flexibility) ---
    # List of specific app identifiers (e.g., bundle IDs, package names) blocked by this rule
    blocked_apps = Column(JSONB, nullable=True)

    # List of specific app identifiers explicitly allowed (overrides blocks if defined)
    allowed_apps = Column(JSONB, nullable=True)

    # List of AppCategory enum values blocked by this rule
    blocked_categories = Column(JSONB, nullable=True)

    # List of AppCategory enum values explicitly allowed (overrides blocks if defined)
    allowed_categories = Column(JSONB, nullable=True)

    # --- Rule Status & Overrides ---
    # Whether this rule is currently enabled
    is_active = Column(Boolean, default=True, nullable=False)

    # Can the child request more time when hitting limits imposed by this rule?
    can_request_extension = Column(Boolean, default=True, nullable=False)

    # Optional limit on how many extra minutes can be granted per extension request
    extension_limit_minutes = Column(Integer, nullable=True)

    # Relationship to extension requests made against this rule
    extension_requests: List["ScreenTimeExtensionRequest"] = relationship(
        "ScreenTimeExtensionRequest", back_populates="rule" # Correct back_populates
    )

    def __repr__(self):
        return f"<ScreenTimeRule id={self.id} name='{self.name}' user_id={self.user_id}>"


# --- Screen Time Usage Model ---
# IMPORTANT: Remember to run `SELECT create_hypertable('screen_time_usage', 'start_time');`
#            in PostgreSQL AFTER this table is created by your migrations/init script.
class ScreenTimeUsage(Base):
    """
    Records of actual screen time usage logged from device agents.
    Intended to be a TimescaleDB hypertable partitioned by 'start_time'.
    """
    __tablename__ = "screen_time_usage" # Explicit table name

    # --- Associations ---
    # User whose usage is being recorded
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    user: "User" = relationship("User", backref="screen_time_usage")

    # --- Time Period ---
    # Start time of the usage session (timezone aware) - Partition Key for TimescaleDB
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    # End time of the usage session (timezone aware)
    end_time = Column(DateTime(timezone=True), nullable=False)
    # Duration of the session in seconds
    duration_seconds = Column(Integer, nullable=False)

    # --- Device and Application ---
    # Identifier for the device used (optional)
    device_id = Column(String, nullable=True, index=True)
    # User-friendly name of the device (optional)
    device_name = Column(String, nullable=True)
    # Identifier of the application used (e.g., bundle ID, package name) (optional)
    app_identifier = Column(String, nullable=True, index=True)
    # User-friendly name of the application (optional)
    app_name = Column(String, nullable=True)
    # Detected or assigned category of the application (optional)
    app_category = Column(String, nullable=True, index=True) # Using String for simplicity

    # --- Additional Context ---
    # Type of activity if detectable (e.g., "browsing", "watching", "gaming") (optional)
    activity_type = Column(String, nullable=True)
    # Flexible JSONB for any other relevant context data (optional)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<ScreenTimeUsage user={self.user_id} app='{self.app_name}' duration={self.duration_seconds}s start={self.start_time}>"


# --- Screen Time Extension Request Model ---
class ScreenTimeExtensionRequest(Base):
    """
    Model representing a child's request for additional screen time,
    potentially overriding limits set by a ScreenTimeRule.
    """
    __tablename__ = "screen_time_extension_request" # Explicit table name

    # --- Associations ---
    # User making the request (child)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    user: "User" = relationship("User", foreign_keys=[user_id], backref="screen_time_requests")

    # The specific rule this request relates to
    # Corrected ForeignKey target table name (SQLAlchemy default lowercase)
    rule_id = Column(PG_UUID(as_uuid=True), ForeignKey("screen_time_rule.id"), nullable=False, index=True)
    rule: "ScreenTimeRule" = relationship("ScreenTimeRule", back_populates="extension_requests") # Correct back_populates

    # --- Request Details ---
    # How many extra minutes are being requested
    requested_minutes = Column(Integer, nullable=False)
    # Reason provided by the user for the request
    reason = Column(Text, nullable=True)

    # --- Status Tracking ---
    # Current status of the request (pending, approved, denied)
    status = Column(SQLEnum(RequestStatus, name="request_status_enum", create_type=True), nullable=False, default=RequestStatus.PENDING, index=True)

    # --- Response Details (filled when approved/denied) ---
    # Timestamp when the request was responded to
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # User (parent/caregiver) who responded to the request
    responded_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    responded_by: Optional["User"] = relationship("User", foreign_keys=[responded_by_id], backref="handled_screen_time_requests")

    # Actual number of extra minutes granted (may differ from requested)
    approved_minutes = Column(Integer, nullable=True)

    # Optional note from the responder
    response_note = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ScreenTimeExtensionRequest id={self.id} user={self.user_id} status={self.status} requested={self.requested_minutes}min>"