"""
Pydantic schemas for admin-specific entities.

This module contains request/response schemas for:
- Administrator management
- Payment tracking and analytics
- Amazon account management  
- Proxy server configuration
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from pydantic.types import constr

from app.models.admin import (
    AdminRole,
    AdminStatus, 
    PaymentStatus,
    PaymentMethod,
    ServerStatus,
    CrawlerStatus,
    CrawlerType
)


# ==================== ADMINISTRATOR SCHEMAS ====================

class AdministratorBase(BaseModel):
    """Base administrator schema with common fields."""
    name: constr(min_length=1, max_length=255) = Field(..., description="Administrator full name")
    email: EmailStr = Field(..., description="Administrator email address")
    role: AdminRole = Field(default=AdminRole.ADMIN, description="Administrator role")
    status: AdminStatus = Field(default=AdminStatus.ACTIVE, description="Administrator status")


class AdministratorCreate(AdministratorBase):
    """Schema for creating a new administrator."""
    password: constr(min_length=8, max_length=128) = Field(..., description="Administrator password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class AdministratorUpdate(BaseModel):
    """Schema for updating an administrator."""
    name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Administrator full name")
    email: Optional[EmailStr] = Field(None, description="Administrator email address")
    role: Optional[AdminRole] = Field(None, description="Administrator role")
    status: Optional[AdminStatus] = Field(None, description="Administrator status")
    password: Optional[constr(min_length=8, max_length=128)] = Field(None, description="New password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password complexity if provided."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class AdministratorResponse(AdministratorBase):
    """Schema for administrator response data."""
    id: int = Field(..., description="Administrator ID")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total login count")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    class Config:
        from_attributes = True


# ==================== PAYMENT SCHEMAS ====================

class PaymentBase(BaseModel):
    """Base payment schema with common fields."""
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: constr(min_length=3, max_length=3) = Field(default="USD", description="Currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    description: Optional[str] = Field(None, max_length=1000, description="Payment description")


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment record."""
    user_id: int = Field(..., description="User ID associated with payment")
    external_payment_id: Optional[str] = Field(None, description="External payment provider ID")
    payment_provider: Optional[str] = Field(None, description="Payment provider name")


class PaymentUpdate(BaseModel):
    """Schema for updating payment status."""
    status: PaymentStatus = Field(..., description="Updated payment status")
    failure_reason: Optional[str] = Field(None, description="Failure reason if applicable")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")


