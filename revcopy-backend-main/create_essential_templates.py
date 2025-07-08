#!/usr/bin/env python3
"""
Create Essential Prompt Templates

This script creates the essential prompt templates that the frontend actually requests.
These templates match the exact categories used by the frontend mapping.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import get_async_session
from app.models.prompts import PromptTemplate

async def create_essential_templates():
    """Create essential prompt templates for frontend integration."""
    
    # Essential templates that frontend actually requests
    essential_templates = [
        {
            "template_type": "product_description",
            "name": "Product Description Generator",
            "description": "Generate detailed product descriptions based on customer reviews and product data",
            "category": "product_description",
            "user_prompt_template": """Write a compelling product description for {product_name}:

**Product Information:**
{product_description}
Brand: {brand}
Price: {price}

**What customers love (from reviews):**
{positive_reviews}

**Address these concerns:**
{negative_reviews}

Create a description that:
1. Highlights key features and benefits
2. Uses customer feedback to build trust
3. Addresses common concerns
4. Includes clear value proposition
5. Is optimized for conversions

Write in a professional yet engaging tone.""",
            "system_prompt": "You are an expert product copywriter specializing in e-commerce descriptions that convert browsers into buyers.",
            "default_temperature": 0.7,
            "default_max_tokens": 1200,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "google_ad",
            "name": "Google Ad Generator",
            "description": "Create effective Google Ads with headlines and descriptions",
            "category": "google_ad",
            "user_prompt_template": """Create a Google Ad for {product_name}:

**Product:** {product_name} by {brand} - {price}
**Positive feedback:** {positive_reviews}
**Address concerns:** {negative_reviews}

Create:
1. **Headline** (30 characters max): Attention-grabbing, include key benefit
2. **Description** (90 characters max): Clear value prop, include price if competitive
3. **Call-to-Action**: Strong action word

Requirements:
- Highlight main customer benefits
- Include price if it's competitive  
- Address main customer concerns
- Use power words for urgency
- Comply with Google Ads policies

Format:
Headline: [Your headline]
Description: [Your description]
CTA: [Your call to action]""",
            "system_prompt": "You are a Google Ads expert who creates high-converting search ads that maximize click-through rates and conversions.",
            "default_temperature": 0.8,
            "default_max_tokens": 400,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "instagram_caption",
            "name": "Instagram Caption Generator", 
            "description": "Create engaging Instagram captions with hashtags and emojis",
            "category": "instagram_caption",
            "user_prompt_template": """Create an Instagram caption for {product_name}:

**Product:** {product_name} by {brand}
**Price:** {price}
**Product details:** {product_description}
**Customer love:** {positive_reviews}
**Address concerns:** {negative_reviews}

Create a caption that:
1. Starts with a hook or question
2. Highlights customer benefits from reviews
3. Uses appropriate emojis (3-5 max)
4. Includes 3-5 relevant hashtags
5. Mentions price if competitive
6. Ends with clear call-to-action
7. Keeps conversational and visual tone
8. Maximum 2200 characters

