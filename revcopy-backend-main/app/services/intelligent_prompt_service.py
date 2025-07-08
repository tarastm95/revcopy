"""
Intelligent Prompt Service

World-class prompt management system with:
- Context-aware prompt selection
- Multi-language and cultural adaptation  
- Performance-based optimization
- Real-time analytics and insights
- A/B testing capabilities
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import structlog
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.prompts import (
    PromptTemplate, CulturalAdaptation, AIContentGeneration, 
    TemplatePerformanceMetric, ABTestExperiment
)
from app.services.ai import AIService

logger = structlog.get_logger(__name__)


class ContentType(Enum):
    """Supported content types for intelligent generation."""
    PRODUCT_DESCRIPTION = "product_description"
    FACEBOOK_AD = "facebook_ad"
    GOOGLE_AD = "google_ad"
    INSTAGRAM_CAPTION = "instagram_caption"
    EMAIL_CAMPAIGN = "email_campaign"
    BLOG_ARTICLE = "blog_article"
    FAQ = "faq"
    PRODUCT_COMPARISON = "product_comparison"
    LANDING_PAGE = "landing_page"
    PRESS_RELEASE = "press_release"


class CulturalRegion(Enum):
    """Cultural regions for content adaptation."""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    MIDDLE_EAST = "middle_east"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    AFRICA = "africa"


class ContentTone(Enum):
    """Content tone options."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    LUXURIOUS = "luxurious"
    CASUAL = "casual"
    AUTHORITATIVE = "authoritative"
    EMOTIONAL = "emotional"
    MINIMALIST = "minimalist"
    PLAYFUL = "playful"


@dataclass
class IntelligentPromptRequest:
    """Request for intelligent prompt-based content generation."""
    content_type: ContentType
    product_data: Dict[str, Any]
    reviews_data: List[Dict] = field(default_factory=list)
    
    # Language and cultural preferences
    language: str = "en"
    cultural_region: CulturalRegion = CulturalRegion.NORTH_AMERICA
    country_code: Optional[str] = None
    
    # Content targeting
    target_audience: Optional[str] = None
    tone: ContentTone = ContentTone.PROFESSIONAL
    urgency_level: str = "medium"  # low, medium, high
    personalization_level: str = "standard"  # minimal, standard, high
    
    # Business context
    brand_personality: Optional[str] = None
    price_range: Optional[str] = None  # budget, mid_range, premium, luxury
    product_category: Optional[str] = None
    
    # Generation preferences
    ai_provider: str = "deepseek"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # A/B testing
    enable_ab_testing: bool = True
    force_template_id: Optional[int] = None
    
    # Custom variables
    custom_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Session context
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class IntelligentPromptResponse:
    """Response from intelligent prompt generation."""
    content: str
    template_id: int
    template_name: str
    adaptation_id: Optional[int] = None
    
    # Selection metadata
    selection_score: float = 0.0
    alternatives_considered: List[Dict] = field(default_factory=list)
    
    # Cultural adaptations applied
    adaptations_applied: Dict[str, Any] = field(default_factory=dict)
    cultural_notes: List[str] = field(default_factory=list)
    
    # Performance metadata
    generation_time_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    
    # Quality metrics
    content_quality_score: float = 0.0
    uniqueness_score: float = 0.0
    cultural_appropriateness_score: float = 0.0
    
    # A/B testing info
    ab_test_group: Optional[str] = None
    ab_test_variant: Optional[str] = None
    
    # Recommendations
    optimization_suggestions: List[str] = field(default_factory=list)
    performance_insights: Dict[str, Any] = field(default_factory=dict)