class PaymentResponse(PaymentBase):
    """Schema for payment response data."""
    id: str = Field(..., description="Payment ID")
    user_id: int = Field(..., description="Associated user ID")
    status: PaymentStatus = Field(..., description="Payment status")
    user_name: Optional[str] = Field(None, description="User name")
    user_email: Optional[str] = Field(None, description="User email")
    external_payment_id: Optional[str] = Field(None, description="External payment ID")
    payment_provider: Optional[str] = Field(None, description="Payment provider")
    provider_fee: Optional[Decimal] = Field(None, description="Provider fee")
    failure_reason: Optional[str] = Field(None, description="Failure reason")
    created_at: datetime = Field(..., description="Payment creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    
    class Config:
        from_attributes = True


class PaymentStatsResponse(BaseModel):
    """Schema for payment statistics response."""
    total_revenue: Decimal = Field(..., description="Total revenue amount")
    monthly_revenue: Decimal = Field(..., description="Current month revenue")
    average_payment: Decimal = Field(..., description="Average payment amount")
    success_rate: float = Field(..., description="Payment success rate percentage")
    total_payments: int = Field(..., description="Total number of payments")
    monthly_payments: int = Field(..., description="Current month payment count")
    payment_method_breakdown: Dict[str, int] = Field(..., description="Payment methods distribution")
    status_breakdown: Dict[str, int] = Field(..., description="Payment status distribution")


# ==================== AMAZON ACCOUNT SCHEMAS ====================

class AmazonAccountBase(BaseModel):
    """Base Amazon account schema."""
    username: constr(min_length=1, max_length=255) = Field(..., description="Amazon username")
    status: ServerStatus = Field(default=ServerStatus.ACTIVE, description="Account status")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")


class AmazonAccountCreate(AmazonAccountBase):
    """Schema for creating Amazon account."""
    password: constr(min_length=1, max_length=255) = Field(..., description="Amazon password")


class AmazonAccountUpdate(BaseModel):
    """Schema for updating Amazon account."""
    password: Optional[constr(min_length=1, max_length=255)] = Field(None, description="New password")
    status: Optional[ServerStatus] = Field(None, description="Account status")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")


class AmazonAccountResponse(AmazonAccountBase):
    """Schema for Amazon account response."""
    id: int = Field(..., description="Account ID")
    password_masked: str = Field(..., description="Masked password for display")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(default=0, description="Total usage count")
    success_count: int = Field(default=0, description="Successful operations count")
    failure_count: int = Field(default=0, description="Failed operations count")
    health_status: Optional[str] = Field(None, description="Account health status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    class Config:
        from_attributes = True


# ==================== PROXY SERVER SCHEMAS ====================

class ProxyServerBase(BaseModel):
    """Base proxy server schema."""
    name: constr(min_length=1, max_length=255) = Field(..., description="Proxy server name")
    address: constr(min_length=1, max_length=500) = Field(..., description="Proxy address (user:pass@host:port)")
    location: constr(min_length=1, max_length=100) = Field(..., description="Geographic location")
    status: ServerStatus = Field(default=ServerStatus.ACTIVE, description="Server status")


class ProxyServerCreate(ProxyServerBase):
    """Schema for creating proxy server."""
    rate_limit_per_hour: Optional[int] = Field(None, gt=0, description="Rate limit per hour")


class ProxyServerUpdate(BaseModel):
    """Schema for updating proxy server."""
    name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Proxy server name")
    address: Optional[constr(min_length=1, max_length=500)] = Field(None, description="Proxy address")
    location: Optional[constr(min_length=1, max_length=100)] = Field(None, description="Geographic location")
    status: Optional[ServerStatus] = Field(None, description="Server status")
    rate_limit_per_hour: Optional[int] = Field(None, gt=0, description="Rate limit per hour")


class ProxyServerResponse(ProxyServerBase):
    """Schema for proxy server response."""
    id: int = Field(..., description="Server ID")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(default=0, description="Total usage count")
    success_count: int = Field(default=0, description="Successful operations count")
    failure_count: int = Field(default=0, description="Failed operations count")
    avg_response_time: Optional[Decimal] = Field(None, description="Average response time (ms)")
    uptime_percentage: Optional[Decimal] = Field(None, description="Uptime percentage")
    health_status: Optional[str] = Field(None, description="Server health status")
    rate_limit_per_hour: Optional[int] = Field(None, description="Rate limit per hour")
    current_hour_usage: int = Field(default=0, description="Current hour usage count")
    created_at: datetime = Field(..., description="Server creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    class Config:
        from_attributes = True


# ==================== CRAWLER SCHEMAS ====================

class CrawlerBase(BaseModel):
    """Base crawler schema."""
    name: constr(min_length=1, max_length=255) = Field(..., description="Crawler name")
    crawler_type: CrawlerType = Field(default=CrawlerType.GENERAL_CRAWLER, description="Type of crawler")
    target_url: constr(min_length=1, max_length=500) = Field(..., description="Target URL to crawl")
    css_selector: Optional[str] = Field(None, max_length=500, description="CSS selector for content extraction")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    interval_minutes: int = Field(default=5, ge=1, le=1440, description="Crawl interval in minutes")


class CrawlerCreate(CrawlerBase):
    """Schema for creating crawler."""
    pass


class CrawlerUpdate(BaseModel):
    """Schema for updating crawler."""
    name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Crawler name")
    crawler_type: Optional[CrawlerType] = Field(None, description="Type of crawler")
    target_url: Optional[constr(min_length=1, max_length=500)] = Field(None, description="Target URL to crawl")
    css_selector: Optional[str] = Field(None, max_length=500, description="CSS selector for content extraction")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    interval_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Crawl interval in minutes")
    status: Optional[CrawlerStatus] = Field(None, description="Crawler status")


class CrawlerResponse(CrawlerBase):
    """Schema for crawler response."""
    id: int = Field(..., description="Crawler ID")
    status: CrawlerStatus = Field(..., description="Current crawler status")
    last_run_at: Optional[datetime] = Field(None, description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(None, description="Next scheduled run")
    total_runs: int = Field(default=0, description="Total number of runs")
    successful_runs: int = Field(default=0, description="Number of successful runs")
    failed_runs: int = Field(default=0, description="Number of failed runs")
    items_collected: int = Field(default=0, description="Total items collected")
    avg_runtime_seconds: Optional[Decimal] = Field(None, description="Average runtime in seconds")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_at: Optional[datetime] = Field(None, description="Last error timestamp")
    consecutive_failures: int = Field(default=0, description="Consecutive failure count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    class Config:
        from_attributes = True


class CrawlerStatusUpdate(BaseModel):
    """Schema for updating crawler status."""
    status: CrawlerStatus = Field(..., description="New crawler status")


# ==================== PAGINATION SCHEMAS ====================

class PaginationResponse(BaseModel):
    """Generic pagination response schema."""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total items count")
    total_pages: int = Field(..., description="Total pages count")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class PaymentListResponse(BaseModel):
    """Response schema for payment list with pagination."""
    payments: List[PaymentResponse] = Field(..., description="Payment list")
    pagination: PaginationResponse = Field(..., description="Pagination information")


# ==================== ERROR SCHEMAS ====================

class AdminErrorResponse(BaseModel):
    """Standard error response schema for admin endpoints."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 