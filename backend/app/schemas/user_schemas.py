# ./backend/app/schemas/user_schemas.py
"""
Pydantic schemas for User data validation and API responses.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Import the UserRole enum from the model file
# Adjust path if UserRole enum is moved elsewhere
from app.db.models.user_model import UserRole


# --- Base Schema ---
# Contains common fields shared across other User schemas
class UserBase(BaseModel):
    # Fields loaded from Keycloak token or user input, not directly from DB Base typically
    # keycloak_id: Optional[str] = None # Usually handled internally based on token 'sub'
    username: Optional[str] = Field(None, description="Unique username", examples=["john_doe"])
    email: Optional[EmailStr] = Field(None, description="User's email address", examples=["user@example.com"])
    first_name: Optional[str] = Field(None, description="User's first name", examples=["John"])
    last_name: Optional[str] = Field(None, description="User's last name", examples=["Doe"])
    role: Optional[UserRole] = Field(None, description="User's role within the family")
    is_active: Optional[bool] = Field(True, description="Whether the user account is active")
    family_id: Optional[UUID] = Field(None, description="ID of the family the user belongs to")
    parent_id: Optional[UUID] = Field(None, description="ID of the user's parent (if applicable)")


# --- Create Schema ---
# Fields required when creating a new user (e.g., via admin or linking Keycloak user)
# Often minimal as Keycloak handles primary registration
class UserCreate(UserBase):
    keycloak_id: str = Field(..., description="Keycloak user ID ('sub' claim)")
    username: str # Make username required on creation
    role: UserRole = UserRole.CHILD # Default role on creation
    family_id: Optional[UUID] = None # Family might be assigned later


# --- Update Schema ---
# Fields allowed when updating a user's profile (e.g., PUT /users/me)
class UserUpdate(UserBase):
    # Allow updating optional fields like name, maybe email if synced
    # Keycloak ID, username, role changes might require specific admin actions
    username: Optional[str] = None # Usually username shouldn't be easily changeable
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    # Role/Family changes might need dedicated endpoints


# --- Read Schema (Database Representation) ---
# Represents a User object read from the database, used in API responses.
# Inherits fields from UserBase and adds DB-generated fields.
class UserRead(UserBase):
    id: UUID # Inherited from db.base.Base, now required in response
    keycloak_id: str # Always present when read from DB
    username: str # Always present when read from DB
    role: UserRole # Always present when read from DB
    is_active: bool # Always present when read from DB
    created_at: datetime # Inherited from db.base.Base
    updated_at: datetime # Inherited from db.base.Base

    # Optional relationships to include (if needed by frontend in specific responses)
    # family: Optional[Any] = None # Replace Any with FamilyRead schema if defined
    # children: Optional[List['UserRead']] = [] # Self-referential requires forward ref or post-update

    class Config:
        from_attributes = True # Enable creating schema from ORM model instance


# --- Minimal Read Schema (Used by Auth Dependency) ---
# A smaller schema, potentially returned by get_current_active_user dependency
class UserReadMinimal(BaseModel):
    id: UUID
    username: str
    family_id: Optional[UUID]
    role: UserRole # Return the Enum directly if possible, or str
    is_active: bool
    first_name: Optional[str] = None

    class Config:
        from_attributes = True

# If using self-referencing relationships like 'children' in UserRead,
# you might need to update forward refs after all models are defined:
# UserRead.model_rebuild()