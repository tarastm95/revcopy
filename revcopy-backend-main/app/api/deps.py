"""
API dependencies for authentication and common functionality.
Provides reusable dependency functions for FastAPI endpoints.
"""

from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import verify_token
from app.models.user import User
from app.schemas.user import TokenData

# Configure logging
logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token and extract user ID
        user_id = verify_token(credentials.credentials, "access")
        if user_id is None:
            logger.warning("Invalid token provided")
            raise credentials_exception
            
        # Get user from database
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning("User not found", user_id=user_id)
            raise credentials_exception
            
        # Check if user account is active
        if not user.is_active:
            logger.warning("Inactive user attempted access", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account"
            )
            
        # Check if account is locked
        if user.is_locked:
            logger.warning("Locked user attempted access", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked"
            )
            
        return user
        
    except ValueError as e:
        logger.error("Token verification error", error=str(e))
        raise credentials_exception
    except Exception as e:
        logger.error("Unexpected error in authentication", error=str(e))
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (alias for consistency).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Active user
    """
    return current_user


async def get_current_premium_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user with premium access.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Premium user
        
    Raises:
        HTTPException: If user doesn't have premium access
    """
    if not current_user.is_premium:
        logger.warning("Non-premium user attempted premium access", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user with admin access.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        logger.warning("Non-admin user attempted admin access", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def check_usage_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Check if user can make API calls based on usage limits.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: User if within limits
        
    Raises:
        HTTPException: If usage limit exceeded
    """
    if not current_user.can_make_api_call():
        logger.warning("User exceeded usage limit", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Usage limit exceeded. Used {current_user.usage_count}/{current_user.usage_limit} calls."
        )
    
    # Increment usage counter
    current_user.increment_usage()
    await db.commit()
    
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_async_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.
    
    Args:
        db: Database session
        credentials: Optional HTTP authorization credentials
        
    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if not credentials:
        return None
        
    try:
        user_id = verify_token(credentials.credentials, "access")
        if user_id is None:
            return None
            
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if user and user.is_active and not user.is_locked:
            return user
        return None
        
    except Exception:
        return None


class RoleChecker:
    """
    Dependency class for checking user roles.
    Can be used with specific roles as parameters.
    """
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Check if user has one of the allowed roles.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User: User if role is allowed
            
        Raises:
            HTTPException: If user role is not allowed
        """
        if current_user.role not in self.allowed_roles:
            logger.warning(
                "User with insufficient role attempted access",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_roles=[role.value for role in self.allowed_roles]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user


# Common pagination dependencies
async def get_pagination_params(
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Get pagination parameters with validation.
    
    Args:
        page: Page number (starts from 1)
        page_size: Items per page
        
    Returns:
        dict: Pagination parameters
        
    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be 1 or greater"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    return {
        "page": page,
        "page_size": page_size,
        "skip": (page - 1) * page_size,
        "limit": page_size,
    }


# Database transaction dependency
class TransactionDep:
    """Dependency for database transactions."""
    
    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        self.db = db
    
    async def __aenter__(self):
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.db.rollback()
        else:
            await self.db.commit() 