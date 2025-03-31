# ./backend/app/core/config.py (Revised)
"""
Configuration settings for the application, loaded from environment variables / .env file.
"""
from typing import List, Optional, Union, Any
from pathlib import Path # Added for potential relative path loading

from pydantic import AnyHttpUrl, PostgresDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load .env file located at project root relative to this file's location
    # Assumes config.py is in app/core/
    # Adjust the path depth ('../..') if your file structure differs
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parent.parent.parent / '.env', extra='ignore')

    # Project info
    PROJECT_NAME: str = "LocalAI Family Wellness Platform"
    PROJECT_DESCRIPTION: str = "A local, safe, and free stateful AI family wellness platform"
    VERSION: str = "0.1.0"

    # API
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [] # Default to empty list, load from env

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            # Handle comma-separated string from environment variable
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid BACKEND_CORS_ORIGINS format: {v}")

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres" # Service name in Docker Compose
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None # Will be assembled

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            # Convert string manually if it's from environment variable
            if v.startswith('postgresql+psycopg://'):
                parts = v.split('@')
                if len(parts) == 2:
                    auth, server = parts
                    prefix = auth.split('://')[0] + '://'
                    user_pass = auth.split('://')[1]
                    return prefix + user_pass + '@' + server
            return v
        
        # Otherwise, assemble it from components
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )

    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_HOST: str = "redis" # Service name in Docker Compose
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None # Will be assembled

    @field_validator('REDIS_URL', mode='before')
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        password = f":{values.get('REDIS_PASSWORD')}" if values.get('REDIS_PASSWORD') else ""
        return f"redis://{password}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # Ollama
    OLLAMA_HOST: str = "ollama" # Service name in Docker Compose
    OLLAMA_PORT: int = 11434
    OLLAMA_URL: Optional[str] = None # Will be assembled
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_CHAT_MODEL: str = "llama3:latest" # Or another default like mistral

    @field_validator('OLLAMA_URL', mode='before')
    @classmethod
    def assemble_ollama_url(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"http://{values.get('OLLAMA_HOST')}:{values.get('OLLAMA_PORT')}"

    # Keycloak
    KEYCLOAK_HOST: str = "keycloak" # Service name in Docker Compose
    KEYCLOAK_PORT: int = 8080
    KEYCLOAK_URL: Optional[str] = None # Will be assembled
    KEYCLOAK_REALM: str = "localai-family" # Ensure this matches realm created in Keycloak
    KEYCLOAK_CLIENT_ID: str = "backend-api" # Ensure this client exists in the realm
    # Removed KEYCLOAK_ADMIN_* credentials

    @field_validator('KEYCLOAK_URL', mode='before')
    @classmethod
    def assemble_keycloak_url(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"http://{values.get('KEYCLOAK_HOST')}:{values.get('KEYCLOAK_PORT')}"


    # MinIO
    MINIO_HOST: str = "minio" # Service name in Docker Compose
    MINIO_PORT: int = 9000
    MINIO_ENDPOINT: Optional[str] = None # Will be assembled
    MINIO_ACCESS_KEY: str # Application-specific key from .env
    MINIO_SECRET_KEY: str # Application-specific secret from .env
    MINIO_USE_SSL: bool = False # Default for internal docker http

    @field_validator('MINIO_ENDPOINT', mode='before')
    @classmethod
    def assemble_minio_endpoint(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"{values.get('MINIO_HOST')}:{values.get('MINIO_PORT')}"

    # Ntfy
    NTFY_HOST: str = "ntfy" # Service name in Docker Compose
    NTFY_PORT: int = 80 # Default port inside container
    NTFY_URL: Optional[str] = None # Will be assembled
    NTFY_DEFAULT_TOPIC: str = "localai-family"
    NTFY_USERNAME: Optional[str] = None # Load from .env if ntfy server requires auth
    NTFY_PASSWORD: Optional[str] = None # Load from .env if ntfy server requires auth

    @field_validator('NTFY_URL', mode='before')
    @classmethod
    def assemble_ntfy_url(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"http://{values.get('NTFY_HOST')}:{values.get('NTFY_PORT')}"

    # Email (Optional SMTP Relay)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True # Assume TLS usually needed for port 587
    EMAILS_FROM_EMAIL: Optional[str] = None # Sender address
    EMAILS_FROM_NAME: Optional[str] = None # Sender display name

    # Tool Config (Simplified - assuming file is within package)
    # TOOL_CONFIG_PATH: str = "/app/config/tools_config.json" # Removed

    # mDNS Service Discovery
    MDNS_SERVICE_NAME: str = "localai-family" # Name to advertise
    MDNS_SERVICE_TYPE: str = "_http._tcp.local."

    # Security (Critical - MUST be overridden in .env)
    SECRET_KEY: str # Used potentially for signing internal things, password resets etc.


settings = Settings()

# Log loaded settings for verification (optional, remove sensitive keys in production logs)
# import json
# print("Loaded Settings:", json.dumps(settings.model_dump(), indent=2))