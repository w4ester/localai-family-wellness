# Local AI Family Wellness Platform - API Version 1 Endpoints

This directory contains the specific API endpoint routers for version 1 (`/api/v1`) of the platform's backend service. Each file groups endpoints related to a specific domain or feature.

These routers are aggregated by `../router.py` (i.e., `backend/app/api/router.py`) and included in the main FastAPI application defined in `../../main.py` (i.e., `backend/app/main.py`).

## Endpoint Modules & Implementation Tasks

The following files contain placeholder endpoint definitions. You need to replace the placeholder comments and logic with actual implementations.

**Key Implementation Areas for MOST Endpoint Files:**

*   **Schemas:** Define Pydantic models for request bodies (`Create`, `Update`) and response bodies (`Read`) in the `app.schemas` directory (e.g., `app/schemas/user.py`, `app/schemas/family.py`). Import and use these schemas for validation and serialization in the endpoint function signatures (`request: UserCreate`, `response_model=UserRead`).
*   **CRUD/Service Functions:** Implement the core business logic for interacting with the database (Create, Read, Update, Delete operations) in the `app.crud` or `app/services` directory (e.g., `app/crud/user.py`, `app/services/chore_service.py`). Import and call these functions from within your endpoint handlers.
*   **Dependencies:**
    *   **Authentication:** Implement dependency functions (e.g., in `app/auth/dependencies.py`) like `get_current_active_user` or role-specific ones (`get_current_active_parent`) to handle token validation (using Keycloak JWTs) and retrieve the authenticated user object. Use `Depends()` with these functions in endpoint signatures to protect routes and get user context.
    *   **Database Session:** Use the database connection dependency `get_db_conn` (defined in `app/db/session.py`) via `Depends(get_db_conn)` in endpoint signatures to get a database connection from the pool.
*   **Endpoint Logic:** Write the main logic within each endpoint function (`async def ...`), calling CRUD/service functions, handling potential errors (e.g., raising `HTTPException` for 404 Not Found or 403 Forbidden), and returning the appropriate data according to the response schema.
*   **Permission Checks:** Explicitly implement logic within endpoints to verify if the `current_user` has the necessary permissions (based on their role, family membership, ownership, etc.) to perform the requested action.

---

### 1. `auth.py`

*   **File Path:** `./auth.py`
*   **Purpose:** Handles API interactions related to authentication, primarily providing configuration details for frontend OIDC clients or potentially handling token exchanges if needed.
*   **Tasks:**
    *   Implement the `/api/v1/auth/config` endpoint: Define a schema (e.g., `KeycloakConfig`) in `app/schemas/` and return the necessary Keycloak details (`realm`, `url`, *frontend* `clientId`) from `app.core.config.settings`.
    *   Decide if other endpoints (like `/login/access-token` or `/refresh`) are truly necessary given the Keycloak OIDC redirect flow. Implement if required, including interaction with Keycloak's token endpoint.

---

### 2. `users.py`

*   **File Path:** `./users.py`
*   **Purpose:** Endpoints for managing user profiles and retrieving user information.
*   **Tasks:**
    *   Define `UserRead`, `UserUpdate` schemas in `app/schemas/user.py`.
    *   Implement `get_current_active_user` dependency in `app/auth/dependencies.py`.
    *   Implement CRUD functions for users (get, get_multi, update) in `app/crud/user.py`.
    *   Implement `GET /api/v1/users/me`: Use `get_current_active_user` dependency and return user data based on `UserRead` schema.
    *   Implement `GET /api/v1/users/{user_id}`: Fetch user using CRUD function, implement permission checks (e.g., admin or family member), return data based on `UserRead`.
    *   Implement `PUT /api/v1/users/me`: Use `get_current_active_user`, validate input using `UserUpdate` schema, update user using CRUD function, return updated data.
    *   Consider other admin endpoints like `GET /api/v1/users/` (list all) or `DELETE /api/v1/users/{user_id}` with strict permission checks.

---

### 3. `families.py`

*   **File Path:** `./families.py`
*   **Purpose:** Endpoints for creating, joining, managing, and retrieving family information.
*   **Tasks:**
    *   Define `FamilyRead`, `FamilyCreate`, `FamilyUpdate` schemas in `app/schemas/family.py`. Reference `UserRead` schema for members list.
    *   Implement `get_current_active_user` (and potentially `get_current_active_parent`) dependency.
    *   Implement CRUD functions for families (create, get, update, add\_member, remove\_member, generate\_code) in `app/crud/family.py`.
    *   Implement `POST /api/v1/families/`: Use auth dependency, validate input (`FamilyCreate`), call CRUD `create_with_owner` function, return `FamilyRead`.
    *   Implement `GET /api/v1/families/{family_id}`: Use auth dependency, implement permission check (user is member), call CRUD `get` function, return `FamilyRead`.
    *   Implement `GET /api/v1/families/{family_id}/members`: Use auth dependency, implement permission check, call optimized CRUD function to get family with members, return `List[UserRead]`.
    *   Implement endpoints for joining, leaving, inviting, managing members, and handling join codes, each with appropriate permission checks.

