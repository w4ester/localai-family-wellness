# ./backend/app/auth/dependencies.py
"""
FastAPI dependencies for handling authentication and authorization using
Keycloak JWT tokens and verifying against the local user database.
"""
import logging
from typing import Optional, Dict, Any, Union, List # Added Union, List
from uuid import UUID
from datetime import datetime # Needed for expiration check potentially

import httpx # To fetch Keycloak public key if needed
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Standard way to extract Bearer token
from jose import JWTError, jwt # For decoding/validating JWTs
from pydantic import ValidationError, BaseModel, Field, field_validator, ValidationInfo # Import necessary Pydantic parts

# Import necessary components from your application
from app.core.config import settings # Your app settings
import psycopg # Type hint for DB connection
from psycopg_pool import AsyncConnectionPool # Type hint for pool
from app.db.session import get_db_conn # DB connection dependency (provides pool)
from app.db.models.user_model import User as DBUser # Import your SQLAlchemy User model
# !!! IMPORTANT: Ensure this file and schema exist !!!
from app.schemas.user_schemas import UserReadMinimal # Import the user schema to return


logger = logging.getLogger(__name__)

# --- OAuth2 Scheme Definition ---
# This tells FastAPI to look for a token in the 'Authorization: Bearer <token>' header.
# The tokenUrl should point to Keycloak's token endpoint.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
)

# --- Keycloak Public Key Fetching and Caching ---
# WARNING: This basic implementation fetches the key on first request without robust caching.
#          For production, implement proper caching (e.g., using cachetools library @cached decorator)
#          with a reasonable expiration time (e.g., 1 hour) to avoid hitting Keycloak constantly.
_keycloak_public_key_cache: Optional[str] = None

async def get_keycloak_public_key() -> str:
    """
    Fetches the realm's public key from Keycloak's certs endpoint.
    Includes basic in-memory caching (replace with robust cache for production).
    """
    global _keycloak_public_key_cache
    # TODO: Implement proper caching using cachetools or similar for production
    if _keycloak_public_key_cache:
        logger.debug("Using cached Keycloak public key.")
        return _keycloak_public_key_cache

    certs_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    logger.warning(f"Fetching Keycloak public key from {certs_url} (!!! Caching is basic - IMPROVE FOR PRODUCTION !!!)")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client: # Added timeout
            response = await client.get(certs_url)
            response.raise_for_status() # Raise error for bad status codes (4xx, 5xx)
            jwks = response.json()

            # Find the RSA signing key (often marked with use='sig')
            public_key_data = None
            for key in jwks.get('keys', []):
                # Check for RSA key type and 'sig' (signing) use
                if key.get('kty') == 'RSA' and key.get('use') == 'sig':
                    # Optionally check 'alg' like RS256 if needed
                    public_key_data = key
                    break

            if not public_key_data:
                logger.error("RSA signing key ('sig') not found in Keycloak JWKS response.")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve valid Keycloak signing key")

            # Construct PEM public key using cryptography library
            # Ensure 'cryptography' is installed (via python-jose[cryptography])
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import base64

            def decode_base64url(value):
                """Decodes base64url string, adding padding if necessary."""
                padding = '=' * (4 - (len(value) % 4))
                return base64.urlsafe_b64decode(value + padding)

            # Decode modulus (n) and exponent (e) from base64url format
            try:
                modulus_n = int.from_bytes(decode_base64url(public_key_data['n']), 'big')
                exponent_e = int.from_bytes(decode_base64url(public_key_data['e']), 'big')
            except KeyError as ke:
                 logger.error(f"JWK missing required field 'n' or 'e': {ke}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid Keycloak signing key format")

            # Create RSA public key object
            public_key_obj = rsa.RSAPublicNumbers(exponent_e, modulus_n).public_key()

            # Serialize key to PEM format
            pem = public_key_obj.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            _keycloak_public_key_cache = pem.decode('utf-8') # Cache the PEM string
            logger.info("Successfully fetched and formatted Keycloak public key.")
            return _keycloak_public_key_cache

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching Keycloak public key from {certs_url}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service timed out")
    except httpx.RequestError as e:
        logger.error(f"HTTP error fetching Keycloak public key: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to authentication service")
    except (KeyError, IndexError, ValueError, TypeError, ImportError) as e:
        # Catch errors during key processing/parsing/cryptography
        logger.error(f"Error processing Keycloak public key data: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing authentication configuration")
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error fetching Keycloak public key: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error during authentication setup")


