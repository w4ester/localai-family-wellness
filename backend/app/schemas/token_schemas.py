# ./backend/app/schemas/token_schemas.py
"""
Pydantic schemas related to authentication tokens.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union

class Token(BaseModel):
    """
    Schema for representing an access token response (e.g., from /auth/login/access-token).
    """
    access_token: str = Field(..., description="The JWT access token.")
    token_type: str = Field(default="bearer", description="The type of token (typically 'bearer').")
    # Add refresh token since our implementation uses it
    refresh_token: Optional[str] = None
    # expires_in: Optional[int] = None # Seconds until expiry


class TokenPayload(BaseModel):
    """
    Schema representing the expected payload (claims) inside a validated JWT.
    Used internally by authentication dependencies.
    Matches the definition in app/auth/dependencies.py
    """
    sub: str # Subject (Keycloak User ID)
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    aud: Optional[Union[str, List[str]]] = None
    # Add other claims you expect from Keycloak
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    family_name: Optional[str] = None # Example custom claim
    given_name: Optional[str] = None
    realm_access: Optional[Dict[str, List[str]]] = None