---

### 4. `ai.py`

*   **File Path:** `./ai.py`
*   **Purpose:** Endpoints for interacting with the core AI features (chat, memory search, insights).
*   **Tasks:**
    *   Define `AIChatRequest`, `AIChatResponse`, `AIMemoryRead` schemas in `app/schemas/ai.py`.
    *   Implement `get_current_active_user` dependency.
    *   Implement AI service functions (e.g., in `app/ai/service.py`) that orchestrate LangChain/LlamaIndex interactions:
        *   `process_chat_message`: Takes user input, fetches context from `pgvector` (via CRUD helper), calls Ollama via LangChain, updates memory (stores new embedding in `pgvector`), returns response.
        *   `search_memories`: Takes a query, generates embedding, performs vector similarity search in `pgvector`, retrieves relevant memories, implements permission filtering.
    *   Implement `POST /api/v1/ai/chat`: Use auth dependency, validate request (`AIChatRequest`), call `process_chat_message` service function, return `AIChatResponse`.
    *   Implement `GET /api/v1/ai/memory`: Use auth dependency, validate query parameter, call `search_memories` service function, implement permission filtering, return `List[AIMemoryRead]`.
    *   Consider endpoints for retrieving generated insights or providing feedback on memory items.

---

### 5. `chores.py`

*   **File Path:** `./chores.py`
*   **Purpose:** Endpoints for creating, assigning, updating, and listing chores.
*   **Tasks:**
    *   Define `ChoreRead`, `ChoreCreate`, `ChoreUpdate` schemas in `app/schemas/chore.py`.
    *   Implement `get_current_active_user` (and potentially `get_current_active_parent`) dependency.
    *   Implement CRUD functions for chores (create, get, get\_multi, update, delete) in `app/crud/chore.py`.
    *   Implement `POST /api/v1/chores/`: Use auth dependency, check permissions (e.g., parent role), validate input (`ChoreCreate`), call CRUD `create` function, return `ChoreRead`.
    *   Implement `GET /api/v1/chores/`: Use auth dependency, get chores for user's family using CRUD `get_multi_by_family` (implement filtering by assignee/status), return `List[ChoreRead]`.
    *   Implement `PUT /api/v1/chores/{chore_id}`: Use auth dependency, fetch chore using CRUD `get`, implement permission checks (e.g., assignee can mark complete, parent can verify/edit), validate input (`ChoreUpdate`), call CRUD `update` function. Potentially trigger Celery task for reward processing upon verification. Return `ChoreRead`.
    *   Implement `GET /api/v1/chores/{chore_id}` and `DELETE /api/v1/chores/{chore_id}` with appropriate permissions.

---

### 6. `screen_time.py`

*   **File Path:** `./screen_time.py`
*   **Purpose:** Endpoints for managing screen time rules, logging usage, and handling extension requests.
*   **Tasks:**
    *   Define schemas (`ScreenTimeRuleRead/Create/Update`, `ScreenTimeUsageRead/Create`, `ScreenTimeExtensionRequestRead/Create/Update`) in `app/schemas/screen_time.py`.
    *   Implement necessary auth dependencies (`get_current_active_user`, `get_current_active_parent`, potentially an `get_agent_user` or API key check for usage logging).
    *   Implement CRUD functions for rules, usage logs, and extension requests in `app/crud/screen_time.py` (or separate files).
    *   Implement rule endpoints (`POST /rules`, `GET /rules`, `PUT /rules/{rule_id}`, `DELETE /rules/{rule_id}`) with parent permission checks.
    *   Implement usage logging endpoint (`POST /usage`) - ensure proper authentication/authorization for device agents logging data. Consider rate limiting. Potentially trigger Celery tasks for limit enforcement checks.
    *   Implement usage retrieval endpoint (`GET /usage`) with filtering (user, time range) and permission checks (parent sees family, child sees own).
    *   Implement extension request endpoints (`POST /requests` - child action, `PUT /requests/{request_id}` - parent action, `GET /requests`) with appropriate logic and notifications.

---

By systematically implementing the schemas, CRUD/service functions, dependencies, and endpoint logic outlined above for each file, you will build out the functional API for your platform.
