#!/usr/bin/env python3
"""
Fix AI provider configuration to use DeepSeek instead of Mock provider
"""

import os
import asyncio
from app.services.ai import AIService

async def test_ai_providers():
    """Test and configure AI providers properly."""
    
    print("🔧 Checking AI provider configuration...")
    
    # Create AI service instance
    ai_service = AIService()
    
    print(f"Available providers: {ai_service.get_available_providers()}")
    
    # Test content generation
    test_prompt = """Create a Facebook ad for iPhone 15 Pro based on these customer reviews:

Positive reviews:
- "The camera quality is absolutely stunning"
- "Battery life is incredible, lasts all day"
- "Super fast performance for gaming"

Product: iPhone 15 Pro
Price: $999
Rating: 4.8/5 stars (1,234 reviews)
"""
    
    print("\n🧪 Testing DeepSeek provider...")
    try:
        result = await ai_service.generate_content_with_context(
            prompt=test_prompt,
            platform="facebook_ad",
            provider="deepseek",
            temperature=0.7,
            max_tokens=150
        )
        
        print("✅ DeepSeek result:")
        print(f"Content: {result.get('content', 'No content')}")
        print(f"Provider: {result.get('provider', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ DeepSeek failed: {e}")
        
        # Fall back to mock
        print("\n🧪 Testing Mock provider...")
        result = await ai_service.generate_content_with_context(
            prompt=test_prompt,
            platform="facebook_ad",
            provider="mock",
            temperature=0.7,
            max_tokens=150
        )
        
        print("✅ Mock result:")
        print(f"Content: {result.get('content', 'No content')}")
        print(f"Provider: {result.get('provider', 'Unknown')}")
    
    await ai_service.close()


if __name__ == "__main__":
    asyncio.run(test_ai_providers()) 