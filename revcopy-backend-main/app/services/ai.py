"""
AI Service for content generation using multiple providers (OpenAI, DeepSeek).
Supports configurable prompts and advanced content generation.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import json

import aiohttp
import ssl
import certifi
import structlog
# Graceful fallback for AI providers
HAS_OPENAI = False
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    try:
        from openai import OpenAI as AsyncOpenAI
        HAS_OPENAI = True
    except ImportError:
        AsyncOpenAI = None
        HAS_OPENAI = False

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings

logger = structlog.get_logger(__name__)


class AIProvider:
    """Base AI provider interface."""
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate content using the AI provider."""
        raise NotImplementedError


class MockAIProvider(AIProvider):
    """Mock AI provider for testing without actual AI services."""
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        platform: Optional[str] = None,
        cultural_context: Optional[Dict] = None,
        **kwargs
    ) -> str:
        """Generate realistic mock content for testing based on platform and parameters."""
        # Determine content length based on max_tokens
        is_short = max_tokens <= 200
        is_medium = 200 < max_tokens <= 600
        is_long = max_tokens > 600
        
        # Extract tone from system prompt or kwargs
        tone = "professional"
        if system_prompt:
            if "emotional" in system_prompt.lower() or "storytelling" in system_prompt.lower():
                tone = "emotional"
            elif "casual" in system_prompt.lower() or "friendly" in system_prompt.lower():
                tone = "casual"
        
        # Extract product information from prompt
        product_name = "this amazing product"
        price = ""
        rating = "4.5"
        benefits = ["high quality", "great value", "excellent design"]
        
        # Parse prompt to extract real product details
        if "Product:" in prompt:
            lines = prompt.split('\n')
            for line in lines:
                if line.strip().startswith("Product:"):
                    product_name = line.replace("Product:", "").strip()
                elif line.strip().startswith("Price:"):
                    price = line.replace("Price:", "").strip()
                elif "Average Rating:" in line:
                    rating_part = line.split("Average Rating:")[1].split("/")[0].strip()
                    rating = rating_part if rating_part else "4.5"
                elif line.strip().startswith("- "):
                    # Extract benefits from bullet points
                    benefit = line.strip()[2:].lower()
                    if any(word in benefit for word in ["appreciate", "love", "praise", "find"]):
                        benefits.append(benefit)
        
        # Clean product name
        if product_name and product_name != "Product":
            product_name = product_name.replace("'", "").strip()
        else:
            product_name = "this amazing product"
        
        # Generate platform-specific content
        if platform == "facebook_ad":
            return self._generate_facebook_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
        elif platform == "google_ad":
            return self._generate_google_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
        elif platform == "instagram_caption":
            return self._generate_instagram_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
        elif platform == "email_campaign":
            return self._generate_email_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
        elif platform == "product_description":
            return self._generate_product_description_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
        else:
            # Default Facebook ad
            return self._generate_facebook_content(product_name, price, rating, benefits, tone, is_short, is_medium, is_long)
    
    
    def _generate_facebook_content(self, product_name: str, price: str, rating: str, benefits: list, tone: str, is_short: bool, is_medium: bool, is_long: bool) -> str:
        """Generate Facebook ad content based on real product data."""
        
        if is_short:
            if tone == "emotional":
                return f"💫 Fall in love with {product_name}! {rating}⭐ rated by customers who can't stop raving about the quality. Transform your experience today! ✨ {price if price else 'Shop now'} #GameChanger"
            else:
                return f"🚀 {product_name} - {rating}⭐ customer rated! Premium quality that customers love. {price if price else 'Limited time'} - Experience the difference today! 💯"
        
        elif is_medium:
            if tone == "emotional":
                return f"""💫 Ready to experience something special?
                
{product_name} isn't just another product - it's the solution customers have been searching for! 

⭐ {rating}/5 stars from real customers
✨ "The quality exceeded my expectations" 
💝 "Best value for money I've found"
🎯 "Easy to use and beautifully designed"

Join thousands of happy customers who discovered something amazing. {price if price else 'Limited time offer'}

Don't wait - your perfect experience is just one click away! 

#CustomerApproved #QualityMatters #MustHave"""
            else:
                return f"""🎯 {product_name} - The Choice of Smart Customers

⭐ {rating}/5 star average rating
✅ Customers consistently praise the premium quality  
✅ Users love the convenient, easy-to-use design
✅ "Great value for money" mentioned in 70+ reviews
✅ Professional results that exceed expectations

{price if price else 'Special pricing available'}

Ready to see what all the excitement is about? Join thousands of satisfied customers today!

#QualityFirst #CustomerChoice #ProfessionalGrade"""
        
        else:  # Long content
            if tone == "emotional":
                return f"""💫 Discover Why Customers Are Obsessed with {product_name}

Picture this: You're looking for something that truly delivers on its promises. Something that doesn't just meet expectations - it shatters them completely.

That's exactly what happened to Sarah from California: "I was skeptical at first, but {product_name} has completely transformed my experience. The quality is outstanding!"

✨ What makes customers fall in love:
• The premium quality that feels luxurious yet accessible
• Intuitive design that works perfectly from day one  
• Exceptional value that makes you feel smart about your purchase
• Professional results that boost your confidence

⭐ {rating}/5 stars from 200+ verified customers
💝 "This exceeded every expectation I had"
🎯 "Finally found something that actually works as advertised"
🌟 "The customer service is phenomenal too"

{price if price else 'Investment starting at just $X'}

But here's what really matters: Every single day you wait is another day you're missing out on the experience that could change everything.

Don't spend another moment settling for less. Join our community of customers who made the smart choice.

Click below and discover what you've been missing! ⬇️

#TransformYourExperience #CustomerObsessed #QualityThatMatters #LifeChanging"""
            else:
                return f"""🚀 {product_name}: Why Industry Professionals Choose Quality

When it comes to making smart purchasing decisions, successful people don't compromise on quality. They choose products with proven track records and outstanding customer satisfaction.

📊 THE NUMBERS SPEAK FOR THEMSELVES:
⭐ {rating}/5 star rating from verified customers
📈 95% customer satisfaction rate
🎯 Recommended by industry professionals
💯 Premium quality construction and materials

🔥 WHAT CUSTOMERS LOVE MOST:
✅ "The build quality is exceptional - feels premium"
✅ "Incredibly easy to use, works exactly as advertised"  
✅ "Outstanding value for money compared to competitors"
✅ "Customer service team is responsive and helpful"
✅ "Reliable performance that exceeds expectations"

💡 SMART FEATURES THAT MATTER:
• Professional-grade components and design
• User-friendly interface that saves time
• Durable construction built to last
• Comprehensive support and documentation
• Flexible options that adapt to your needs

{price if price else 'Professional pricing with volume discounts available'}

🎯 WHY WAIT? Smart customers act when they find quality.

Ready to experience the difference that quality makes? Join thousands of professionals who've already made the smart choice.

Order now and see why customers consistently rate this as their best purchase decision.

#ProfessionalGrade #SmartChoice #QualityInvestment #CustomerApproved #IndustryLeading"""

    def _generate_google_content(self, product_name: str, price: str, rating: str, benefits: list, tone: str, is_short: bool, is_medium: bool, is_long: bool) -> str:
        """Generate Google ad content based on real product data."""
        
        if is_short:
            return f"{product_name} - {rating}⭐ Rated | {price if price else 'Special Pricing'} | Free Shipping Available"
        elif is_medium:
            return f"""{product_name} - {rating}⭐ Customer Rated
✅ Premium Quality | Professional Results | Fast Shipping
🎯 {price if price else 'Limited Time Offer'} | 30-Day Guarantee | Free Returns
Shop Now & Experience the Difference!"""
        else:
            return f"""{product_name} - The #1 Choice for Quality & Value
⭐ {rating}/5 Stars from Verified Customers | Premium Quality Guaranteed
✅ Professional Results | Easy to Use | Outstanding Customer Service
💰 {price if price else 'Competitive Pricing'} | Free Shipping Over $50 | 30-Day Money Back
🎁 Limited Time: Free Bonus Gift with Purchase
Order Now & Join Thousands of Satisfied Customers!"""
    
    def _generate_instagram_content(self, product_name: str, price: str, rating: str, benefits: list, tone: str, is_short: bool, is_medium: bool, is_long: bool) -> str:
        """Generate Instagram caption based on real product data."""
        
        if is_short:
            return f"""✨ Obsessed with {product_name}! {rating}⭐ rated by customers who can't stop raving about it 💕
            
#QualityFinds #CustomerApproved #MustHave"""
        elif is_medium:
            return f"""✨ Can we talk about {product_name}? Because I'm OBSESSED! 💕

{rating}⭐ rating from real customers and I can see why:
🌟 The quality is incredible
🌟 So easy to use  
🌟 Amazing value for money
🌟 Customer service is top-tier

{price if price else 'Perfect timing'} - who else needs this in their life?

Drop a 💫 if you're ready to upgrade!

#QualityFinds #CustomerApproved #MustHave #ProductReview #WorthIt"""
        else:
            return f"""✨ Can we talk about {product_name}? Because I'm completely OBSESSED and I need to tell you why! 💕

After trying literally everything in this category, I finally found THE ONE that actually lives up to the hype. And with {rating}⭐ from thousands of customers, I'm clearly not alone in this obsession!

🌟 What makes it so special:
• The quality is absolutely incredible - you can feel the difference immediately
• So intuitive and easy to use, works exactly as promised
• Amazing value for money compared to other options
• Customer service team is responsive and genuinely helpful
• It just works - no complicated setup or learning curve

Real talk: I've recommended this to everyone I know and they all come back thanking me. There's something so satisfying about finding a product that actually delivers on its promises!

{price if price else 'The timing is perfect'} and honestly, it's one of those purchases that just makes sense. You know when you find something that's going to make your life easier/better? This is it.

Who else has found their holy grail product recently? I love hearing about game-changers! Drop your favorites below 👇

And if you've been on the fence about this one - just go for it. Your future self will thank you! 💫

#QualityFinds #CustomerApproved #MustHave #ProductReview #WorthIt #GameChanger #HolyGrail"""
    
    def _generate_email_content(self, product_name: str, price: str, rating: str, benefits: list, tone: str, is_short: bool, is_medium: bool, is_long: bool) -> str:
        """Generate email campaign content based on real product data."""
        
        if is_short:
            return f"""Subject: Your {product_name} is waiting ✨

Ready to experience what {rating}⭐ customers are raving about? 

{product_name} delivers the quality and results you've been looking for.

Shop Now → [Link]"""
        elif is_medium:
            return f"""Subject: Why {rating}⭐ customers choose {product_name} ✨

Hi there!

Ready to discover what thousands of customers already know? {product_name} isn't just another product - it's the solution you've been searching for.

What customers love:
• Outstanding quality and craftsmanship  
• Easy to use right out of the box
• Exceptional value for the price
• Reliable performance that exceeds expectations

{price if price else 'Special pricing available'} - your satisfaction is guaranteed.

Shop Now → [Link]

Best regards,
The Team"""
        else:
            return f"""Subject: The {product_name} Story - Why {rating}⭐ Customers Can't Stop Raving

Hi there!

I wanted to share something special with you today - the story behind {product_name} and why it's earned {rating}⭐ from thousands of satisfied customers.

When we set out to create this product, we had one goal: deliver exceptional quality at a fair price. We wanted something that would exceed expectations, not just meet them.

Here's what customers tell us they love most:

✨ The Quality Difference
"The build quality is exceptional - you can immediately tell this is premium" - Sarah M.

✨ User-Friendly Design  
"So easy to use, worked perfectly right out of the box" - Mike R.

✨ Outstanding Value
"Best investment I've made in this category - worth every penny" - Lisa K.

✨ Reliable Performance
"Consistent results every time, exactly as advertised" - David T.

What really makes me proud is reading reviews from customers who say this solved a problem they'd been struggling with for years. That's exactly what we hoped to achieve.

{price if price else 'Current pricing'} includes:
• Fast, free shipping
• 30-day satisfaction guarantee  
• Responsive customer support
• Comprehensive product guide

Ready to see what all the excitement is about? Your satisfaction is 100% guaranteed.

Shop Now → [SHOP LINK]

To your success,
[Name]
The Team

P.S. With our 30-day guarantee, you've got nothing to lose and everything to gain. Try it risk-free!"""
    
    def _generate_product_description_content(self, product_name: str, price: str, rating: str, benefits: list, tone: str, is_short: bool, is_medium: bool, is_long: bool) -> str:
        """Generate product description based on real product data."""
        
        if is_short:
            return f"""Experience the quality of {product_name} - rated {rating}⭐ by satisfied customers. Premium design meets exceptional performance for outstanding results."""
        elif is_medium:
            return f"""Experience the Quality of {product_name}

Rated {rating}⭐ by thousands of satisfied customers, {product_name} delivers the premium quality and reliable performance you deserve.

Key Features:
• Outstanding build quality and design
• User-friendly and intuitive operation
• Exceptional value for money
• Reliable, consistent performance
• Comprehensive customer support

{price if price else 'Competitively priced'} with satisfaction guaranteed. Join thousands of customers who've made the smart choice.

Perfect for anyone seeking quality, reliability, and outstanding value."""
        else:
            return f"""Experience the Premium Quality of {product_name}

Discover why {product_name} has earned {rating}⭐ from thousands of satisfied customers worldwide. This isn't just another product - it's a carefully crafted solution designed to exceed your expectations.

🌟 Premium Quality & Design
Built with attention to detail and premium materials, {product_name} delivers the quality you can see and feel. Every component has been carefully selected to ensure lasting performance and satisfaction.

🔧 User-Friendly Excellence  
Designed with the user in mind, {product_name} works exactly as intended from day one. No complicated setup, no learning curve - just reliable performance when you need it.

💰 Outstanding Value
{price if price else 'Competitively priced'} for premium quality that lasts. Customers consistently tell us this represents exceptional value compared to alternatives.

⭐ Proven Performance
With {rating}⭐ average rating from verified customers, the results speak for themselves. Join thousands who've experienced the difference quality makes.

🛡️ Complete Confidence
• 30-day satisfaction guarantee
• Responsive customer support team  
• Comprehensive product documentation
• Fast, reliable shipping

What Customers Say:
"The quality exceeded my expectations - clearly built to last" - Verified Customer
"Easy to use and works exactly as advertised" - Verified Customer  
"Best value I've found in this category" - Verified Customer

Perfect for professionals and enthusiasts who demand quality, reliability, and outstanding performance. Experience the difference that premium quality makes.

Order now with complete confidence - your satisfaction is guaranteed."""


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str):
        if not HAS_OPENAI:
            raise ImportError("OpenAI package not available")
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate content using OpenAI API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("OpenAI generation failed", error=str(e))
            raise


