"""
User model for database storage.
"""
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

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
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    # User information
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # User role
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.CHILD)
    
    # Family relationship
    family_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("family.id"), nullable=True)
    family: Mapped[Optional["Family"]] = relationship("Family", back_populates="members")
    
    # Parent-child relationship
    parent_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    children: Mapped[List["User"]] = relationship("User", foreign_keys=[parent_id], backref="parent", remote_side="User.id")
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Settings and preferences would be stored in a separate table</function_content>
