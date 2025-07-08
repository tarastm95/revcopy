# DeepSeek AI Integration for RevCopy

## 🚀 Overview

RevCopy now features full integration with DeepSeek AI for advanced content generation. This integration provides platform-specific content optimization, cultural adaptation, and intelligent prompt management for creating high-converting marketing copy.

## 🎯 Features

### AI-Powered Content Generation
- **Platform Optimization**: Specialized prompts for Facebook Ads, Google Ads, Instagram, Email campaigns, and Product descriptions
- **Cultural Adaptation**: Support for multiple regions (North America, Middle East, Europe, Asia Pacific)
- **Multi-language Support**: Hebrew, English, Arabic, and other languages with proper cultural context
- **Intelligent Retry Logic**: Automatic retry with exponential backoff for reliability

### Platform-Specific Features

#### Facebook Ads
- Maximum 125 characters
- Emoji support and emotional triggers
- Call-to-action optimization
- Social proof integration

#### Google Ads  
- Headlines: 30 characters max
- Descriptions: 90 characters max
- Keyword optimization
- No emoji policy compliance

#### Instagram Captions
- Storytelling approach
- 8-11 hashtag recommendations
- Authentic, engaging tone
- Up to 2200 characters

#### Email Campaigns
- Compelling subject lines (50 chars max)
- Personalization features
- Mobile optimization
- Clear call-to-action

#### Product Descriptions
- Benefits over features approach
- SEO optimization
- Social proof integration
- Up to 2000 characters

## 🛠️ Quick Setup

### 1. Run the Setup Script

```bash
cd backend
python setup_deepseek.py
```

The script will:
- Guide you through API key configuration
- Create a `.env` file with optimal settings
- Test your DeepSeek API connection
- Show platform requirements and usage examples

### 2. Manual Configuration

If you prefer manual setup, create a `.env` file:

```env
# DeepSeek API Configuration
DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"
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
```

### 3. Get Your DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Create an account or log in
3. Navigate to API keys section
4. Generate a new API key
5. Copy the key (starts with `sk-`)

## 📡 API Usage

### Basic Content Generation

```bash
curl -X POST "http://localhost:8000/api/v1/content-generation/intelligent/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "product_url": "https://example.com/product",
       "content_type": "facebook_ad",
       "language": "en",
       "cultural_region": "north_america",
       "tone": "professional",
       "ai_provider": "deepseek"
     }'
```

### Advanced Usage with Cultural Adaptation

```bash
curl -X POST "http://localhost:8000/api/v1/content-generation/intelligent/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "product_url": "https://kyliecosmetics.com/en-il/products/lip-butter",
       "content_type": "instagram_caption",
       "language": "he",
       "cultural_region": "middle_east",
       "tone": "friendly",
       "target_audience": "young women",
       "brand_personality": "trendy and inclusive",
       "ai_provider": "deepseek",
       "temperature": 0.8,
       "max_tokens": 300
     }'
```

### Python Client Example

```python
import httpx
import asyncio

async def generate_content():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/content-generation/intelligent/generate",
            json={
                "product_url": "https://example.com/product",
                "content_type": "email_campaign",
                "language": "en",
                "cultural_region": "north_america",
                "tone": "professional",
                "target_audience": "business professionals",
                "personalization_level": "high",
                "ai_provider": "deepseek"
            }
        )
        return response.json()

# Run the function
result = asyncio.run(generate_content())
print(result['content'])
```

## 🎨 Content Types and Parameters

### Supported Content Types
- `facebook_ad` - Facebook/Meta advertising copy
- `google_ad` - Google Ads headlines and descriptions  
- `instagram_caption` - Instagram post captions
- `email_campaign` - Email marketing content
- `product_description` - E-commerce product descriptions

### Cultural Regions
- `north_america` - US, Canada (English, Spanish, French)
- `middle_east` - Israel, Arab countries (Hebrew, Arabic)
- `europe` - European markets (English, German, French, Spanish, Italian)
- `asia_pacific` - Asian markets (English, Chinese, Japanese, Korean)

### Tone Options
- `professional` - Business-appropriate, formal
- `friendly` - Warm, approachable
- `casual` - Relaxed, conversational
- `authoritative` - Expert, confident
- `emotional` - Feeling-driven, personal
- `luxurious` - Premium, sophisticated
- `playful` - Fun, energetic

