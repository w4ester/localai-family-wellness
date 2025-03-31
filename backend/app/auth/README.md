# Authentication System Documentation

This document describes the authentication system for the LocalAI Family Wellness Platform.

## Overview

The application uses Keycloak as its authentication provider with the OAuth2 Authorization Code flow. This provides:

- Secure authentication with JWT tokens
- Role-based authorization
- User management outside the application

## Architecture

1. **Frontend**: Initiates the OAuth flow by redirecting to Keycloak's login page
2. **Keycloak**: Authenticates the user and redirects back with an authorization code
3. **Backend**: Exchanges the code for tokens and validates them

## Components

### Dependencies (dependencies.py)

Provides FastAPI dependencies for securing endpoints:

- `get_current_user`: Extracts and validates JWT token, fetches user from database
- `get_current_active_user`: Ensures user is active
- `get_current_active_parent_or_admin`: Role-based authorization

### Service (service.py)

Provides functions for token exchange and management:

- `exchange_code_for_token`: Exchanges authorization code for tokens
- `refresh_token`: Refreshes access tokens using refresh tokens
- `logout`: Invalidates tokens at Keycloak

### API Endpoints (auth.py)

- `/auth/config`: Provides Keycloak configuration for frontend
- `/auth/token`: Exchanges authorization code for tokens
- `/auth/refresh`: Refreshes access tokens
- `/auth/logout`: Logs out a user
- `/auth/me`: Returns information about the current user

## Setup Requirements

1. Keycloak server running with:
   - Realm created (default: "localai-family")
   - Client created (default: "backend-api")
   - Client configured for Authorization Code flow
   - Client has appropriate roles and permissions

2. Environment variables set:
   - `KEYCLOAK_URL`: URL of Keycloak server
   - `KEYCLOAK_REALM`: Realm name
   - `KEYCLOAK_CLIENT_ID`: Client ID for backend

## Token Flow

1. Frontend redirects to Keycloak for login
2. After successful login, Keycloak redirects back with an authorization code
3. Frontend sends the code to the backend's `/auth/token` endpoint
4. Backend exchanges the code for access and refresh tokens
5. Frontend stores tokens and uses the access token for subsequent requests
6. When the access token expires, the frontend uses the refresh token to get a new one

## Security Considerations

- All token exchange happens server-side
- JWTs are validated cryptographically using Keycloak's public key
- Access tokens have short lifetimes
- Refresh tokens are invalidated on logout
