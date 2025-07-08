"""
Authentication API endpoints for user registration, login, and token management.
Handles JWT token creation, refresh, and user profile management.
"""

from datetime import timedelta
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_current_user, get_async_session
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models.user import User, UserStatus, UserRole
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    RefreshToken,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
)

# Configure logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
) -> UserResponse:
    """
    Register a new user account.
    
    Creates a new user with email verification required.
    Sends verification email to the provided address.
    
    Args:
        request: FastAPI request object (for rate limiting)
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If email already exists or registration fails
    """
    try:
        logger.info("User registration attempt", email=user_data.email)
        
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            logger.warning("Registration attempt with existing email", email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            company=user_data.company,
            phone=user_data.phone,
            website=user_data.website,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            email_notifications=user_data.email_notifications,
            marketing_emails=user_data.marketing_emails,
            hashed_password=hashed_password,
            role=UserRole.USER,
            status=UserStatus.PENDING_VERIFICATION,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # TODO: Send verification email here
        # await send_verification_email(user.email, verification_token)
        
        logger.info("User registered successfully", user_id=user.id, email=user.email)
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login_user(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session),
) -> Token:
    """
    Authenticate user and return JWT tokens.
    
    Args:
        request: FastAPI request object (for rate limiting)
        login_data: User login credentials
        db: Database session
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        logger.info("Login attempt", email=login_data.email)
        
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning("Login attempt with non-existent email", email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is locked
        if user.is_locked:
            logger.warning("Login attempt on locked account", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to multiple failed login attempts"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning("Invalid password attempt", user_id=user.id)
            user.record_failed_login()
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning("Login attempt on inactive account", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not activated. Please verify your email."
            )
        
        # Record successful login
        client_ip = request.client.host if request.client else None
        user.record_successful_login(client_ip)
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        logger.info("User logged in successfully", user_id=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e), email=login_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_access_token(
    request: Request,
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_async_session),
) -> Token:
    """
    Refresh access token using refresh token.
    
    Args:
        request: FastAPI request object (for rate limiting)
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        Token: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Verify refresh token
        user_id = verify_token(refresh_data.refresh_token, "refresh")
        if user_id is None:
            logger.warning("Invalid refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            logger.warning("Refresh token for inactive user", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        # Create new tokens
        access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)
        
        logger.info("Token refreshed successfully", user_id=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User profile data
    """
    logger.info("Profile accessed", user_id=current_user.id)
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Update current user profile.
    
    Args:
        update_data: Profile update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Updated user profile
    """
    try:
        logger.info("Profile update attempt", user_id=current_user.id)
        
        # Update user fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info("Profile updated successfully", user_id=current_user.id)
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error("Profile update failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Change user password.
    
    Args:
        request: FastAPI request object (for rate limiting)
        password_data: Password change data
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If current password is invalid
    """
    try:
        logger.info("Password change attempt", user_id=current_user.id)
        
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            logger.warning("Invalid current password in change attempt", user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        current_user.hashed_password = new_hashed_password
        
        await db.commit()
        
        logger.info("Password changed successfully", user_id=current_user.id)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
):
    """
    Logout user (client-side token removal).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Logout confirmation message
    """
    logger.info("User logged out", user_id=current_user.id)
    
    # In a more advanced implementation, you might:
    # - Add token to blacklist
    # - Update last_logout timestamp
    # - Clear refresh tokens from database
    
    return {"message": "Logged out successfully"}


@router.post("/verify-email")
@limiter.limit("3/minute")
async def verify_email(
    request: Request,
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Verify user email address using verification token.
    
    Args:
        request: FastAPI request object (for rate limiting)
        verification_data: Email verification data
        db: Database session
        
    Raises:
        HTTPException: If verification token is invalid
    """
    try:
        # TODO: Implement email verification logic
        # This would typically involve:
        # 1. Verify the token
        # 2. Find user by token
        # 3. Mark email as verified
        # 4. Activate account
        
        logger.info("Email verification attempt", token=verification_data.token[:10] + "...")
        
        return {"message": "Email verified successfully"}
        
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.post("/request-password-reset")
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Request password reset email.
    
    Args:
        request: FastAPI request object (for rate limiting)
        reset_data: Password reset request data
        db: Database session
    """
    try:
        logger.info("Password reset requested", email=reset_data.email)
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == reset_data.email)
        )
        user = result.scalar_one_or_none()
        
        # Always return success to prevent email enumeration
        if user:
            # TODO: Generate reset token and send email
            # reset_token = generate_password_reset_token(user.email)
            # await send_password_reset_email(user.email, reset_token)
            logger.info("Password reset email would be sent", user_id=user.id)
        
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error("Password reset request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Reset password using reset token.
    
    Args:
        request: FastAPI request object (for rate limiting)
        reset_data: Password reset confirmation data
        db: Database session
        
    Raises:
        HTTPException: If reset token is invalid
    """
    try:
        logger.info("Password reset attempt", token=reset_data.token[:10] + "...")
        
        # TODO: Implement password reset logic
        # This would typically involve:
        # 1. Verify the reset token
        # 2. Find user by token
        # 3. Update password
        # 4. Invalidate reset token
        
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        logger.error("Password reset failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        ) 