class IntelligentPromptService:
    """
    World-class intelligent prompt management service.
    
    Provides enterprise-level prompt selection, cultural adaptation,
    and performance optimization capabilities.
    """
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self._cultural_adaptations_cache = {}
        self._performance_cache = {}
        self._load_cultural_intelligence()
    
    def _load_cultural_intelligence(self) -> None:
        """Load cultural intelligence data for different regions and languages."""
        
        # Cultural intelligence for different regions
        self.cultural_intelligence = {
            "north_america": {
                "english": {
                    "greeting_style": "friendly_professional",
                    "urgency_approach": "direct",
                    "social_proof_style": "individual_focused",
                    "currency_format": "${amount}",
                    "cultural_values": ["individualism", "efficiency", "innovation", "value"],
                    "communication_style": "direct_confident",
                    "trust_building": ["testimonials", "guarantees", "reviews"],
                    "privacy_concerns": True
                }
            },
            "middle_east": {
                "hebrew": {
                    "greeting_style": "respectful_warm",
                    "urgency_approach": "respectful_persistent",
                    "social_proof_style": "community_focused",
                    "currency_format": "₪{amount}",
                    "cultural_values": ["family", "tradition", "quality", "trust"],
                    "communication_style": "respectful_direct",
                    "trust_building": ["local_presence", "community_endorsement", "certifications"],
                    "family_orientation": True,
                    "text_direction": "rtl"
                },
                "arabic": {
                    "greeting_style": "formal_respectful",
                    "urgency_approach": "measured_respectful",
                    "social_proof_style": "authority_focused",
                    "currency_format": "currency varies by country",
                    "cultural_values": ["honor", "family", "tradition", "respect"],
                    "communication_style": "formal_respectful",
                    "trust_building": ["authority_endorsement", "tradition", "reputation"],
                    "formal_language_preferred": True,
                    "text_direction": "rtl"
                }
            },
            "europe": {
                "english": {
                    "greeting_style": "professional_sophisticated",
                    "urgency_approach": "measured",
                    "social_proof_style": "quality_focused",
                    "currency_format": "€{amount}",
                    "cultural_values": ["quality", "sustainability", "craftsmanship", "heritage"],
                    "communication_style": "sophisticated_informative",
                    "trust_building": ["certifications", "heritage", "quality_standards"],
                    "privacy_emphasis": True
                }
            }
        }
        
        # Language-specific adaptations - English only
        self.language_adaptations = {
            "en": {
                "direction": "ltr",
                "greeting": "Hello",
                "urgency_words": ["limited", "exclusive", "limited time", "unique opportunity"],
                "positive_adjectives": ["excellent", "quality", "amazing", "exceptional", "recommended"],
                "call_to_action": ["order now", "buy today", "discover more", "start here"],
                "social_proof": ["satisfied customers", "positive reviews", "highly recommended"],
                "guarantee_terms": ["full warranty", "money back", "no risk"],
                "cultural_context": {
                    "family_oriented": True,
                    "value_conscious": True,
                    "trust_building_important": True,
                    "community_focused": True
                }
            }
        }
    
    def _detect_product_language(self, product_data: Dict[str, Any]) -> str:
        """
        Detect the language of the product based on its content.
        
        Args:
            product_data: Product information
            
        Returns:
            Language code (always 'en' for English-only system)
        """
        # Always return English - no multi-language support
        return "en"
    
    async def generate_intelligent_content(
        self,
        request: IntelligentPromptRequest,
        db: AsyncSession
    ) -> IntelligentPromptResponse:
        """
        Generate content using intelligent prompt selection and cultural adaptation.
        
        Args:
            request: Intelligent prompt request with all context
            db: Database session
            
        Returns:
            IntelligentPromptResponse with generated content and metadata
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "Starting intelligent content generation",
                content_type=request.content_type.value,
                language=request.language,
                cultural_region=request.cultural_region.value,
                target_audience=request.target_audience
            )
            
            # Step 1: Intelligent template selection
            template, selection_metadata = await self._select_optimal_template(
                request, db
            )
            
            # Step 2: Get or create cultural adaptation
            adaptation = await self._get_cultural_adaptation(
                template, request, db
            )
            
            # Step 3: Apply A/B testing if enabled
            if request.enable_ab_testing and not request.force_template_id:
                template, ab_metadata = await self._apply_ab_testing(
                    template, request, db
                )
            else:
                ab_metadata = {}
            
            # Step 4: Prepare enhanced variables
            variables = await self._prepare_intelligent_variables(
                request, template, adaptation
            )
            
            # Step 5: Generate content with cultural adaptation
            content_result = await self._generate_culturally_adapted_content(
                template, adaptation, variables, request
            )
            
            # Step 6: Post-process content
            processed_content = await self._post_process_content(
                content_result["content"], request, adaptation
            )
            
            # Step 7: Analyze content quality
            quality_metrics = await self._analyze_content_quality(
                processed_content, request, template
            )
            
            # Step 8: Record generation for analytics
            generation_record = await self._record_generation(
                template, adaptation, request, content_result, quality_metrics, db
            )
            
            # Step 9: Generate performance insights
            insights = await self._generate_performance_insights(
                template, request, quality_metrics, db
            )
            
            # Calculate total generation time
            generation_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build response
            response = IntelligentPromptResponse(
                content=processed_content,
                template_id=template.id,
                template_name=template.name,
                adaptation_id=adaptation.id if adaptation else None,
                selection_score=selection_metadata.get("selection_score", 0.0),
                alternatives_considered=selection_metadata.get("alternatives", []),
                adaptations_applied=adaptation.cultural_modifications if adaptation else {},
                cultural_notes=self._generate_cultural_notes(adaptation, request),
                generation_time_ms=generation_time,
                tokens_used=content_result.get("tokens_used", 0),
                cost_estimate=content_result.get("cost_estimate", 0.0),
                content_quality_score=quality_metrics.get("overall_quality", 0.0),
                uniqueness_score=quality_metrics.get("uniqueness", 0.0),
                cultural_appropriateness_score=quality_metrics.get("cultural_appropriateness", 0.0),
                ab_test_group=ab_metadata.get("group"),
                ab_test_variant=ab_metadata.get("variant"),
                optimization_suggestions=insights.get("suggestions", []),
                performance_insights=insights.get("insights", {})
            )
            
            logger.info(
                "Intelligent content generation completed",
                template_id=template.id,
                adaptation_used=adaptation.id if adaptation else None,
                generation_time_ms=generation_time,
                quality_score=quality_metrics.get("overall_quality", 0.0)
            )
            
            return response
            
        except Exception as e:
            logger.error("Intelligent content generation failed", error=str(e))
            # Record the failure for analytics
            await self._record_generation_failure(request, str(e), db)
            raise
    
    async def _select_optimal_template(
        self,
        request: IntelligentPromptRequest,
        db: AsyncSession
    ) -> Tuple[PromptTemplate, Dict[str, Any]]:
        """Select the optimal template based on intelligent criteria."""
        
        if request.force_template_id:
            # Use forced template
            result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.id == request.force_template_id)
            )
            template = result.scalar_one_or_none()
            if not template:
                raise ValueError(f"Forced template {request.force_template_id} not found")
            return template, {"selection_score": 1.0, "method": "forced"}
        
        # Get candidate templates
        candidates_query = select(PromptTemplate).where(
            and_(
                PromptTemplate.template_type == request.content_type.value,
                PromptTemplate.is_active == True
            )
        ).options(
            selectinload(PromptTemplate.cultural_adaptations),
            selectinload(PromptTemplate.performance_metrics)
        )
        
        result = await db.execute(candidates_query)
        candidates = result.scalars().all()
        
        if not candidates:
            raise ValueError(f"No active templates found for {request.content_type.value}")
        
        # Score and rank candidates
        scored_candidates = []
        for template in candidates:
            score = await self._calculate_template_score(template, request, db)
            scored_candidates.append((template, score))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        best_template, best_score = scored_candidates[0]
        
        # Prepare selection metadata
        alternatives = [
            {
                "template_id": t.id,
                "template_name": t.name,
                "score": score,
                "version": t.version
            }
            for t, score in scored_candidates[1:3]  # Top 3 alternatives
        ]
        
        selection_metadata = {
            "selection_score": best_score,
            "method": "intelligent_scoring",
            "alternatives": alternatives,
            "total_candidates": len(candidates)
        }
        
        return best_template, selection_metadata
    
    async def _calculate_template_score(
        self,
        template: PromptTemplate,
        request: IntelligentPromptRequest,
        db: AsyncSession
    ) -> float:
        """Calculate comprehensive template score for selection."""
        
        score = 0.0
        
        # Performance metrics (35% weight)
        performance_score = (
            template.success_rate * 0.4 +
            min(template.average_user_rating / 5.0, 1.0) * 0.3 +
            min(template.conversion_rate * 10, 1.0) * 0.2 +
            (1.0 - min(template.average_generation_time / 30.0, 1.0)) * 0.1
        )
        score += performance_score * 0.35
        
        # Language and cultural fit (25% weight)
        cultural_score = await self._calculate_cultural_fit_score(template, request)
        score += cultural_score * 0.25
        
        # Context relevance (20% weight)
        context_score = self._calculate_context_relevance_score(template, request)
        score += context_score * 0.20
        
        # Template quality and recency (15% weight)
        quality_score = (
            template.content_quality_score * 0.6 +
            template.uniqueness_score * 0.2 +
            template.relevance_score * 0.2
        )
        score += quality_score * 0.15
        
        # A/B test performance bonus (5% weight)
        ab_bonus = await self._calculate_ab_test_bonus(template, db)
        score += ab_bonus * 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _calculate_cultural_fit_score(
        self,
        template: PromptTemplate,
        request: IntelligentPromptRequest
    ) -> float:
        """Calculate how well a template fits cultural requirements."""
        
        score = 0.0
        
        # Language support
        if request.language in template.supported_languages:
            score += 0.4
        elif "en" in template.supported_languages:  # Fallback to English
            score += 0.2
        
        # Cultural region support
        if request.cultural_region.value in template.cultural_regions:
            score += 0.3
        
        # Tone alignment
        if template.tone == request.tone.value:
            score += 0.2
        elif template.tone in ["professional", "friendly"]:  # Universal tones
            score += 0.1
        
        # Target audience alignment
        if (request.target_audience and 
            template.target_audience and 
            request.target_audience.lower() in template.target_audience.lower()):
            score += 0.1
        
        return score
    
    def _calculate_context_relevance_score(
        self,
        template: PromptTemplate,
        request: IntelligentPromptRequest
    ) -> float:
        """Calculate context relevance score."""
        
        score = 0.0
        
        # Product category match
        if (request.product_category and 
            template.product_categories and 
            request.product_category in template.product_categories):
            score += 0.3
        
        # Price range match
        if (request.price_range and 
            template.price_ranges and 
            request.price_range in template.price_ranges):
            score += 0.2
        
        # Brand personality match
        if (request.brand_personality and 
            template.brand_personalities and 
            request.brand_personality in template.brand_personalities):
            score += 0.2
        
        # Urgency level match
        if template.urgency_level == request.urgency_level:
            score += 0.15
        
        # Personalization level match
        if template.personalization_level == request.personalization_level:
            score += 0.15
        
        return score
    
    async def _calculate_ab_test_bonus(
        self,
        template: PromptTemplate,
        db: AsyncSession
    ) -> float:
        """Calculate A/B test performance bonus."""
        
        if not template.ab_test_group:
            return 0.0
        
        # Query recent A/B test results
        recent_date = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(ABTestExperiment).where(
                and_(
                    ABTestExperiment.status == "completed",
                    ABTestExperiment.end_date >= recent_date,
                    ABTestExperiment.winning_variant == str(template.id)
                )
            )
        )
        
        winning_experiments = result.scalars().all()
        
        # Bonus based on recent wins
        return min(len(winning_experiments) * 0.1, 0.5)
    
    async def _get_cultural_adaptation(
        self,
        template: PromptTemplate,
        request: IntelligentPromptRequest,
        db: AsyncSession
    ) -> Optional[CulturalAdaptation]:
        """Get or create cultural adaptation for the template."""
        
        # Detect language from product data first
        detected_language = self._detect_product_language(request.product_data)
        
        # Override request language if detected language is different and more reliable
        effective_language = detected_language if detected_language != "en" else request.language
        
        logger.info(
            "Cultural adaptation check",
            requested_language=request.language,
            detected_language=detected_language,
            effective_language=effective_language,
            product_title=request.product_data.get("title", "")
        )
        
        # Only apply adaptations for non-English content or explicit requests
        if effective_language == "en" and request.cultural_region == CulturalRegion.NORTH_AMERICA:
            logger.info("Skipping cultural adaptation for English product in North America")
            return None  # No adaptation needed for default English content
        
        # Look for existing adaptation
        result = await db.execute(
            select(CulturalAdaptation).where(
                and_(
                    CulturalAdaptation.template_id == template.id,
                    CulturalAdaptation.language_code == effective_language,
                    CulturalAdaptation.cultural_region == request.cultural_region.value
                )
            )
        )
        
        adaptation = result.scalar_one_or_none()
        
        if adaptation:
            return adaptation
        
        # Only create adaptation if language is not English or explicitly requested
        if effective_language != "en":
            # Create new adaptation if none exists
            adaptation = await self._create_cultural_adaptation(
                template, request, db, effective_language
            )
            return adaptation
        
        return None
    
    async def _create_cultural_adaptation(
        self,
        template: PromptTemplate,
        request: IntelligentPromptRequest,
        db: AsyncSession,
        language: str
    ) -> CulturalAdaptation:
        """Create a new cultural adaptation."""
        
        # Get cultural intelligence for this language/region
        cultural_data = self._get_cultural_intelligence(language, request.cultural_region)
        
        # Adapt system prompt
        adapted_system_prompt = await self._adapt_system_prompt(
            template.system_prompt, cultural_data, request
        )
        
        # Adapt user prompt template
        adapted_user_prompt = await self._adapt_user_prompt(
            template.user_prompt_template, cultural_data, request
        )
        
        # Create adaptation record
        adaptation = CulturalAdaptation(
            template_id=template.id,
            language_code=language,
            cultural_region=request.cultural_region.value,
            adapted_system_prompt=adapted_system_prompt,
            adapted_user_prompt=adapted_user_prompt,
            cultural_modifications=cultural_data,
            linguistic_modifications=self.language_adaptations.get(language, {}),
            text_direction=cultural_data.get("text_direction", "ltr"),
            currency_symbol=cultural_data.get("currency_format", "$"),
            created_by="intelligent_system"
        )
        
        db.add(adaptation)
        await db.commit()
        await db.refresh(adaptation)
        
        logger.info(
            "Created new cultural adaptation",
            template_id=template.id,
            language=language,
            cultural_region=request.cultural_region.value,
            adaptation_id=adaptation.id
        )
        
        return adaptation
    
    def _get_cultural_intelligence(
        self,
        language: str,
        cultural_region: CulturalRegion
    ) -> Dict[str, Any]:
        """Get cultural intelligence data for language/region combination."""
        
        region_data = self.cultural_intelligence.get(cultural_region.value, {})
        language_data = region_data.get(language, {})
        
        # Fallback to English if language not found
        if not language_data and language != "english":
            language_data = region_data.get("english", {})
        
        # Merge with language-specific adaptations
        lang_adaptations = self.language_adaptations.get(language, {})
        
        return {**language_data, **lang_adaptations}
    
    async def _prepare_intelligent_variables(
        self,
        request: IntelligentPromptRequest,
        template: PromptTemplate,
        adaptation: Optional[CulturalAdaptation]
    ) -> Dict[str, Any]:
        """Prepare enhanced template variables with cultural adaptation."""
        
        # Start with basic product data
        variables = {
            "product_name": request.product_data.get("title", "Product"),
            "brand": request.product_data.get("brand", "Brand"),
            "price": request.product_data.get("price", 0),
            "currency": request.product_data.get("currency", "$"),
            "category": request.product_category or "Product",
            "description": request.product_data.get("description", ""),
        }
        
        # Add cultural adaptations
        if adaptation:
            cultural_mods = adaptation.cultural_modifications
            variables.update({
                "currency_symbol": adaptation.currency_symbol,
                "greeting": cultural_mods.get("greeting", "Hello"),
                "urgency_words": cultural_mods.get("urgency_words", ["limited", "exclusive"]),
                "call_to_action": cultural_mods.get("call_to_action", ["Order now", "Buy today"]),
                "social_proof_style": cultural_mods.get("social_proof_style", "individual_focused"),
                "trust_building_elements": cultural_mods.get("trust_building", [])
            })
        
        # Process reviews data
        if request.reviews_data:
            strengths, weaknesses = await self._analyze_reviews_intelligently(
                request.reviews_data, request.language
            )
            variables.update({
                "strengths": "\n".join([f"• {s}" for s in strengths]),
                "weaknesses": "\n".join([f"• {w}" for w in weaknesses]),
                "total_reviews": len(request.reviews_data),
                "average_rating": sum(r.get("rating", 0) for r in request.reviews_data) / len(request.reviews_data),
                "positive_count": len([r for r in request.reviews_data if r.get("rating", 0) >= 4]),
                "negative_count": len([r for r in request.reviews_data if r.get("rating", 0) <= 2])
            })
        else:
            # Default values when no reviews
            variables.update({
                "strengths": "• High-quality product\n• Excellent customer satisfaction",
                "weaknesses": "• Limited availability",
                "total_reviews": 0,
                "average_rating": 4.5,
                "positive_count": 0,
                "negative_count": 0
            })
        
        # Add custom variables
        variables.update(request.custom_variables)
        
        return variables
    
    # Additional helper methods would continue here...
    
    async def get_template_performance_analytics(
        self,
        template_id: Optional[int] = None,
        language: Optional[str] = None,
        cultural_region: Optional[str] = None,
        time_range_days: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance analytics for templates."""
        # Implementation for performance analytics
        pass
    
    async def optimize_template_performance(
        self,
        template_id: int,
        optimization_criteria: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Automatically optimize template performance."""
        # Implementation for automatic optimization
        pass

    async def _record_generation_failure(
        self,
        request: IntelligentPromptRequest,
        error_message: str,
        db: AsyncSession
    ) -> None:
        """Record generation failure for analytics and improvement."""
        try:
            # This is a placeholder for analytics recording
            # In a full implementation, this would record to a failure tracking table
            logger.error(
                "Generation failure recorded",
                content_type=request.content_type.value,
                language=request.language,
                cultural_region=request.cultural_region.value,
                error=error_message
            )
            
            # Could add database recording here for failure analytics
            # failure_record = GenerationFailure(
            #     content_type=request.content_type.value,
            #     language=request.language,
            #     cultural_region=request.cultural_region.value,
            #     error_message=error_message,
            #     timestamp=datetime.utcnow()
            # )
            # db.add(failure_record)
            # await db.commit()
            
        except Exception as e:
            logger.error("Failed to record generation failure", error=str(e))

    async def get_cultural_insights(
        self,
        language: str,
        cultural_region: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Get cultural insights for a specific combination."""
        try:
            cultural_region_enum = CulturalRegion(cultural_region)
            intelligence = self._get_cultural_intelligence(language, cultural_region_enum)
            
            return {
                "cultural_values": intelligence.get("cultural_values", []),
                "communication_style": intelligence.get("communication_style", ""),
                "trust_building": intelligence.get("trust_building", []),
                "currency_format": intelligence.get("currency_format", ""),
                "special_considerations": intelligence.get("special_considerations", []),
                "recommendations": [
                    f"Use {intelligence.get('greeting_style', 'professional')} greeting style",
                    f"Apply {intelligence.get('urgency_approach', 'balanced')} urgency approach",
                    f"Focus on {intelligence.get('social_proof_style', 'individual')} social proof"
                ]
            }
        except Exception as e:
            logger.error("Failed to get cultural insights", error=str(e))
            return {"error": f"Failed to get cultural insights: {str(e)}"}

    async def get_template_performance_analytics(
        self,
        template_id: Optional[int] = None,
        language: Optional[str] = None,
        cultural_region: Optional[str] = None,
        time_range_days: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance analytics for templates."""
        # Implementation for performance analytics
        pass

    async def optimize_template_performance(
        self,
        template_id: int,
        optimization_criteria: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Automatically optimize template performance."""
        # Implementation for automatic optimization
        pass 