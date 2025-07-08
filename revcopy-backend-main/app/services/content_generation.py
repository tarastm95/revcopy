"""
Content Generation Service.
Integrates AI models with product analysis for intelligent content creation.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.prompts import PromptTemplate, AIContentGeneration, ContentGenerationStats
from app.schemas.prompts import ContentGenerationRequest, ContentGenerationResponse
from app.services.ai import ai_service
from app.services.product import ProductService
from app.services.review_scraping import ReviewScrapingService

logger = structlog.get_logger(__name__)


class ContentGenerationService:
    """Service for generating intelligent content based on product analysis."""
    
    def __init__(self):
        self.product_service = ProductService()
        self.review_service = ReviewScrapingService()
        self.ai_service = ai_service
    
    async def generate_content(
        self,
        db: AsyncSession,
        request: ContentGenerationRequest,
        user_id: Optional[str] = None
    ) -> ContentGenerationResponse:
        """
        Generate intelligent content based on product analysis.
        
        Args:
            db: Database session
            request: Content generation request
            user_id: User ID for tracking
            
        Returns:
            Content generation response
        """
        start_time = time.time()
        generation_record = None
        
        try:
            logger.info(
                "Starting content generation",
                product_url=request.product_url,
                template_type=request.template_type,
                ai_provider=request.ai_provider
            )
            
            # Create generation record
            generation_record = AIContentGeneration(
                template_type=request.template_type,
                ai_provider=request.ai_provider,
                product_url=request.product_url,
                session_id=user_id
            )
            db.add(generation_record)
            await db.commit()
            await db.refresh(generation_record)
            
            # Get or load prompt template
            template = await self._get_prompt_template(db, request)
            if template:
                generation_record.template_id = template.id
            
            # Extract product data and reviews
            product_data, reviews_data = await self._extract_product_and_reviews(request.product_url)
            
            # Update generation record with input data
            generation_record.product_data = product_data
            generation_record.reviews_analyzed = len(reviews_data)
            generation_record.input_parameters = request.custom_variables
            generation_record.temperature = str(request.temperature or template.default_temperature if template else settings.AI_TEMPERATURE)
            generation_record.max_tokens = request.max_tokens or (template.default_max_tokens if template else settings.AI_MAX_TOKENS)
            
            # Generate content using AI service
            result = await self._generate_with_ai(
                template=template,
                product_data=product_data,
                reviews_data=reviews_data,
                request=request
            )
            
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # Update generation record with results
            generation_record.generated_content = result["content"]
            generation_record.content_metadata = result
            generation_record.generation_time_ms = generation_time_ms
            generation_record.success = True
            
            # Update template usage statistics
            if template:
                await self._update_template_stats(db, template.id, success=True)
            
            await db.commit()
            
            # Create response
            response = ContentGenerationResponse(
                id=generation_record.id,
                success=True,
                generated_content=result["content"],
                template_type=request.template_type,
                ai_provider=request.ai_provider,
                generation_time_ms=generation_time_ms,
                content_metadata=result,
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                product_data=product_data,
                reviews_analyzed=len(reviews_data),
                created_at=generation_record.created_at
            )
            
            logger.info(
                "Content generation completed successfully",
                generation_id=generation_record.id,
                generation_time_ms=generation_time_ms,
                content_length=len(result["content"]) if result["content"] else 0
            )
            
            # Update daily statistics
            await self._update_daily_stats(db, request.template_type, request.ai_provider, success=True)
            
            return response
            
        except Exception as e:
            logger.error("Content generation failed", error=str(e), product_url=request.product_url)
            
            # Update generation record with error
            if generation_record:
                generation_record.success = False
                generation_record.error_message = str(e)
                generation_record.generation_time_ms = int((time.time() - start_time) * 1000)
                await db.commit()
                
                # Update template stats
                if hasattr(generation_record, 'template_id') and generation_record.template_id:
                    await self._update_template_stats(db, generation_record.template_id, success=False)
            
            # Update daily statistics
            await self._update_daily_stats(db, request.template_type, request.ai_provider, success=False)
            
            return ContentGenerationResponse(
                id=generation_record.id if generation_record else 0,
                success=False,
                generated_content=None,
                template_type=request.template_type,
                ai_provider=request.ai_provider,
                error_message=str(e),
                created_at=datetime.utcnow()
            )
    
    async def _get_prompt_template(
        self,
        db: AsyncSession,
        request: ContentGenerationRequest
    ) -> Optional[PromptTemplate]:
        """Get prompt template for the request."""
        try:
            if request.template_id:
                # Get specific template by ID
                result = await db.execute(
                    select(PromptTemplate).where(
                        PromptTemplate.id == request.template_id,
                        PromptTemplate.is_active == True
                    )
                )
                return result.scalar_one_or_none()
            else:
                # Get default template for type
                result = await db.execute(
                    select(PromptTemplate).where(
                        PromptTemplate.template_type == request.template_type,
                        PromptTemplate.is_active == True,
                        PromptTemplate.is_default == True
                    )
                )
                template = result.scalar_one_or_none()
                
                if not template:
                    # Get any active template for type
                    result = await db.execute(
                        select(PromptTemplate).where(
                            PromptTemplate.template_type == request.template_type,
                            PromptTemplate.is_active == True
                        ).limit(1)
                    )
                    template = result.scalar_one_or_none()
                
                return template
                
        except Exception as e:
            logger.error("Failed to get prompt template", error=str(e))
            return None
    
    async def _extract_product_and_reviews(self, product_url: str) -> Tuple[Dict, List[Dict]]:
        """Extract product data and reviews from URL."""
        try:
            # Extract product information
            product_data = await self.product_service.extract_product(product_url)
            
            # Extract reviews
            reviews_data = []
            if product_data:
                reviews_result = await self.review_service.scrape_reviews(
                    product_url, 
                    max_reviews=settings.MAX_REVIEWS_FOR_ANALYSIS
                )
                reviews_data = reviews_result.get("reviews", [])
            
            return product_data, reviews_data
            
        except Exception as e:
            logger.error("Failed to extract product and reviews", error=str(e), url=product_url)
            return {}, []
    
    async def _generate_with_ai(
        self,
        template: Optional[PromptTemplate],
        product_data: Dict,
        reviews_data: List[Dict],
        request: ContentGenerationRequest
    ) -> Dict[str, Any]:
        """Generate content using AI service."""
        try:
            # If we have a custom template, use it
            if template:
                # Use template's AI generation logic
                result = await self._generate_with_template(
                    template, product_data, reviews_data, request
                )
            else:
                # Use default AI service
                result = await self.ai_service.generate_product_description(
                    product_data=product_data,
                    reviews_data=reviews_data,
                    template_type=request.template_type,
                    provider=request.ai_provider
                )
            
            return result
            
        except Exception as e:
            logger.error("AI generation failed", error=str(e))
            raise
    
    async def _generate_with_template(
        self,
        template: PromptTemplate,
        product_data: Dict,
        reviews_data: List[Dict],
        request: ContentGenerationRequest
    ) -> Dict[str, Any]:
        """Generate content using a specific template."""
        try:
            # Prepare template variables
            variables = await self._prepare_template_variables(
                product_data, reviews_data, request.custom_variables
            )
            
            # Format the prompt
            formatted_prompt = template.user_prompt_template.format(**variables)
            
            # Get AI provider
            provider_name = request.ai_provider
            if provider_name not in self.ai_service.providers:
                provider_name = list(self.ai_service.providers.keys())[0]
            
            provider = self.ai_service.providers[provider_name]
            
            # Generate content
            temperature = request.temperature or float(template.default_temperature)
            max_tokens = request.max_tokens or template.default_max_tokens
            
            generated_content = await provider.generate_content(
                prompt=formatted_prompt,
                system_prompt=template.system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Analyze reviews for metadata
            strengths, weaknesses = await self.ai_service._analyze_reviews(reviews_data)
            
            return {
                "content": generated_content,
                "provider": provider_name,
                "template_type": template.template_type,
                "template_id": template.id,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "generated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "total_reviews": len(reviews_data),
                    "positive_reviews": len([r for r in reviews_data if r.get("rating", 0) >= 4]),
                    "negative_reviews": len([r for r in reviews_data if r.get("rating", 0) <= 2]),
                    "average_rating": sum(r.get("rating", 0) for r in reviews_data) / len(reviews_data) if reviews_data else 0,
                    "template_variables": variables
                }
            }
            
        except Exception as e:
            logger.error("Template-based generation failed", error=str(e))
            raise
    
    async def _prepare_template_variables(
        self,
        product_data: Dict,
        reviews_data: List[Dict],
        custom_variables: Dict
    ) -> Dict[str, Any]:
        """Prepare variables for template formatting."""
        try:
            # Analyze reviews
            strengths, weaknesses = await self.ai_service._analyze_reviews(reviews_data)
            
            # Calculate statistics
            positive_count = len([r for r in reviews_data if r.get("rating", 0) >= 4])
            negative_count = len([r for r in reviews_data if r.get("rating", 0) <= 2])
            avg_rating = sum(r.get("rating", 0) for r in reviews_data) / len(reviews_data) if reviews_data else 0
            
            # Prepare base variables
            variables = {
                "product_name": product_data.get("title", "Product"),
                "brand": product_data.get("brand", "Brand"),
                "price": f"{product_data.get('currency', '$')}{product_data.get('price', 0)}",
                "category": product_data.get("category", "Product"),
                "description": product_data.get("description", ""),
                "strengths": "\n".join([f"• {s}" for s in strengths]) if strengths else "• High customer satisfaction",
                "weaknesses": "\n".join([f"• {w}" for w in weaknesses]) if weaknesses else "• No significant concerns reported",
                "total_reviews": len(reviews_data),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "average_rating": round(avg_rating, 1),
                "rating_stars": "★" * int(avg_rating) + "☆" * (5 - int(avg_rating)),
                "review_summary": f"{len(reviews_data)} customer reviews with {round(avg_rating, 1)}/5 average rating"
            }
            
            # Add custom variables
            variables.update(custom_variables)
            
            return variables
            
        except Exception as e:
            logger.error("Failed to prepare template variables", error=str(e))
            return {}
    
    async def _update_template_stats(self, db: AsyncSession, template_id: int, success: bool):
        """Update template usage statistics."""
        try:
            result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            
            if template:
                template.usage_count += 1
                
                # Update success rate
                if success:
                    current_rate = float(template.success_rate)
                    new_rate = ((current_rate * (template.usage_count - 1)) + 100) / template.usage_count
                    template.success_rate = str(round(new_rate, 2))
                else:
                    current_rate = float(template.success_rate)
                    new_rate = (current_rate * (template.usage_count - 1)) / template.usage_count
                    template.success_rate = str(round(new_rate, 2))
                
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to update template stats", error=str(e))
    
    async def _update_daily_stats(
        self,
        db: AsyncSession,
        template_type: str,
        ai_provider: str,
        success: bool
    ):
        """Update daily generation statistics."""
        try:
            today = datetime.utcnow().date()
            
            # Get or create today's stats
            result = await db.execute(
                select(ContentGenerationStats).where(
                    ContentGenerationStats.date >= today,
                    ContentGenerationStats.date < today + timedelta(days=1),
                    ContentGenerationStats.period_type == "daily"
                )
            )
            stats = result.scalar_one_or_none()
            
            if not stats:
                stats = ContentGenerationStats(
                    date=datetime.combine(today, datetime.min.time()),
                    period_type="daily"
                )
                db.add(stats)
            
            # Update statistics
            stats.total_generations += 1
            if success:
                stats.successful_generations += 1
            else:
                stats.failed_generations += 1
            
            # Update provider stats
            if ai_provider == "openai":
                stats.openai_usage += 1
            elif ai_provider == "deepseek":
                stats.deepseek_usage += 1
            
            # Update content type stats
            if template_type == "product_description":
                stats.product_descriptions += 1
            elif template_type == "faq":
                stats.faqs_generated += 1
            elif template_type == "comparison":
                stats.comparisons_generated += 1
            
            await db.commit()
            
        except Exception as e:
            logger.error("Failed to update daily stats", error=str(e))
    
    async def get_generation_history(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get content generation history."""
        try:
            query = select(AIContentGeneration).order_by(AIContentGeneration.created_at.desc()).limit(limit)
            
            if user_id:
                query = query.where(AIContentGeneration.session_id == user_id)
            
            result = await db.execute(query)
            generations = result.scalars().all()
            
            return [
                {
                    "id": gen.id,
                    "template_type": gen.template_type,
                    "ai_provider": gen.ai_provider,
                    "product_url": gen.product_url,
                    "success": gen.success,
                    "reviews_analyzed": gen.reviews_analyzed,
                    "generation_time_ms": gen.generation_time_ms,
                    "created_at": gen.created_at,
                    "error_message": gen.error_message
                }
                for gen in generations
            ]
            
        except Exception as e:
            logger.error("Failed to get generation history", error=str(e))
            return []
    
    async def provide_feedback(
        self,
        db: AsyncSession,
        generation_id: int,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Provide feedback for generated content."""
        try:
            result = await db.execute(
                select(AIContentGeneration).where(AIContentGeneration.id == generation_id)
            )
            generation = result.scalar_one_or_none()
            
            if generation:
                generation.user_rating = rating
                generation.user_feedback = feedback
                await db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to provide feedback", error=str(e))
            return False 