"""
Pydantic schemas for AI prompt management and content generation.
Enhanced with cultural adaptations, A/B testing, and enterprise features.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator


# ================== BASE PROMPT TEMPLATE SCHEMAS ==================

class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates."""
    template_type: str = Field(..., description="Type of content (product_description, faq, comparison)")
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    system_prompt: Optional[str] = Field(None, description="System prompt for AI")
    user_prompt_template: str = Field(..., description="User prompt template with variables")
    default_temperature: float = Field(0.7, ge=0.0, le=2.0, description="Default temperature")
    default_max_tokens: int = Field(1500, ge=100, le=4000, description="Default max tokens")
    supported_providers: List[str] = Field(default=["deepseek", "openai"], description="Supported AI providers")
    required_variables: List[str] = Field(default=[], description="Required template variables")
    optional_variables: List[str] = Field(default=[], description="Optional template variables")
    example_output: Optional[str] = Field(None, description="Example output")
    is_active: bool = Field(True, description="Is template active")
    is_default: bool = Field(False, description="Is default template for type")


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template."""
    
    # Enhanced properties
    category: Optional[str] = Field(None, description="Template category")
    primary_language: str = Field("en", description="Primary language (ISO 639-1)")
    supported_languages: List[str] = Field(default=["en"], description="Supported languages")
    cultural_regions: List[str] = Field(default=["north_america"], description="Supported cultural regions")
    
    # Targeting and style
    target_audience: Optional[str] = Field(None, description="Target audience")
    tone: str = Field("professional", description="Content tone")
    urgency_level: str = Field("medium", description="Urgency level")
    product_categories: List[str] = Field(default=[], description="Suitable product categories")
    
    # Quality guidelines
    content_guidelines: Dict[str, Any] = Field(default={}, description="Content quality guidelines")
    output_format: str = Field("text", description="Output format")
    max_output_length: Optional[int] = Field(None, description="Maximum output length")
    min_output_length: Optional[int] = Field(None, description="Minimum output length")
    
    # Advanced settings
    is_experimental: bool = Field(False, description="Is experimental template")
    tags: List[str] = Field(default=[], description="Template tags")
    
    @validator('template_type')
    def validate_template_type(cls, v):
        """Validate template type."""
        allowed_types = [
            'product_description', 'faq', 'comparison', 'product_features', 
            'email_campaign', 'facebook_ad', 'google_ad', 'instagram_caption',
            'blog_article', 'newsletter', 'product_summary', 'marketing_copy'
        ]
        if v not in allowed_types:
            raise ValueError(f'Template type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('supported_providers')
    def validate_providers(cls, v):
        """Validate supported providers."""
        allowed_providers = ['openai', 'deepseek']
        for provider in v:
            if provider not in allowed_providers:
                raise ValueError(f'Provider {provider} not supported. Allowed: {", ".join(allowed_providers)}')
        return v


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    supported_providers: Optional[List[str]] = None
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    example_output: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_experimental: Optional[bool] = None
    tone: Optional[str] = None
    urgency_level: Optional[str] = None
    target_audience: Optional[str] = None
    tags: Optional[List[str]] = None


class PromptTemplateInDB(PromptTemplateBase):
    """Schema for prompt template in database."""
    id: int
    version: str
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class PromptTemplateResponse(PromptTemplateInDB):
    """Schema for prompt template API response."""
    # Enhanced response properties
    primary_language: Optional[str] = None
    supported_languages: Optional[List[str]] = None
    cultural_regions: Optional[List[str]] = None
    average_user_rating: Optional[float] = None
    content_quality_score: Optional[float] = None
    conversion_rate: Optional[float] = None
    is_experimental: Optional[bool] = None


# ================== CULTURAL ADAPTATION SCHEMAS ==================

class CulturalAdaptationBase(BaseModel):
    """Base schema for cultural adaptations."""
    template_id: int = Field(..., description="Template ID")
    language_code: str = Field(..., description="Language code (ISO 639-1)")
    cultural_region: str = Field(..., description="Cultural region")
    country_code: Optional[str] = Field(None, description="Country code (ISO 3166-1)")
    
    # Adaptation content
    adapted_prompt: str = Field(..., description="Culturally adapted prompt")
    cultural_modifications: Dict[str, Any] = Field(default={}, description="Cultural modifications")
    linguistic_adaptations: Dict[str, Any] = Field(default={}, description="Linguistic adaptations")
    
    # Metadata
    confidence_score: float = Field(0.8, ge=0.0, le=1.0, description="Adaptation confidence")
    is_active: bool = Field(True, description="Is adaptation active")


class CulturalAdaptationCreate(CulturalAdaptationBase):
    """Schema for creating a cultural adaptation."""
    
    # Additional creation properties
    adaptation_notes: Optional[str] = Field(None, description="Adaptation notes")
    cultural_context: Dict[str, Any] = Field(default={}, description="Cultural context information")
    
    @validator('language_code')
    def validate_language_code(cls, v):
        """Validate ISO 639-1 language code."""
        valid_codes = ['en', 'he', 'es', 'fr', 'de', 'ar', 'ja', 'ko', 'zh']
        if v not in valid_codes:
            raise ValueError(f'Language code must be one of: {", ".join(valid_codes)}')
        return v
    
    @validator('cultural_region')
    def validate_cultural_region(cls, v):
        """Validate cultural region."""
        valid_regions = ['north_america', 'europe', 'middle_east', 'asia_pacific', 'latin_america', 'africa']
        if v not in valid_regions:
            raise ValueError(f'Cultural region must be one of: {", ".join(valid_regions)}')
        return v


class CulturalAdaptationUpdate(BaseModel):
    """Schema for updating a cultural adaptation."""
    adapted_prompt: Optional[str] = None
    cultural_modifications: Optional[Dict[str, Any]] = None
    linguistic_adaptations: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    adaptation_notes: Optional[str] = None


class CulturalAdaptationResponse(CulturalAdaptationBase):
    """Schema for cultural adaptation API response."""
    id: int
    usage_count: int = Field(default=0, description="Number of times used")
    success_rate: float = Field(default=0.0, description="Success rate")
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


# ================== A/B TEST EXPERIMENT SCHEMAS ==================

class ABTestExperimentBase(BaseModel):
    """Base schema for A/B test experiments."""
    name: str = Field(..., min_length=3, max_length=200, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    
    # Test configuration
    control_template_id: int = Field(..., description="Control template ID")
    variant_template_ids: List[int] = Field(..., description="Variant template IDs")
    traffic_allocation: Dict[str, float] = Field(..., description="Traffic allocation percentages")
    
    # Success metrics
    primary_metric: str = Field(..., description="Primary success metric")
    secondary_metrics: List[str] = Field(default=[], description="Secondary metrics")
    minimum_sample_size: int = Field(100, description="Minimum sample size per variant")
    
    # Duration
    start_date: datetime = Field(..., description="Experiment start date")
    end_date: datetime = Field(..., description="Experiment end date")
    
    # Configuration
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Statistical confidence level")
    is_active: bool = Field(True, description="Is experiment active")


class ABTestExperimentCreate(ABTestExperimentBase):
    """Schema for creating an A/B test experiment."""
    
    # Additional creation properties
    experiment_type: str = Field("performance", description="Type of experiment")
    target_language: Optional[str] = Field(None, description="Target language for experiment")
    target_region: Optional[str] = Field(None, description="Target region for experiment")
    
    @validator('traffic_allocation')
    def validate_traffic_allocation(cls, v):
        """Validate traffic allocation sums to 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError('Traffic allocation must sum to 1.0')
        return v
    
    @validator('primary_metric')
    def validate_primary_metric(cls, v):
        """Validate primary metric."""
        valid_metrics = ['success_rate', 'quality_score', 'user_rating', 'conversion_rate', 'engagement_rate']
        if v not in valid_metrics:
            raise ValueError(f'Primary metric must be one of: {", ".join(valid_metrics)}')
        return v


