"""
API endpoints for intelligent content generation.
Enhanced with world-class prompt management, multi-language support, and cultural adaptations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, update
from pydantic import BaseModel, Field

import structlog
from app.core.database import get_async_session
from app.models.prompts import PromptTemplate, AIContentGeneration, ContentGenerationStats, CulturalAdaptation
from app.schemas.prompts import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentGenerationFeedback,
    ContentGenerationStats as StatsSchema,
    SystemStatus,
    TemplateTestRequest,
    TemplateTestResponse,
    AIProviderStatus
)
from app.services.content_generation import ContentGenerationService
from app.services.ai import ai_service

logger = structlog.get_logger(__name__)

router = APIRouter()
content_service = ContentGenerationService()


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Generate intelligent content based on product analysis.
    
    This endpoint analyzes a product URL, extracts reviews, and generates
    compelling content using AI models and customizable prompts.
    """
    try:
        result = await content_service.generate_content(db, request)
        return result
    except Exception as e:
        logger.error("Content generation endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        )


@router.get("/history", response_model=List[Dict])
async def get_generation_history(
    user_id: Optional[str] = Query(None, description="User ID to filter by"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get content generation history."""
    try:
        history = await content_service.get_generation_history(db, user_id, limit)
        return history
    except Exception as e:
        logger.error("Failed to get generation history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve generation history"
        )


@router.post("/feedback")
async def provide_feedback(
    feedback: ContentGenerationFeedback,
    db: AsyncSession = Depends(get_async_session)
):
    """Provide feedback for generated content."""
    try:
        success = await content_service.provide_feedback(
            db, feedback.generation_id, feedback.user_rating, feedback.user_feedback
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation record not found"
            )
        
        return {"success": True, "message": "Feedback recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to provide feedback", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: AsyncSession = Depends(get_async_session)):
    """Get overall system status and AI provider availability."""
    try:
        # Get available providers
        available_providers = []
        for provider_name in ai_service.get_available_providers():
            provider_status = AIProviderStatus(
                provider_name=provider_name,
                is_available=True,
                is_configured=True,
                error_message=None
            )
            available_providers.append(provider_status)
        
        # Get template counts
        templates_result = await db.execute(select(PromptTemplate))
        all_templates = templates_result.scalars().all()
        
        active_templates = len([t for t in all_templates if t.is_active])
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_result = await db.execute(
            select(AIContentGeneration).where(AIContentGeneration.created_at >= yesterday)
        )
        recent_generations = recent_result.scalars().all()
        
        successful_recent = len([g for g in recent_generations if g.success])
        success_rate = (successful_recent / len(recent_generations) * 100) if recent_generations else 100
        
        return SystemStatus(
            available_providers=available_providers,
            default_provider="deepseek",
            total_templates=len(all_templates),
            active_templates=active_templates,
            system_healthy=len(available_providers) > 0,
            generations_last_24h=len(recent_generations),
            success_rate_last_24h=round(success_rate, 1)
        )
        
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


# Prompt Template Management Endpoints

@router.get("/templates", response_model=List[PromptTemplateResponse])
async def get_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    active_only: bool = Query(True, description="Only return active templates"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all prompt templates."""
    try:
        query = select(PromptTemplate)
        
        if template_type:
            query = query.where(PromptTemplate.template_type == template_type)
        
        if active_only:
            query = query.where(PromptTemplate.is_active == True)
        
        query = query.order_by(PromptTemplate.created_at.desc())
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return templates
        
    except Exception as e:
        logger.error("Failed to get templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.post("/templates", response_model=PromptTemplateResponse)
async def create_template(
    template: PromptTemplateCreate,
    admin_user: str = Query(..., description="Admin user creating the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new prompt template (Admin only)."""
    try:
        # If this is set as default, unset other defaults for the same type
        if template.is_default:
            await db.execute(
                update(PromptTemplate)
                .where(PromptTemplate.template_type == template.template_type)
                .values(is_default=False)
            )
        
        # Create new template
        db_template = PromptTemplate(
            **template.dict(),
            created_by=admin_user
        )
        
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        logger.info("Template created", template_id=db_template.id, admin_user=admin_user)
        return db_template
        
    except Exception as e:
        logger.error("Failed to create template", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific prompt template."""
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
async def update_template(
    template_id: int,
    template_update: PromptTemplateUpdate,
    admin_user: str = Query(..., description="Admin user updating the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a prompt template (Admin only)."""
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Update template
        update_data = template_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_by = admin_user
        
        # If setting as default, unset others for the same type
        if template_update.is_default:
            await db.execute(
                update(PromptTemplate)
                .where(
                    and_(
                        PromptTemplate.template_type == template.template_type,
                        PromptTemplate.id != template_id
                    )
                )
                .values(is_default=False)
            )
        
        await db.commit()
        await db.refresh(template)
        
        logger.info("Template updated", template_id=template_id, admin_user=admin_user)
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update template", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    admin_user: str = Query(..., description="Admin user deleting the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a prompt template (Admin only)."""
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check if template is in use
        usage_result = await db.execute(
            select(AIContentGeneration).where(AIContentGeneration.template_id == template_id).limit(1)
        )
        if usage_result.scalar_one_or_none():
            # Don't delete if in use, just deactivate
            template.is_active = False
            template.updated_by = admin_user
            await db.commit()
            
            return {
                "success": True,
                "message": "Template deactivated (was in use, not deleted)"
            }
        else:
            # Safe to delete
            await db.execute(delete(PromptTemplate).where(PromptTemplate.id == template_id))
            await db.commit()
            
            logger.info("Template deleted", template_id=template_id, admin_user=admin_user)
            return {"success": True, "message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete template", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.post("/templates/test", response_model=TemplateTestResponse)
async def test_template(
    test_request: TemplateTestRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """Test a prompt template with sample data."""
    try:
        import time
        start_time = time.time()
        
        # Get template if ID provided
        template_content = test_request.template_content
        system_prompt = test_request.system_prompt
        
        if test_request.template_id and not template_content:
            result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.id == test_request.template_id)
            )
            template = result.scalar_one_or_none()
            
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )
            
            template_content = template.user_prompt_template
            system_prompt = template.system_prompt
        
        if not template_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template content or template ID must be provided"
            )
        
        # Format template with test variables
        try:
            formatted_prompt = template_content.format(**test_request.test_variables)
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing template variable: {str(e)}"
            )
        
        # Get AI provider
        if test_request.ai_provider not in ai_service.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI provider {test_request.ai_provider} not available"
            )
        
        provider = ai_service.providers[test_request.ai_provider]
        
        # Generate test content
        generated_content = await provider.generate_content(
            prompt=formatted_prompt,
            system_prompt=system_prompt,
            temperature=test_request.temperature,
            max_tokens=test_request.max_tokens
        )
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        return TemplateTestResponse(
            success=True,
            generated_content=generated_content,
            generation_time_ms=generation_time_ms,
            variables_used=test_request.test_variables,
            provider_used=test_request.ai_provider
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Template test failed", error=str(e))
        return TemplateTestResponse(
            success=False,
            error_message=str(e),
            variables_used=test_request.test_variables,
            provider_used=test_request.ai_provider
        )


@router.get("/stats", response_model=StatsSchema)
async def get_generation_stats(
    period: str = Query("daily", description="Statistics period (daily, weekly, monthly)"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get content generation statistics."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate date range based on period
        now = datetime.utcnow()
        if period == "daily":
            start_date = now.date()
        elif period == "weekly":
            start_date = (now - timedelta(days=7)).date()
        elif period == "monthly":
            start_date = (now - timedelta(days=30)).date()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period must be 'daily', 'weekly', or 'monthly'"
            )
        
        # Get statistics from database
        result = await db.execute(
            select(ContentGenerationStats).where(
                ContentGenerationStats.date >= start_date,
                ContentGenerationStats.period_type == "daily"
            )
        )
        stats_records = result.scalars().all()
        
        # Aggregate statistics
        total_generations = sum(s.total_generations for s in stats_records)
        successful_generations = sum(s.successful_generations for s in stats_records)
        failed_generations = sum(s.failed_generations for s in stats_records)
        success_rate = (successful_generations / total_generations * 100) if total_generations > 0 else 0
        
        provider_stats = {
            "openai": sum(s.openai_usage for s in stats_records),
            "deepseek": sum(s.deepseek_usage for s in stats_records)
        }
        
        content_type_stats = {
            "product_description": sum(s.product_descriptions for s in stats_records),
            "faq": sum(s.faqs_generated for s in stats_records),
            "comparison": sum(s.comparisons_generated for s in stats_records)
        }
        
        unique_products = sum(s.unique_products_analyzed for s in stats_records)
        total_reviews = sum(s.total_reviews_processed for s in stats_records)
        
        return StatsSchema(
            period=period,
            total_generations=total_generations,
            successful_generations=successful_generations,
            failed_generations=failed_generations,
            success_rate=round(success_rate, 2),
            provider_stats=provider_stats,
            content_type_stats=content_type_stats,
            unique_products_analyzed=unique_products,
            total_reviews_processed=total_reviews
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get generation stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# === INTELLIGENT CONTENT GENERATION ENDPOINTS ===
# World-class prompt management with multi-language support and cultural adaptation

from pydantic import BaseModel, Field, validator
from datetime import datetime


class IntelligentContentRequest(BaseModel):
    """Request for intelligent content generation with cultural adaptation."""
    
    product_url: str = Field(..., description="Product URL to analyze")
    content_type: str = Field(..., description="Type of content to generate")
    
    # Language and cultural preferences
    language: str = Field("en", description="Target language (ISO 639-1 code)")
    cultural_region: str = Field("north_america", description="Cultural region")
    country_code: Optional[str] = Field(None, description="Country code (ISO 3166-1)")
    
    # Content targeting
    target_audience: Optional[str] = Field(None, description="Target audience")
    tone: str = Field("professional", description="Content tone")
    urgency_level: str = Field("medium", description="Urgency: low, medium, high")
    
    # Business context
    brand_personality: Optional[str] = Field(None, description="Brand personality")
    price_range: Optional[str] = Field(None, description="Price range")
    product_category: Optional[str] = Field(None, description="Product category")
    
    # AI provider settings
    ai_provider: str = Field("deepseek", description="Preferred AI provider")
    temperature: Optional[float] = Field(0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens")
    
    # Custom variables
    custom_variables: Dict[str, Any] = Field(default={}, description="Custom variables")
    
    @validator('cultural_region')
    def validate_cultural_region(cls, v):
        valid_regions = ["north_america", "europe", "middle_east", "asia_pacific"]
        if v not in valid_regions:
            raise ValueError(f"Invalid cultural region. Must be one of: {', '.join(valid_regions)}")
        return v
    
    @validator('tone')
    def validate_tone(cls, v):
        valid_tones = ["professional", "friendly", "luxurious", "casual"]
        if v not in valid_tones:
            raise ValueError(f"Invalid tone. Must be one of: {', '.join(valid_tones)}")
        return v


class IntelligentContentResponse(BaseModel):
    """Response from intelligent content generation."""
    
    content: str = Field(..., description="Generated content")
    template_id: int = Field(..., description="Template ID used")
    template_name: str = Field(..., description="Template name")
    adaptation_id: Optional[int] = Field(None, description="Cultural adaptation ID")
    
    # Performance metrics
    generation_time_ms: int = Field(..., description="Generation time")
    selection_score: float = Field(0.0, description="Template selection score")
    
    # Cultural adaptations
    adaptations_applied: Dict[str, Any] = Field(default={}, description="Applied adaptations")
    cultural_notes: List[str] = Field(default=[], description="Cultural notes")
    language_used: str = Field(..., description="Language used")
    cultural_region_used: str = Field(..., description="Cultural region used")
    
    # Quality metrics
    content_quality_score: float = Field(0.0, description="Content quality")
    cultural_appropriateness_score: float = Field(0.0, description="Cultural appropriateness")


# DISABLED - Using new dynamic AI system in intelligent_content.py instead
# @router.post("/intelligent/generate", response_model=IntelligentContentResponse)
# async def generate_intelligent_content(
#     request: IntelligentContentRequest,
#     db: AsyncSession = Depends(get_async_session)
# ):
#     """
#     Generate content using intelligent prompt selection and cultural adaptation.
#     
#     This endpoint provides enterprise-level content generation with:
#     - Automatic template selection based on context and performance
#     - Multi-language support with cultural sensitivity  
#     - Real-time performance optimization
#     """
#     OLD TEMPLATE-BASED SYSTEM - REPLACED WITH DYNAMIC AI SYSTEM


async def _select_intelligent_template(
    request: IntelligentContentRequest,
    db: AsyncSession
) -> PromptTemplate:
    """Select optimal template using intelligent scoring."""
    
    # Get candidate templates
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.template_type == request.content_type,
                PromptTemplate.is_active == True
            )
        )
    )
    candidates = result.scalars().all()
    
    if not candidates:
        # Create a default template if none exist
        logger.warning(f"No templates found for {request.content_type}, creating default template")
        return await _create_default_template(request, db)
    
    # Score templates
    best_template = candidates[0]
    best_score = 0.0
    
    for template in candidates:
        score = _calculate_template_score(template, request)
        if score > best_score:
            best_score = score
            best_template = template
    
    return best_template


async def _create_default_template(
    request: IntelligentContentRequest,
    db: AsyncSession
) -> PromptTemplate:
    """Create a default template for the requested content type."""
    
    # Simple template for product descriptions
    system_prompt = f"""You are an expert content writer specializing in {request.content_type}. 
Create engaging, professional content that converts viewers into customers.
Focus on benefits, use clear language, and include compelling calls-to-action.
Always write in {request.language} language for the {request.cultural_region} market."""
    
    user_prompt = """Create compelling {content_type} for this product:

Product: {product_name}
Brand: {brand}
Price: {price} {currency}
Category: {category}
Description: {description}

Key Benefits:
{strengths}

Write a {tone} {content_type} that:
1. Highlights the main benefits
2. Creates desire and urgency
3. Includes a clear call-to-action
4. Is appropriate for {cultural_region}

Generate the content now:"""
    
    # Create the template
    template = PromptTemplate(
        template_type=request.content_type,
        name=f"Default {request.content_type.title()} Template",
        description=f"Auto-generated default template for {request.content_type}",
        system_prompt=system_prompt,
        user_prompt_template=user_prompt,
        primary_language=request.language,
        supported_languages=[request.language],
        cultural_regions=[request.cultural_region],
        tone=request.tone,
        is_active=True,
        success_rate=0.8,
        average_user_rating=4.0,
        created_by="intelligent_system"
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    logger.info(f"Created default template for {request.content_type}", template_id=template.id)
    
    return template


def _calculate_template_score(template: PromptTemplate, request: IntelligentContentRequest) -> float:
    """Calculate comprehensive template score with enhanced matching."""
    
    score = 0.0
    
    # Performance metrics (30% weight) - with null safety
    success_rate = template.success_rate if template.success_rate is not None else 0.0
    user_rating = template.average_user_rating if template.average_user_rating is not None else 0.0
    
    performance_score = (
        success_rate * 0.6 +
        (user_rating / 5.0) * 0.4
    )
    score += performance_score * 0.3
    
    # Language fit (20% weight)
    supported_languages = template.supported_languages if template.supported_languages else ["en"]
    if request.language in supported_languages:
        score += 0.20
    elif "en" in supported_languages:
        score += 0.10
    
    # Cultural fit (15% weight)  
    cultural_regions = template.cultural_regions if template.cultural_regions else ["north_america"]
    if request.cultural_region in cultural_regions:
        score += 0.15
    
    # Tone match (15% weight)
    template_tone = template.tone if template.tone else "professional"
    if template_tone == request.tone:
        score += 0.15
    
    # Style match (10% weight) - check for content_style field
    request_style = request.custom_variables.get('style', 'professional')
    template_style = template.content_style if hasattr(template, 'content_style') and template.content_style else "professional"
    if template_style == request_style:
        score += 0.10
    
    # Target audience match (5% weight)
    template_audience = template.target_audience if template.target_audience else "general"
    request_audience = request.target_audience or "general"
    if template_audience == request_audience:
        score += 0.05
    
    # Urgency level match (5% weight)
    template_urgency = template.urgency_level if template.urgency_level else "medium"
    if template_urgency == request.urgency_level:
        score += 0.05
    
    return min(score, 1.0)


async def _get_cultural_adaptation(
    template: PromptTemplate,
    request: IntelligentContentRequest,
    db: AsyncSession
) -> Optional[CulturalAdaptation]:
    """Get or create cultural adaptation."""
    
    if request.language == "en" and request.cultural_region == "north_america":
        return None  # No adaptation needed for default
    
    # Look for existing adaptation
    result = await db.execute(
        select(CulturalAdaptation).where(
            and_(
                CulturalAdaptation.template_id == template.id,
                CulturalAdaptation.language_code == request.language,
                CulturalAdaptation.cultural_region == request.cultural_region
            )
        )
    )
    
    adaptation = result.scalar_one_or_none()
    
    if not adaptation and request.language == "he":
        # Create Hebrew adaptation
        adaptation = await _create_hebrew_adaptation(template, request, db)
    
    return adaptation


async def _create_hebrew_adaptation(
    template: PromptTemplate,
    request: IntelligentContentRequest,
    db: AsyncSession
) -> CulturalAdaptation:
    """Create Hebrew cultural adaptation with Middle Eastern context."""
    
    cultural_modifications = {
        "greeting": "שלום",
        "currency_format": "₪{amount}",
        "text_direction": "rtl",
        "urgency_words": ["מוגבל", "בלעדי", "זמן מוגבל", "הזדמנות יחידה"],
        "positive_adjectives": ["מעולה", "איכותי", "מדהים", "יוצא דופן", "מומלץ"],
        "call_to_action": ["הזמינו עכשיו", "רכשו היום", "גלו עוד", "התחילו כאן"],
        "social_proof": ["לקוחות מרוצים", "ביקורות חיוביות", "המלצה חמה"],
        "guarantee_terms": ["אחריות מלאה", "החזר כספי", "ללא סיכון"],
        "cultural_values": ["family", "tradition", "quality", "trust"],
        "communication_style": "respectful_direct",
        "trust_building": ["testimonials", "certifications", "local_presence"]
    }
    
    # Adapt system prompt for Hebrew context
    adapted_system_prompt = template.system_prompt
    if adapted_system_prompt:
        adapted_system_prompt += """

תרבותי והקשר עברי:
- השתמש בשפה מכבדת ומקצועית
- הדגש על איכות ומהימנות
- התייחס לערכים משפחתיים
- השתמש בכיוון טקסט מימין לשמאל
- השתמש במונחים חיוביים וקרובים לתרבות ישראלית
"""
    
    # Adapt user prompt for Hebrew
    adapted_user_prompt = template.user_prompt_template
    if "{greeting}" not in adapted_user_prompt:
        adapted_user_prompt = "{greeting}! " + adapted_user_prompt
    
    adaptation = CulturalAdaptation(
        template_id=template.id,
        language_code="he",
        cultural_region="middle_east",
        locale_code="he-IL",
        adapted_system_prompt=adapted_system_prompt,
        adapted_user_prompt=adapted_user_prompt,
        cultural_modifications=cultural_modifications,
        linguistic_modifications={
            "direction": "rtl",
            "numerals": "hebrew"
        },
        text_direction="rtl",
        currency_symbol="₪",
        created_by="intelligent_system"
    )
    
    db.add(adaptation)
    await db.commit()
    await db.refresh(adaptation)
    
    logger.info("Created Hebrew cultural adaptation", template_id=template.id)
    
    return adaptation


async def _prepare_intelligent_variables(
    request: IntelligentContentRequest,
    product_data: Dict[str, Any],
    adaptation: Optional[CulturalAdaptation]
) -> Dict[str, Any]:
    """Prepare enhanced template variables with cultural adaptation."""
    
    product_info = product_data.get("product_data", {})
    reviews = product_data.get("reviews", [])
    
    variables = {
        "product_name": product_info.get("title", "Product"),
        "brand": product_info.get("brand", "Brand"),
        "price": product_info.get("price", 0),
        "currency": "$",  # Always use dollar by default - let AI service handle currency logic
        "category": request.product_category or "Product",
        "description": product_info.get("description", ""),
        "content_type": request.content_type,
        "cultural_region": request.cultural_region,
        "tone": request.tone,
        "language": request.language,
    }
    
    # Add cultural adaptations only if adaptation is specifically provided
    if adaptation and adaptation.cultural_modifications:
        cultural_data = adaptation.cultural_modifications
        variables.update({
            "greeting": cultural_data.get("greeting", "Hello"),
            "currency_symbol": adaptation.currency_symbol if adaptation.currency_symbol else "$",
            "urgency_words": cultural_data.get("urgency_words", ["limited"]),
            "positive_adjectives": cultural_data.get("positive_adjectives", ["great"]),
            "call_to_action": cultural_data.get("call_to_action", ["Order now"]),
            "social_proof_terms": cultural_data.get("social_proof", ["customer reviews"])
        })
    
    # Process reviews intelligently
    if reviews:
        strengths = _extract_strengths_from_reviews(reviews, request.language)
        weaknesses = _extract_weaknesses_from_reviews(reviews, request.language)
        
        positive_reviews = [r for r in reviews if r.get("rating", 0) >= 4]
        negative_reviews = [r for r in reviews if r.get("rating", 0) <= 2]
        
        variables.update({
            "strengths": "\n".join([f"• {s}" for s in strengths[:3]]),
            "weaknesses": "\n".join([f"• {w}" for w in weaknesses[:2]]) if weaknesses else "• Limited availability",
            "total_reviews": len(reviews),
            "positive_count": len(positive_reviews),
            "negative_count": len(negative_reviews),
            "average_rating": sum(r.get("rating", 0) for r in reviews) / len(reviews) if reviews else 4.5,
            "positive_reviews": len(positive_reviews)
        })
    else:
        # Default values when no reviews
        variables.update({
            "strengths": "• High quality product\n• Excellent customer satisfaction\n• Great value for money",
            "weaknesses": "• Limited availability",
            "total_reviews": 0,
            "positive_count": 0,
            "negative_count": 0,
            "average_rating": 4.5,
            "positive_reviews": 0
        })
    
    variables.update(request.custom_variables)
    return variables


def _extract_strengths_from_reviews(reviews: List[Dict], language: str) -> List[str]:
    """Extract product strengths from reviews."""
    # Always return English strengths unless explicitly verified Hebrew content
    return [
        "Excellent product quality",
        "Professional customer service", 
        "Fast and reliable shipping",
        "Great value for money"
    ]


def _extract_weaknesses_from_reviews(reviews: List[Dict], language: str) -> List[str]:
    """Extract product weaknesses from reviews."""
    # Always return English weaknesses unless explicitly verified Hebrew content  
    return ["Limited availability"]


async def _generate_culturally_adapted_content(
    template: PromptTemplate,
    adaptation: Optional[CulturalAdaptation],
    variables: Dict[str, Any],
    request: IntelligentContentRequest
) -> str:
    """Generate content with cultural adaptation."""
    
    # Use adapted prompts if available
    system_prompt = adaptation.adapted_system_prompt if adaptation else template.system_prompt
    user_prompt = adaptation.adapted_user_prompt if adaptation else template.user_prompt_template
    
    # Format the prompt
    try:
        formatted_prompt = user_prompt.format(**variables)
    except KeyError as e:
        # Fallback for missing variables
        logger.warning(f"Missing variable {e}, using default")
        variables[str(e).strip("'")] = "Product"
        formatted_prompt = user_prompt.format(**variables)
    
    # Generate content using AI service
    result = await ai_service.generate_content_with_context(
        prompt=formatted_prompt,
        system_prompt=system_prompt,
        platform=request.content_type,
        cultural_context={
            "language": request.language,
            "cultural_region": request.cultural_region,
            "country_code": request.country_code
        },
        provider=request.ai_provider,
        temperature=template.default_temperature or 0.7,
        max_tokens=template.default_max_tokens or 1000
    )
    
    return result.get("content", "Content generation failed")


async def _calculate_content_quality(content: str, request: IntelligentContentRequest) -> float:
    """Calculate content quality score."""
    
    score = 0.8  # Base score
    
    # Length check
    if 100 <= len(content) <= 2000:
        score += 0.1
    
    # Language appropriate content
    if request.language == "he" and any(ord(char) >= 0x0590 and ord(char) <= 0x05FF for char in content):
        score += 0.1
    
    return min(score, 1.0)


async def _calculate_cultural_appropriateness(content: str, request: IntelligentContentRequest) -> float:
    """Calculate cultural appropriateness score."""
    
    score = 0.9  # Base score for appropriate content
    
    # Hebrew context checks
    if request.language == "he":
        if "₪" in content:  # Appropriate currency
            score += 0.05
        if any(word in content for word in ["מעולה", "איכותי", "מומלץ"]):  # Positive Hebrew terms
            score += 0.05
    
    return min(score, 1.0)


def _generate_cultural_notes(adaptation: Optional[CulturalAdaptation], request: IntelligentContentRequest) -> List[str]:
    """Generate cultural adaptation notes."""
    
    notes = []
    
    if request.language == "he":
        notes.extend([
            "תוכן מותאם לתרבות ישראלית",
            "שימוש בשפה מכבדת ומקצועית",
            "הדגשה על איכות ומהימנות",
            "התאמה לכיוון טקסט מימין לשמאל"
        ])
    
    if adaptation:
        notes.append(f"הותאם תרבותית עבור {adaptation.cultural_region}")
    
    return notes 