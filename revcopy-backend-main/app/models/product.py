"""
Product model for storing e-commerce product information.
Includes product details, images, and metadata from crawled sources.
"""

import enum
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProductStatus(enum.Enum):
    """Product processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class EcommercePlatform(enum.Enum):
    """Supported e-commerce platforms."""
    AMAZON = "amazon"
    EBAY = "ebay"
    ALIEXPRESS = "aliexpress"
    SHOPIFY = "shopify"
    CUSTOM = "custom"


class Product(Base):
    """
    Product model for storing e-commerce product information.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user who imported the product
        url: Original product URL
        platform: E-commerce platform
        product_id: Platform-specific product ID
        title: Product title/name
        description: Product description
        price: Product price information
        rating: Average rating
        review_count: Total number of reviews
        images: Associated product images
        metadata: Additional platform-specific data
        status: Processing status
        timestamps: Creation and update times
    """
    
    __tablename__ = "products"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Product identification
    url: Mapped[str] = mapped_column(String(2000), nullable=False, index=True)
    platform: Mapped[EcommercePlatform] = mapped_column(
        Enum(EcommercePlatform), nullable=False, index=True
    )
    external_product_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    # Basic product information
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Pricing information
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Review metrics
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_distribution: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Product specifications
    specifications: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    features: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    dimensions: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Availability and shipping
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shipping_info: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Processing status
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), default=ProductStatus.PENDING, nullable=False
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Crawling metadata
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    crawl_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cache and optimization
    cached_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    cache_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # SEO and marketing data
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    competitive_products: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis", back_populates="product", cascade="all, delete-orphan"
    )
    generated_content: Mapped[List["GeneratedContent"]] = relationship(
        "GeneratedContent", back_populates="product", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of Product."""
        return f"<Product(id={self.id}, title='{self.title[:50]}...', platform='{self.platform.value}')>"
    
    @property
    def is_processed(self) -> bool:
        """Check if product has been successfully processed."""
        return self.status == ProductStatus.COMPLETED
    
    @property
    def is_processing(self) -> bool:
        """Check if product is currently being processed."""
        return self.status == ProductStatus.PROCESSING
    
    @property
    def has_failed(self) -> bool:
        """Check if product processing has failed."""
        return self.status == ProductStatus.FAILED
    
    @property
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cached_data or not self.cache_expires_at:
            return False
        return datetime.utcnow() < self.cache_expires_at
    
    @property
    def formatted_price(self) -> Optional[str]:
        """Get formatted price string."""
        if not self.price:
            return None
        currency_symbol = {"USD": "$", "EUR": "€", "GBP": "£"}.get(self.currency, self.currency or "")
        return f"{currency_symbol}{self.price:.2f}"
    
    @property
    def has_good_reviews(self) -> bool:
        """Check if product has sufficient and good reviews."""
        return (
            self.review_count >= 50 and 
            self.rating is not None and 
            self.rating >= 4.0
        )
    
    def mark_as_processing(self) -> None:
        """Mark product as currently being processed."""
        self.status = ProductStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.error_message = None
    
    def mark_as_completed(self) -> None:
        """Mark product as successfully processed."""
        self.status = ProductStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark product processing as failed."""
        self.status = ProductStatus.FAILED
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()
    
    def update_cache(self, data: Dict, ttl_hours: int = 24) -> None:
        """Update cached data with TTL."""
        from datetime import timedelta
        self.cached_data = data
        self.cache_expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        self.cached_data = None
        self.cache_expires_at = None


class ProductImage(Base):
    """
    Product image model for storing product photos and thumbnails.
    
    Attributes:
        id: Primary key
        product_id: Foreign key to associated product
        url: Image URL
        image_type: Type of image (main, thumbnail, gallery)
        alt_text: Alternative text for accessibility
        position: Display order
        metadata: Image metadata (size, format, etc.)
    """
    
    __tablename__ = "product_images"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Product relationship
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    # Image information
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    image_type: Mapped[str] = mapped_column(String(50), default="gallery", nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Display properties
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Local storage (if downloaded)
    local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Image metadata
    image_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")
    
    def __repr__(self) -> str:
        """String representation of ProductImage."""
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, type='{self.image_type}')>"
    
    @property
    def is_main_image(self) -> bool:
        """Check if this is the main product image."""
        return self.image_type == "main" or self.position == 0
    
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio."""
        if self.width and self.height:
            return self.width / self.height
        return None 