class ABTestExperimentUpdate(BaseModel):
    """Schema for updating an A/B test experiment."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    traffic_allocation: Optional[Dict[str, float]] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None


class ABTestExperimentResponse(ABTestExperimentBase):
    """Schema for A/B test experiment API response."""
    id: int
    status: str = Field(default="draft", description="Experiment status")
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    
    # Results
    statistical_significance: Optional[float] = None
    winner_template_id: Optional[int] = None
    results_summary: Dict[str, Any] = Field(default={}, description="Experiment results")
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


# ================== PERFORMANCE METRICS SCHEMAS ==================

class TemplatePerformanceMetricBase(BaseModel):
    """Base schema for template performance metrics."""
    template_id: int = Field(..., description="Template ID")
    metric_date: date = Field(..., description="Date of the metric")
    
    # Context
    language_code: str = Field("en", description="Language code")
    cultural_region: str = Field("north_america", description="Cultural region")
    content_type: str = Field(..., description="Content type")
    
    # Core metrics
    generation_count: int = Field(0, description="Number of generations")
    success_count: int = Field(0, description="Number of successful generations")
    total_generation_time_ms: int = Field(0, description="Total generation time in ms")
    total_tokens_used: int = Field(0, description="Total tokens used")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")


class TemplatePerformanceMetricCreate(TemplatePerformanceMetricBase):
    """Schema for creating a performance metric."""
    # Quality metrics
    average_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Average quality score")
    average_user_rating: float = Field(0.0, ge=0.0, le=5.0, description="Average user rating")
    conversion_rate: float = Field(0.0, ge=0.0, le=1.0, description="Conversion rate")
    
    # Additional metrics
    unique_users: int = Field(0, description="Number of unique users")
    repeat_usage_rate: float = Field(0.0, description="Repeat usage rate")


class TemplatePerformanceMetricResponse(TemplatePerformanceMetricBase):
    """Schema for performance metric API response."""
    id: int
    
    # Calculated metrics
    success_rate: float = Field(default=0.0, description="Success rate")
    average_generation_time_ms: float = Field(default=0.0, description="Average generation time")
    average_quality_score: float = Field(default=0.0, description="Average quality score")
    average_user_rating: float = Field(default=0.0, description="Average user rating")
    cost_per_generation: float = Field(default=0.0, description="Cost per generation")
    
    # Trends
    performance_trend: Optional[str] = Field(None, description="Performance trend")
    
    created_at: datetime
    
    class Config:
        from_attributes = True


# ================== CONTENT GENERATION SCHEMAS ==================

class ContentGenerationRequest(BaseModel):
    """Enhanced content generation request."""
    product_url: str = Field(..., description="Product URL to analyze")
    template_type: str = Field(..., description="Type of content to generate")
    template_id: Optional[int] = Field(None, description="Specific template ID to use")
    
    # Language and cultural preferences
    language: str = Field("en", description="Target language")
    cultural_region: str = Field("north_america", description="Cultural region")
    
    # Generation parameters
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, ge=100, le=4000, description="Maximum tokens")
    ai_provider: str = Field("deepseek", description="AI provider to use")
    
    # Additional options
    enable_cultural_adaptation: bool = Field(True, description="Enable cultural adaptation")
    include_performance_tracking: bool = Field(True, description="Include performance tracking")
    user_id: Optional[str] = Field(None, description="User ID for analytics")


class ContentGenerationResponse(BaseModel):
    """Enhanced content generation response."""
    generated_content: str = Field(..., description="Generated content")
    template_id: int = Field(..., description="Template ID used")
    template_name: str = Field(..., description="Template name used")
    
    # Generation metadata
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    tokens_used: int = Field(0, description="Tokens consumed")
    cost_estimate: float = Field(0.0, description="Estimated cost")
    
    # Quality metrics
    quality_score: float = Field(0.0, description="Content quality score")
    cultural_appropriateness: float = Field(0.0, description="Cultural appropriateness score")
    
    # Cultural adaptation info
    cultural_adaptation_used: bool = Field(False, description="Whether cultural adaptation was used")
    adaptations_applied: Dict[str, Any] = Field(default={}, description="Adaptations applied")
    
    # Provider and metadata
    ai_provider: str = Field(..., description="AI provider used")
    language_used: str = Field(..., description="Language used")
    cultural_region_used: str = Field(..., description="Cultural region used")
    generation_timestamp: datetime = Field(..., description="Generation timestamp")


class ContentGenerationFeedback(BaseModel):
    """Schema for content generation feedback."""
    generation_id: int = Field(..., description="Generation ID")
    user_rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="Optional feedback text")
    is_useful: bool = Field(..., description="Is the content useful")
    suggestions: Optional[str] = Field(None, description="Improvement suggestions")


class ContentGenerationStats(BaseModel):
    """Schema for content generation statistics."""
    total_generations: int = Field(0, description="Total generations")
    successful_generations: int = Field(0, description="Successful generations")
    average_quality_score: float = Field(0.0, description="Average quality score")
    average_user_rating: float = Field(0.0, description="Average user rating")
    most_used_templates: List[Dict[str, Any]] = Field(default=[], description="Most used templates")
    performance_by_language: Dict[str, Any] = Field(default={}, description="Performance by language")
    cultural_adaptation_usage: Dict[str, Any] = Field(default={}, description="Cultural adaptation usage")


# ================== SYSTEM SCHEMAS ==================

class SystemStatus(BaseModel):
    """Schema for system status."""
    status: str = Field(..., description="System status")
    timestamp: float = Field(..., description="Status timestamp")
    version: str = Field(..., description="Application version")
    database_status: str = Field(..., description="Database status")
    ai_providers_status: Dict[str, str] = Field(..., description="AI providers status")
    active_templates: int = Field(0, description="Number of active templates")
    total_generations_today: int = Field(0, description="Total generations today")
    
    # Feature flags
    features: Dict[str, bool] = Field(default={
        "intelligent_prompts": True,
        "cultural_adaptations": True,
        "ab_testing": True,
        "performance_analytics": True,
        "multi_language": True
    }, description="Available features")


class TemplateTestRequest(BaseModel):
    """Schema for testing a template."""
    template_id: int = Field(..., description="Template ID to test")
    test_data: Dict[str, Any] = Field(..., description="Test data for variables")
    language: str = Field("en", description="Language for testing")
    cultural_region: str = Field("north_america", description="Cultural region for testing")


class TemplateTestResponse(BaseModel):
    """Schema for template test response."""
    success: bool = Field(..., description="Test success")
    generated_content: Optional[str] = Field(None, description="Generated test content")
    generation_time_ms: int = Field(0, description="Generation time")
    quality_score: float = Field(0.0, description="Quality score")
    errors: List[str] = Field(default=[], description="Any errors encountered")


class AIProviderStatus(BaseModel):
    """Schema for AI provider status."""
    provider_name: str = Field(..., description="Provider name")
    status: str = Field(..., description="Provider status")
    response_time_ms: Optional[int] = Field(None, description="Average response time")
    success_rate: float = Field(0.0, description="Success rate")
    last_check: datetime = Field(..., description="Last status check")
    error_message: Optional[str] = Field(None, description="Last error message if any") 