class DeepSeekProvider(AIProvider):
    """Enhanced DeepSeek provider implementation with platform optimization."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.model = settings.DEEPSEEK_MODEL
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper SSL configuration."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=settings.DEEPSEEK_TIMEOUT)
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=30,
                keepalive_timeout=30
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector,
                headers={
                    "User-Agent": "RevCopy/1.0 (AI Content Generation)",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def generate_content(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        platform: Optional[str] = None,
        cultural_context: Optional[Dict] = None
    ) -> str:
        """
        Generate content using DeepSeek API with platform optimization.
        
        Args:
            prompt: User prompt for content generation
            system_prompt: System prompt for context
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            platform: Target platform for optimization
            cultural_context: Cultural adaptation context
        """
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                
                # Optimize parameters based on platform
                optimized_params = self._optimize_for_platform(
                    temperature, max_tokens, platform
                )
                
                # Enhance system prompt with cultural context
                enhanced_system_prompt = self._enhance_system_prompt(
                    system_prompt, platform, cultural_context
                )
                
                messages = []
                if enhanced_system_prompt:
                    messages.append({"role": "system", "content": enhanced_system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": optimized_params["temperature"],
                    "max_tokens": optimized_params["max_tokens"],
                    "stream": False,
                    "top_p": 0.95,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.1
                }
                
                # Add platform-specific parameters
                if platform:
                    payload.update(self._get_platform_specific_params(platform))
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                logger.info(
                    "Sending request to DeepSeek",
                    model=self.model,
                    temperature=optimized_params["temperature"],
                    max_tokens=optimized_params["max_tokens"],
                    platform=platform,
                    attempt=attempt + 1
                )
                
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"].strip()
                        
                        # Log usage metrics
                        usage = result.get("usage", {})
                        logger.info(
                            "DeepSeek generation successful",
                            tokens_used=usage.get("total_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            platform=platform
                        )
                        
                        return content
                    
                    elif response.status == 429:  # Rate limit
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            "DeepSeek rate limit hit, retrying",
                            attempt=attempt + 1,
                            wait_time=wait_time,
                            status=response.status
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    
                    elif response.status in [500, 502, 503, 504]:  # Server errors
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            "DeepSeek server error, retrying",
                            attempt=attempt + 1,
                            wait_time=wait_time,
                            status=response.status,
                            response=response_text[:200]
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_detail = response_text
                        try:
                            error_json = await response.json()
                            error_detail = error_json.get("error", {}).get("message", response_text)
                        except:
                            pass
                        
                        raise Exception(f"DeepSeek API error {response.status}: {error_detail}")
                        
            except asyncio.TimeoutError:
                logger.warning(
                    "DeepSeek request timeout",
                    attempt=attempt + 1,
                    timeout=settings.DEEPSEEK_TIMEOUT
                )
                if attempt == self.max_retries - 1:
                    raise Exception("DeepSeek API timeout after all retries")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error("DeepSeek generation failed after all retries", error=str(e))
                    raise
                
                logger.warning(
                    "DeepSeek generation failed, retrying",
                    attempt=attempt + 1,
                    error=str(e)
                )
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
        
        raise Exception("DeepSeek generation failed after all retries")
    
    def _optimize_for_platform(
        self, 
        temperature: float, 
        max_tokens: int, 
        platform: Optional[str]
    ) -> Dict[str, Any]:
        """Optimize generation parameters for specific platforms."""
        if not platform or platform not in settings.PLATFORM_LIMITS:
            return {"temperature": temperature, "max_tokens": max_tokens}
        
        platform_limits = settings.PLATFORM_LIMITS[platform]
        
        # Adjust max_tokens based on platform character limits
        if "max_characters" in platform_limits:
            # Rough estimation: 1 token ≈ 4 characters
            estimated_tokens = platform_limits["max_characters"] // 3
            max_tokens = min(max_tokens, estimated_tokens)
        
        # Adjust temperature for platform requirements
        if platform in ["google_ad", "email_campaign"]:
            # More focused and direct content
            temperature = max(0.3, temperature - 0.2)
        elif platform in ["instagram_caption", "twitter_post"]:
            # More creative and engaging content
            temperature = min(1.0, temperature + 0.1)
        
        return {
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def _enhance_system_prompt(
        self,
        system_prompt: Optional[str],
        platform: Optional[str],
        cultural_context: Optional[Dict]
    ) -> str:
        """Enhance system prompt with platform and cultural context."""
        base_prompt = system_prompt or "You are an expert content creator specializing in marketing copy."
        
        enhancements = []
        
        # Add platform-specific instructions
        if platform and platform in settings.PLATFORM_LIMITS:
            platform_info = settings.PLATFORM_LIMITS[platform]
            
            if platform == "facebook_ad":
                enhancements.append(
                    f"Create Facebook ad copy that is engaging and action-oriented. "
                    f"Keep it under {platform_info['max_characters']} characters. "
                    f"Include a clear call-to-action. Emojis are encouraged."
                )
            elif platform == "google_ad":
                enhancements.append(
                    f"Create Google Ads copy with headlines under {platform_info['max_headline_length']} characters "
                    f"and descriptions under {platform_info['max_description_length']} characters. "
                    f"Focus on keywords and clear value propositions. No emojis."
                )
            elif platform == "instagram_caption":
                enhancements.append(
                    f"Create an Instagram caption that tells a story and engages followers. "
                    f"Include relevant hashtags and emojis. Keep it engaging and authentic."
                )
            elif platform == "email_campaign":
                enhancements.append(
                    f"Create email content that is personal, clear, and drives action. "
                    f"Include a compelling subject line under {platform_info['max_subject_length']} characters."
                )
        
        # Add cultural context
        if cultural_context:
            region = cultural_context.get("cultural_region", "")
            language = cultural_context.get("language", "en")
            
            if region in settings.CULTURAL_REGIONS:
                region_info = settings.CULTURAL_REGIONS[region]
                communication_style = region_info.get("communication_style", "")
                cultural_values = region_info.get("cultural_values", [])
                
                enhancements.append(
                    f"Adapt the content for {region} market with {communication_style} communication style. "
                    f"Consider cultural values: {', '.join(cultural_values)}. "
                    f"Write in {language} language."
                )
                
                if region_info.get("formal_language_preferred"):
                    enhancements.append("Use formal, respectful language.")
                
                if region_info.get("text_direction") == "rtl":
                    enhancements.append("Consider right-to-left text layout preferences.")
        
        if enhancements:
            return f"{base_prompt}\n\nAdditional Instructions:\n" + "\n".join(f"• {enhancement}" for enhancement in enhancements)
        
        return base_prompt
    
    def _get_platform_specific_params(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific API parameters."""
        params = {}
        
        if platform in ["google_ad", "email_campaign"]:
            # More focused output
            params["top_p"] = 0.85
            params["frequency_penalty"] = 0.2
        elif platform in ["instagram_caption", "twitter_post"]:
            # More creative output
            params["top_p"] = 0.95
            params["frequency_penalty"] = 0.05
        
        return params
    
    async def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None


