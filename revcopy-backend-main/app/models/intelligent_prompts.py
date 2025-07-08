"""
Advanced database models for intelligent prompt management system.

This module provides enterprise-level database models for:
- Multi-language prompt templates
- Cultural adaptations
- A/B testing framework
- Performance analytics
- Template versioning
- Usage optimization
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, JSON, Float,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class PromptTemplateV2(Base):
    """
    Enhanced prompt template model with enterprise features.
    """
    __tablename__ = "prompt_templates_v2"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Template identification
    template_type = Column(String(50), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)  # e_commerce, luxury, tech, etc.
    
    # Multi-language support
    primary_language = Column(String(10), default="en", index=True)
    supported_languages = Column(JSON, default=["en"])  # List of ISO language codes
    cultural_regions = Column(JSON, default=["north_america"])  # Supported regions
    
    # Template content
    system_prompt = Column(Text)
    user_prompt_template = Column(Text, nullable=False)
    
    # Advanced configuration
    context_tags = Column(JSON, default=[])  # Context-specific tags
    target_audience = Column(String(100))  # target demographic
    tone = Column(String(50), default="professional")  # tone of voice
    urgency_level = Column(String(20), default="medium")
    personalization_level = Column(String(20), default="standard")
    
    # Generation parameters
    default_temperature = Column(Float, default=0.7)
    default_max_tokens = Column(Integer, default=1500)
    default_top_p = Column(Float, default=0.9)
    default_frequency_penalty = Column(Float, default=0.0)
    default_presence_penalty = Column(Float, default=0.0)
    
    # Provider support
    supported_providers = Column(JSON, default=["deepseek", "openai"])
    provider_preferences = Column(JSON, default={})  # Provider-specific settings
    
    # Template variables and validation
    required_variables = Column(JSON, default=[])
    optional_variables = Column(JSON, default=[])
    variable_types = Column(JSON, default={})  # Type hints for variables
    validation_rules = Column(JSON, default={})  # Validation rules
    
    # Content quality
    content_guidelines = Column(JSON, default={})  # Content quality guidelines
    output_format = Column(String(50), default="text")  # text, html, markdown, json
    max_output_length = Column(Integer)
    min_output_length = Column(Integer)
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    average_generation_time = Column(Float, default=0.0)
    average_user_rating = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    # Template management
    version = Column(String(20), default="1.0.0")
    parent_template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"))
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)
    is_experimental = Column(Boolean, default=False)
    
    # A/B testing
    ab_test_group = Column(String(50))  # A, B, C, control, etc.
    ab_test_weight = Column(Float, default=1.0)  # Traffic allocation weight
    ab_test_start_date = Column(DateTime(timezone=True))
    ab_test_end_date = Column(DateTime(timezone=True))
    
    # Access control
    visibility = Column(String(20), default="public")  # public, private, organization
    access_roles = Column(JSON, default=[])  # Roles that can use this template
    
    # Metadata
    tags = Column(JSON, default=[])
    template_metadata = Column(JSON, default={})
    example_output = Column(Text)
    documentation_url = Column(String(500))
    
    # Timestamps and tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    # Relationships
    parent_template = relationship("PromptTemplateV2", remote_side=[id])
    child_templates = relationship("PromptTemplateV2", back_populates="parent_template")
    generations = relationship("IntelligentGeneration", back_populates="template")
    performance_metrics = relationship("TemplatePerformanceMetric", back_populates="template")
    adaptations = relationship("CulturalAdaptation", back_populates="template")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_template_type_language', 'template_type', 'primary_language'),
        Index('ix_active_templates', 'is_active', 'template_type'),
        Index('ix_template_performance', 'success_rate', 'usage_count'),
        Index('ix_ab_test_templates', 'ab_test_group', 'is_active'),
        UniqueConstraint('template_type', 'name', 'version', name='uq_template_name_version'),
    )


class CulturalAdaptation(Base):
    """
    Cultural and linguistic adaptations for prompt templates.
    """
    __tablename__ = "cultural_adaptations"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"), nullable=False)
    
    # Localization details
    language_code = Column(String(10), nullable=False, index=True)  # ISO 639-1
    cultural_region = Column(String(50), nullable=False, index=True)
    country_code = Column(String(5))  # ISO 3166-1
    
    # Adapted content
    adapted_system_prompt = Column(Text)
    adapted_user_prompt = Column(Text)
    
    # Cultural modifications
    cultural_modifications = Column(JSON, default={})  # Specific cultural adaptations
    linguistic_modifications = Column(JSON, default={})  # Language-specific changes
    formatting_rules = Column(JSON, default={})  # Date, currency, number formats
    
    # Content preferences
    preferred_tone = Column(String(50))
    preferred_style = Column(String(50))
    taboo_words = Column(JSON, default=[])  # Words to avoid
    preferred_terminology = Column(JSON, default={})  # Preferred translations
    
    # Visual and UX adaptations
    text_direction = Column(String(10), default="ltr")  # ltr, rtl
    color_preferences = Column(JSON, default=[])
    imagery_guidelines = Column(JSON, default={})
    
    # Performance in this locale
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    user_satisfaction = Column(Float, default=0.0)
    
    # Validation and quality
    is_validated = Column(Boolean, default=False)
    validated_by = Column(String(100))  # Native speaker/cultural expert
    validation_date = Column(DateTime(timezone=True))
    quality_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    template = relationship("PromptTemplateV2", back_populates="adaptations")
    
    __table_args__ = (
        Index('ix_adaptation_locale', 'language_code', 'cultural_region'),
        UniqueConstraint('template_id', 'language_code', 'cultural_region', 
                        name='uq_template_adaptation'),
    )


class IntelligentGeneration(Base):
    """
    Enhanced generation tracking with intelligence metrics.
    """
    __tablename__ = "intelligent_generations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Template and generation details
    template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"))
    adaptation_id = Column(Integer, ForeignKey("cultural_adaptations.id"))
    
    # Request context
    content_type = Column(String(50), index=True)
    language_requested = Column(String(10), index=True)
    cultural_region = Column(String(50), index=True)
    context_tags = Column(JSON, default=[])
    
    # Input data
    product_url = Column(String(500))
    product_data = Column(JSON)
    reviews_analyzed = Column(Integer, default=0)
    input_variables = Column(JSON, default={})
    
    # Selection criteria
    selection_criteria = Column(JSON)  # PromptSelectionCriteria as JSON
    selection_score = Column(Float)  # Template selection score
    alternatives_considered = Column(JSON, default=[])  # Other templates considered
    
    # Generation parameters
    ai_provider = Column(String(50), nullable=False)
    temperature = Column(Float)
    max_tokens = Column(Integer)
    top_p = Column(Float)
    frequency_penalty = Column(Float)
    presence_penalty = Column(Float)
    
    # Output results
    generated_content = Column(Text)
    content_metadata = Column(JSON)
    adaptations_applied = Column(JSON, default={})
    
    # Performance metrics
    generation_time_ms = Column(Integer)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_estimate = Column(Float)  # Estimated cost in USD
    
    # Quality metrics
    success = Column(Boolean, default=False, index=True)
    error_message = Column(Text)
    content_quality_score = Column(Float)  # AI-assessed quality
    uniqueness_score = Column(Float)  # Content uniqueness
    relevance_score = Column(Float)  # Relevance to input
    coherence_score = Column(Float)  # Text coherence
    
    # User feedback
    user_rating = Column(Integer)  # 1-5 rating
    user_feedback = Column(Text)
    user_id = Column(String(100))  # User who generated this
    session_id = Column(String(100), index=True)
    
    # Business metrics
    conversion_tracked = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    conversion_value = Column(Float)
    
    # A/B testing
    ab_test_group = Column(String(50))
    ab_test_variant = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    template = relationship("PromptTemplateV2", back_populates="generations")
    performance_impacts = relationship("TemplatePerformanceMetric", 
                                     foreign_keys="TemplatePerformanceMetric.generation_id")
    
    __table_args__ = (
        Index('ix_generation_performance', 'template_id', 'success', 'created_at'),
        Index('ix_generation_language', 'language_requested', 'cultural_region'),
        Index('ix_generation_ab_test', 'ab_test_group', 'ab_test_variant'),
        Index('ix_generation_user', 'user_id', 'session_id'),
    )


class TemplatePerformanceMetric(Base):
    """
    Detailed performance metrics for template optimization.
    """
    __tablename__ = "template_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"), nullable=False)
    generation_id = Column(Integer, ForeignKey("intelligent_generations.id"))
    
    # Time period for metrics
    metric_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    period_type = Column(String(20), default="daily")  # hourly, daily, weekly, monthly
    
    # Basic usage metrics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Performance metrics
    average_generation_time = Column(Float, default=0.0)
    median_generation_time = Column(Float, default=0.0)
    p95_generation_time = Column(Float, default=0.0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Quality metrics
    average_quality_score = Column(Float, default=0.0)
    average_user_rating = Column(Float, default=0.0)
    average_uniqueness_score = Column(Float, default=0.0)
    average_relevance_score = Column(Float, default=0.0)
    
    # Business metrics
    conversion_rate = Column(Float, default=0.0)
    total_conversion_value = Column(Float, default=0.0)
    revenue_per_generation = Column(Float, default=0.0)
    
    # Context-specific metrics
    language_breakdown = Column(JSON, default={})  # Performance by language
    region_breakdown = Column(JSON, default={})  # Performance by region
    context_breakdown = Column(JSON, default={})  # Performance by context
    
    # Comparative metrics
    relative_performance = Column(Float, default=1.0)  # Relative to template average
    rank_in_category = Column(Integer)  # Rank among similar templates
    
    # Trends
    trend_direction = Column(String(20))  # improving, declining, stable
    trend_strength = Column(Float, default=0.0)  # -1 to 1
    
    # Updated timestamp
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    template = relationship("PromptTemplateV2", back_populates="performance_metrics")
    
    __table_args__ = (
        Index('ix_performance_template_date', 'template_id', 'metric_date'),
        Index('ix_performance_period', 'period_type', 'metric_date'),
        UniqueConstraint('template_id', 'metric_date', 'period_type', 
                        name='uq_performance_metric'),
    )


class ABTestExperiment(Base):
    """
    A/B testing experiments for prompt optimization.
    """
    __tablename__ = "ab_test_experiments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Experiment details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)  # What we're testing
    
    # Test configuration
    content_type = Column(String(50), index=True)
    test_variants = Column(JSON, nullable=False)  # List of template IDs and weights
    traffic_allocation = Column(JSON, nullable=False)  # Traffic split
    
    # Target criteria
    target_languages = Column(JSON, default=["en"])
    target_regions = Column(JSON, default=["north_america"])
    target_contexts = Column(JSON, default=[])
    
    # Experiment parameters
    success_metric = Column(String(50), default="user_rating")  # Primary metric
    secondary_metrics = Column(JSON, default=[])  # Additional metrics to track
    minimum_sample_size = Column(Integer, default=100)
    confidence_level = Column(Float, default=0.95)
    
    # Status and timeline
    status = Column(String(20), default="draft", index=True)  # draft, running, paused, completed
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    planned_duration_days = Column(Integer)
    
    # Results
    statistical_significance = Column(Boolean, default=False)
    winning_variant = Column(String(50))  # Template ID or variant name
    confidence_interval = Column(JSON)  # Statistical confidence interval
    p_value = Column(Float)
    effect_size = Column(Float)
    
    # Current metrics
    total_samples = Column(Integer, default=0)
    variant_performance = Column(JSON, default={})  # Performance by variant
    
    # Metadata
    created_by = Column(String(100))
    updated_by = Column(String(100))
    reviewed_by = Column(String(100))  # Who reviewed the results
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_experiment_status_date', 'status', 'start_date'),
        Index('ix_experiment_type', 'content_type', 'status'),
        CheckConstraint('confidence_level > 0 AND confidence_level < 1', 
                       name='check_confidence_level'),
    )


class PromptOptimizationJob(Base):
    """
    Automated prompt optimization jobs.
    """
    __tablename__ = "prompt_optimization_jobs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Job details
    job_type = Column(String(50), nullable=False, index=True)  # performance_optimize, cultural_adapt
    target_template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"))
    
    # Optimization parameters
    optimization_criteria = Column(JSON)  # What to optimize for
    constraints = Column(JSON, default={})  # Optimization constraints
    target_metrics = Column(JSON)  # Target performance metrics
    
    # Job configuration
    algorithm = Column(String(50), default="genetic")  # genetic, gradient, random
    iterations = Column(Integer, default=100)
    population_size = Column(Integer, default=50)
    mutation_rate = Column(Float, default=0.1)
    
    # Status
    status = Column(String(20), default="pending", index=True)
    progress_percentage = Column(Float, default=0.0)
    current_iteration = Column(Integer, default=0)
    
    # Results
    best_template_id = Column(Integer, ForeignKey("prompt_templates_v2.id"))
    improvement_percentage = Column(Float)
    optimization_log = Column(JSON, default=[])  # Detailed optimization log
    
    # Performance
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    __table_args__ = (
        Index('ix_optimization_status', 'status', 'job_type'),
        Index('ix_optimization_template', 'target_template_id', 'status'),
    ) 