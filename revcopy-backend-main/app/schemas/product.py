"""
Product schemas for product management and analysis.
Includes validation for URLs and product data.
"""

from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, HttpUrl, Field, validator

from app.models.product import EcommercePlatform, ProductStatus


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    url: HttpUrl
    
    @validator("url")
    def validate_product_url(cls, v):
        """Validate that URL is from supported platform."""
        url_str = str(v).lower()
        
        # Supported traditional platforms
        traditional_domains = [
            "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
            "ebay.com", "ebay.co.uk", "ebay.de",
            "aliexpress.com", "aliexpress.us"
        ]
        
        # Shopify platforms (known and pattern-based)
        shopify_domains = ["myshopify.com", "shopify.com"]
        shopify_patterns = ["/products/"]
        
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.replace("www.", "")
        path = parsed_url.path
        
        # Check traditional platforms
        is_traditional = any(supported in domain for supported in traditional_domains)
        
        # Check Shopify platforms
        is_shopify = (
            any(shopify_domain in domain for shopify_domain in shopify_domains) or
            any(pattern in path for pattern in shopify_patterns)
        )
        
        if not (is_traditional or is_shopify):
            raise ValueError(
                "Unsupported platform. Supported platforms: Amazon, eBay, AliExpress, Shopify stores"
            )
        
        # Validate specific platform URL patterns
        if is_traditional:
            if "amazon" in domain and "/dp/" not in url_str and "/gp/product/" not in url_str:
                raise ValueError("Invalid Amazon product URL")
            if "ebay" in domain and "/itm/" not in url_str:
                raise ValueError("Invalid eBay product URL")
            if "aliexpress" in domain and "/item/" not in url_str:
                raise ValueError("Invalid AliExpress product URL")
        
        if is_shopify and "/products/" not in path:
            raise ValueError("Invalid Shopify product URL - must contain /products/")
            
        return v


class ProductAnalyzeRequest(BaseModel):
    """Schema for product analysis request."""
    url: HttpUrl
    analysis_depth: str = Field("full", pattern="^(quick|standard|full)$")
    include_images: bool = True
    max_reviews: int = Field(200, ge=50, le=1000)
    
    @validator("url")
    def validate_product_url(cls, v):
        """Validate product URL format."""
        # Use the same validation logic as ProductCreate
        url_str = str(v).lower()
        
        # Supported traditional platforms
        traditional_domains = [
            "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
            "ebay.com", "ebay.co.uk", "ebay.de",
            "aliexpress.com", "aliexpress.us"
        ]
        
        # Shopify platforms (known and pattern-based)
        shopify_domains = ["myshopify.com", "shopify.com"]
        shopify_patterns = ["/products/"]
        
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.replace("www.", "")
        path = parsed_url.path
        
        # Check traditional platforms
        is_traditional = any(supported in domain for supported in traditional_domains)
        
        # Check Shopify platforms
        is_shopify = (
            any(shopify_domain in domain for shopify_domain in shopify_domains) or
            any(pattern in path for pattern in shopify_patterns)
        )
        
        if not (is_traditional or is_shopify):
            raise ValueError(
                "Unsupported platform. Supported platforms: Amazon, eBay, AliExpress, Shopify stores"
            )
        
        # Validate specific platform URL patterns
        if is_traditional:
            if "amazon" in domain and "/dp/" not in url_str and "/gp/product/" not in url_str:
                raise ValueError("Invalid Amazon product URL")
            if "ebay" in domain and "/itm/" not in url_str:
                raise ValueError("Invalid eBay product URL")
            if "aliexpress" in domain and "/item/" not in url_str:
                raise ValueError("Invalid AliExpress product URL")
        
        if is_shopify and "/products/" not in path:
            raise ValueError("Invalid Shopify product URL - must contain /products/")
            
        return v


