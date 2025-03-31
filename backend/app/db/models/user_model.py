"""
User model for database storage.
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserRole(str, Enum):
    """Enum for user roles."""
    PARENT = "parent"
    CHILD = "child"
    CAREGIVER = "caregiver"
    ADMIN = "admin"


class User(Base):
    """
    User model for storing user information.
    Note: We don't store credentials here as they are managed by Keycloak.
    """
    
    # Keycloak user ID
    keycloak_id = Column(String, unique=True, index=True, nullable=False)
    
    # User information
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # User role
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CHILD)
    
    # Family relationship
    family_id = Column(UUID(as_uuid=True), ForeignKey("family.id"), nullable=True)
    family = relationship("Family", back_populates="members")
    
    # Parent-child relationship
    parent_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    children = relationship("User", backref="parent", remote_side=[id])
    
    # User status
    is_active = Column(Boolean, default=True)
    
    # Settings and preferences would be stored in a separate table