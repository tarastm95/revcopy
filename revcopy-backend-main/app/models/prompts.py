"""
Enhanced database models for intelligent prompt management system.

Supports multi-language content generation, cultural adaptations, 
A/B testing, and performance analytics for enterprise-level prompt optimization.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class PromptTemplate(Base):
    """
    Enhanced model for storing AI prompt templates with intelligent features.
    Supports multi-language, cultural adaptations, and performance optimization.
    """
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Template identification
    template_type = Column(String(50), index=True, nullable=False)  # product_description, faq, comparison
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True)  # e_commerce, luxury, tech, etc.
    
    # Multi-language and cultural support
    primary_language = Column(String(10), default="en", index=True)  # ISO 639-1 language code
    supported_languages = Column(JSON, default=["en"])  # List of supported languages
    cultural_regions = Column(JSON, default=["north_america"])  # Supported cultural regions
    localization_notes = Column(Text)  # Notes for localization teams
    
    # Context and targeting
    context_tags = Column(JSON, default=[])  # Context-specific tags (luxury, budget, tech, etc.)
    target_audience = Column(String(100))  # Target demographic
    product_categories = Column(JSON, default=[])  # Suitable product categories
    price_ranges = Column(JSON, default=["all"])  # low, medium, high, luxury
    brand_personalities = Column(JSON, default=[])  # formal, casual, playful, etc.
    
    # Prompt content
    system_prompt = Column(Text, nullable=True)
    user_prompt_template = Column(Text, nullable=False)
    
    # Advanced prompt configuration
    tone = Column(String(50), default="professional")  # professional, friendly, casual, luxurious
    urgency_level = Column(String(20), default="medium")  # low, medium, high
    personalization_level = Column(String(20), default="standard")  # minimal, standard, high
    content_style = Column(String(50), default="balanced")  # balanced, enthusiastic, conservative
    content_length = Column(String(20), default="medium")  # short, medium, long
    
    # Template configuration
    default_temperature = Column(Float, default=0.7)
    default_max_tokens = Column(Integer, default=1500)
    default_top_p = Column(Float, default=0.9)
    default_frequency_penalty = Column(Float, default=0.0)
    default_presence_penalty = Column(Float, default=0.0)
    supported_providers = Column(JSON, default=["deepseek", "openai"])
    provider_preferences = Column(JSON, default={})  # Provider-specific optimizations
    
    # Template variables and validation
    required_variables = Column(JSON, default=[])  # List of required template variables
    optional_variables = Column(JSON, default=[])  # List of optional template variables
    variable_types = Column(JSON, default={})  # Type hints for variables
    validation_rules = Column(JSON, default={})  # Validation rules for variables
    example_output = Column(Text, nullable=True)
    
    # Content quality guidelines
    content_guidelines = Column(JSON, default={})  # Quality guidelines and rules
    output_format = Column(String(50), default="text")  # text, html, markdown, json
    max_output_length = Column(Integer)
    min_output_length = Column(Integer)
    prohibited_terms = Column(JSON, default=[])  # Terms to avoid
    required_elements = Column(JSON, default=[])  # Required content elements
    
    # Performance tracking and analytics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Changed from string to float
    average_generation_time = Column(Float, default=0.0)  # Average time in seconds
    average_user_rating = Column(Float, default=0.0)  # 1-5 scale
    conversion_rate = Column(Float, default=0.0)  # Business conversion rate
    cost_per_generation = Column(Float, default=0.0)  # Average cost in USD
    
    # Quality metrics
    content_quality_score = Column(Float, default=0.0)  # AI-assessed content quality
    uniqueness_score = Column(Float, default=0.0)  # Content uniqueness
    relevance_score = Column(Float, default=0.0)  # Relevance to prompt
    coherence_score = Column(Float, default=0.0)  # Text coherence
    
    # A/B testing support
    ab_test_group = Column(String(50))  # A, B, C, control, etc.
    ab_test_weight = Column(Float, default=1.0)  # Traffic allocation weight
    ab_test_start_date = Column(DateTime(timezone=True))
    ab_test_end_date = Column(DateTime(timezone=True))
    ab_test_results = Column(JSON, default={})  # A/B test results
    
    # Status and metadata
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)
    is_experimental = Column(Boolean, default=False)
    visibility = Column(String(20), default="public")  # public, private, organization
    version = Column(String(20), default="1.0.0")
    parent_template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    
    # Performance optimization
    optimization_status = Column(String(20), default="none")  # none, optimizing, optimized
    optimization_score = Column(Float, default=0.0)
    last_optimization_date = Column(DateTime(timezone=True))
    optimization_notes = Column(Text)
    
    # Access control and collaboration
    access_roles = Column(JSON, default=[])  # Roles that can use this template
    collaboration_notes = Column(Text)  # Notes for team collaboration
    review_status = Column(String(20), default="draft")  # draft, review, approved
    reviewed_by = Column(String(100))
    review_date = Column(DateTime(timezone=True))
    
    # Metadata and documentation
    tags = Column(JSON, default=[])
    template_metadata = Column(JSON, default={})
    documentation_url = Column(String(500))
    changelog = Column(JSON, default=[])  # Version change history
    
    # Analytics and insights
    performance_insights = Column(JSON, default={})  # AI-generated insights
    usage_patterns = Column(JSON, default={})  # Usage pattern analysis
    optimization_suggestions = Column(JSON, default=[])  # AI suggestions for improvement
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    parent_template = relationship("PromptTemplate", remote_side=[id])
    child_templates = relationship("PromptTemplate", back_populates="parent_template")
    cultural_adaptations = relationship("CulturalAdaptation", back_populates="template")
    generations = relationship("AIContentGeneration", back_populates="template")
    performance_metrics = relationship("TemplatePerformanceMetric", back_populates="template")
    
    # Database constraints and indexes for performance
    __table_args__ = (
        Index('ix_template_type_language', 'template_type', 'primary_language'),
        Index('ix_template_performance', 'success_rate', 'average_user_rating'),
        Index('ix_template_active_category', 'is_active', 'category'),
        Index('ix_template_ab_test', 'ab_test_group', 'is_active'),
        UniqueConstraint('template_type', 'name', 'version', name='uq_template_name_version'),
    )


class CulturalAdaptation(Base):
    """
    Cultural and linguistic adaptations for prompt templates.
    Enables localization and cultural sensitivity.
    """
    __tablename__ = "cultural_adaptations"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    
    # Localization details
    language_code = Column(String(10), nullable=False, index=True)  # ISO 639-1
    cultural_region = Column(String(50), nullable=False, index=True)  # north_america, middle_east, etc.
    country_codes = Column(JSON, default=[])  # ISO 3166-1 country codes
    locale_code = Column(String(20))  # Full locale code (e.g., he-IL, ar-AE)
    
    # Adapted content
    adapted_system_prompt = Column(Text)
    adapted_user_prompt = Column(Text)
    adapted_example_output = Column(Text)
    
    # Cultural modifications
    cultural_modifications = Column(JSON, default={})  # Specific cultural adaptations
    linguistic_modifications = Column(JSON, default={})  # Language-specific changes
    formatting_rules = Column(JSON, default={})  # Date, currency, number formats
    
    # Content preferences and restrictions
    preferred_tone = Column(String(50))
    preferred_style = Column(String(50))
    taboo_words = Column(JSON, default=[])  # Words to avoid
    taboo_concepts = Column(JSON, default=[])  # Concepts to avoid
    preferred_terminology = Column(JSON, default={})  # Preferred translations
    cultural_sensitivities = Column(JSON, default=[])  # Cultural sensitivity notes
    
    # Visual and UX adaptations
    text_direction = Column(String(10), default="ltr")  # ltr, rtl
    number_format = Column(String(20), default="western")  # western, arabic, etc.
    date_format = Column(String(20), default="MM/DD/YYYY")
    currency_symbol = Column(String(10), default="$")
    measurement_system = Column(String(20), default="metric")  # metric, imperial
    
    # Color and design preferences
    color_preferences = Column(JSON, default=[])
    color_restrictions = Column(JSON, default=[])  # Colors to avoid
    imagery_guidelines = Column(JSON, default={})
    layout_preferences = Column(JSON, default={})
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    user_satisfaction = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    # Quality assurance
    is_validated = Column(Boolean, default=False)
    validated_by = Column(String(100))  # Native speaker/cultural expert
    validation_date = Column(DateTime(timezone=True))
    validation_notes = Column(Text)
    quality_score = Column(Float, default=0.0)
    
    # Review and approval process
    review_status = Column(String(20), default="draft")  # draft, review, approved
    reviewed_by = Column(String(100))
    review_date = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Metadata
    adaptation_notes = Column(Text)
    translator_notes = Column(Text)
    cultural_expert_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    # Relationships
    template = relationship("PromptTemplate", back_populates="cultural_adaptations")
    
    __table_args__ = (
        Index('ix_adaptation_locale', 'language_code', 'cultural_region'),
        Index('ix_adaptation_performance', 'success_rate', 'user_satisfaction'),
        UniqueConstraint('template_id', 'language_code', 'cultural_region', 
                        name='uq_template_adaptation'),
    )


class AIContentGeneration(Base):
    """
    Enhanced model for storing AI-generated content history with intelligence metrics.
    Tracks all content generation requests, results, and performance analytics.
    """
    __tablename__ = "ai_generated_content"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Generation request details
    template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    adaptation_id = Column(Integer, ForeignKey("cultural_adaptations.id"))
    template_type = Column(String(50), index=True, nullable=False)
    ai_provider = Column(String(30), nullable=False)
    
    # Request context and selection
    selection_criteria = Column(JSON)  # PromptSelectionCriteria as JSON
    selection_score = Column(Float)  # Template selection score
    alternatives_considered = Column(JSON, default=[])  # Other templates considered
    
    # Language and cultural context
    language_requested = Column(String(10), index=True)
    cultural_region = Column(String(50), index=True)
    context_tags = Column(JSON, default=[])
    target_audience = Column(String(100))
    
    # Input data
    product_url = Column(String(500), nullable=True)
    product_data = Column(JSON, nullable=True)
    reviews_analyzed = Column(Integer, default=0)
    input_parameters = Column(JSON, nullable=True)
    custom_variables = Column(JSON, default={})
    
    # Generation parameters
    temperature = Column(Float)
    max_tokens = Column(Integer)
    top_p = Column(Float)
    frequency_penalty = Column(Float)
    presence_penalty = Column(Float)
    generation_config = Column(JSON, default={})  # Additional config
    
    # Output results
    generated_content = Column(Text, nullable=True)
    content_metadata = Column(JSON, nullable=True)
    adaptations_applied = Column(JSON, default={})
    post_processing_applied = Column(JSON, default=[])
    
    # Performance metrics
    generation_time_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_estimate = Column(Float)  # Estimated cost in USD
    
    # Quality metrics
    success = Column(Boolean, default=False, index=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(50))  # timeout, rate_limit, content_filter, etc.
    content_quality_score = Column(Float)  # AI-assessed quality
    uniqueness_score = Column(Float)  # Content uniqueness
    relevance_score = Column(Float)  # Relevance to input
    coherence_score = Column(Float)  # Text coherence
    creativity_score = Column(Float)  # Content creativity
    
    # User feedback and interaction
    user_rating = Column(Integer)  # 1-5 user rating
    user_feedback = Column(Text, nullable=True)
    user_id = Column(String(100))
    session_id = Column(String(100), index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Business and conversion metrics
    conversion_tracked = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    conversion_value = Column(Float)
    time_to_conversion = Column(Integer)  # Seconds from generation to conversion
    
    # A/B testing
    ab_test_group = Column(String(50))
    ab_test_variant = Column(String(50))
    ab_test_experiment_id = Column(String(100))
    
    # Content analysis
    sentiment_score = Column(Float)  # Content sentiment
    readability_score = Column(Float)  # Text readability
    complexity_score = Column(Float)  # Content complexity
    keyword_density = Column(JSON, default={})  # Keyword analysis
    content_categories = Column(JSON, default=[])  # Auto-categorized content
    
    # Monitoring and alerts
    flagged_content = Column(Boolean, default=False)
    flag_reasons = Column(JSON, default=[])
    reviewed_by_human = Column(Boolean, default=False)
    human_reviewer = Column(String(100))
    review_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    
    # Relationships
    template = relationship("PromptTemplate", back_populates="generations")
    adaptation = relationship("CulturalAdaptation")
    
    __table_args__ = (
        Index('ix_generation_template_success', 'template_id', 'success', 'created_at'),
        Index('ix_generation_language_region', 'language_requested', 'cultural_region'),
        Index('ix_generation_ab_test', 'ab_test_group', 'ab_test_variant'),
        Index('ix_generation_user_session', 'user_id', 'session_id'),
        Index('ix_generation_performance', 'content_quality_score', 'user_rating'),
    )


class TemplatePerformanceMetric(Base):
    """
    Detailed performance metrics for template optimization and analytics.
    Tracks performance over time periods for data-driven improvements.
    """
    __tablename__ = "template_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    
    # Time period for metrics
    metric_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    period_type = Column(String(20), default="daily", index=True)  # hourly, daily, weekly, monthly
    
    # Basic usage metrics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Performance metrics
    average_generation_time = Column(Float, default=0.0)
    median_generation_time = Column(Float, default=0.0)
    p95_generation_time = Column(Float, default=0.0)  # 95th percentile
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    cost_per_generation = Column(Float, default=0.0)
    
    # Quality metrics
    average_quality_score = Column(Float, default=0.0)
    average_user_rating = Column(Float, default=0.0)
    average_uniqueness_score = Column(Float, default=0.0)
    average_relevance_score = Column(Float, default=0.0)
    content_flagged_rate = Column(Float, default=0.0)
    
    # Business metrics
    conversion_rate = Column(Float, default=0.0)
    total_conversion_value = Column(Float, default=0.0)
    revenue_per_generation = Column(Float, default=0.0)
    
    # Contextual breakdowns
    language_breakdown = Column(JSON, default={})  # Performance by language
    region_breakdown = Column(JSON, default={})  # Performance by cultural region
    context_breakdown = Column(JSON, default={})  # Performance by context tags
    provider_breakdown = Column(JSON, default={})  # Performance by AI provider
    
    # User satisfaction
    user_ratings_distribution = Column(JSON, default={})  # Distribution of ratings
    positive_feedback_rate = Column(Float, default=0.0)
    negative_feedback_rate = Column(Float, default=0.0)
    
    # Comparative metrics
    relative_performance = Column(Float, default=1.0)  # Relative to category average
    rank_in_category = Column(Integer)  # Rank among similar templates
    market_share = Column(Float, default=0.0)  # Share of usage in category
    
    # Trend analysis
    trend_direction = Column(String(20))  # improving, declining, stable
    trend_strength = Column(Float, default=0.0)  # -1 to 1 trend strength
    volatility_score = Column(Float, default=0.0)  # Performance volatility
    
    # Predictive metrics
    predicted_performance = Column(Float)  # AI-predicted future performance
    confidence_interval = Column(JSON, default=[])  # Prediction confidence
    optimization_potential = Column(Float, default=0.0)  # Potential for improvement
    
    # Metadata
    calculation_method = Column(String(50), default="standard")
    data_quality_score = Column(Float, default=1.0)  # Quality of underlying data
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    template = relationship("PromptTemplate", back_populates="performance_metrics")
    
    __table_args__ = (
        Index('ix_performance_template_date', 'template_id', 'metric_date'),
        Index('ix_performance_period_type', 'period_type', 'metric_date'),
        Index('ix_performance_trends', 'trend_direction', 'trend_strength'),
        UniqueConstraint('template_id', 'metric_date', 'period_type', 
                        name='uq_performance_metric'),
    )


class ABTestExperiment(Base):
    """
    A/B testing experiments for prompt optimization and performance comparison.
    Enables data-driven prompt improvement through controlled experiments.
    """
    __tablename__ = "ab_test_experiments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Experiment identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)  # What we're testing
    experiment_type = Column(String(50), default="template_comparison")
    
    # Test configuration
    content_type = Column(String(50), index=True)
    test_variants = Column(JSON, nullable=False)  # List of template IDs and configurations
    traffic_allocation = Column(JSON, nullable=False)  # Traffic split percentages
    control_variant = Column(String(50))  # Control group identifier
    
    # Target criteria
    target_languages = Column(JSON, default=["en"])
    target_regions = Column(JSON, default=["north_america"])
    target_contexts = Column(JSON, default=[])
    target_audience = Column(JSON, default=[])
    inclusion_criteria = Column(JSON, default={})
    exclusion_criteria = Column(JSON, default={})
    
    # Experiment parameters
    success_metric = Column(String(50), default="user_rating")  # Primary success metric
    secondary_metrics = Column(JSON, default=[])  # Additional metrics to track
    minimum_sample_size = Column(Integer, default=100)
    minimum_effect_size = Column(Float, default=0.1)  # Minimum meaningful difference
    confidence_level = Column(Float, default=0.95)
    statistical_power = Column(Float, default=0.8)
    
    # Status and timeline
    status = Column(String(20), default="draft", index=True)  # draft, running, paused, completed, cancelled
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    planned_duration_days = Column(Integer)
    actual_duration_days = Column(Integer)
    
    # Results and analysis
    statistical_significance = Column(Boolean, default=False)
    winning_variant = Column(String(50))  # Template ID or variant name
    confidence_interval = Column(JSON)  # Statistical confidence interval
    p_value = Column(Float)
    effect_size = Column(Float)
    practical_significance = Column(Boolean, default=False)
    
    # Current metrics
    total_samples = Column(Integer, default=0)
    samples_per_variant = Column(JSON, default={})
    variant_performance = Column(JSON, default={})  # Performance by variant
    interim_results = Column(JSON, default=[])  # Historical interim analyses
    
    # Quality assurance
    randomization_check = Column(Boolean, default=False)
    balance_check_results = Column(JSON, default={})
    data_quality_issues = Column(JSON, default=[])
    bias_analysis = Column(JSON, default={})
    
    # Decision and follow-up
    decision = Column(String(50))  # implement_winner, no_change, needs_more_data
    decision_rationale = Column(Text)
    implementation_date = Column(DateTime(timezone=True))
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    # Metadata and collaboration
    created_by = Column(String(100))
    updated_by = Column(String(100))
    reviewed_by = Column(String(100))
    approved_by = Column(String(100))
    stakeholders = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_experiment_status_date', 'status', 'start_date'),
        Index('ix_experiment_type_status', 'experiment_type', 'status'),
        Index('ix_experiment_content_type', 'content_type', 'status'),
    )


class ContentGenerationStats(Base):
    """
    Enhanced model for tracking content generation statistics and analytics.
    Provides comprehensive insights for system optimization and business intelligence.
    """
    __tablename__ = "content_generation_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time period
    date = Column(DateTime(timezone=True), index=True, nullable=False)
    period_type = Column(String(20), default="daily", index=True)  # hourly, daily, weekly, monthly
    
    # Generation statistics
    total_generations = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)
    failed_generations = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Provider statistics
    provider_usage = Column(JSON, default={})  # Usage by provider
    provider_performance = Column(JSON, default={})  # Performance by provider
    provider_costs = Column(JSON, default={})  # Costs by provider
    
    # Content type statistics
    content_type_breakdown = Column(JSON, default={})  # Usage by content type
    content_type_performance = Column(JSON, default={})  # Performance by type
    
    # Language and cultural statistics
    language_breakdown = Column(JSON, default={})  # Usage by language
    region_breakdown = Column(JSON, default={})  # Usage by cultural region
    language_performance = Column(JSON, default={})  # Performance by language
    
    # Performance metrics
    avg_generation_time_ms = Column(Float)
    median_generation_time_ms = Column(Float)
    p95_generation_time_ms = Column(Float)
    avg_quality_score = Column(Float)
    avg_user_rating = Column(Float)
    
    # Token and cost analytics
    total_tokens_used = Column(Integer, default=0)
    avg_tokens_per_generation = Column(Float)
    total_cost_usd = Column(Float, default=0.0)
    avg_cost_per_generation = Column(Float)
    cost_efficiency_score = Column(Float)  # Quality per dollar
    
    # Business metrics
    unique_products_analyzed = Column(Integer, default=0)
    total_reviews_processed = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    total_conversion_value = Column(Float, default=0.0)
    revenue_per_generation = Column(Float, default=0.0)
    
    # User engagement
    unique_users = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    avg_generations_per_user = Column(Float)
    user_retention_rate = Column(Float, default=0.0)
    
    # Quality and content analysis
    content_flagged_count = Column(Integer, default=0)
    content_flagged_rate = Column(Float, default=0.0)
    avg_uniqueness_score = Column(Float)
    avg_relevance_score = Column(Float)
    avg_coherence_score = Column(Float)
    
    # System performance
    system_uptime_percentage = Column(Float, default=100.0)
    avg_system_response_time = Column(Float)
    error_rate_by_type = Column(JSON, default={})
    capacity_utilization = Column(Float, default=0.0)
    
    # Trends and insights
    trend_analysis = Column(JSON, default={})  # Trend calculations
    performance_insights = Column(JSON, default=[])  # AI-generated insights
    anomalies_detected = Column(JSON, default=[])  # Statistical anomalies
    optimization_opportunities = Column(JSON, default=[])  # Improvement suggestions
    
    # Comparative analysis
    period_over_period_change = Column(JSON, default={})  # Change vs previous period
    year_over_year_change = Column(JSON, default={})  # Change vs same period last year
    benchmark_comparison = Column(JSON, default={})  # Comparison to benchmarks
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_stats_date_period', 'date', 'period_type'),
        Index('ix_stats_performance', 'success_rate', 'avg_quality_score'),
        UniqueConstraint('date', 'period_type', name='uq_stats_date_period'),
    ) 