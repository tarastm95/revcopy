"""
Comprehensive Prompt Management API

Enterprise-level CRUD operations for:
- Prompt Templates
- Cultural Adaptations  
- A/B Test Experiments
- Performance Metrics
- Template Optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, update, func, desc, asc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, validator
import structlog

from app.core.database import get_async_session
from app.models.prompts import (
    PromptTemplate, 
    CulturalAdaptation, 
    ABTestExperiment, 
    TemplatePerformanceMetric,
    AIContentGeneration
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# ================== PYDANTIC SCHEMAS ==================

class PromptTemplateCreate(BaseModel):
    """Schema for creating a prompt template."""
    template_type: str = Field(..., description="Content type (product_description, facebook_ad, etc.)")
    name: str = Field(..., min_length=3, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    
    # Multi-language support
    primary_language: str = Field("en", description="Primary language (ISO 639-1)")
    supported_languages: List[str] = Field(default=["en"], description="Supported languages")
    cultural_regions: List[str] = Field(default=["north_america"], description="Supported cultural regions")
    
    # Content
    system_prompt: Optional[str] = Field(None, description="System prompt")
    user_prompt_template: str = Field(..., description="User prompt template with variables")
    
    # Configuration
    tone: str = Field("professional", description="Content tone")
    urgency_level: str = Field("medium", description="Urgency level (called 'urgency' in frontend)")
    style: str = Field("professional", description="Content style")
    length: str = Field("medium", description="Content length preference")
    target_audience: Optional[str] = Field("general", description="Target audience (called 'audience' in frontend)")
    product_categories: List[str] = Field(default=[], description="Suitable product categories")
    
    # Generation parameters
    default_temperature: float = Field(0.7, ge=0.0, le=2.0, description="Default temperature")
    default_max_tokens: int = Field(1500, ge=100, le=4000, description="Default max tokens")
    supported_providers: List[str] = Field(default=["deepseek"], description="Supported AI providers")
    
    # Variables
    required_variables: List[str] = Field(default=[], description="Required template variables")
    optional_variables: List[str] = Field(default=[], description="Optional template variables")
    
    # Settings
    is_active: bool = Field(True, description="Is template active")
    is_default: bool = Field(False, description="Is default template for type")
    is_experimental: bool = Field(False, description="Is experimental template")


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    tone: Optional[str] = None
    urgency_level: Optional[str] = None
    style: Optional[str] = None
    length: Optional[str] = None
    target_audience: Optional[str] = None
    default_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    default_max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_experimental: Optional[bool] = None


class CulturalAdaptationCreate(BaseModel):
    """Schema for creating a cultural adaptation."""
    template_id: int = Field(..., description="Template ID to adapt")
    language_code: str = Field(..., description="Language code (ISO 639-1)")
    cultural_region: str = Field(..., description="Cultural region")
    country_code: Optional[str] = Field(None, description="Country code (ISO 3166-1)")
    
    # Adaptations
    adapted_prompt: str = Field(..., description="Culturally adapted prompt")
    cultural_modifications: Dict[str, Any] = Field(default={}, description="Cultural modifications")
    linguistic_adaptations: Dict[str, Any] = Field(default={}, description="Linguistic adaptations")
    
    # Settings
    is_active: bool = Field(True, description="Is adaptation active")
    confidence_score: float = Field(0.8, ge=0.0, le=1.0, description="Adaptation confidence")


class ABTestExperimentCreate(BaseModel):
    """Schema for creating an A/B test experiment."""
    name: str = Field(..., min_length=3, max_length=200, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    
    # Test configuration
    control_template_id: int = Field(..., description="Control template ID")
    variant_template_ids: List[int] = Field(..., description="Variant template IDs")
    traffic_allocation: Dict[str, float] = Field(..., description="Traffic allocation percentages")
    
    # Target metrics
    primary_metric: str = Field(..., description="Primary success metric")
    secondary_metrics: List[str] = Field(default=[], description="Secondary metrics")
    minimum_sample_size: int = Field(100, description="Minimum sample size per variant")
    
    # Duration
    start_date: datetime = Field(..., description="Experiment start date")
    end_date: datetime = Field(..., description="Experiment end date")
    
    # Configuration
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Statistical confidence level")
    is_active: bool = Field(True, description="Is experiment active")


class PerformanceMetricCreate(BaseModel):
    """Schema for creating a performance metric."""
    template_id: int = Field(..., description="Template ID")
    
    # Context
    language_code: str = Field("en", description="Language code")
    cultural_region: str = Field("north_america", description="Cultural region")
    content_type: str = Field(..., description="Content type")
    
    # Metrics
    generation_count: int = Field(0, description="Number of generations")
    success_count: int = Field(0, description="Number of successful generations")
    total_generation_time_ms: int = Field(0, description="Total generation time in ms")
    total_tokens_used: int = Field(0, description="Total tokens used")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")
    
    # Quality metrics
    average_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Average quality score")
    average_user_rating: float = Field(0.0, ge=0.0, le=5.0, description="Average user rating")
    conversion_rate: float = Field(0.0, ge=0.0, le=1.0, description="Conversion rate")


class TemplateResponse(BaseModel):
    """Response schema for template."""
    id: int
    template_type: str
    name: str
    description: Optional[str]
    category: Optional[str]
    primary_language: str
    tone: str
    urgency_level: str
    content_style: str
    content_length: str
    target_audience: Optional[str]
    default_temperature: float
    default_max_tokens: int
    is_active: bool
    is_default: bool
    usage_count: int
    success_rate: float
    average_user_rating: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CulturalAdaptationResponse(BaseModel):
    """Response schema for cultural adaptation."""
    id: int
    template_id: int
    language_code: str
    cultural_region: str
    country_code: Optional[str]
    is_active: bool
    confidence_score: float
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ABTestExperimentResponse(BaseModel):
    """Response schema for A/B test experiment."""
    id: int
    name: str
    description: Optional[str]
    status: str
    primary_metric: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    statistical_significance: Optional[float]
    winner_template_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ================== PROMPT TEMPLATE ENDPOINTS ==================

@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    active_only: bool = Query(True, description="Only return active templates"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all prompt templates with filtering and pagination."""
    try:
        query = select(PromptTemplate)
        
        if template_type:
            query = query.where(PromptTemplate.template_type == template_type)
            
        if language:
            query = query.where(PromptTemplate.primary_language == language)
            
        if active_only:
            query = query.where(PromptTemplate.is_active == True)
        
        query = query.order_by(desc(PromptTemplate.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        logger.info("Retrieved templates", count=len(templates), filters={"type": template_type, "language": language})
        return templates
        
    except Exception as e:
        logger.error("Failed to get templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


def map_frontend_to_db_fields(data: dict) -> dict:
    """Map frontend field names to database field names."""
    field_mapping = {
        'urgency': 'urgency_level',
        'audience': 'target_audience', 
        'style': 'content_style',
        'length': 'content_length',
        'language': 'primary_language',
        'maxTokens': 'default_max_tokens',
        'temperature': 'default_temperature'
    }
    
    mapped_data = {}
    for key, value in data.items():
        # Map field names if needed
        db_key = field_mapping.get(key, key)
        mapped_data[db_key] = value
    
    return mapped_data


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    template: PromptTemplateCreate,
    admin_user: str = Query(..., description="Admin user creating the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new prompt template."""
    try:
        # If this is set as default, unset other defaults for the same type
        if template.is_default:
            await db.execute(
                update(PromptTemplate)
                .where(PromptTemplate.template_type == template.template_type)
                .values(is_default=False)
            )
        
        # Map frontend field names to database field names
        template_data = map_frontend_to_db_fields(template.dict())
        
        # Create new template
        db_template = PromptTemplate(
            **template_data,
            created_by=admin_user,
            updated_by=admin_user
        )
        
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        logger.info("Template created", template_id=db_template.id, name=template.name, admin_user=admin_user)
        return db_template
        
    except Exception as e:
        logger.error("Failed to create template", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=TemplateResponse)
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
        logger.error("Failed to get template", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: PromptTemplateUpdate,
    admin_user: str = Query(..., description="Admin user updating the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a prompt template."""
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
        
        # Map frontend field names to database field names
        mapped_update_data = map_frontend_to_db_fields(update_data)
        
        for field, value in mapped_update_data.items():
            setattr(template, field, value)
        
        template.updated_by = admin_user
        template.updated_at = datetime.utcnow()
        
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
        logger.error("Failed to update template", template_id=template_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    force: bool = Query(False, description="Force delete even if in use"),
    admin_user: str = Query(..., description="Admin user deleting the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a prompt template."""
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
        if not force:
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
                    "message": "Template deactivated (was in use, not deleted)",
                    "action": "deactivated"
                }
        
        # Safe to delete or forced delete
        await db.execute(delete(PromptTemplate).where(PromptTemplate.id == template_id))
        await db.commit()
        
        logger.info("Template deleted", template_id=template_id, admin_user=admin_user, forced=force)
        return {
            "success": True,
            "message": "Template deleted successfully",
            "action": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete template", template_id=template_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


# ================== CULTURAL ADAPTATION ENDPOINTS ==================

@router.get("/cultural-adaptations", response_model=List[CulturalAdaptationResponse])
async def get_cultural_adaptations(
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    language: Optional[str] = Query(None, description="Filter by language"),
    cultural_region: Optional[str] = Query(None, description="Filter by cultural region"),
    active_only: bool = Query(True, description="Only return active adaptations"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get cultural adaptations with filtering."""
    try:
        query = select(CulturalAdaptation)
        
        if template_id:
            query = query.where(CulturalAdaptation.template_id == template_id)
            
        if language:
            query = query.where(CulturalAdaptation.language_code == language)
            
        if cultural_region:
            query = query.where(CulturalAdaptation.cultural_region == cultural_region)
            
        if active_only:
            query = query.where(CulturalAdaptation.is_active == True)
        
        query = query.order_by(desc(CulturalAdaptation.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        adaptations = result.scalars().all()
        
        logger.info("Retrieved cultural adaptations", count=len(adaptations))
        return adaptations
        
    except Exception as e:
        logger.error("Failed to get cultural adaptations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cultural adaptations"
        )


@router.post("/cultural-adaptations", response_model=CulturalAdaptationResponse)
async def create_cultural_adaptation(
    adaptation: CulturalAdaptationCreate,
    admin_user: str = Query(..., description="Admin user creating the adaptation"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new cultural adaptation."""
    try:
        # Check if template exists
        template_result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == adaptation.template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create adaptation
        db_adaptation = CulturalAdaptation(
            **adaptation.dict(),
            created_by=admin_user,
            updated_by=admin_user
        )
        
        db.add(db_adaptation)
        await db.commit()
        await db.refresh(db_adaptation)
        
        logger.info("Cultural adaptation created", adaptation_id=db_adaptation.id, template_id=adaptation.template_id)
        return db_adaptation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create cultural adaptation", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cultural adaptation: {str(e)}"
        )


@router.get("/cultural-adaptations/{adaptation_id}", response_model=CulturalAdaptationResponse)
async def get_cultural_adaptation(
    adaptation_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific cultural adaptation."""
    try:
        result = await db.execute(
            select(CulturalAdaptation).where(CulturalAdaptation.id == adaptation_id)
        )
        adaptation = result.scalar_one_or_none()
        
        if not adaptation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultural adaptation not found"
            )
        
        return adaptation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get cultural adaptation", adaptation_id=adaptation_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cultural adaptation"
        )


@router.delete("/cultural-adaptations/{adaptation_id}")
async def delete_cultural_adaptation(
    adaptation_id: int,
    admin_user: str = Query(..., description="Admin user deleting the adaptation"),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a cultural adaptation."""
    try:
        result = await db.execute(
            select(CulturalAdaptation).where(CulturalAdaptation.id == adaptation_id)
        )
        adaptation = result.scalar_one_or_none()
        
        if not adaptation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultural adaptation not found"
            )
        
        await db.execute(delete(CulturalAdaptation).where(CulturalAdaptation.id == adaptation_id))
        await db.commit()
        
        logger.info("Cultural adaptation deleted", adaptation_id=adaptation_id, admin_user=admin_user)
        return {"success": True, "message": "Cultural adaptation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete cultural adaptation", adaptation_id=adaptation_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cultural adaptation"
        )


# ================== A/B TEST EXPERIMENT ENDPOINTS ==================

@router.get("/ab-tests", response_model=List[ABTestExperimentResponse])
async def get_ab_test_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(True, description="Only return active experiments"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get A/B test experiments."""
    try:
        query = select(ABTestExperiment)
        
        if status:
            query = query.where(ABTestExperiment.status == status)
            
        if active_only:
            query = query.where(ABTestExperiment.is_active == True)
        
        query = query.order_by(desc(ABTestExperiment.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        experiments = result.scalars().all()
        
        logger.info("Retrieved A/B test experiments", count=len(experiments))
        return experiments
        
    except Exception as e:
        logger.error("Failed to get A/B test experiments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B test experiments"
        )


@router.post("/ab-tests", response_model=ABTestExperimentResponse)
async def create_ab_test_experiment(
    experiment: ABTestExperimentCreate,
    admin_user: str = Query(..., description="Admin user creating the experiment"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new A/B test experiment."""
    try:
        # Validate templates exist
        all_template_ids = [experiment.control_template_id] + experiment.variant_template_ids
        for template_id in all_template_ids:
            template_result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.id == template_id)
            )
            template = template_result.scalar_one_or_none()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Template {template_id} not found"
                )
        
        # Create experiment
        db_experiment = ABTestExperiment(
            **experiment.dict(),
            status="draft",
            created_by=admin_user,
            updated_by=admin_user
        )
        
        db.add(db_experiment)
        await db.commit()
        await db.refresh(db_experiment)
        
        logger.info("A/B test experiment created", experiment_id=db_experiment.id, name=experiment.name)
        return db_experiment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create A/B test experiment", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test experiment: {str(e)}"
        )


@router.get("/ab-tests/{experiment_id}", response_model=ABTestExperimentResponse)
async def get_ab_test_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific A/B test experiment."""
    try:
        result = await db.execute(
            select(ABTestExperiment).where(ABTestExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test experiment not found"
            )
        
        return experiment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get A/B test experiment", experiment_id=experiment_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B test experiment"
        )


@router.post("/ab-tests/{experiment_id}/start")
async def start_ab_test_experiment(
    experiment_id: int,
    admin_user: str = Query(..., description="Admin user starting the experiment"),
    db: AsyncSession = Depends(get_async_session)
):
    """Start an A/B test experiment."""
    try:
        result = await db.execute(
            select(ABTestExperiment).where(ABTestExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test experiment not found"
            )
        
        if experiment.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Experiment can only be started from draft status"
            )
        
        experiment.status = "running"
        experiment.actual_start_date = datetime.utcnow()
        experiment.updated_by = admin_user
        
        await db.commit()
        
        logger.info("A/B test experiment started", experiment_id=experiment_id, admin_user=admin_user)
        return {"success": True, "message": "Experiment started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start A/B test experiment", experiment_id=experiment_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start A/B test experiment"
        )


@router.post("/ab-tests/{experiment_id}/stop")
async def stop_ab_test_experiment(
    experiment_id: int,
    admin_user: str = Query(..., description="Admin user stopping the experiment"),
    db: AsyncSession = Depends(get_async_session)
):
    """Stop an A/B test experiment."""
    try:
        result = await db.execute(
            select(ABTestExperiment).where(ABTestExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test experiment not found"
            )
        
        if experiment.status != "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only stop running experiments"
            )
        
        experiment.status = "completed"
        experiment.actual_end_date = datetime.utcnow()
        experiment.updated_by = admin_user
        
        await db.commit()
        
        logger.info("A/B test experiment stopped", experiment_id=experiment_id, admin_user=admin_user)
        return {"success": True, "message": "Experiment stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop A/B test experiment", experiment_id=experiment_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop A/B test experiment"
        )


# ================== PERFORMANCE METRICS ENDPOINTS ==================

@router.get("/performance-metrics")
async def get_performance_metrics(
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    language: Optional[str] = Query(None, description="Filter by language"),
    cultural_region: Optional[str] = Query(None, description="Filter by cultural region"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get performance metrics with filtering."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(TemplatePerformanceMetric).where(
            TemplatePerformanceMetric.created_at >= start_date
        )
        
        if template_id:
            query = query.where(TemplatePerformanceMetric.template_id == template_id)
            
        if language:
            query = query.where(TemplatePerformanceMetric.language_code == language)
            
        if cultural_region:
            query = query.where(TemplatePerformanceMetric.cultural_region == cultural_region)
        
        query = query.order_by(desc(TemplatePerformanceMetric.metric_date))
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        logger.info("Retrieved performance metrics", count=len(metrics), days=days)
        return [
            {
                "id": metric.id,
                "template_id": metric.template_id,
                "language_code": metric.language_code,
                "cultural_region": metric.cultural_region,
                "metric_date": metric.metric_date,
                "generation_count": metric.generation_count,
                "success_rate": metric.success_rate,
                "average_generation_time_ms": metric.average_generation_time_ms,
                "average_quality_score": metric.average_quality_score,
                "average_user_rating": metric.average_user_rating,
                "conversion_rate": metric.conversion_rate,
                "total_cost_usd": metric.total_cost_usd
            }
            for metric in metrics
        ]
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.post("/performance-metrics", response_model=dict)
async def create_performance_metric(
    metric: PerformanceMetricCreate,
    admin_user: str = Query(..., description="Admin user creating the metric"),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new performance metric entry."""
    try:
        # Check if template exists
        template_result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == metric.template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create metric
        db_metric = TemplatePerformanceMetric(
            **metric.dict(),
            metric_date=datetime.utcnow().date(),
            created_by=admin_user
        )
        
        db.add(db_metric)
        await db.commit()
        await db.refresh(db_metric)
        
        logger.info("Performance metric created", metric_id=db_metric.id, template_id=metric.template_id)
        return {"success": True, "message": "Performance metric created successfully", "id": db_metric.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create performance metric", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create performance metric: {str(e)}"
        )


# ================== ANALYTICS AND INSIGHTS ENDPOINTS ==================

@router.get("/analytics/template-performance")
async def get_template_performance_analytics(
    template_id: Optional[int] = Query(None, description="Specific template ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get comprehensive template performance analytics."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for performance metrics
        query = select(TemplatePerformanceMetric).where(
            TemplatePerformanceMetric.created_at >= start_date
        )
        
        if template_id:
            query = query.where(TemplatePerformanceMetric.template_id == template_id)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        # Aggregate analytics
        analytics = {
            "summary": {
                "total_generations": sum(m.generation_count for m in metrics),
                "total_templates": len(set(m.template_id for m in metrics)),
                "average_success_rate": sum(m.success_rate for m in metrics) / len(metrics) if metrics else 0,
                "average_quality_score": sum(m.average_quality_score for m in metrics) / len(metrics) if metrics else 0,
                "total_cost": sum(m.total_cost_usd for m in metrics)
            },
            "by_template": {},
            "by_language": {},
            "by_cultural_region": {},
            "trends": []
        }
        
        # Group by template
        for metric in metrics:
            template_id = metric.template_id
            if template_id not in analytics["by_template"]:
                analytics["by_template"][template_id] = {
                    "generations": 0,
                    "success_rate": 0,
                    "quality_score": 0,
                    "cost": 0
                }
            
            analytics["by_template"][template_id]["generations"] += metric.generation_count
            analytics["by_template"][template_id]["success_rate"] += metric.success_rate
            analytics["by_template"][template_id]["quality_score"] += metric.average_quality_score
            analytics["by_template"][template_id]["cost"] += metric.total_cost_usd
        
        # Group by language
        for metric in metrics:
            lang = metric.language_code
            if lang not in analytics["by_language"]:
                analytics["by_language"][lang] = {
                    "generations": 0,
                    "success_rate": 0,
                    "quality_score": 0
                }
            
            analytics["by_language"][lang]["generations"] += metric.generation_count
            analytics["by_language"][lang]["success_rate"] += metric.success_rate
            analytics["by_language"][lang]["quality_score"] += metric.average_quality_score
        
        # Group by cultural region
        for metric in metrics:
            region = metric.cultural_region
            if region not in analytics["by_cultural_region"]:
                analytics["by_cultural_region"][region] = {
                    "generations": 0,
                    "success_rate": 0,
                    "quality_score": 0
                }
            
            analytics["by_cultural_region"][region]["generations"] += metric.generation_count
            analytics["by_cultural_region"][region]["success_rate"] += metric.success_rate
            analytics["by_cultural_region"][region]["quality_score"] += metric.average_quality_score
        
        logger.info("Generated template performance analytics", templates=len(analytics["by_template"]), days=days)
        return analytics
        
    except Exception as e:
        logger.error("Failed to get template performance analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/analytics/optimization-opportunities")
async def get_optimization_opportunities(
    db: AsyncSession = Depends(get_async_session)
):
    """Get AI-powered optimization opportunities."""
    try:
        # Get underperforming templates
        result = await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.is_active == True,
                    PromptTemplate.success_rate < 0.8,
                    PromptTemplate.usage_count > 10
                )
            ).order_by(asc(PromptTemplate.success_rate))
        )
        underperforming = result.scalars().all()
        
        # Get high-performing templates for reference
        result = await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.is_active == True,
                    PromptTemplate.success_rate > 0.9,
                    PromptTemplate.usage_count > 10
                )
            ).order_by(desc(PromptTemplate.success_rate)).limit(5)
        )
        high_performers = result.scalars().all()
        
        opportunities = []
        
        for template in underperforming:
            opportunity = {
                "template_id": template.id,
                "template_name": template.name,
                "current_success_rate": template.success_rate,
                "current_quality_score": template.content_quality_score,
                "opportunity_type": "performance_improvement",
                "recommendations": [],
                "estimated_improvement": 0.0
            }
            
            # Generate recommendations based on performance gaps
            if template.success_rate < 0.5:
                opportunity["recommendations"].append("Complete prompt rewrite recommended")
                opportunity["estimated_improvement"] = 0.4
            elif template.success_rate < 0.7:
                opportunity["recommendations"].append("Optimize prompt clarity and instructions")
                opportunity["estimated_improvement"] = 0.2
            else:
                opportunity["recommendations"].append("Fine-tune prompt parameters")
                opportunity["estimated_improvement"] = 0.1
            
            # Add specific recommendations
            if template.content_quality_score < 0.7:
                opportunity["recommendations"].append("Improve content quality guidelines")
            
            if template.average_user_rating < 3.5:
                opportunity["recommendations"].append("Enhance user satisfaction factors")
            
            opportunities.append(opportunity)
        
        # Add cultural expansion opportunities
        for template in high_performers:
            if len(template.supported_languages) == 1:
                opportunities.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "opportunity_type": "cultural_expansion",
                    "recommendations": ["Expand to additional languages and cultural regions"],
                    "estimated_impact": "Medium to High",
                    "suggested_languages": ["he", "es", "fr", "de"],
                    "suggested_regions": ["middle_east", "europe", "latin_america"]
                })
        
        logger.info("Generated optimization opportunities", count=len(opportunities))
        return {
            "opportunities": opportunities,
            "summary": {
                "total_opportunities": len(opportunities),
                "performance_improvements": len([o for o in opportunities if o.get("opportunity_type") == "performance_improvement"]),
                "cultural_expansions": len([o for o in opportunities if o.get("opportunity_type") == "cultural_expansion"])
            }
        }
        
    except Exception as e:
        logger.error("Failed to get optimization opportunities", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization opportunities"
        )


