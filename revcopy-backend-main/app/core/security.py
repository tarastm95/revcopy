"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and security validation.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union

import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create access token: {str(e)}")


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT refresh token string
    """
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create refresh token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Token subject if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            return None
            
        # Check expiration
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            return None
            
        return payload.get("sub")
    except (jwt.JWTError, ValidationError, KeyError):
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Failed to hash password: {str(e)}")


def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.
    
    Args:
        email: User email
        
    Returns:
        Password reset token
    """
    try:
        delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
        now = datetime.utcnow()
        expires = now + delta
        exp = expires.timestamp()
        encoded_jwt = jwt.encode(
            {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to generate password reset token: {str(e)}")


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if token is valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        if decoded_token.get("type") != "password_reset":
            return None
            
        return decoded_token.get("sub")
    except jwt.JWTError:
        return None


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format and structure.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not api_key or len(api_key) < 32:
        return False
    
    # Additional validation logic can be added here
    return True


def generate_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        New API key string
    """
    import secrets
    return secrets.token_urlsafe(32)


class SecurityError(Exception):
    """Custom security-related exception."""
    pass


def require_https() -> bool:
    """
    Check if HTTPS is required based on environment.
    
    Returns:
        True if HTTPS is required, False otherwise
    """
    return settings.ENVIRONMENT == "production"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    import os
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename or "unnamed_file" 