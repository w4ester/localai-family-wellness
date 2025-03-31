# ./backend/app/db/models/family_model.py
"""
Family model representing a family unit within the platform.
"""
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import the Base class from your project structure
from app.db.base import Base

# Type checking imports to avoid circular dependencies at runtime
# These models will import Family, so we use TYPE_CHECKING block
if TYPE_CHECKING:
    from .user_model import User # noqa: F401 - Needed for relationship type hint
    from .chore_model import Chore # noqa: F401 - Needed for relationship type hint
    from .screen_time_model import ScreenTimeRule # noqa: F401


class Family(Base):
    """
    SQLAlchemy model representing a family unit.
    """
    __tablename__ = "family" # Explicit table name

    # --- Family Information ---
    name: Mapped[str] = mapped_column(nullable=False, index=True) # Index name for searching
    description: Mapped[Optional[str]] = mapped_column(nullable=True) # Using Text type for potentially longer descriptions

    # --- Feature Settings ---
    # Flags to enable/disable core features at the family level
    allow_screen_time_monitoring: Mapped[bool] = mapped_column(default=True, nullable=False)
    allow_chore_management: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Add other feature flags as needed

    # --- Joining Mechanism ---
    # Optional unique code that new members can use to request joining this family
    join_code: Mapped[Optional[str]] = mapped_column(unique=True, index=True, nullable=True)

    # --- Relationships ---
    # One-to-Many relationship with User model
    # 'members' attribute will hold a list of User objects belonging to this family
    members: Mapped[List["User"]] = relationship(
        "User",
        back_populates="family", # Links to the 'family' attribute on the User model
        cascade="all, delete-orphan" # Deleting a family deletes its members
    )

    # One-to-Many relationship with Chore model
    # 'chores' attribute will hold a list of Chore objects belonging to this family
    chores: Mapped[List["Chore"]] = relationship(
        "Chore",
        back_populates="family", # Links to the 'family' attribute on the Chore model
        cascade="all, delete-orphan" # Deleting a family deletes its chores
    )

    # One-to-Many relationship with ScreenTimeRule model
    screen_time_rules: Mapped[List["ScreenTimeRule"]] = relationship(
        "ScreenTimeRule",
        back_populates="family", # Links to the 'family' attribute on ScreenTimeRule
        cascade="all, delete-orphan" # Deleting a family deletes its rules
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Family id={self.id} name='{self.name}'>"
