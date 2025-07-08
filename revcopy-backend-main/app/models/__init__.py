"""
Database models for RevCopy application.
Contains SQLAlchemy models for all entities.
"""

from .user import User, UserRole
from .product import Product, ProductImage
from .analysis import Analysis, ReviewInsight, SentimentAnalysis
from .content import Campaign, ContentType
from .prompts import PromptTemplate, AIContentGeneration, ContentGenerationStats
from .admin import (
    Administrator, 
    Payment, 
    AmazonAccount, 
    ProxyServer,
    Crawler,
    AdminRole,
    AdminStatus,
    PaymentStatus,
    PaymentMethod,
    ServerStatus,
    CrawlerStatus,
    CrawlerType
)

__all__ = [
    "User",
    "UserRole",
    "Product",
    "ProductImage", 
    "Analysis",
    "ReviewInsight",
    "SentimentAnalysis",
    "Campaign",
    "ContentType",
    "PromptTemplate",
    "AIContentGeneration",
    "ContentGenerationStats",
    "Administrator",
    "Payment",
    "AmazonAccount",
    "ProxyServer",
    "Crawler",
    "AdminRole",
    "AdminStatus",
    "PaymentStatus", 
    "PaymentMethod",
    "ServerStatus",
    "CrawlerStatus",
    "CrawlerType",
] 