# ================== BULK OPERATIONS ==================

@router.post("/bulk/activate-templates")
async def bulk_activate_templates(
    template_ids: List[int],
    admin_user: str = Query(..., description="Admin user performing bulk operation"),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk activate templates."""
    try:
        await db.execute(
            update(PromptTemplate)
            .where(PromptTemplate.id.in_(template_ids))
            .values(is_active=True, updated_by=admin_user, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("Bulk activated templates", template_ids=template_ids, admin_user=admin_user)
        return {"success": True, "message": f"Activated {len(template_ids)} templates"}
        
    except Exception as e:
        logger.error("Failed to bulk activate templates", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate templates"
        )


@router.post("/bulk/deactivate-templates")
async def bulk_deactivate_templates(
    template_ids: List[int],
    admin_user: str = Query(..., description="Admin user performing bulk operation"),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk deactivate templates."""
    try:
        await db.execute(
            update(PromptTemplate)
            .where(PromptTemplate.id.in_(template_ids))
            .values(is_active=False, updated_by=admin_user, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        logger.info("Bulk deactivated templates", template_ids=template_ids, admin_user=admin_user)
        return {"success": True, "message": f"Deactivated {len(template_ids)} templates"}
        
    except Exception as e:
        logger.error("Failed to bulk deactivate templates", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate templates"
        )


# ================== TEMPLATE CLONING AND VERSIONING ==================

@router.post("/templates/{template_id}/clone", response_model=TemplateResponse)
async def clone_template(
    template_id: int,
    new_name: str = Query(..., description="Name for the cloned template"),
    admin_user: str = Query(..., description="Admin user cloning the template"),
    db: AsyncSession = Depends(get_async_session)
):
    """Clone an existing template."""
    try:
        # Get original template
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        original_template = result.scalar_one_or_none()
        
        if not original_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create cloned template
        cloned_data = {
            "template_type": original_template.template_type,
            "name": new_name,
            "description": f"Clone of {original_template.name}",
            "category": original_template.category,
            "primary_language": original_template.primary_language,
            "supported_languages": original_template.supported_languages,
            "cultural_regions": original_template.cultural_regions,
            "system_prompt": original_template.system_prompt,
            "user_prompt_template": original_template.user_prompt_template,
            "tone": original_template.tone,
            "urgency_level": original_template.urgency_level,
            "target_audience": original_template.target_audience,
            "product_categories": original_template.product_categories,
            "default_temperature": original_template.default_temperature,
            "default_max_tokens": original_template.default_max_tokens,
            "supported_providers": original_template.supported_providers,
            "required_variables": original_template.required_variables,
            "optional_variables": original_template.optional_variables,
            "is_active": False,  # Clone starts as inactive
            "is_default": False,  # Clone is never default
            "is_experimental": True,  # Clone starts as experimental
            "parent_template_id": template_id,
            "created_by": admin_user,
            "updated_by": admin_user
        }
        
        cloned_template = PromptTemplate(**cloned_data)
        
        db.add(cloned_template)
        await db.commit()
        await db.refresh(cloned_template)
        
        logger.info("Template cloned", original_id=template_id, cloned_id=cloned_template.id, admin_user=admin_user)
        return cloned_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to clone template", template_id=template_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone template: {str(e)}"
        )


@router.get("/templates/{template_id}/versions")
async def get_template_versions(
    template_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all versions of a template."""
    try:
        # Get the template and its children (versions)
        result = await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.parent_template_id == template_id,
                    PromptTemplate.is_active == True
                )
            ).order_by(desc(PromptTemplate.created_at))
        )
        versions = result.scalars().all()
        
        # Also get the original template
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        original = result.scalar_one_or_none()
        
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        all_versions = [original] + list(versions)
        
        return {
            "original_template": {
                "id": original.id,
                "name": original.name,
                "version": original.version,
                "created_at": original.created_at,
                "is_current": True
            },
            "versions": [
                {
                    "id": v.id,
                    "name": v.name,
                    "version": v.version,
                    "created_at": v.created_at,
                    "success_rate": v.success_rate,
                    "usage_count": v.usage_count,
                    "is_active": v.is_active
                }
                for v in versions
            ],
            "total_versions": len(all_versions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get template versions", template_id=template_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template versions"
        ) 