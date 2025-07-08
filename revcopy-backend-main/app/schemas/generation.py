"""Content generation schemas for marketing content creation."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.content import ContentType, ContentStatus


class ContentGenerationRequest(BaseModel):
    """Schema for content generation request."""
    product_id: Optional[int] = None
    content_type: ContentType
    style: Optional[str] = None
    focus_area: Optional[str] = None
    length: Optional[str] = None
    target_audience: Optional[str] = None
    language: str = "English"
    additional_parameters: Optional[Dict] = None
    custom_prompt: Optional[str] = Field(None, max_length=1000, description="Custom prompt or context")


class ContentGenerationResponse(BaseModel):
    """Schema for content generation response."""
    id: int
    content_type: ContentType
    title: str
    content: str
    parameters: Optional[Dict] = None
    status: ContentStatus
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    language: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    """Schema for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class CampaignResponse(BaseModel):
    """Schema for campaign response."""
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    content: List[ContentGenerationResponse] = []
    
    class Config:
        from_attributes = True


class BulkContentGeneration(BaseModel):
    """Schema for bulk content generation."""
    product_ids: List[int] = Field(..., min_items=1, max_items=20)
    content_types: List[ContentType] = Field(..., min_items=1)
    common_parameters: Optional[Dict] = None
    
    
class ContentTemplate(BaseModel):
    """Schema for content templates."""
    name: str
    content_type: ContentType
    template: str
    parameters: Dict
    is_active: bool = True 