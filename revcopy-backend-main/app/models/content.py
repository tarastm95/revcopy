"""Content model for storing generated marketing content and campaigns."""

import enum
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContentType(enum.Enum):
    FACEBOOK_ADS = "facebook_ads"
    GOOGLE_ADS = "google_ads"
    INSTAGRAM_CAPTIONS = "instagram_captions"
    PRODUCT_DESCRIPTION = "product_description"
    BLOG_ARTICLE = "blog_article"
    VIDEO_AD_SCRIPT = "video_ad_script"
    FAQ = "faq"
    PAINS_BENEFITS = "pains_benefits"
    SEASONAL_STRATEGIES = "seasonal_strategies"
    SWOT = "swot"
    AVATARS = "avatars"
    ABANDONMENT_CART = "abandonment_cart"
    NEWSLETTER = "newsletter"
    FLASH_SALE = "flash_sale"
    BACK_IN_STOCK = "back_in_stock"


class ContentStatus(enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    campaign_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("campaigns.id"), nullable=True, index=True)
    
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.GENERATED, nullable=False)
    
    # Metadata
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    character_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Performance tracking
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saves: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="generated_content")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="generated_content")
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="content")


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    content: Mapped[List["GeneratedContent"]] = relationship("GeneratedContent", back_populates="campaign") 