# Model Upgrade Notes

## How to Update Other Models

Here's a guide to update your remaining models to SQLAlchemy 2.0:

1. **Imports to Add/Change**:
   ```python
   # From:
   from sqlalchemy import Column, String, Boolean, Text
   from sqlalchemy.orm import relationship
   
   # To:
   from typing import List, Optional
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   ```

2. **Column Definitions**:
   ```python
   # From:
   name = Column(String, nullable=False, index=True)
   
   # To:
   name: Mapped[str] = mapped_column(nullable=False, index=True)
   ```

3. **Nullable Columns**:
   ```python
   # From:
   description = Column(Text, nullable=True)
   
   # To:
   description: Mapped[Optional[str]] = mapped_column(nullable=True)
   ```

4. **Boolean Columns**:
   ```python
   # From:
   is_active = Column(Boolean, default=True)
   
   # To:
   is_active: Mapped[bool] = mapped_column(default=True)
   ```

5. **Foreign Keys**:
   ```python
   # From:
   user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
   
   # To:
   user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
   ```

6. **Relationships**:
   ```python
   # From:
   users: List["User"] = relationship("User", back_populates="parent")
   
   # To:
   users: Mapped[List["User"]] = relationship("User", back_populates="parent")
   ```

7. **Single-Object Relationships**:
   ```python
   # From:
   parent = relationship("User", back_populates="children", foreign_keys=[parent_id])
   
   # To:
   parent: Mapped["User"] = relationship("User", back_populates="children", foreign_keys=[parent_id])
   ```

8. **Optional Relationships**:
   ```python
   # From:
   parent = relationship("User", back_populates="children", foreign_keys=[parent_id], nullable=True)
   
   # To:
   parent: Mapped[Optional["User"]] = relationship("User", back_populates="children", foreign_keys=[parent_id])
   ```

## Common Types to Use

- `str` for String and Text columns
- `int` for Integer columns
- `float` for Float columns
- `bool` for Boolean columns
- `datetime` for DateTime columns
- `uuid.UUID` for UUID columns
- `Dict[str, Any]` for JSONB columns

## Remember:

- Import `Optional` from typing for nullable columns
- Import `List` from typing for collections in relationships
- Update `TYPE_CHECKING` imports if needed
- Wrap relationship targets in quotes for forward references (e.g., `Mapped["User"]` not `Mapped[User]`)
