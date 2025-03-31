# ./backend/app/schemas/family_schemas.py
"""
Pydantic schemas for Family data validation and API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Import related schemas - Use forward references if needed initially
from .user_schemas import UserRead # To represent members

# Type checking imports for forward references if UserRead imports FamilyRead
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # This avoids circular imports at runtime but allows type checking
    pass


# --- Base Schema ---
class FamilyBase(BaseModel):
    name: Optional[str] = Field(None, description="Name of the family unit", examples=["The Doe Family"])
    description: Optional[str] = Field(None, description="Optional description for the family")
    allow_screen_time_monitoring: Optional[bool] = Field(True, description="Family-wide setting to enable/disable screen time features")
    allow_chore_management: Optional[bool] = Field(True, description="Family-wide setting to enable/disable chore features")
    # join_code is typically read-only or managed via specific endpoints


# --- Create Schema ---
class FamilyCreate(FamilyBase):
    name: str = Field(..., description="Name of the family unit", examples=["The Doe Family"])
    # Creator implicitly becomes first member (handled in CRUD/service)


# --- Update Schema ---
class FamilyUpdate(FamilyBase):
    # Allow updating name, description, and settings
    pass # Inherits optional fields from FamilyBase


# --- Read Schema ---
class FamilyRead(FamilyBase):
    id: UUID
    name: str # Name is required when reading
    join_code: Optional[str] = Field(None, description="Code used for joining the family (display only when appropriate)")
    created_at: datetime
    updated_at: datetime

    # Include members when reading family details? Often yes.
    # Use the UserRead schema defined in user_schemas.py
    members: List[UserRead] = [] # Default to empty list

    # Optional: Include ChoreRead, ScreenTimeRuleRead if needed in this response
    # chores: List[ChoreRead] = []
    # screen_time_rules: List[ScreenTimeRuleRead] = []

    class Config:
        from_attributes = True # Enable creating from ORM model instance

# Optional: If UserRead needs FamilyRead, update forward refs after all definitions
# Needs careful handling or separate minimal schemas to avoid deep nesting
# UserRead.model_rebuild()