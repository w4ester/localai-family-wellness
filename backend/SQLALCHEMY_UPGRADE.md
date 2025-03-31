# SQLAlchemy 2.0 Upgrade Guide

This document explains the changes made to upgrade our models to SQLAlchemy 2.0 style.

## Changes Made

1. **Base Class Updated**
   - Changed from `@as_declarative` to extending `DeclarativeBase`
   - Updated column definitions to use `Mapped` types and `mapped_column`
   - Updated `declared_attr` to use `declared_attr.directive`

2. **Model Definitions Updated**
   - Changed `Column` to `mapped_column`
   - Added proper type annotations with `Mapped[type]`
   - Updated relationship definitions to use `Mapped[List["Model"]]`

3. **Alembic Configuration**
   - Updated the engine creation in `env.py`
   - Modified how the SQLAlchemy URL is accessed

## Working with SQLAlchemy 2.0

### Type Annotations

SQLAlchemy 2.0 requires type annotations for model attributes:

```python
# Old style:
name = Column(String, nullable=False, index=True)

# New style:
name: Mapped[str] = mapped_column(nullable=False, index=True)
```

### Relationships

Relationships need to be annotated with `Mapped`:

```python
# Old style:
users: List["User"] = relationship("User", back_populates="parent")

# New style:
users: Mapped[List["User"]] = relationship("User", back_populates="parent")
```

### Optional Fields

For nullable fields, use `Optional`:

```python
# For nullable fields:
description: Mapped[Optional[str]] = mapped_column(nullable=True)
```

## Running Migrations

1. **Generate an initial migration:**

```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
```

2. **Apply migrations:**

```bash
alembic upgrade head
```

3. **Roll back a migration:**

```bash
alembic downgrade -1  # Go back one revision
# OR
alembic downgrade <revision_id>  # Go back to specific revision
```

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy ORM Declarative Mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)
- [Type Annotations with Mapped](https://docs.sqlalchemy.org/en/20/orm/typing.html)