## 🔧 Advanced Configuration

### Platform Limits Configuration

The system automatically enforces platform-specific limits:

```python
PLATFORM_LIMITS = {
    "facebook_ad": {
        "max_characters": 125,
        "call_to_action_required": True,
        "emojis_allowed": True,
        "hashtags_recommended": 2
    },
    "google_ad": {
        "max_headline_length": 30,
        "max_description_length": 90,
        "emojis_allowed": False,
        "keyword_density_target": 0.02
    }
    # ... more platforms
}
```

### Cultural Adaptation Settings

```python
CULTURAL_REGIONS = {
    "middle_east": {
        "languages": ["he", "ar"],
        "currency_symbols": ["₪", "د.إ", "ر.س"],
        "communication_style": "respectful",
        "cultural_values": ["family", "tradition", "honor", "trust"],
        "text_direction": "rtl",
        "formal_language_preferred": True
    }
    # ... more regions
}
```

## 🚨 Error Handling

The integration includes comprehensive error handling:

### Retry Logic
- Automatic retry for rate limits (429)
- Exponential backoff for server errors (5xx)
- Timeout handling with fallback

### Validation
- Content length validation against platform limits
- Required element checking (CTAs, etc.)
- Emoji usage validation per platform rules

### Error Types
```python
# Rate limit error
{
    "error": "rate_limit_exceeded",
    "retry_after": 60,
    "message": "DeepSeek API rate limit hit"
}

# Content validation error
{
    "error": "content_validation_failed",
    "warnings": ["Content exceeds Facebook character limit (150/125)"],
    "suggestions": ["Consider shortening the headline"]
}
```

## 📊 Monitoring and Analytics

### Usage Tracking
- Token usage per request
- Generation time metrics
- Success/failure rates
- Cost estimation

### Performance Optimization
- Template performance scoring
- A/B testing support
- Cultural adaptation effectiveness
- Platform-specific optimization metrics

## 🔒 Security Best Practices

### API Key Management
- Store API keys in environment variables
- Never commit keys to version control
- Rotate keys regularly
- Use different keys for development/production

### Rate Limiting
- Built-in request throttling
- Configurable rate limits
- Queue management for high-volume usage

## 🐛 Troubleshooting

### Common Issues

#### API Key Issues
```bash
# Test your API key
python -c "
import asyncio
from app.services.ai import DeepSeekProvider
async def test():
    provider = DeepSeekProvider('your-api-key')
    result = await provider.generate_content('Test prompt')
    print(result)
asyncio.run(test())
"
```

#### Connection Issues
- Verify internet connectivity
- Check firewall settings
- Confirm API endpoint accessibility

#### Content Quality Issues
- Adjust temperature settings (0.3-1.0)
- Modify max_tokens for length
- Update prompts for better context
- Use appropriate cultural settings

### Debug Mode

Enable detailed logging:

```env
LOG_LEVEL="DEBUG"
```

This will show:
- Request/response details
- Token usage information
- Performance metrics
- Error stack traces

## 📈 Performance Optimization

### Best Practices
1. **Cache Results**: Enable content caching for repeated requests
2. **Batch Processing**: Group similar requests together
3. **Optimal Parameters**: Use platform-specific temperature settings
4. **Cultural Context**: Provide detailed cultural information for better results

### Monitoring
- Track generation time trends
- Monitor token usage patterns
- Analyze success rates by platform
- Review cultural adaptation effectiveness

## 🔄 Updates and Maintenance

### Regular Tasks
- Monitor API usage and costs
- Update prompts based on performance data
- Review and update cultural adaptations
- Test with new product categories

### Version Updates
- Keep DeepSeek API client updated
- Monitor for new platform requirements
- Update cultural intelligence data
- Refresh prompt templates

## 📞 Support

For issues related to:
- **DeepSeek API**: Contact DeepSeek support
- **RevCopy Integration**: Check logs and error messages
- **Platform Requirements**: Refer to platform documentation
- **Cultural Adaptations**: Review cultural intelligence data

---

**Ready to generate amazing content with DeepSeek AI? Run the setup script and start creating!** 🎉 