# --- Pydantic Model for Token Payload ---
class TokenPayload(BaseModel):
    """Pydantic model for validating the claims within the Keycloak JWT."""
    # Standard Claims
    sub: str = Field(..., description="Subject - The Keycloak User ID")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")
    iss: str = Field(..., description="Issuer - URL of the Keycloak realm")
    aud: Union[str, List[str]] = Field(..., description="Audience - Should contain your backend's client ID")

    # Example Optional Keycloak Claims (Add others as needed)
    typ: Optional[str] = None # Type (e.g., Bearer)
    azp: Optional[str] = None # Authorized party (often the client ID)
    preferred_username: Optional[str] = None # Username from Keycloak
    email: Optional[str] = None
    name: Optional[str] = None # Full name
    given_name: Optional[str] = None # First name
    family_name: Optional[str] = None # Last name
    email_verified: Optional[bool] = None
    realm_access: Optional[Dict[str, List[str]]] = None # Contains roles defined in the realm
    resource_access: Optional[Dict[str, Dict[str, List[str]]]] = None # Contains client-specific roles

    @field_validator('aud')
    @classmethod
    def validate_audience(cls, v: Union[str, List[str]], info: ValidationInfo):
        """Ensures the configured backend client ID is in the audience list."""
        # Get expected audience from settings (ensure it's configured)
        allowed_audience = settings.KEYCLOAK_CLIENT_ID
        if not allowed_audience:
             logger.error("KEYCLOAK_CLIENT_ID setting is not configured!")
             raise ValueError("Server configuration error: Audience not set.")

        audience_list = [v] if isinstance(v, str) else v
        if not isinstance(audience_list, list):
             raise ValueError("Audience ('aud') claim must be a string or list of strings")

        if allowed_audience not in audience_list:
            logger.warning(f"Token audience {audience_list} does not contain expected audience '{allowed_audience}'")
            raise ValueError(f"Invalid audience: expected '{allowed_audience}'")
        return v

    @field_validator('iss')
    @classmethod
    def validate_issuer(cls, v: str, info: ValidationInfo):
        """Ensures the token issuer matches the configured Keycloak realm URL."""
        expected_issuer = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
        if v != expected_issuer:
             logger.warning(f"Token issuer '{v}' does not match expected issuer '{expected_issuer}'")
             raise ValueError(f"Invalid issuer: expected '{expected_issuer}'")
        return v


