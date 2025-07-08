#!/usr/bin/env python3
"""
Test the complete workflow: URL scraping → Review analysis → Content generation
This demonstrates the system working with actual product reviews.
"""

import asyncio
import json
from app.services.product import ProductService
from app.services.ai import AIService


async def test_complete_workflow():
    """Test the complete workflow from URL to generated content."""
    
    print("🧪 Testing Complete Workflow")
    print("=" * 50)
    
    # Test product URL (Shopify store)
    test_url = "https://kyliecosmetics.com/products/matte-lip-kit"
    
    print(f"📦 Testing with product URL: {test_url}")
    
    # Step 1: Product analysis and review scraping
    print("\n🔍 Step 1: Analyzing product and scraping reviews...")
    product_service = ProductService()
    
    try:
        product_data = await product_service.analyze_product_comprehensive(
            url=test_url,
            user_id=1
        )
        
        if product_data:
            product_info = product_data.get('product_data', product_data)
            print(f"✅ Product found: {product_info.get('title', 'Unknown')}")
            print(f"📊 Reviews scraped: {len(product_data.get('reviews', []))}")
            
            # Show sample reviews
            reviews = product_data.get('reviews', [])
            if reviews:
                print("\n📝 Sample reviews:")
                for i, review in enumerate(reviews[:3]):
                    rating = review.get('rating', 0)
                    content = review.get('content', '')[:100]
                    print(f"  {i+1}. Rating: {rating}/5 - {content}...")
        else:
            print("❌ No product data found - using mock data")
            product_data = {
                'product': {
                    'title': 'Kylie Cosmetics Matte Lip Kit',
                    'brand': 'Kylie Cosmetics',
                    'price': 27.0,
                    'currency': 'USD',
                    'rating': 4.2,
                    'review_count': 1234
                },
                'reviews': [
                    {'rating': 5, 'content': 'The color is absolutely stunning and stays on all day'},
                    {'rating': 5, 'content': 'Love the matte finish, very comfortable to wear'},
                    {'rating': 4, 'content': 'Good quality but takes time to dry completely'},
                    {'rating': 2, 'content': 'The color was not what I expected from the website'},
                    {'rating': 1, 'content': 'Very drying on my lips, had to remove it after 2 hours'}
                ]
            }
    except Exception as e:
        print(f"⚠️ Product analysis failed: {e}")
        print("Using mock data for demonstration...")
        product_data = {
            'product': {
                'title': 'Kylie Cosmetics Matte Lip Kit',
                'brand': 'Kylie Cosmetics', 
                'price': 27.0,
                'currency': 'USD',
                'rating': 4.2,
                'review_count': 1234
            },
            'reviews': [
                {'rating': 5, 'content': 'The color is absolutely stunning and stays on all day'},
                {'rating': 5, 'content': 'Love the matte finish, very comfortable to wear'},
                {'rating': 4, 'content': 'Good quality but takes time to dry completely'},
                {'rating': 2, 'content': 'The color was not what I expected from the website'},
                {'rating': 1, 'content': 'Very drying on my lips, had to remove it after 2 hours'}
            ]
        }
    
    # Step 2: Test AI content generation with review data
    print("\n🤖 Step 2: Generating content with AI...")
    
    ai_service = AIService()
    
    # Extract review insights
    reviews = product_data.get('reviews', [])
    positive_reviews = [r['content'] for r in reviews if r.get('rating', 0) >= 4]
    negative_reviews = [r['content'] for r in reviews if r.get('rating', 0) <= 2]
    
    # Get product info from the right place
    product_info = product_data.get('product_data', product_data.get('product', {}))
    
    # Test the new template with actual review data
    test_prompt = f"""Create a compelling Facebook ad for {product_info.get('title', 'Product')}.

PRODUCT DETAILS:
- Product: {product_info.get('title', 'Product')}
- Brand: {product_info.get('brand', 'Brand')}
- Price: ${product_info.get('price', 0)}
- Average Rating: {product_info.get('rating', 4.5)}/5 stars ({len(reviews)} reviews)

REAL CUSTOMER INSIGHTS FROM REVIEWS:
Positive highlights that customers love:
{chr(10).join([f'- "{review}"' for review in positive_reviews[:3]])}

Concerns customers mentioned:
{chr(10).join([f'- "{review}"' for review in negative_reviews[:2]])}

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

    try:
        # Test with DeepSeek (should be much better)
        result = await ai_service.generate_content_with_context(
            prompt=test_prompt,
            platform="facebook_ad",
            provider="deepseek",
            temperature=0.7,
            max_tokens=150
        )
        
        print("✅ DeepSeek Content Generation:")
        print(f"📱 Facebook Ad: {result.get('content', 'No content generated')}")
        print(f"🔧 Provider: {result.get('provider', 'Unknown')}")
        print(f"📊 Valid: {result.get('valid', False)}")
        
    except Exception as e:
        print(f"❌ DeepSeek failed: {e}")
    
    # Step 3: Compare with Mock (old system)
    print("\n📊 Step 3: Comparing with old Mock system...")
    
    try:
        mock_result = await ai_service.generate_content_with_context(
            prompt=test_prompt,
            platform="facebook_ad", 
            provider="mock",
            temperature=0.7,
            max_tokens=150
        )
        
        print("📱 Mock Content (Old System):")
        print(f"Content: {mock_result.get('content', 'No content')}")
        
    except Exception as e:
        print(f"❌ Mock failed: {e}")
    
    await ai_service.close()
    
    print("\n🎯 Analysis:")
    print("- The DeepSeek version should use actual customer quotes")
    print("- It should reference specific benefits customers mentioned")
    print("- It should feel more authentic and compelling")
    print("- The Mock version is generic and doesn't use review data")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow()) 