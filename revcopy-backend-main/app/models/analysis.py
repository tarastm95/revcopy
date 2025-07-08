"""
Analysis model for storing NLP processing results and review insights.
Includes sentiment analysis, topic modeling, and extracted insights.
"""

import enum
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, Integer, 
    JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AnalysisStatus(enum.Enum):
    """Analysis processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SentimentType(enum.Enum):
    """Sentiment classification types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class AnalysisType(enum.Enum):
    """Types of analysis performed."""
    FULL_ANALYSIS = "full_analysis"
    SENTIMENT_ONLY = "sentiment_only"
    TOPIC_MODELING = "topic_modeling"
    QUICK_SCAN = "quick_scan"


class Analysis(Base):
    """
    Main analysis model for storing NLP processing results.
    
    Attributes:
        id: Primary key
        product_id: Foreign key to analyzed product
        analysis_type: Type of analysis performed
        status: Processing status
        review_data: Raw review data
        insights: Extracted insights and findings
        sentiment_summary: Overall sentiment analysis
        topics: Discovered topics and themes
        timestamps: Processing times
    """
    
    __tablename__ = "analyses"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Product relationship
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    
    # Analysis configuration
    analysis_type: Mapped[AnalysisType] = mapped_column(
        Enum(AnalysisType), default=AnalysisType.FULL_ANALYSIS, nullable=False
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False
    )
    
    # Review data
    total_reviews_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reviews_data: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    
    # Sentiment analysis results
    overall_sentiment: Mapped[Optional[SentimentType]] = mapped_column(
        Enum(SentimentType), nullable=True
    )
    sentiment_scores: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    sentiment_distribution: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Topic modeling results
    discovered_topics: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    topic_keywords: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    topic_sentiment_mapping: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Key insights and findings
    key_insights: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    pain_points: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    benefits: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    common_complaints: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    common_praises: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Feature analysis
    mentioned_features: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    feature_sentiment: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    feature_frequency: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Customer personas and segments
    customer_segments: Mapped[Optional[List[Dict]]] = mapped_column(JSON, nullable=True)
    use_cases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    user_demographics: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Competitive insights
    comparison_points: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    competitive_advantages: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    areas_for_improvement: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Quality metrics
    analysis_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Processing metadata
    model_versions: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    processing_parameters: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="analyses")
    review_insights: Mapped[List["ReviewInsight"]] = relationship(
        "ReviewInsight", back_populates="analysis", cascade="all, delete-orphan"
    )
    sentiment_analyses: Mapped[List["SentimentAnalysis"]] = relationship(
        "SentimentAnalysis", back_populates="analysis", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of Analysis."""
        return f"<Analysis(id={self.id}, product_id={self.product_id}, status='{self.status.value}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status == AnalysisStatus.COMPLETED
    
    @property
    def is_processing(self) -> bool:
        """Check if analysis is currently processing."""
        return self.status == AnalysisStatus.PROCESSING
    
    @property
    def has_failed(self) -> bool:
        """Check if analysis has failed."""
        return self.status == AnalysisStatus.FAILED
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def dominant_sentiment(self) -> Optional[str]:
        """Get the dominant sentiment from distribution."""
        if not self.sentiment_distribution:
            return self.overall_sentiment.value if self.overall_sentiment else None
        
        max_sentiment = max(self.sentiment_distribution.items(), key=lambda x: x[1])
        return max_sentiment[0]
    
    def mark_as_processing(self) -> None:
        """Mark analysis as currently processing."""
        self.status = AnalysisStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.error_message = None
    
    def mark_as_completed(self) -> None:
        """Mark analysis as completed."""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.error_message = None
        
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def get_top_topics(self, limit: int = 5) -> List[Dict]:
        """Get top discovered topics."""
        if not self.discovered_topics:
            return []
        
        # Sort by relevance score if available
        sorted_topics = sorted(
            self.discovered_topics,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        return sorted_topics[:limit]
    
    def get_sentiment_percentage(self, sentiment: SentimentType) -> float:
        """Get percentage for specific sentiment."""
        if not self.sentiment_distribution:
            return 0.0
        
        return self.sentiment_distribution.get(sentiment.value, 0.0)


class ReviewInsight(Base):
    """
    Individual review insights and extracted information.
    
    Attributes:
        id: Primary key
        analysis_id: Foreign key to parent analysis
        review_text: Original review text
        sentiment: Review sentiment
        extracted_features: Features mentioned in review
        insights: Specific insights from this review
        metadata: Additional review metadata
    """
    
    __tablename__ = "review_insights"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Analysis relationship
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analyses.id"), nullable=False, index=True
    )
    
    # Review content
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    review_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    review_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Review metadata
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified_purchase: Mapped[Optional[bool]] = mapped_column(nullable=True)
    helpful_votes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Analysis results
    sentiment: Mapped[Optional[SentimentType]] = mapped_column(
        Enum(SentimentType), nullable=True
    )
    sentiment_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Extracted information
    mentioned_features: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    key_phrases: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Insights
    insights: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    pain_points: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    benefits: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Processing metadata
    processing_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="review_insights")
    
    def __repr__(self) -> str:
        """String representation of ReviewInsight."""
        return f"<ReviewInsight(id={self.id}, sentiment='{self.sentiment}', rating={self.review_rating})>"


class SentimentAnalysis(Base):
    """
    Detailed sentiment analysis results for different aspects.
    
    Attributes:
        id: Primary key
        analysis_id: Foreign key to parent analysis
        aspect: Product aspect being analyzed
        sentiment: Sentiment for this aspect
        confidence: Confidence score
        evidence: Supporting text evidence
    """
    
    __tablename__ = "sentiment_analyses"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Analysis relationship
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analyses.id"), nullable=False, index=True
    )
    
    # Aspect information
    aspect: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    aspect_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Sentiment results
    sentiment: Mapped[SentimentType] = mapped_column(
        Enum(SentimentType), nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Supporting evidence
    supporting_text: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    mention_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Impact and importance
    importance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impact_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="sentiment_analyses")
    
    def __repr__(self) -> str:
        """String representation of SentimentAnalysis."""
        return f"<SentimentAnalysis(aspect='{self.aspect}', sentiment='{self.sentiment.value}')>"
    
    @property
    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return self.sentiment == SentimentType.POSITIVE
    
    @property
    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return self.sentiment == SentimentType.NEGATIVE
    
    @property
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return self.sentiment == SentimentType.NEUTRAL 