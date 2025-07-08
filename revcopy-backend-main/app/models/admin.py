"""
Admin-specific database models for RevCopy.

This module contains models for administrative functionality:
- Administrator: Admin user management with roles and permissions
- Payment: Payment transaction tracking and analytics
- AmazonAccount: Amazon account credentials for data scraping
- ProxyServer: Proxy server configurations for secure data access
- Crawler: Web crawler management and monitoring
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AdminRole(str, Enum):
    """Admin role enumeration."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


class AdminStatus(str, Enum):
    """Admin status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    STRIPE = "stripe"
    OTHER = "other"


class ServerStatus(str, Enum):
    """Server status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class CrawlerStatus(str, Enum):
    """Crawler status enumeration."""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class CrawlerType(str, Enum):
    """Crawler type enumeration."""
    PRODUCT_SCRAPER = "product_scraper"
    PRICE_MONITOR = "price_monitor"
    REVIEW_COLLECTOR = "review_collector"
    GENERAL_CRAWLER = "general_crawler"


class Administrator(Base):
    """
    Administrator model for admin panel user management.
    
    Separate from regular User model to handle admin-specific data
    and permissions without affecting customer user functionality.
    """
    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=AdminRole.ADMIN)
    status = Column(String(50), nullable=False, default=AdminStatus.ACTIVE)
    
    # Authentication tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Administrator(id={self.id}, email='{self.email}', role='{self.role}')>"


class Payment(Base):
    """
    Payment transaction model for financial tracking and analytics.
    
    Stores all payment-related information for admin panel reporting
    and user billing management.
    """
    __tablename__ = "payments"

    id = Column(String(255), primary_key=True, index=True)  # External payment ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=False)
    
    # External payment provider data
    external_payment_id = Column(String(255), nullable=True, index=True)
    payment_provider = Column(String(100), nullable=True)  # stripe, paypal, etc.
    provider_fee = Column(Numeric(10, 2), nullable=True)
    
    # User information (denormalized for reporting)
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True, index=True)
    
    # Transaction metadata
    description = Column(Text, nullable=True)
    payment_metadata = Column(Text, nullable=True)  # JSON string for additional data
    failure_reason = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id='{self.id}', amount={self.amount}, status='{self.status}')>"


class AmazonAccount(Base):
    """
    Amazon account credentials model for data scraping.
    
    Stores encrypted Amazon account information used for
    product and review data collection.
    """
    __tablename__ = "amazon_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # Encrypted password
    
    # Account metadata
    status = Column(String(50), nullable=False, default=ServerStatus.ACTIVE)
    avatar_url = Column(String(500), nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Rate limiting and health
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    health_check_at = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AmazonAccount(id={self.id}, username='{self.username}', status='{self.status}')>"


class ProxyServer(Base):
    """
    Proxy server configuration model for secure data access.
    
    Stores proxy server information used for anonymous
    web scraping and data collection.
    """
    __tablename__ = "proxy_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)  # format: username:password@host:port
    
    # Server metadata
    location = Column(String(100), nullable=False)  # Geographic location
    status = Column(String(50), nullable=False, default=ServerStatus.ACTIVE)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Numeric(8, 2), nullable=True)  # in milliseconds
    uptime_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Health monitoring
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=True)
    health_details = Column(Text, nullable=True)
    
    # Rate limiting
    rate_limit_per_hour = Column(Integer, nullable=True)
    current_hour_usage = Column(Integer, default=0)
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ProxyServer(id={self.id}, name='{self.name}', location='{self.location}')>"


class Crawler(Base):
    """
    Web crawler configuration and monitoring model.
    
    Manages web crawlers for product data collection,
    price monitoring, and content scraping.
    """
    __tablename__ = "crawlers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    crawler_type = Column(String(50), nullable=False, default=CrawlerType.GENERAL_CRAWLER)
    
    # Configuration
    target_url = Column(String(500), nullable=False)
    css_selector = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True, default="Mozilla/5.0 (compatible; RevCopy-Bot/1.0)")
    interval_minutes = Column(Integer, nullable=False, default=5)
    
    # Status and monitoring
    status = Column(String(50), nullable=False, default=CrawlerStatus.STOPPED)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    items_collected = Column(Integer, default=0)
    avg_runtime_seconds = Column(Numeric(8, 2), nullable=True)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    
    # Configuration metadata
    config_json = Column(Text, nullable=True)  # JSON string for additional configuration
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Crawler(id={self.id}, name='{self.name}', type='{self.crawler_type}', status='{self.status}')>" 