class AIService:
    """Main AI service with multiple provider support."""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available AI providers."""
        try:
            # Initialize DeepSeek if API key is available
            if hasattr(settings, 'DEEPSEEK_API_KEY') and settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY != "sk-test-deepseek":
                self.providers["deepseek"] = DeepSeekProvider(
                    settings.DEEPSEEK_API_KEY, 
                    settings.DEEPSEEK_BASE_URL
                )
                logger.info("DeepSeek provider initialized", model=settings.DEEPSEEK_MODEL)
            
            # Initialize OpenAI if API key is available and package is installed
            if HAS_OPENAI and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "test-key":
                self.providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)
                logger.info("OpenAI provider initialized")
            
            # Always have a mock provider for testing
            if not self.providers:
                self.providers["mock"] = MockAIProvider()
                logger.info("Mock AI provider initialized")
            
        except Exception as e:
            logger.error("Failed to initialize AI providers", error=str(e))
            # Fallback to mock provider
            self.providers = {"mock": MockAIProvider()}
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return list(self.providers.keys())
    
    async def generate_content_with_context(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        platform: Optional[str] = None,
        cultural_context: Optional[Dict] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        custom_variables: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate content with platform and cultural context.
        
        Args:
            prompt: User prompt for generation
            system_prompt: System prompt for context
            platform: Target platform (facebook_ad, google_ad, etc.)
            cultural_context: Cultural adaptation context
            provider: Preferred AI provider
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            custom_variables: Custom variables for template processing
            
        Returns:
            Dict containing generated content and metadata
        """
        start_time = datetime.utcnow()
        
        # Select provider
        provider_name = provider or self._get_best_provider()
        if provider_name not in self.providers:
            provider_name = self._get_best_provider()
        
        ai_provider = self.providers[provider_name]
        
        # Set default parameters
        temperature = temperature or settings.AI_TEMPERATURE
        max_tokens = max_tokens or settings.AI_MAX_TOKENS
        
        # Enhance cultural context with custom variables for MockAIProvider
        enhanced_cultural_context = cultural_context.copy() if cultural_context else {}
        if custom_variables:
            enhanced_cultural_context["custom_variables"] = custom_variables
        
        try:
            # Generate content with enhanced parameters
            if isinstance(ai_provider, DeepSeekProvider):
                content = await ai_provider.generate_content(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    platform=platform,
                    cultural_context=enhanced_cultural_context
                )
            else:
                # Fallback for other providers (including MockAIProvider)
                content = await ai_provider.generate_content(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    platform=platform,
                    cultural_context=enhanced_cultural_context
                )
            
            generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Validate content against platform constraints
            validation_result = self._validate_platform_content(content, platform)
            
            result = {
                "content": content,
                "provider_used": provider_name,
                "generation_time_ms": int(generation_time),
                "platform": platform,
                "cultural_context": enhanced_cultural_context,
                "validation": validation_result,
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
            logger.info(
                "Content generated successfully",
                provider=provider_name,
                platform=platform,
                generation_time_ms=int(generation_time),
                content_length=len(content),
                valid=validation_result.get("valid", True)
            )
            
            return result
            
        except Exception as e:
            generation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                "Content generation failed",
                provider=provider_name,
                platform=platform,
                generation_time_ms=int(generation_time),
                error=str(e)
            )
            raise
    
    def _validate_platform_content(self, content: str, platform: Optional[str]) -> Dict[str, Any]:
        """Validate generated content against platform constraints."""
        if not platform or platform not in settings.PLATFORM_LIMITS:
            return {"valid": True, "warnings": []}
        
        platform_limits = settings.PLATFORM_LIMITS[platform]
        warnings = []
        
        # Check character limits
        content_length = len(content)
        if "max_characters" in platform_limits:
            max_chars = platform_limits["max_characters"]
            if content_length > max_chars:
                warnings.append(f"Content exceeds {platform} character limit ({content_length}/{max_chars})")
        
        # Check for required elements
        if platform_limits.get("call_to_action_required", False):
            cta_keywords = ["buy", "shop", "get", "try", "download", "subscribe", "sign up", "learn more", "click"]
            has_cta = any(keyword in content.lower() for keyword in cta_keywords)
            if not has_cta:
                warnings.append(f"Content should include a call-to-action for {platform}")
        
        # Check emoji usage
        if platform_limits.get("emojis_allowed", True) is False:
            import re
            emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]')
            if emoji_pattern.search(content):
                warnings.append(f"Emojis are not recommended for {platform}")
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "character_count": content_length,
            "platform_limits": platform_limits
        }
    
    def _get_best_provider(self) -> str:
        """Get the best available AI provider (prefer DeepSeek, then OpenAI, then mock)."""
        if "deepseek" in self.providers:
            return "deepseek"
        elif "openai" in self.providers:
            return "openai"
        else:
            return "mock"
    
    async def close(self):
        """Close all provider connections."""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()
    
    async def generate_comprehensive_content(
        self,
        product_data: Dict,
        reviews_data: List[Dict],
        content_types: List[str] = None,
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive content suite based on product and reviews analysis.
        
        Args:
            product_data: Product information
            reviews_data: Customer reviews
            content_types: List of content types to generate
            provider: AI provider to use
            
        Returns:
            Dictionary with generated content for each type
        """
        try:
            if content_types is None:
                content_types = ["product_description", "product_summary", "marketing_copy", "faq_generator"]
            
            # Detect product language first
            detected_language = self._detect_product_language(product_data)
            should_adapt = self._should_apply_cultural_adaptation(product_data, detected_language)
            
            logger.info(
                f"Generating comprehensive content suite: {content_types}",
                detected_language=detected_language,
                cultural_adaptation=should_adapt,
                product_title=product_data.get("title", "")
            )
            
            # Auto-select provider if not specified
            if not provider:
                provider = self._get_best_provider()
            
            # Analyze reviews once for all content types
            strengths, weaknesses = self._analyze_reviews(reviews_data)
            
            # Generate content for each type
            generated_content = {}
            
            for content_type in content_types:
                try:
                    logger.info(f"Generating {content_type} content")
                    
                    result = await self.generate_product_description(
                        product_data=product_data,
                        reviews_data=reviews_data,
                        template_type=content_type,
                        provider=provider
                    )
                    
                    generated_content[content_type] = result
                    
                except Exception as e:
                    logger.error(f"Failed to generate {content_type}", error=str(e))
                    generated_content[content_type] = {
                        "content": f"Error generating {content_type}: {str(e)}",
                        "error": True
                    }
            
            # Create comprehensive summary
            summary = {
                "product_name": product_data.get("title", "Product"),
                "detected_language": detected_language,
                "cultural_adaptation_applied": should_adapt,
                "analysis_summary": {
                    "total_reviews": len(reviews_data),
                    "average_rating": round(sum(r.get("rating", 0) for r in reviews_data) / len(reviews_data), 1) if reviews_data else 0,
                    "positive_reviews": len([r for r in reviews_data if r.get("rating", 0) >= 4]),
                    "negative_reviews": len([r for r in reviews_data if r.get("rating", 0) <= 2]),
                    "key_strengths": strengths,
                    "key_concerns": weaknesses
                },
                "generated_content": generated_content,
                "provider_used": provider,
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error("Comprehensive content generation failed", error=str(e))
            raise

    def _detect_product_language(self, product_data: Dict) -> str:
        """
        Detect the language of the product based on its content.
        
        Args:
            product_data: Product information
            
        Returns:
            Language code (always 'en' for English-only system)
        """
        # Always return English - no multi-language support
        return "en"
    
    def _should_apply_cultural_adaptation(self, product_data: Dict, detected_language: str) -> bool:
        """
        Determine if cultural adaptation should be applied based on product content.
        
        Args:
            product_data: Product information
            detected_language: Detected language code
            
        Returns:
            Boolean indicating if cultural adaptation should be applied (always False for English-only)
        """
        # No cultural adaptations in English-only system
        return False

    def _analyze_reviews(self, reviews_data: List[Dict]) -> Tuple[List[str], List[str]]:
        """
        Analyze reviews to extract key strengths and weaknesses with deeper insights.
        
        Args:
            reviews_data: List of customer reviews
            
        Returns:
            Tuple of (strengths, weaknesses) lists
        """
        if not reviews_data:
            return [], []
        
        positive_reviews = [r for r in reviews_data if r.get("rating", 0) >= 4]
        negative_reviews = [r for r in reviews_data if r.get("rating", 0) <= 2]
        
        # Extract key themes from positive reviews with more specific analysis
        strengths = []
        strength_patterns = {
            "quality": ["quality", "well-made", "solid", "durable", "excellent", "premium", "high-quality", "superior"],
            "shipping": ["fast shipping", "quick delivery", "arrived quickly", "prompt delivery", "shipping", "delivery"],
            "value": ["worth it", "great value", "good price", "affordable", "reasonable", "value", "money's worth"],
            "customer_service": ["customer service", "support", "helpful", "responsive", "professional service"],
            "easy_to_use": ["easy to use", "user-friendly", "simple", "straightforward", "intuitive", "convenient"],
            "appearance": ["looks great", "beautiful", "attractive", "stylish", "gorgeous", "aesthetic", "design"],
            "performance": ["works great", "performs well", "effective", "efficient", "reliable", "consistent"],
            "packaging": ["well packaged", "secure packaging", "good packaging", "arrived safely", "protected"],
            "exceeded_expectations": ["exceeded expectations", "better than expected", "surprised", "impressed", "amazing"],
            "recommend": ["recommend", "would buy again", "love it", "perfect", "exactly what I wanted"]
        }
        
        for review in positive_reviews:
            content = review.get("content", "").lower()
            for theme, keywords in strength_patterns.items():
                if any(keyword in content for keyword in keywords):
                    if theme not in strengths:
                        strengths.append(theme.replace("_", " ").title())
        
        # Extract concerns from negative reviews with specific analysis
        weaknesses = []
        weakness_patterns = {
            "price": ["expensive", "overpriced", "too costly", "pricey", "not worth the money"],
            "quality": ["poor quality", "cheaply made", "broke", "defective", "flimsy", "cheap"],
            "shipping": ["slow shipping", "late delivery", "delayed", "took too long", "shipping issues"],
            "sizing": ["wrong size", "too small", "too large", "doesn't fit", "sizing issues"],
            "packaging": ["damaged packaging", "poor packaging", "arrived damaged", "broken box"],
            "customer_service": ["poor service", "rude", "unhelpful", "no response", "bad support"],
            "description": ["not as described", "misleading", "different from picture", "false advertising"],
            "durability": ["didn't last", "broke quickly", "fell apart", "cheap material", "fragile"]
        }
        
        for review in negative_reviews:
            content = review.get("content", "").lower()
            for theme, keywords in weakness_patterns.items():
                if any(keyword in content for keyword in keywords):
                    if theme not in weaknesses:
                        weaknesses.append(theme.replace("_", " ").title())
        
        # If no specific themes found, use generic analysis based on ratings
        if not strengths and positive_reviews:
            strengths = ["Customer Satisfaction", "Quality", "Value"]
        
        if not weaknesses and negative_reviews:
            weaknesses = ["Price Point"]
        
        return strengths[:5], weaknesses[:3]  # Limit to top 5 strengths and 3 weaknesses

    async def generate_product_description(
        self,
        product_data: Dict,
        reviews_data: List[Dict],
        template_type: str = "product_description",
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Generate product description using AI based on product data and reviews.
        
        Args:
            product_data: Product information
            reviews_data: Customer reviews
            template_type: Type of content to generate
            provider: AI provider to use
            
        Returns:
            Generated content with metadata
        """
        try:
            if not provider:
                provider = self._get_best_provider()
            
            # Analyze reviews for insights
            strengths, weaknesses = self._analyze_reviews(reviews_data)
            
            # Build comprehensive prompt with review insights
            product_name = product_data.get("title", "Product")
            price = product_data.get("price", "")
            avg_rating = round(sum(r.get("rating", 0) for r in reviews_data) / len(reviews_data), 1) if reviews_data else 4.5
            
            # Get sample positive and negative reviews with actual quotes
            positive_reviews = [r for r in reviews_data if r.get("rating", 0) >= 4][:3]
            negative_reviews = [r for r in reviews_data if r.get("rating", 0) <= 2][:2]
            
            # Extract actual customer quotes
            positive_quotes = []
            for review in positive_reviews:
                content = review.get("content", "").strip()
                if content and len(content) > 10:  # Only meaningful quotes
                    # Extract the most impactful part of the review
                    if len(content) > 80:
                        # Find the most compelling sentence
                        sentences = content.split('.')
                        for sentence in sentences:
                            if any(word in sentence.lower() for word in ['love', 'great', 'perfect', 'amazing', 'excellent', 'recommend']):
                                positive_quotes.append(sentence.strip())
                                break
                        else:
                            positive_quotes.append(content[:80] + "...")
                    else:
                        positive_quotes.append(content)
            
            # Create dynamic prompt based on template type
            if template_type == "facebook_ad":
                system_prompt = """You are an expert Facebook advertising copywriter who creates authentic, conversion-focused ads. 
                
Your style:
- Use real customer language and quotes
- Create emotional connection
- Include specific benefits customers mentioned
- Use emojis strategically
- Strong call-to-action
- Feel authentic, not corporate
- Maximum 125 characters total

AVOID:
- Generic phrases like "customers love"
- Template language
- Overly promotional tone
- Vague benefits"""
                
                customer_benefits = ', '.join(strengths) if strengths else "quality and value"
                best_quote = positive_quotes[0] if positive_quotes else "Great product!"
                
                user_prompt = f"""Create a compelling Facebook ad for {product_name} that feels authentic and personal.

PRODUCT DETAILS:
- Name: {product_name}
- Price: ${price} 
- Rating: {avg_rating}⭐ ({len(reviews_data)} reviews)
- Top customer benefits: {customer_benefits}

REAL CUSTOMER FEEDBACK:
"{best_quote}" - Verified Customer

ADDITIONAL POSITIVE QUOTES:
{chr(10).join([f'• "{quote}"' for quote in positive_quotes[1:3]])}

REQUIREMENTS:
1. Lead with the most compelling customer benefit
2. Use an actual customer quote or paraphrase their language
3. Include the star rating naturally
4. Price mention (${price})
5. Strong call-to-action
6. Use 2-3 relevant emojis
7. Feel personal, not corporate
8. Maximum 125 characters

Create an ad that makes people think "I need this!" based on what real customers actually said."""
            
            elif template_type == "product_description":
                system_prompt = """You are an expert e-commerce copywriter who creates product descriptions that convert browsers into buyers.

Your approach:
- Lead with customer-validated benefits
- Use authentic customer language
- Address real concerns naturally
- Include specific details customers mentioned
- Create emotional connection
- Build trust through social proof
- Make it scannable and engaging

AVOID:
- Generic product descriptions
- Corporate jargon
- Vague benefits
- Ignoring customer feedback"""
                
                # Build comprehensive customer insights
                positive_themes = []
                for review in positive_reviews:
                    content = review.get("content", "").lower()
                    if "quality" in content:
                        positive_themes.append("quality")
                    if any(word in content for word in ["fast", "quick", "shipping", "delivery"]):
                        positive_themes.append("fast shipping")
                    if any(word in content for word in ["easy", "simple", "user-friendly"]):
                        positive_themes.append("easy to use")
                    if any(word in content for word in ["love", "perfect", "exactly"]):
                        positive_themes.append("customer satisfaction")
                
                concerns_section = ""
                if negative_reviews:
                    concerns = []
                    for review in negative_reviews:
                        content = review.get("content", "").lower()
                        if "price" in content or "expensive" in content:
                            concerns.append("price value")
                        if "size" in content or "fit" in content:
                            concerns.append("sizing")
                        if "delivery" in content or "shipping" in content:
                            concerns.append("shipping")
                    
                    if concerns:
                        concerns_section = f"\nCUSTOMER CONCERNS TO ADDRESS:\n{', '.join(set(concerns))}"
                
                user_prompt = f"""Create a compelling product description for {product_name} that converts visitors into customers.

PRODUCT DETAILS:
- Name: {product_name}
- Price: ${price}
- Customer Rating: {avg_rating}⭐ from {len(reviews_data)} verified reviews
- Proven Benefits: {', '.join(strengths)}

REAL CUSTOMER INSIGHTS:
What customers love most:
{chr(10).join([f'• "{quote}"' for quote in positive_quotes[:3]])}

Top themes from reviews: {', '.join(set(positive_themes))}
{concerns_section}

REQUIREMENTS:
1. Hook: Start with the #1 benefit customers mentioned
2. Use specific customer language and quotes
3. Include 3-4 key benefits with proof
4. Address any concerns naturally
5. Social proof integration (rating/reviews)
6. Clear value proposition
7. Scannable format with bullet points
8. 200-300 words optimal
9. End with confidence-building statement

Make it feel like a friend recommending this product based on real experiences."""
            
            elif template_type == "google_ad":
                system_prompt = """You are a Google Ads specialist creating high-converting search ads.

Your approach:
- Focus on search intent
- Use customer-validated benefits
- Include specific proof points
- Clear value proposition
- Strong call-to-action
- No emojis
- Keyword-rich but natural

Headlines: Max 30 characters
Descriptions: Max 90 characters"""
                
                top_benefit = strengths[0] if strengths else "Quality"
                
                user_prompt = f"""Create a Google Ads campaign for {product_name} that captures search intent and converts.

PRODUCT DETAILS:
- Name: {product_name}
- Price: ${price}
- Rating: {avg_rating}⭐ ({len(reviews_data)} reviews)
- Top customer benefit: {top_benefit}

CUSTOMER PROOF:
"{positive_quotes[0] if positive_quotes else 'Customers love this product'}"

REQUIREMENTS:
1. Headline 1: Product name + top benefit (30 chars)
2. Headline 2: Rating + price/value (30 chars)  
3. Headline 3: Call-to-action (30 chars)
4. Description 1: Benefits + proof (90 chars)
5. Description 2: Social proof + urgency (90 chars)

Focus on what customers actually search for and what they care about most."""
            
            else:
                # Default content generation with enhanced prompting
                system_prompt = f"""You are an expert content writer creating {template_type} content that converts.

Use real customer insights and authentic language to create compelling content that resonates with your audience."""
                
                user_prompt = f"""Create compelling {template_type} content for {product_name}.

PRODUCT: {product_name} - ${price} - {avg_rating}⭐ ({len(reviews_data)} reviews)
CUSTOMER BENEFITS: {', '.join(strengths)}
CUSTOMER QUOTES: {', '.join(positive_quotes[:2])}

Make it authentic and customer-focused."""
            
            # Generate content using the selected provider
            result = await self.generate_content_with_context(
                prompt=user_prompt,
                system_prompt=system_prompt,
                platform=template_type,
                provider=provider,
                temperature=0.8,
                max_tokens=200 if template_type == "facebook_ad" else 500
            )
            
            return {
                "content": result.get("content", ""),
                "template_type": template_type,
                "provider": provider,
                "insights_used": {
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "avg_rating": avg_rating,
                    "review_count": len(reviews_data),
                    "positive_quotes": positive_quotes,
                    "customer_benefits": strengths
                },
                "template_id": 9999,  # Dynamic generation marker
                "valid": result.get("validation", {}).get("valid", True)
            }
            
        except Exception as e:
            logger.error(f"Product description generation failed for {template_type}", error=str(e))
            return {
                "content": f"Error generating {template_type}: {str(e)}",
                "error": True,
                "template_type": template_type,
                "template_id": 0
            }


# Global AI service instance
ai_service = AIService()

