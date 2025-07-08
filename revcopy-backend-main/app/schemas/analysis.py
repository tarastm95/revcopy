"""Analysis schemas for NLP processing and insights."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.analysis import AnalysisStatus, SentimentType


class AnalysisCreate(BaseModel):
    """Schema for creating analysis."""
    product_id: int
    analysis_type: str = Field("full_analysis", pattern="^(full_analysis|sentiment_only|topic_modeling|quick_scan)$")
    max_reviews: int = Field(200, ge=50, le=1000)


class SentimentResponse(BaseModel):
    """Schema for sentiment analysis response."""
    id: int
    aspect: str
    sentiment: SentimentType
    confidence_score: float
    supporting_text: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class ReviewInsightResponse(BaseModel):
    """Schema for review insight response."""
    id: int
    review_text: str
    sentiment: Optional[SentimentType] = None
    insights: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    id: int
    product_id: int
    status: AnalysisStatus
    total_reviews_processed: int
    overall_sentiment: Optional[SentimentType] = None
    key_insights: Optional[List[str]] = None
    pain_points: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    review_insights: List[ReviewInsightResponse] = []
    sentiment_analyses: List[SentimentResponse] = []
    
    class Config:
        from_attributes = True 