class ProductAnalysisRequest(BaseModel):
    """Schema for comprehensive product analysis and content generation request."""
    url: HttpUrl
    content_types: List[str] = Field(
        default=["product_description", "product_summary", "marketing_copy", "faq_generator"],
        description="List of content types to generate"
    )
    ai_provider: Optional[str] = Field(None, description="Preferred AI provider (openai, deepseek, mock)")
    analysis_depth: str = Field("full", pattern="^(quick|standard|full)$")
    max_reviews: int = Field(200, ge=50, le=1000)
    
    @validator("url")
    def validate_product_url(cls, v):
        """Validate product URL format."""
        # Use the same validation logic as ProductAnalyzeRequest
        url_str = str(v).lower()
        
        # Supported traditional platforms
        traditional_domains = [
            "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
            "ebay.com", "ebay.co.uk", "ebay.de",
            "aliexpress.com", "aliexpress.us"
        ]
        
        # Shopify platforms (known and pattern-based)
        shopify_domains = ["myshopify.com", "shopify.com"]
        shopify_patterns = ["/products/"]
        
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.replace("www.", "")
        path = parsed_url.path
        
        # Check traditional platforms
        is_traditional = any(supported in domain for supported in traditional_domains)
        
        # Check Shopify platforms
        is_shopify = (
            any(shopify_domain in domain for shopify_domain in shopify_domains) or
            any(pattern in path for pattern in shopify_patterns)
        )
        
        if not (is_traditional or is_shopify):
            raise ValueError(
                "Unsupported platform. Supported platforms: Amazon, eBay, AliExpress, Shopify stores"
            )
        
        # Validate specific platform URL patterns
        if is_traditional:
            if "amazon" in domain and "/dp/" not in url_str and "/gp/product/" not in url_str:
                raise ValueError("Invalid Amazon product URL")
            if "ebay" in domain and "/itm/" not in url_str:
                raise ValueError("Invalid eBay product URL")
            if "aliexpress" in domain and "/item/" not in url_str:
                raise ValueError("Invalid AliExpress product URL")
        
        if is_shopify and "/products/" not in path:
            raise ValueError("Invalid Shopify product URL - must contain /products/")
            
        return v


class ProductUpdate(ProductBase):
    """Schema for updating product information."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    
    @validator("price")
    def validate_price(cls, v):
        """Validate price is positive."""
        if v is not None and v < 0:
            raise ValueError("Price must be non-negative")
        return v


class ProductImageResponse(BaseModel):
    """Schema for product image response."""
    id: int
    url: str
    image_type: str
    alt_text: Optional[str] = None
    position: int
    width: Optional[int] = None
    height: Optional[int] = None
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Schema for individual review response."""
    id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    content: str
    author: str
    date: str
    verified_purchase: bool = False
    helpful_count: int = 0
    source: str
    page: Optional[int] = None
    
    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    """Schema for product response data."""
    id: int
    user_id: int
    url: str
    platform: EcommercePlatform
    external_product_id: Optional[str] = None
    status: ProductStatus
    rating: Optional[float] = None
    review_count: int = 0
    rating_distribution: Optional[Dict] = None
    in_stock: bool = True
    images: List[ProductImageResponse] = []
    reviews: List[ReviewResponse] = []
    analysis_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
        
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
        return self.review_count >= 50 and self.rating is not None and self.rating >= 4.0


class ProductListResponse(BaseModel):
    """Schema for paginated product list."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductSearchRequest(BaseModel):
    """Schema for product search request."""
    query: Optional[str] = None
    platform: Optional[EcommercePlatform] = None
    status: Optional[ProductStatus] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    min_reviews: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|rating|review_count|title)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class ProductStatsResponse(BaseModel):
    """Schema for product statistics."""
    total_products: int
    processed_products: int
    failed_products: int
    avg_rating: Optional[float] = None
    avg_review_count: Optional[float] = None
    platform_distribution: Dict[str, int]
    status_distribution: Dict[str, int]


class ProductValidationResponse(BaseModel):
    """Schema for product URL validation response."""
    is_valid: bool
    platform: Optional[EcommercePlatform] = None
    reason: Optional[str] = None
    estimated_reviews: Optional[int] = None
    estimated_rating: Optional[float] = None


class ProductRecommendation(BaseModel):
    """Schema for product recommendation based on analysis."""
    title: str
    reason: str
    impact: str = Field(..., pattern="^(low|medium|high)$")
    category: str
    priority: int = Field(..., ge=1, le=5)


class ProductInsights(BaseModel):
    """Schema for product insights summary."""
    product_id: int
    overall_sentiment: Optional[str] = None
    key_strengths: List[str] = []
    key_weaknesses: List[str] = []
    target_audience: List[str] = []
    content_opportunities: List[str] = []
    recommendations: List[ProductRecommendation] = []
    competitor_analysis: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class BulkProductImport(BaseModel):
    """Schema for bulk product import."""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50)
    analysis_depth: str = Field("standard", pattern="^(quick|standard|full)$")
    
    @validator("urls")
    def validate_urls(cls, v):
        """Validate all URLs are from supported platforms."""
        for url in v:
            ProductCreate.validate_product_url(url)
        return v


class BulkImportResponse(BaseModel):
    """Schema for bulk import response."""
    task_id: str
    total_urls: int
    status: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class ProductExport(BaseModel):
    """Schema for product data export."""
    format: str = Field("json", pattern="^(json|csv|xlsx)$")
    include_analysis: bool = True
    include_images: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    products: Optional[List[int]] = None  # Specific product IDs 