# --- Core User Retrieval Dependency ---
async def get_current_user(
    token: str = Depends(oauth2_scheme), # Extracts token from Authorization header
    pool: AsyncConnectionPool = Depends(get_db_conn) # Injects DB pool
) -> DBUser: # Returns the SQLAlchemy User model instance from your DB
    """
    Validates the Keycloak JWT token and fetches the corresponding user
    from the local database based on the 'sub' claim (keycloak_id).

    Raises HTTPException for invalid tokens or users not found.
    """
    # Define standard exception for authentication errors
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Get Keycloak's public key (replace with cached version in prod)
        keycloak_public_key = await get_keycloak_public_key()

        # 2. Decode and Validate JWT using python-jose
        payload_dict = jwt.decode(
            token,
            keycloak_public_key,
            algorithms=["RS256"], # Keycloak typically uses RS256
            # Audience & Issuer are validated by the Pydantic model now
            options={
                "verify_signature": True,
                "verify_exp": True, # Verify expiration
                # Add leeway for clock skew if needed: "leeway": 60 (seconds)
            }
        )
        # 3. Parse payload into Pydantic model for further validation and easy access
        payload = TokenPayload(**payload_dict)
        keycloak_user_id: str = payload.sub # Keycloak User ID ('sub' claim)

    # Handle specific validation errors from jose or pydantic
    except JWTError as e:
        logger.error(f"JWT validation/decoding error: {e}", exc_info=False) # Don't log full trace for common errors
        raise credentials_exception from e
    except ValidationError as e:
         logger.error(f"Token payload validation failed: {e}", exc_info=False)
         raise credentials_exception from e
    except HTTPException:
        # Re-raise HTTPExceptions specifically raised during key fetching
        raise
    except Exception as e:
        # Catch any other unexpected errors during token processing
        logger.error(f"Unexpected error validating token: {e}", exc_info=True)
        raise credentials_exception from e

    # 4. Fetch User from Local Database using Keycloak ID
    user: Optional[DBUser] = None
    logger.debug(f"Fetching user from DB with keycloak_id: {keycloak_user_id}")
    async with pool.connection() as conn:
        # Use row factory to map result directly to DBUser class
        # Ensure DBUser is correctly imported and mapped
        async with conn.cursor(row_factory=psycopg.rows.class_row(DBUser)) as cur:
            # Query the 'user' table (SQLAlchemy default lowercase name)
            # using the keycloak_id column. Ensure this column exists and is indexed.
            # Ensure connection/cursor are async compatible if DBUser needs relationship loading
            try:
                await cur.execute(
                    # Use explicit table name from model if available, else lowercase default
                    f'SELECT * FROM "{DBUser.__tablename__}" WHERE keycloak_id = %s',
                    (keycloak_user_id,)
                )
                user = await cur.fetchone()
            except Exception as db_exc:
                 logger.error(f"Database error fetching user by keycloak_id {keycloak_user_id}: {db_exc}", exc_info=True)
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during user lookup")


    if user is None:
        # User exists in Keycloak but not locally. Decide how to handle this.
        # Option 1 (Current): Raise 404. Requires user sync process.
        logger.warning(f"Authenticated user with Keycloak ID '{keycloak_user_id}' not found in local DB.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found in application")
        # Option 2 (Future): Implement auto-registration using token claims.
        # logger.info(f"User {keycloak_user_id} not found locally, attempting auto-registration...")
        # user = await auto_register_user(pool, payload) # Needs implementation
        # if not user: raise HTTPException(...)

    logger.debug(f"Token validated for user: {user.username} (DB ID: {user.id})")
    return user


# --- Active User Dependency ---
async def get_current_active_user(
    # This dependency implicitly calls get_current_user first
    current_user: DBUser = Depends(get_current_user)
) -> DBUser: # Return your SQLAlchemy User model instance
    """
    FastAPI dependency that checks if the user retrieved from the token
    is marked as active in the local database.
    """
    if not current_user.is_active:
        logger.warning(f"Authentication attempt by inactive user: {current_user.username} (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    logger.debug(f"User confirmed active: {current_user.username}")
    # IMPORTANT: Return the DBUser model instance here. FastAPI endpoints using this
    # dependency will receive the full DBUser object. If endpoints should return
    # a Pydantic schema (like UserReadMinimal), the conversion happens based on
    # the endpoint's response_model.
    return current_user


# --- Role-Specific Dependency Example ---
# (Adjust roles based on your UserRole enum)
async def get_current_active_parent_or_admin(
    current_user: DBUser = Depends(get_current_active_user) # Ensures user is valid and active first
) -> DBUser:
    """
    Dependency ensuring the current user is active AND has a role
    permitted to perform parent or admin level actions.
    """
    # Import your UserRole enum if not already imported
    from app.db.models.user_model import UserRole

    # Define allowed roles using the enum for type safety
    allowed_roles = {UserRole.PARENT, UserRole.CAREGIVER, UserRole.ADMIN}

    # Check if the user's role (which should be the enum type on the DBUser model)
    # is in the set of allowed roles.
    if current_user.role not in allowed_roles:
         logger.warning(f"Authorization failed: User {current_user.username} (Role: {current_user.role}) attempted parent/admin action.")
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="User does not have sufficient privileges for this action."
         )
    logger.debug(f"User {current_user.username} authorized as parent/admin equivalent.")
    return current_user