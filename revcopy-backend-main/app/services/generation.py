"""
Generation service for AI-powered content creation.
"""

from typing import Dict, List, Optional
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import GeneratedContent, ContentStatus, ContentType
from app.models.analysis import Analysis

# Configure logging
logger = structlog.get_logger(__name__)


class GenerationService:
    """Service for AI-powered content generation."""
    
    async def generate_content(
        self,
        analysis: Analysis,
        content_type: ContentType,
        generation_params: Dict,
        db: AsyncSession
    ) -> GeneratedContent:
        """Generate marketing content from analysis."""
        try:
            logger.info(
                "Generating content",
                analysis_id=analysis.id,
                content_type=content_type.value
            )
            
            # Create content record
            content = GeneratedContent(
                analysis_id=analysis.id,
                content_type=content_type,
                tone=generation_params.get("tone", "professional"),
                target_audience=generation_params.get("target_audience"),
                platform=generation_params.get("platform"),
                status=ContentStatus.PENDING,
                generation_parameters=generation_params,
            )
            
            db.add(content)
            await db.commit()
            await db.refresh(content)
            
            # Generate content based on type
            await self._generate_content_by_type(content, analysis, db)
            
            logger.info("Content generated", content_id=content.id)
            return content
            
        except Exception as e:
            logger.error("Content generation failed", error=str(e))
            raise
    
    async def _generate_content_by_type(
        self,
        content: GeneratedContent,
        analysis: Analysis,
        db: AsyncSession
    ) -> None:
        """Generate content based on content type."""
        try:
            content.status = ContentStatus.GENERATING
            content.generation_started_at = datetime.utcnow()
            await db.commit()
            
            # Mock content generation based on type
            content_templates = {
                ContentType.FACEBOOK_AD: self._generate_facebook_ad,
                ContentType.GOOGLE_AD: self._generate_google_ad,
                ContentType.INSTAGRAM_CAPTION: self._generate_instagram_caption,
                ContentType.PRODUCT_DESCRIPTION: self._generate_product_description,
                ContentType.EMAIL_NEWSLETTER: self._generate_email_newsletter,
                ContentType.BLOG_ARTICLE: self._generate_blog_article,
            }
            
            generator = content_templates.get(content.content_type)
            if generator:
                generated_text = generator(analysis, content)
            else:
                generated_text = f"Generated {content.content_type.value} content based on customer insights."
            
            content.generated_text = generated_text
            content.word_count = len(generated_text.split())
            content.status = ContentStatus.COMPLETED
            content.generation_completed_at = datetime.utcnow()
            content.quality_score = 0.85
            
            await db.commit()
            
        except Exception as e:
            content.status = ContentStatus.FAILED
            content.error_message = str(e)
            await db.commit()
            raise
    
    def _generate_facebook_ad(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate Facebook ad content."""
        insights = analysis.key_insights or []
        benefits = analysis.benefits or []
        
        return f"""🚀 Transform Your Experience with This Amazing Product!

Based on {analysis.total_reviews_processed}+ customer reviews:

✅ {insights[0] if insights else "Outstanding quality"}
✅ {benefits[0] if benefits else "Excellent value"}
✅ {analysis.overall_sentiment.value.title() if analysis.overall_sentiment else "Positive"} customer feedback

Join thousands of satisfied customers!

#QualityMatters #CustomerApproved #MustHave"""
    
    def _generate_google_ad(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate Google ad content."""
        return f"""Premium Quality Product - {analysis.total_reviews_processed}+ Reviews
{analysis.overall_sentiment.value.title() if analysis.overall_sentiment else "Positive"} customer feedback. Experience the difference today.
Free shipping • 30-day returns • Verified reviews"""
    
    def _generate_instagram_caption(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate Instagram caption."""
        insights = analysis.key_insights or []
        
        return f"""When customers say "{insights[0] if insights else "this exceeded my expectations"}" 😍

You know youve found something special ✨

Based on {analysis.total_reviews_processed}+ real reviews from happy customers!

Ready to see what all the excitement is about? 

#CustomerLove #QualityFirst #MustHave #ProductReviews"""
    
    def _generate_product_description(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate product description."""
        benefits = analysis.benefits or []
        insights = analysis.key_insights or []
        
        return f"""Premium Product Description

Key Features:
- {benefits[0] if benefits else "High-quality construction"}
- {benefits[1] if len(benefits) > 1 else "User-friendly design"}
- {insights[0] if insights else "Outstanding performance"}

Customer Feedback:
Based on {analysis.total_reviews_processed}+ verified reviews, customers consistently praise this product for its quality and value.

{analysis.overall_sentiment.value.title() if analysis.overall_sentiment else "Positive"} customer satisfaction rating ensures youre making a smart choice."""
    
    def _generate_email_newsletter(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate email newsletter content."""
        return f"""Subject: Discover Why Customers Love This Product

Hi there!

Weve analyzed {analysis.total_reviews_processed}+ customer reviews to bring you the inside scoop on this amazing product.

What customers are saying:
- "{analysis.key_insights[0] if analysis.key_insights else "Best purchase Ive made"}"
- "{analysis.benefits[0] if analysis.benefits else "Excellent quality and value"}"

With {analysis.overall_sentiment.value if analysis.overall_sentiment else "positive"} customer feedback, this product is quickly becoming a customer favorite.

Ready to experience it yourself?

Best regards,
The Team"""
    
    def _generate_blog_article(self, analysis: Analysis, content: GeneratedContent) -> str:
        """Generate blog article content."""
        return f"""# Customer Review Analysis: What {analysis.total_reviews_processed}+ Buyers Really Think

## Overview

Weve analyzed hundreds of customer reviews to give you an unbiased look at this popular product.

## Key Findings

### What Customers Love
{chr(10).join([f"- {benefit}" for benefit in (analysis.benefits or [])[:3]])}

### Areas for Improvement
{chr(10).join([f"- {pain}" for pain in (analysis.pain_points or [])[:2]])}

## Customer Sentiment
Overall sentiment: {analysis.overall_sentiment.value.title() if analysis.overall_sentiment else "Positive"}

## Conclusion
Based on our analysis of {analysis.total_reviews_processed} customer reviews, this product delivers on its promises and provides excellent value for customers."""

