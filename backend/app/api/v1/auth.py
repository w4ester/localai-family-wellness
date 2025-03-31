# ./backend/app/api/v1/auth.py
"""API endpoints for authentication related operations (e.g., login proxy, tokens).
Note: Primary authentication flow might redirect to Keycloak. This handles
token exchange or provides info needed by frontend OIDC clients.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

# Import necessary components
from app.schemas.token_schemas import Token
from app.auth.service import exchange_code_for_token, refresh_token, logout
from app.auth.dependencies import get_current_active_user
from app.core.config import settings
from app.db.models.user_model import User as DBUser

router = APIRouter()


class TokenExchangeRequest(BaseModel):
    """Request body for exchanging an authorization code for tokens."""
    code: str
    redirect_uri: str


class TokenRefreshRequest(BaseModel):
    """Request body for refreshing an access token."""
    refresh_token: str


@router.get("/config", tags=["Authentication"])
async def get_auth_config():
    """
    Provide necessary Keycloak configuration for frontend OIDC clients.
    """
    return {
        "realm": settings.KEYCLOAK_REALM,
        "url": settings.KEYCLOAK_URL,
        "clientId": settings.KEYCLOAK_CLIENT_ID
    }


@router.post("/token", response_model=Token)
async def token_exchange(request: TokenExchangeRequest):
    """
    Exchange an authorization code for access and refresh tokens.
    Used as part of the OAuth2 authorization code flow.
    """
    try:
        token_data = await exchange_code_for_token(request.code, request.redirect_uri)
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "refresh_token": token_data.get("refresh_token")
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service
        raise e
    except Exception as e:
        # Log and convert other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during token exchange: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: TokenRefreshRequest):
    """
    Refresh an access token using a refresh token.
    """
    try:
        token_data = await refresh_token(request.refresh_token)
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "refresh_token": token_data.get("refresh_token")
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions from the service
        raise e
    except Exception as e:
        # Log and convert other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during token refresh: {str(e)}"
        )


@router.post("/logout")
async def logout_user(refresh_token: Optional[str] = None):
    """
    Log out a user by invalidating their refresh token in Keycloak.
    """
    success = await logout(refresh_token)
    return {"success": success}


@router.get("/me")
async def get_current_user_info(current_user: DBUser = Depends(get_current_active_user)):
    """
    Get information about the currently authenticated user.
    This is a convenience endpoint for client applications to verify authentication
    and get basic user profile data.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "family_id": current_user.family_id,
        "is_active": current_user.is_active
    }
