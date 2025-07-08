"""
Pydantic schemas for request/response validation.
Contains data validation and serialization schemas.
"""

from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    TokenData,
)
from .product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductAnalyzeRequest,
)
from .analysis import (
    AnalysisResponse,
    AnalysisCreate,
    ReviewInsightResponse,
    SentimentResponse,
)
from .generation import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    CampaignCreate,
    CampaignResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    # Product schemas
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "ProductAnalyzeRequest",
    # Analysis schemas
    "AnalysisResponse",
    "AnalysisCreate",
    "ReviewInsightResponse",
    "SentimentResponse",
    # Generation schemas
    "ContentGenerationRequest",
    "ContentGenerationResponse",
    "CampaignCreate",
    "CampaignResponse",
] 