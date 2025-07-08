#!/usr/bin/env python3
"""
Seed script for default prompt templates.
Run this after database migration to populate with initial templates.
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.prompts import PromptTemplate


async def create_default_templates():
    """Create default prompt templates."""
    
    # Create async engine with constructed database URL
    db_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    default_templates = [
        {
            "template_type": "product_description",
            "name": "Smart & Balanced Product Description",
            "description": "Template for creating smart and balanced product descriptions based on customer review strengths and weaknesses",
            "system_prompt": """You are an expert copywriter specializing in product descriptions for e-commerce websites. Your goal is to create compelling, honest, and professional content that builds trust with potential customers.

Writing principles:
1. Use clear and simple language
2. Be honest about product weaknesses
3. Highlight strengths based on real customer reviews
4. Include calculated social proof
5. Create healthy urgency
6. Focus on customer benefits""",
            "user_prompt_template": """Create a professional and compelling product description for:

**Product Details:**
Product Name: {product_name}
Brand: {brand}
Price: {price}
Category: {category}

**Strengths (based on {total_reviews} customer reviews):**
{strengths}

**Areas for Improvement (constructive customer feedback):**
{weaknesses}

**Review Statistics:**
- Average rating: {average_rating}/5 stars
- Positive reviews: {positive_count}
- Critical reviews: {negative_count}

**Writing Guidelines:**
1. Start with an engaging headline highlighting the main benefit
2. Open with a sentence that immediately explains why the product is special
3. Highlight main strengths based on customer evidence
4. Honestly address improvement points and provide solutions or context
5. Include social proof (number of customers, average rating)
6. End with a compelling but not pushy call to action

**Desired Structure:**
- Engaging headline (up to 60 characters)
- Opening paragraph (2-3 sentences)
- Main strengths (3-4 points)
- Addressing weaknesses (1-2 points)
- Social proof
- Call to action

Write in English, use a warm and professional tone, and be honest and trustworthy.""",
            "default_temperature": 0.7,
            "default_max_tokens": 2000,
            "supported_providers": ["deepseek", "openai"],
            "required_variables": ["product_name", "brand", "price", "category", "strengths", "weaknesses", "total_reviews", "average_rating", "positive_count", "negative_count"],
            "optional_variables": ["description"],
            "is_active": True,
            "is_default": True,
            "version": "1.0",
            "created_by": "system"
        },
        {
            "template_type": "faq",
            "name": "Review-Based FAQ Generator",
            "description": "Creating frequently asked questions based on real concerns and questions from customer reviews",
            "system_prompt": """You are an expert in customer service and creating helpful FAQ content. Your goal is to create questions and answers based on real customer concerns that appear in reviews.""",
            "user_prompt_template": """Create a frequently asked questions (FAQ) list for the product:

**Product Details:**
{product_name} by {brand}

**Strengths that customers highlight:**
{strengths}

**Concerns and questions raised in reviews:**
{weaknesses}

**Review Data:**
- {total_reviews} reviews, average rating {average_rating}/5

Create 8-10 frequently asked questions with detailed answers based on:
1. The main strengths of the product
2. Concerns and questions from reviews
3. Common technical questions
4. Questions about shipping and returns

Write in English with a helpful and professional tone.""",
            "default_temperature": 0.6,
            "default_max_tokens": 1500,
            "supported_providers": ["deepseek", "openai"],
            "required_variables": ["product_name", "brand", "strengths", "weaknesses", "total_reviews", "average_rating"],
            "optional_variables": [],
            "is_active": True,
            "is_default": True,
            "version": "1.0",
            "created_by": "system"
        },
        {
            "template_type": "comparison",
            "name": "Competitive Product Comparison",
            "description": "Creating comparisons that highlight competitive advantages based on customer feedback",
            "system_prompt": """You are a product analyst expert in creating fair and compelling competitive comparisons. The goal is to present the product in a positive light while maintaining credibility.""",
            "user_prompt_template": """Create a competitive comparison for:

**Our Product:**
{product_name} by {brand} at {price}

**Competitive Advantages (based on reviews):**
{strengths}

**Potential Improvement Points:**
{weaknesses}

**Performance:**
Customer rating: {average_rating}/5 ({total_reviews} reviews)

Create a comparison focusing on:
1. Unique advantages of the product vs competitors
2. Value for money
3. Customer satisfaction
4. Key differentiation points

Write in English with a professional and objective tone.""",
            "default_temperature": 0.7,
            "default_max_tokens": 1200,
            "supported_providers": ["deepseek", "openai"],
            "required_variables": ["product_name", "brand", "price", "strengths", "weaknesses", "average_rating", "total_reviews"],
            "optional_variables": [],
            "is_active": True,
            "is_default": True,
            "version": "1.0",
            "created_by": "system"
        },
        {
            "template_type": "product_features",
            "name": "Review-Based Feature List",
            "description": "Highlighting product features based on what customers actually appreciate",
            "system_prompt": """You are an expert in highlighting product features in a way that speaks directly to customer needs.""",
            "user_prompt_template": """Create a core features list for {product_name}:

**Features customers especially appreciate:**
{strengths}

**Features that need clarification:**
{weaknesses}

**Data:**
{total_reviews} reviews, rating {average_rating}/5

Create a structured feature list with:
1. Main features (based on customer praise)
2. Important technical specifications
3. Clarifications for features customers ask about

Write in English in a clean and clear list style.""",
            "default_temperature": 0.5,
            "default_max_tokens": 1000,
            "supported_providers": ["deepseek", "openai"],
            "required_variables": ["product_name", "strengths", "weaknesses", "total_reviews", "average_rating"],
            "optional_variables": [],
            "is_active": True,
            "is_default": True,
            "version": "1.0",
            "created_by": "system"
        },
        {
            "template_type": "email_campaign",
            "name": "Review-Based Email Campaign",
            "description": "Creating email campaign content based on social proof from reviews",
            "system_prompt": """You are an expert in digital marketing and creating email content that drives action. Use social proof to build trust and healthy urgency.""",
            "user_prompt_template": """Create email campaign content for {product_name}:

**Product:** {product_name} by {brand} - {price}
**Performance:** {average_rating}/5 stars ({total_reviews} reviews)

**What customers love:**
{strengths}

**Concerns addressed:**
{weaknesses}

Create an email including:
1. Engaging subject line (up to 50 characters)
2. Personal and friendly opening
3. Highlighting benefits based on reviews
4. Strong social proof
5. Addressing objections
6. Clear call to action
7. Healthy sense of urgency

Write in English with a warm and personal tone.""",
            "default_temperature": 0.8,
            "default_max_tokens": 1800,
            "supported_providers": ["deepseek", "openai"],
            "required_variables": ["product_name", "brand", "price", "average_rating", "total_reviews", "strengths", "weaknesses"],
            "optional_variables": [],
            "is_active": True,
            "is_default": True,
            "version": "1.0",
            "created_by": "system"
        }
    ]
    
    async with async_session() as session:
        try:
            for template_data in default_templates:
                print(f"Creating template: {template_data['name']}")
                template = PromptTemplate(**template_data)
                session.add(template)
            
            await session.commit()
            print(f"\n✅ Successfully created {len(default_templates)} default templates!")
            
        except Exception as e:
            print(f"❌ Error creating templates: {e}")
            await session.rollback()
            sys.exit(1)
        finally:
            await session.close()
    
    await engine.dispose()


if __name__ == "__main__":
    print("🚀 Creating default prompt templates...")
    asyncio.run(create_default_templates())
    print("🎉 Seeding completed!") 