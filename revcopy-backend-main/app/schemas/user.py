"""
User schemas for authentication and profile management.
Includes request/response models with validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    email_notifications: bool = True
    marketing_emails: bool = False


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    email_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and len(v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")) < 10:
            raise ValueError("Invalid phone number format")
        return v


class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    role: UserRole
    status: UserStatus
    is_verified: bool
    usage_count: int
    usage_limit: int
    subscription_tier: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username or str(self.email)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium access."""
        return self.role in [UserRole.PREMIUM, UserRole.ENTERPRISE, UserRole.ADMIN]


class UserProfileUpdate(BaseModel):
    """Schema for comprehensive profile updates."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = None
    language: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        """Validate that new passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New passwords do not match")
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator("confirm_password")
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str


class Token(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[int] = None
    email: Optional[str] = None


class RefreshToken(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class APIKeyCreate(BaseModel):
    """Schema for API key creation."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    name: str
    description: Optional[str] = None
    key: str  # Only returned on creation
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_products_analyzed: int
    total_content_generated: int
    total_campaigns: int
    usage_this_month: int
    usage_limit: int
    subscription_tier: Optional[str] = None
    account_age_days: int


class UserPreferences(BaseModel):
    """Schema for user preferences."""
    default_language: str = "en"
    default_content_style: Optional[str] = None
    email_notifications: bool = True
    marketing_emails: bool = False
    auto_save_content: bool = True
    theme: str = "light"
    
    class Config:
        from_attributes = True 