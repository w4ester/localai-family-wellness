# Backend Naming Fixes

This document outlines critical naming issues found in the LocalAI Family Wellness backend codebase and the required fixes.

## Critical Issues

### 1. File Naming Mismatch
There's a critical mismatch between the actual file name and how it's being imported and referenced.

**Action Required:**
- Rename `/Users/willf/smartIndex/epicforesters/localai-family-wellness/backend/app/db/models/screentime_model.py` to `screen_time_model.py`
- This file is being imported as `app.db.models.screen_time_model` in other files but the actual filename doesn't match

### 2. Missing Imports in API Files
In `screen_time.py`, you're using `user_crud` but it's not imported.

**Action Required:**
- Add to `/Users/willf/smartIndex/epicforesters/localai-family-wellness/backend/app/api/v1/screen_time.py`:
```python
from app.crud import user_crud
```

### 3. Missing Imports in CRUD Files
In `screen_time_crud.py`, you're using `HTTPException` and `status` but they're not imported.

**Action Required:**
- Add to `/Users/willf/smartIndex/epicforesters/localai-family-wellness/backend/app/crud/screen_time_crud.py`:
```python
from fastapi import HTTPException, status
```

### 4. Empty `/schema` Directory Removal
✅ You've already removed the empty `/schema` directory with the `.DS_Store` file.

### 5. Schema Validation Typo
In `screen_time_schemas.py`, there is a typo in an import.

**Action Required:**
- Change `model_validscreen_time_crudator` to `model_validator` in `/Users/willf/smartIndex/epicforesters/localai-family-wellness/backend/app/schemas/screen_time_schemas.py`

## Recommendations

### 1. Database Model Imports in Table Creation
Ensure all model imports are present in the `ensure_tables_created()` function in `session.py`.

**Recommendation:**
- Add these imports:
```python
from app.db.models.screen_time_model import ScreenTimeRule, ScreenTimeUsage, ScreenTimeExtensionRequest
from app.db.models.chore_model import Chore, ChoreCompletion  # If they exist
from app.db.models.ai_memory import AIMemory  # If it exists
```

### 2. Database Reference Consistency in CRUD Files
For consistency, use model attributes for table names rather than string literals.

**Recommendation:**
- Use this pattern consistently:
```python
sql = f'SELECT * FROM "{DBScreenTimeRule.__tablename__}" WHERE id = %s'
```

### 3. API Endpoint Naming Consistency
Your API endpoints mix singular and plural naming.

**Recommendation:**
- Standardize on plural naming for all endpoints:
```
ai.py → ais.py
auth.py → auths.py
```

## Implementation Checklist
- [ ] Rename screentime_model.py to screen_time_model.py
- [ ] Add missing import to screen_time.py: `from app.crud import user_crud`
- [ ] Add missing imports to screen_time_crud.py: `from fastapi import HTTPException, status`
- [ ] Fix the typo in screen_time_schemas.py: change `model_validscreen_time_crudator` to `model_validator` 
- [ ] Update model imports in session.py's `ensure_tables_created()` function (recommended)
- [ ] Standardize database reference pattern in CRUD files (recommended)
- [ ] Consider standardizing API endpoint naming (optional but recommended)
