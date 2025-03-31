"""
Main API router for the application.
"""
from fastapi import APIRouter

from app.api.v1 import users, families, ai, chores, screen_time, auth

# Main router
api_router = APIRouter()

# Include all API endpoints by category
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(families.router, prefix="/families", tags=["Families"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(chores.router, prefix="/chores", tags=["Chores"])
api_router.include_router(screen_time.router, prefix="/screen-time", tags=["Screen Time"])