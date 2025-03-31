"""
Base class for SQLAlchemy models.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


# Setup naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # Unique constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Foreign key
    "pk": "pk_%(table_name)s"  # Primary key
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)


# Base class using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all database models.
    
    Provides common columns:
    - id: UUID primary key
    - created_at: Timestamp when the record was created
    - updated_at: Timestamp when the record was last updated
    
    And automatic tablename generation based on class name.
    """
    # Use the configured metadata
    metadata = metadata
    
    # Primary key column with UUID type
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamps for creation and updates
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
                                               default=datetime.utcnow, 
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
                                               default=datetime.utcnow, 
                                               server_default=func.now(), 
                                               onupdate=func.now())
    
    # Auto-generate tablename from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate tablename from class name in lowercase (singular)."""
        return cls.__name__.lower()
