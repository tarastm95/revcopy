"""
Core configuration settings for RevCopy application.
Manages environment variables and application settings.
"""

import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, validator, Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    PROJECT_NAME: str = Field(default="RevCopy API")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = Field(default="AI-powered content generation platform")
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480)  # 8 hours for development
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = Field(default="HS256")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="revcopy")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Build database URL from components."""
        if isinstance(v, str):
            return v
        
        # Build database URL manually for compatibility
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "")
        
        if user and password and host:
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        return None
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour default
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Web Scraping
    SCRAPING_TIMEOUT: int = 30
    SCRAPING_MAX_RETRIES: int = 3
    SCRAPING_DELAY: float = 1.0
    USER_AGENT_ROTATION: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Monitoring
    SENTRY_DSN: Optional[HttpUrl] = None
    LOG_LEVEL: str = Field(default="INFO")
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = Field(default=False)
    
    # Email (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Testing
    TEST_DATABASE_URL: Optional[str] = None
    
    # DeepSeek API
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None)
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat")  # or deepseek-coder for code generation
    DEEPSEEK_MAX_TOKENS: int = Field(default=4000)
    DEEPSEEK_TEMPERATURE: float = Field(default=0.7)
    DEEPSEEK_TIMEOUT: int = Field(default=60)
    
    # AI provider preferences
    DEFAULT_AI_PROVIDER: str = Field(default="deepseek")
    AI_GENERATION_TIMEOUT: int = Field(default=60)  # seconds
    AI_MAX_TOKENS: int = Field(default=2000)
    AI_TEMPERATURE: float = Field(default=0.7)
    
    # Platform-specific content generation settings
    PLATFORM_LIMITS: Dict[str, Dict[str, Any]] = Field(default={
        "facebook_ad": {
            "max_characters": 125,
            "recommended_characters": 90,
            "max_headline_length": 25,
            "call_to_action_required": True,
            "emojis_allowed": True,
            "hashtags_recommended": 2
        },
        "google_ad": {
            "max_headline_length": 30,
            "max_description_length": 90,
            "max_headlines": 15,
            "max_descriptions": 4,
            "call_to_action_required": True,
            "emojis_allowed": False,
            "keyword_density_target": 0.02
        },
        "instagram_caption": {
            "max_characters": 2200,
            "recommended_characters": 300,
            "hashtags_recommended": 11,
            "emojis_encouraged": True,
            "story_telling_preferred": True
        },
        "email_campaign": {
            "max_subject_length": 50,
            "max_preview_text": 90,
            "personalization_required": True,
            "clear_cta_required": True,
            "mobile_optimized": True
        },
        "linkedin_post": {
            "max_characters": 3000,
            "recommended_characters": 150,
            "professional_tone_required": True,
            "hashtags_recommended": 3,
            "industry_keywords_preferred": True
        },
        "twitter_post": {
            "max_characters": 280,
            "hashtags_recommended": 2,
            "emojis_allowed": True,
            "trending_topics_encouraged": True,
            "thread_support": True
        },
        "product_description": {
            "max_characters": 2000,
            "recommended_characters": 500,
            "bullet_points_preferred": True,
            "benefits_over_features": True,
            "seo_optimized": True
        }
    })
    
    # Cultural adaptation settings
    CULTURAL_REGIONS: Dict[str, Dict[str, Any]] = Field(default={
        "north_america": {
            "languages": ["en", "es", "fr"],
            "currency_symbols": ["$", "CAD$"],
            "date_format": "MM/DD/YYYY",
            "communication_style": "direct",
            "cultural_values": ["individualism", "efficiency", "innovation"]
        },
        "middle_east": {
            "languages": ["he", "ar"],
            "currency_symbols": ["₪", "د.إ", "ر.س"],
            "date_format": "DD/MM/YYYY",
            "communication_style": "respectful",
            "cultural_values": ["family", "tradition", "honor", "trust"],
            "text_direction": "rtl",
            "formal_language_preferred": True
        },
        "europe": {
            "languages": ["en", "de", "fr", "es", "it"],
            "currency_symbols": ["€", "£"],
            "date_format": "DD/MM/YYYY",
            "communication_style": "formal_polite",
            "cultural_values": ["quality", "tradition", "sustainability"]
        },
        "asia_pacific": {
            "languages": ["en", "zh", "ja", "ko"],
            "currency_symbols": ["¥", "₹", "₩"],
            "date_format": "YYYY/MM/DD",
            "communication_style": "hierarchical_respectful",
            "cultural_values": ["respect", "harmony", "quality", "innovation"]
        }
    })
    
    # Content generation settings
    ENABLE_CONTENT_CACHING: bool = Field(default=True)
    CONTENT_CACHE_TTL: int = Field(default=3600)  # 1 hour in seconds
    MAX_REVIEWS_FOR_ANALYSIS: int = Field(default=100)
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)  # seconds
    
    # External APIs
    SHOPIFY_REQUEST_TIMEOUT: int = Field(default=30)
    MAX_CONCURRENT_REQUESTS: int = Field(default=10)
    
    # Amazon Crawler Service (Go microservice)
    AMAZON_CRAWLER_URL: str = Field(default="http://localhost:8080")
    AMAZON_CRAWLER_TIMEOUT: int = Field(default=30)
    AMAZON_CRAWLER_USERNAME: str = Field(default="crawler")
    AMAZON_CRAWLER_PASSWORD: str = Field(default="crawler123")
    
    # Logging
    LOG_FORMAT: str = Field(default="json")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=[
        "http://localhost:3000",
        "http://localhost:3001",  # Admin panel
        "http://localhost:3002",  # Admin panel
        "http://localhost:3003",  # Admin panel
        "http://localhost:3004",  # Admin panel
        "http://localhost:3005",  # Admin panel
        "http://localhost:5173",  # Frontend dev
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",  # Admin panel
        "http://127.0.0.1:3002",  # Admin panel
        "http://127.0.0.1:3003",  # Admin panel
        "http://127.0.0.1:3004",  # Admin panel
        "http://127.0.0.1:3005",  # Admin panel
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175"
    ])
    ALLOWED_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    ALLOWED_HEADERS: List[str] = Field(default=["*"])
    
    # Feature flags
    ENABLE_MOCK_DATA: bool = Field(default=True)
    ENABLE_AI_GENERATION: bool = Field(default=True)
    ENABLE_REVIEW_ANALYSIS: bool = Field(default=True)
    ENABLE_ADMIN_PANEL: bool = Field(default=True)
    
    class Config:
        """Pydantic configuration."""
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 