#!/usr/bin/env python3
"""
Create a realistic Facebook ad template that uses actual product reviews 
to generate compelling, personalized content instead of generic templates.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_session, create_async_engine_instance
from app.models.prompts import PromptTemplate


async def create_realistic_facebook_template():
    """Create a Facebook ad template that uses actual review insights."""
    
    print("🎯 Creating realistic Facebook ad template...")
    
    # System prompt for Facebook ads
    system_prompt = """You are an expert Facebook Ads copywriter who creates compelling, scroll-stopping ad copy that converts.

Your specialty is analyzing real customer reviews to extract powerful selling points and create authentic social proof.

FACEBOOK AD REQUIREMENTS:
- Maximum 125 characters total
- Use emotional triggers and benefits-focused language
- Include compelling call-to-action
- Use emojis strategically for visual appeal
- Focus on customer benefits from real reviews
- Create urgency and desire

TONE: Friendly, authentic, engaging
GOAL: Drive clicks and conversions by using real customer voices"""

    # User prompt template that uses real review data
    user_prompt = """Create a compelling Facebook ad for {product_name}.

PRODUCT DETAILS:
- Product: {product_name}
- Brand: {brand}
- Price: {price}
- Average Rating: {average_rating}/5 stars ({total_reviews} reviews)

REAL CUSTOMER INSIGHTS FROM REVIEWS:
Positive highlights that customers love:
{positive_reviews}

Concerns customers mentioned:
{negative_reviews}

REQUIREMENTS:
1. Start with an attention-grabbing hook
2. Use the actual customer praise from the positive reviews above
3. Address any concerns naturally if relevant
4. Include star rating as social proof
5. End with a strong call-to-action
6. Keep under 125 characters total
7. Use friendly tone with strategic emojis
8. Make it feel authentic, not salesy

Focus on what real customers actually said they love about this product. Use their words and sentiments to create desire."""

    engine = await create_async_engine_instance()
    async with AsyncSession(engine) as session:
        # Check if template already exists
        existing_template = await session.execute(
            select(PromptTemplate.id).where(
                PromptTemplate.template_type == 'facebook_ad',
                PromptTemplate.name == 'Realistic Facebook Ad (Review-Based)'
            )
        )
        existing = existing_template.fetchone()
        
        if existing:
            print(f"✅ Realistic Facebook ad template already exists (ID: {existing[0]})")
            return

        # Create the new template
        template = PromptTemplate(
            template_type="facebook_ad",
            name="Realistic Facebook Ad (Review-Based)",
            description="Facebook ad template that uses actual customer reviews to create compelling, authentic content",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt,
            
            # Configuration
            primary_language="en",
            supported_languages=["en", "he"],
            cultural_regions=["north_america", "middle_east"],
            tone="friendly",
            urgency_level="medium",
            
            # Template settings
            default_temperature=0.7,
            default_max_tokens=150,  # Short Facebook ad
            is_active=True,
            is_default=True,  # Make this the default Facebook template
            
            # Required variables
            required_variables=[
                "product_name", "brand", "price", "average_rating", 
                "total_reviews", "positive_reviews", "negative_reviews"
            ],
            optional_variables=["currency", "category"],
            
            # Quality guidelines
            content_guidelines={
                "max_length": 125,
                "tone": "friendly",
                "use_emojis": True,
                "include_cta": True,
                "use_social_proof": True
            },
            
            created_by="system"
        )
        
        session.add(template)
        await session.commit()
        await session.refresh(template)
        
        print(f"✅ Created realistic Facebook ad template (ID: {template.id})")


async def main():
    """Main function."""
    try:
        await create_realistic_facebook_template()
        print("🎉 Successfully created realistic Facebook ad template!")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 