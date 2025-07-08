"""
User model for authentication and profile management.
Includes role-based access control and user preferences.
"""

import enum
from datetime import datetime
from typing import List, Optional
import enum

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(enum.Enum):
    """User role enumeration for RBAC."""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserStatus(enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """
    User model for authentication and profile management.
    
    Attributes:
        id: Primary key
        email: User email (unique)
        username: User display name
        hashed_password: Bcrypt hashed password
        role: User role for permissions
        status: Account status
        is_verified: Email verification status
        profile fields: Personal information
        usage tracking: API usage and limits
        timestamps: Creation and update times
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False
    )
    
    # Verification and security
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Usage tracking and limits
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    last_api_call: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Subscription and billing
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subscription_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Preferences and settings
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    marketing_emails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Security settings
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="user", cascade="all, delete-orphan"
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign", back_populates="user", cascade="all, delete-orphan"
    )
    generated_content: Mapped[List["GeneratedContent"]] = relationship(
        "GeneratedContent", back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username or self.email
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium access."""
        return self.role in [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN]
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE and self.is_verified
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is temporarily locked."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_make_api_call(self) -> bool:
        """Check if user can make API calls based on usage limits."""
        if self.is_admin:
            return True
        return self.usage_count < self.usage_limit
    
    def increment_usage(self) -> None:
        """Increment API usage counter."""
        self.usage_count += 1
        self.last_api_call = datetime.utcnow()
    
    def reset_password_token_valid(self) -> bool:
        """Check if password reset token is still valid."""
        if not self.reset_token or not self.reset_token_expires:
            return False
        return datetime.utcnow() < self.reset_token_expires
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock user account for specified duration."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_failed_login(self) -> None:
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(30)  # Lock for 30 minutes
    
    def record_successful_login(self, ip_address: Optional[str] = None) -> None:
        """Record a successful login."""
        self.last_login = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None 