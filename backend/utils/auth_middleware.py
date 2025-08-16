"""Authentication middleware for FastAPI route protection"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import User
from services.auth_service import AuthService


# Security scheme for JWT Bearer token
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for protecting routes"""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """Get current authenticated user from JWT token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get user
        user = await self.auth_service.verify_token(token)
        return user
    
    async def get_current_user_optional(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        """Get current user if authenticated, otherwise return None"""
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            user = await self.auth_service.verify_token(token)
            return user
        except HTTPException:
            return None


# Create global instance
auth_middleware = AuthMiddleware()


# Dependency functions for use in FastAPI routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency to get current authenticated user"""
    return await auth_middleware.get_current_user(credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Dependency to get current user if authenticated"""
    return await auth_middleware.get_current_user_optional(credentials)


def require_auth(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires authentication"""
    return user


def optional_auth(user: Optional[User] = Depends(get_current_user_optional)) -> Optional[User]:
    """Dependency for optional authentication"""
    return user