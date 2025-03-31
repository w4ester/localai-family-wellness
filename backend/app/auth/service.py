"""
Authentication service for handling token exchange with Keycloak.
"""
import logging
from typing import Optional, Dict, Any
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange an authorization code for a token using Keycloak's token endpoint.
    This is used in the authorization code flow.
    
    Args:
        code: The authorization code received from Keycloak
        redirect_uri: The redirect URI used in the initial authorization request
        
    Returns:
        Dict containing access_token, refresh_token, etc.
    """
    token_endpoint = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error exchanging code for token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error communicating with authentication server"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Keycloak error during token exchange: {e.response.text}", exc_info=True)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Authentication server error: {e.response.text}"
        )

async def refresh_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh an access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to use
        
    Returns:
        Dict containing new access_token, refresh_token, etc.
    """
    token_endpoint = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "refresh_token": refresh_token
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error communicating with authentication server"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Keycloak error during token refresh: {e.response.text}", exc_info=True)
        # For invalid refresh tokens, return a more specific error
        if e.response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Authentication server error: {e.response.text}"
        )

async def logout(refresh_token: Optional[str] = None) -> bool:
    """
    Log out a user from Keycloak by invalidating their refresh token.
    
    Args:
        refresh_token: The refresh token to invalidate
        
    Returns:
        True if logout was successful
    """
    if not refresh_token:
        return True
        
    logout_endpoint = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    
    data = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "refresh_token": refresh_token
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(logout_endpoint, data=data)
            response.raise_for_status()
            return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        return False  # Non-critical error - let client proceed with local logout