Write for Instagram's visual platform with engaging, authentic voice.""",
            "system_prompt": "You are a social media expert who creates viral Instagram content that drives engagement and sales.",
            "default_temperature": 0.9,
            "default_max_tokens": 800,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "blog_article",
            "name": "Blog Article Generator",
            "description": "Write comprehensive blog articles about products",
            "category": "blog_article", 
            "user_prompt_template": """Write a blog article about {product_name}:

**Product Information:**
Name: {product_name}
Brand: {brand}
Price: {price}
Description: {product_description}

**Customer Insights:**
Positive feedback: {positive_reviews}
Common concerns: {negative_reviews}

Create a comprehensive article with:

1. **Compelling headline** (60 chars max for SEO)
2. **Introduction** (hook readers with a problem/benefit)
3. **Product overview** (features and specifications)
4. **Customer experience** (based on reviews)
5. **Pros and cons** (honest assessment)
6. **Who it's best for** (target audience)
7. **Final verdict** (recommendation)
8. **Clear call-to-action**

Write in an informative yet engaging tone. Use customer reviews as social proof throughout the article.""",
            "system_prompt": "You are a professional content writer who creates in-depth, helpful blog articles that educate readers and drive conversions.",
            "default_temperature": 0.7,
            "default_max_tokens": 2000,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "product_comparison",
            "name": "Product Comparison Generator",
            "description": "Create detailed product comparisons highlighting competitive advantages",
            "category": "product_comparison",
            "user_prompt_template": """Create a product comparison analysis for {product_name}:

**Our Product:**
Name: {product_name}
Brand: {brand}
Price: {price}
Description: {product_description}

**Customer Feedback:**
Strengths: {positive_reviews}
Areas for improvement: {negative_reviews}

Create a comparison that covers:

1. **Overview** (product category and positioning)
2. **Key features comparison** (vs typical competitors)
3. **Price value analysis** (cost vs benefits)
4. **Customer satisfaction** (based on reviews)
5. **Unique advantages** (what sets it apart)
6. **Best use cases** (when to choose this product)
7. **Bottom line** (clear recommendation)

Be objective but highlight competitive advantages. Use customer reviews as evidence. Focus on value proposition.""",
            "system_prompt": "You are a product analyst who creates fair, detailed comparisons that help customers make informed purchasing decisions.",
            "default_temperature": 0.6,
            "default_max_tokens": 1500,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "faq",
            "name": "FAQ Generator",
            "description": "Generate frequently asked questions based on customer reviews",
            "category": "faq",
            "user_prompt_template": """Create FAQ for {product_name}:

**Product:** {product_name} by {brand} - {price}
**Description:** {product_description}
**Customer praise:** {positive_reviews}
**Customer concerns:** {negative_reviews}

Generate 8-10 FAQ pairs covering:

1. **Product basics** (what it is, who it's for)
2. **Key features** (based on customer highlights)
3. **Common concerns** (from negative reviews)
4. **Usage and setup** (how to use effectively)
5. **Pricing and value** (cost justification)
6. **Shipping and returns** (if applicable)
7. **Compatibility** (technical questions)
8. **Warranty/support** (after-purchase concerns)

Format each as:
**Q: [Question]**
A: [Detailed, helpful answer]

Base questions on real customer concerns from reviews. Provide comprehensive, honest answers.""",
            "system_prompt": "You are a customer service expert who creates helpful FAQs that address real customer concerns and reduce support tickets.",
            "default_temperature": 0.5,
            "default_max_tokens": 1800,
            "is_active": True,
            "created_by": "system"
        },
        {
            "template_type": "email_campaign",
            "name": "Email Campaign Generator",
            "description": "Create engaging email campaigns with social proof",
            "category": "email_campaign",
            "user_prompt_template": """Create an email campaign for {product_name}:

**Product Details:**
Name: {product_name}
Brand: {brand}
Price: {price}
Description: {product_description}

**Social Proof:**
Customer love: {positive_reviews}
Address objections: {negative_reviews}

Create an email with:

1. **Subject line** (50 characters max, compelling)
2. **Personal greeting** (warm, friendly)
3. **Hook** (problem/benefit that resonates) 
4. **Product introduction** (brief, benefit-focused)
5. **Social proof** (customer reviews/testimonials)
6. **Address objections** (handle common concerns)
7. **Special offer** (create urgency if appropriate)
8. **Clear CTA** (strong action button)
9. **P.S.** (additional incentive or urgency)

Tone: Personal, friendly, trustworthy
Goal: Drive clicks and conversions
Include pricing strategy if competitive.""",
            "system_prompt": "You are an email marketing expert who creates high-converting campaigns that build relationships and drive sales.",
            "default_temperature": 0.8,
            "default_max_tokens": 1600,
            "is_active": True,
            "created_by": "system"
        }
    ]
    
    async for session in get_async_session():
        try:
            # Check which templates already exist
            existing_templates = {}
            for template_data in essential_templates:
                result = await session.execute(
                    select(PromptTemplate).where(
                        PromptTemplate.template_type == template_data["template_type"]
                    )
                )
                existing = result.scalars().first()
                if existing:
                    existing_templates[template_data["template_type"]] = existing
                    print(f"✅ Template {template_data['template_type']} already exists (ID: {existing.id})")
                
            # Create missing templates
            created_count = 0
            for template_data in essential_templates:
                if template_data["template_type"] not in existing_templates:
                    template = PromptTemplate(**template_data)
                    session.add(template)
                    created_count += 1
                    print(f"➕ Creating template: {template_data['template_type']}")
            
            if created_count > 0:
                await session.commit()
                print(f"\n🎉 Successfully created {created_count} new essential templates!")
            else:
                print(f"\n✨ All essential templates already exist!")
                
            # Show summary
            result = await session.execute(select(PromptTemplate))
            all_templates = result.scalars().all()
            print(f"\nTotal templates in database: {len(all_templates)}")
            
            print("\nCurrent templates by category:")
            categories = {}
            for template in all_templates:
                cat = template.template_type
                if cat in categories:
                    categories[cat] += 1
                else:
                    categories[cat] = 1
            
            for cat, count in sorted(categories.items()):
                print(f"  {cat}: {count}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating templates: {e}")
            raise
            
        finally:
            await session.close()

if __name__ == "__main__":
    print("🚀 Creating essential prompt templates...")
    asyncio.run(create_essential_templates())
    print("✅ Done!") 