#!/usr/bin/env python3
"""
Setup script for DeepSeek API integration with RevCopy.
Run this script to configure your DeepSeek API credentials and test the connection.
"""

import os
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.ai import DeepSeekProvider
from app.core.config import settings


async def test_deepseek_connection(api_key: str, base_url: str = "https://api.deepseek.com"):
    """Test DeepSeek API connection."""
    try:
        provider = DeepSeekProvider(api_key, base_url)
        
        test_prompt = "Write a brief, professional product description for a premium coffee mug."
        system_prompt = "You are a professional copywriter creating e-commerce product descriptions."
        
        print("🧪 Testing DeepSeek API connection...")
        
        result = await provider.generate_content(
            prompt=test_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=150,
            platform="product_description",
            cultural_context={
                "language": "en",
                "cultural_region": "north_america"
            }
        )
        
        print("✅ DeepSeek API connection successful!")
        print(f"📝 Generated content: {result[:100]}...")
        
        await provider.close()
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API connection failed: {str(e)}")
        return False


def create_env_file():
    """Create or update .env file with DeepSeek configuration."""
    env_path = Path(__file__).parent / ".env"
    
    print("\n🔧 Setting up DeepSeek API configuration...")
    
    # Get API key from user
    api_key = input("Enter your DeepSeek API key (starts with 'sk-'): ").strip()
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: DeepSeek API keys usually start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Setup cancelled")
            return None
    
    # Basic configuration
    env_content = f"""# RevCopy Backend Environment Configuration

# DeepSeek API Configuration
DEEPSEEK_API_KEY="{api_key}"
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_MODEL="deepseek-chat"
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TIMEOUT=60

# Application Settings
DEFAULT_AI_PROVIDER="deepseek"
AI_GENERATION_TIMEOUT=60
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7

# Database Configuration (Update these)
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/revcopy"

# CORS Settings
BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost:8082"

# Feature Flags
ENABLE_AI_GENERATION=true
ENABLE_REVIEW_ANALYSIS=true
ENABLE_MOCK_DATA=false

# Security
SECRET_KEY="your-secret-key-here-please-change-in-production"

# Logging
LOG_LEVEL="INFO"
LOG_FORMAT="json"
"""
    
    # Write to .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Environment file created at {env_path}")
    return api_key


def show_platform_info():
    """Show information about supported platforms and their requirements."""
    print("\n📋 Supported Content Platforms and Requirements:")
    print("=" * 60)
    
    platforms = {
        "facebook_ad": {
            "max_chars": 125,
            "features": ["Emojis encouraged", "Call-to-action required", "Emotional triggers"]
        },
        "google_ad": {
            "max_chars": "Headlines: 30, Descriptions: 90",
            "features": ["No emojis", "Keyword optimization", "Clear value proposition"]
        },
        "instagram_caption": {
            "max_chars": 2200,
            "features": ["Storytelling preferred", "8-11 hashtags", "Authentic tone"]
        },
        "email_campaign": {
            "max_chars": "Subject: 50, Body: unlimited",
            "features": ["Personalization", "Mobile-optimized", "Clear CTA"]
        },
        "product_description": {
            "max_chars": 2000,
            "features": ["Benefits over features", "SEO-optimized", "Social proof"]
        }
    }
    
    for platform, info in platforms.items():
        print(f"\n🎯 {platform.replace('_', ' ').title()}:")
        print(f"   Max Characters: {info['max_chars']}")
        print(f"   Features: {', '.join(info['features'])}")
    
    print("\n🌍 Supported Cultural Regions:")
    print("   • North America (en, es, fr)")
    print("   • Middle East (he, ar)")  
    print("   • Europe (en, de, fr, es, it)")
    print("   • Asia Pacific (en, zh, ja, ko)")


def show_usage_examples():
    """Show usage examples for the API."""
    print("\n📖 API Usage Examples:")
    print("=" * 40)
    
    print("\n🔗 Example API Request:")
    print("""
curl -X POST "http://localhost:8000/api/v1/content-generation/intelligent/generate" \\
     -H "Content-Type: application/json" \\
     -d '{
       "product_url": "https://example.com/product",
       "content_type": "facebook_ad",
       "language": "en",
       "cultural_region": "north_america",
       "tone": "professional",
       "ai_provider": "deepseek"
     }'
    """)
    
    print("\n🐍 Example Python Usage:")
    print("""
import httpx

async def generate_content():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/content-generation/intelligent/generate",
            json={
                "product_url": "https://example.com/product",
                "content_type": "instagram_caption",
                "language": "en",
                "cultural_region": "north_america",
                "tone": "friendly",
                "target_audience": "young adults",
                "ai_provider": "deepseek"
            }
        )
        return response.json()
    """)


async def main():
    """Main setup function."""
    print("🚀 RevCopy DeepSeek Integration Setup")
    print("=" * 40)
    
    # Show platform information
    show_platform_info()
    
    # Create environment file
    api_key = create_env_file()
    
    if api_key:
        # Test the connection
        print(f"\n🧪 Testing DeepSeek API with key: {api_key[:20]}...")
        success = await test_deepseek_connection(api_key)
        
        if success:
            print("\n✅ Setup completed successfully!")
            print("\n📝 Next steps:")
            print("1. Update DATABASE_URL in .env with your PostgreSQL connection")
            print("2. Run: python run.py (to start the backend)")
            print("3. Test the API endpoints")
            
            show_usage_examples()
            
        else:
            print("\n❌ Setup failed - please check your API key and try again")
            print("💡 Make sure you have a valid DeepSeek API key from: https://platform.deepseek.com/")
    
    print("\n🎉 Setup complete! Your RevCopy backend is ready to generate content with DeepSeek AI.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("💡 Please check your configuration and try again") 