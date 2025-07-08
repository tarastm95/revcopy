"""
Product service for managing products and e-commerce platform integration.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product, ProductStatus, EcommercePlatform, ProductImage
from app.models.user import User
from crawlers.shopify_crawler import ShopifyCrawler

# Configure logging
logger = structlog.get_logger(__name__)


class ProductService:
    """Service for product management and e-commerce integration."""
    
    def detect_platform(self, url: str) -> Optional[EcommercePlatform]:
        """Detect e-commerce platform from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            if 'amazon' in domain:
                return EcommercePlatform.AMAZON
            elif 'ebay' in domain:
                return EcommercePlatform.EBAY
            elif 'aliexpress' in domain:
                return EcommercePlatform.ALIEXPRESS
            elif 'myshopify.com' in domain or 'shopify.com' in domain or '/products/' in path:
                return EcommercePlatform.SHOPIFY
            else:
                # Try to detect Shopify by checking if .json endpoint works
                async def check_shopify():
                    try:
                        async with ShopifyCrawler() as crawler:
                            if crawler.is_shopify_url(url):
                                return EcommercePlatform.SHOPIFY
                    except:
                        pass
                    return None
                
                # For now, return custom for unknown domains
                return EcommercePlatform.CUSTOM
            
        except Exception:
            return None
    
    async def validate_and_extract_product(
        self,
        url: str,
        user_id: int,
        db: AsyncSession
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Validate product URL and extract basic information."""
        try:
            logger.info("Validating product URL", url=url, user_id=user_id)
            
            if not url or not url.startswith(('http://', 'https://')):
                return False, {}, "Invalid URL format"
            
            # Detect platform
            platform = self.detect_platform(url)
            if not platform:
                return False, {}, "Unsupported e-commerce platform"
            
            # Note: We don't check for existing products here as that's handled in the API layer
            
            # Extract product data based on platform
            if platform == EcommercePlatform.SHOPIFY:
                product_data = await self._extract_shopify_product(url, user_id)
            elif platform == EcommercePlatform.AMAZON:
                product_data = await self._extract_amazon_product(url, user_id)
            else:
                # For other platforms, use mock data for now
                product_data = await self._extract_mock_product(url, platform, user_id)
            
            if not product_data:
                return False, {}, "Failed to extract product information"
            
            return True, product_data, None
            
        except Exception as e:
            logger.error("Product validation failed", error=str(e), url=url, user_id=user_id)
            return False, {}, f"Validation error: {str(e)}"
    
    async def _extract_shopify_product(self, url: str, user_id: int) -> Optional[Dict]:
        """Extract product data from Shopify store including reviews."""
        try:
            async with ShopifyCrawler() as crawler:
                # Extract product data including reviews
                product_data = await crawler.extract_product_data(url, include_reviews=True)
                
                if not product_data:
                    return None
                
                return {
                    "url": url,
                    "platform": EcommercePlatform.SHOPIFY,
                    "external_product_id": product_data.id,
                    "title": product_data.title,
                    "description": product_data.description,
                    "brand": product_data.vendor,
                    "category": product_data.product_type,
                    "price": product_data.price,
                    "currency": product_data.currency,
                    "original_price": product_data.compare_at_price,
                    "rating": product_data.rating,  # Now includes calculated rating from reviews
                    "review_count": product_data.review_count,  # Now includes actual review count
                    "in_stock": product_data.availability == "in_stock",
                    "tags": product_data.tags,
                    "crawl_metadata": {
                        "handle": product_data.handle,
                        "shopify_id": product_data.id,
                        "variants_count": len(product_data.variants),
                        "images_count": len(product_data.images),
                        "review_system": "detected" if product_data.reviews else "none",
                        "created_at": product_data.created_at.isoformat() if product_data.created_at else None,
                        "updated_at": product_data.updated_at.isoformat() if product_data.updated_at else None,
                    },
                    "images_data": [
                        {
                            "url": img.get("src", ""),
                            "alt_text": img.get("alt", ""),
                            "position": img.get("position", 0),
                            "width": img.get("width"),
                            "height": img.get("height"),
                        }
                        for img in product_data.images
                    ],
                    "reviews_data": product_data.reviews,  # Include extracted reviews
                    "user_id": user_id,
                }
                
        except Exception as e:
            logger.error("Shopify extraction failed", error=str(e), url=url)
            return None
    
    async def _extract_amazon_product(self, url: str, user_id: int) -> Optional[Dict]:
        """Extract product data from Amazon using the crawler service."""
        try:
            from app.services.amazon_crawler_client import AmazonCrawlerClient
            
            async with AmazonCrawlerClient() as client:
                # Scrape product data including reviews
                product_data = await client.scrape_product(url)
                
                if not product_data:
                    logger.error("Amazon crawler returned no data", url=url)
                    return None
                
                # Get targeted reviews: 15 positive + 15 negative
                positive_reviews, negative_reviews = await client.get_targeted_reviews(url, 15, 15)
                
                # Combine all reviews
                all_reviews = positive_reviews + negative_reviews
                
                # Calculate average rating from reviews
                if all_reviews:
                    total_rating = sum(review.get("rating", 0) for review in all_reviews)
                    avg_rating = total_rating / len(all_reviews)
                else:
                    avg_rating = product_data.get("rating", 4.5)
                
                return {
                    "url": url,
                    "platform": EcommercePlatform.AMAZON,
                    "external_product_id": product_data.get("asin"),
                    "title": product_data.get("title", ""),
                    "description": product_data.get("description", ""),
                    "brand": product_data.get("brand"),
                    "category": product_data.get("category"),
                    "price": product_data.get("price"),
                    "currency": product_data.get("currency", "USD"),
                    "original_price": product_data.get("original_price"),
                    "rating": avg_rating,
                    "review_count": len(all_reviews),
                    "in_stock": product_data.get("in_stock", True),
                    "tags": product_data.get("tags", []),
                    "crawl_metadata": {
                        "asin": product_data.get("asin"),
                        "amazon_url": url,
                        "images_count": len(product_data.get("images", [])),
                        "positive_reviews": len(positive_reviews),
                        "negative_reviews": len(negative_reviews),
                        "crawler_version": "go_microservice",
                        "scraped_at": datetime.utcnow().isoformat(),
                    },
                    "images_data": [
                        {
                            "url": img.get("url", img.get("src", "")),
                            "alt_text": img.get("alt", product_data.get("title", "")),
                            "position": idx,
                            "width": img.get("width"),
                            "height": img.get("height"),
                        }
                        for idx, img in enumerate(product_data.get("images", []))
                    ],
                    "reviews_data": all_reviews,  # Include all targeted reviews
                    "user_id": user_id,
                }
                
        except Exception as e:
            logger.error("Amazon extraction failed", error=str(e), url=url)
            return None
    
    async def _extract_mock_product(self, url: str, platform: EcommercePlatform, user_id: int) -> Dict:
        """Extract mock product data for non-Shopify platforms."""
        return {
            "url": url,
            "platform": platform,
            "external_product_id": f"MOCK_{platform.value.upper()}123",
            "title": f"Sample {platform.value.title()} Product",
            "description": f"Product description from {platform.value}",
            "price": 29.99,
            "currency": "USD",
            "rating": 4.5,
            "review_count": 100,
            "user_id": user_id,
            "images_data": [],
        }
    
    async def create_product(self, product_data: Dict, db: AsyncSession) -> Product:
        """Create a new product record with images."""
        try:
            # Create product
            product = Product(
                user_id=product_data["user_id"],
                url=product_data["url"],
                platform=product_data["platform"],
                external_product_id=product_data.get("external_product_id"),
                title=product_data.get("title", ""),
                description=product_data.get("description", ""),
                brand=product_data.get("brand"),
                category=product_data.get("category"),
                price=product_data.get("price"),
                currency=product_data.get("currency"),
                original_price=product_data.get("original_price"),
                rating=product_data.get("rating"),
                review_count=product_data.get("review_count", 0),
                in_stock=product_data.get("in_stock", True),
                tags=product_data.get("tags", []),
                status=ProductStatus.PENDING,  # Will be processed later
                crawl_metadata=product_data.get("crawl_metadata"),
                last_crawled_at=datetime.utcnow(),
            )
            
            db.add(product)
            await db.flush()  # Get the product ID
            
            # Create product images if provided
            images_data = product_data.get("images_data", [])
            for img_data in images_data:
                if img_data.get("url"):
                    image = ProductImage(
                        product_id=product.id,
                        url=img_data["url"],
                        alt_text=img_data.get("alt_text"),
                        position=img_data.get("position", 0),
                        width=img_data.get("width"),
                        height=img_data.get("height"),
                        image_type="main" if img_data.get("position") == 1 else "gallery",
                    )
                    db.add(image)
            
            await db.commit()
            await db.refresh(product)
            
            logger.info("Product created successfully", 
                       product_id=product.id, 
                       platform=product.platform.value,
                       images_count=len(images_data))
            return product
            
        except Exception as e:
            logger.error("Product creation failed", error=str(e))
            await db.rollback()
            raise
    
    async def analyze_product_comprehensive(
        self,
        url: str,
        user_id: int
    ) -> Optional[Dict]:
        """
        Comprehensive product analysis including product data and reviews.
        
        Args:
            url: Product URL to analyze
            user_id: User ID for the analysis
            
        Returns:
            Dict containing product data, reviews, and analysis
        """
        try:
            logger.info("Starting comprehensive product analysis", url=url, user_id=user_id)
            
            # Validate URL format
            if not url or not url.startswith(('http://', 'https://')):
                return None
            
            # Detect platform
            platform = self.detect_platform(url)
            if not platform:
                logger.error("Unsupported platform", url=url)
                return None
            
            # Extract product data based on platform
            if platform == EcommercePlatform.SHOPIFY:
                product_data = await self._extract_shopify_product(url, user_id)
            elif platform == EcommercePlatform.AMAZON:
                product_data = await self._extract_amazon_product(url, user_id)
            else:
                # For other platforms, use mock data
                product_data = await self._extract_mock_product(url, platform, user_id)
            
            if not product_data:
                logger.error("Failed to extract product data", url=url)
                return None
            
            # Extract reviews if available
            reviews = product_data.get("reviews_data", [])
            
            # Prepare comprehensive analysis result
            analysis_result = {
                "product_data": {
                    "title": product_data.get("title", ""),
                    "description": product_data.get("description", ""),
                    "brand": product_data.get("brand", ""),
                    "category": product_data.get("category", ""),
                    "price": product_data.get("price", 0),
                    "currency": product_data.get("currency", "USD"),
                    "rating": product_data.get("rating", 4.5),
                    "review_count": product_data.get("review_count", 0),
                    "url": url,
                    "platform": platform.value,
                    "images": product_data.get("images_data", []),
                    "tags": product_data.get("tags", []),
                    "in_stock": product_data.get("in_stock", True),
                },
                "reviews": reviews,
                "analysis": {
                    "total_reviews": len(reviews),
                    "average_rating": product_data.get("rating", 4.5),
                    "sentiment_distribution": self._analyze_sentiment_distribution(reviews),
                    "key_topics": self._extract_key_topics(reviews),
                    "strengths": self._extract_strengths(reviews),
                    "weaknesses": self._extract_weaknesses(reviews),
                },
                "metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "platform": platform.value,
                    "user_id": user_id,
                    "crawler_version": "v1.0",
                }
            }
            
            logger.info(
                "Comprehensive product analysis completed",
                url=url,
                product_title=product_data.get("title", "")[:50],
                reviews_count=len(reviews),
                platform=platform.value
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error("Comprehensive product analysis failed", error=str(e), url=url)
            return None
    
    def _analyze_sentiment_distribution(self, reviews: List[Dict]) -> Dict[str, int]:
        """Analyze sentiment distribution of reviews."""
        if not reviews:
            return {"positive": 0, "neutral": 0, "negative": 0}
        
        positive = len([r for r in reviews if r.get("rating", 0) >= 4])
        negative = len([r for r in reviews if r.get("rating", 0) <= 2])
        neutral = len(reviews) - positive - negative
        
        return {
            "positive": positive,
            "neutral": neutral,
            "negative": negative
        }
    
    def _extract_key_topics(self, reviews: List[Dict]) -> List[str]:
        """Extract key topics from reviews."""
        if not reviews:
            return ["quality", "value", "customer satisfaction"]
        
        # Simple keyword extraction for now
        topics = []
        common_words = ["quality", "value", "price", "shipping", "customer service", "product", "recommend"]
        
        for review in reviews:
            text = review.get("text", "").lower()
            for word in common_words:
                if word in text and word not in topics:
                    topics.append(word)
        
        return topics[:10]  # Return top 10 topics
    
    def _extract_strengths(self, reviews: List[Dict]) -> List[str]:
        """Extract product strengths from positive reviews."""
        if not reviews:
            return ["High quality product", "Good value for money", "Excellent customer satisfaction"]
        
        strengths = []
        positive_reviews = [r for r in reviews if r.get("rating", 0) >= 4]
        
        for review in positive_reviews[:5]:  # Check top 5 positive reviews
            text = review.get("text", "").lower()
            if "quality" in text:
                strengths.append("High quality product")
            if "fast" in text or "quick" in text:
                strengths.append("Fast delivery")
            if "recommend" in text:
                strengths.append("Highly recommended by customers")
            if "value" in text or "price" in text:
                strengths.append("Good value for money")
        
        # Remove duplicates and return top 5
        return list(set(strengths))[:5] if strengths else ["High customer satisfaction"]
    
    def _extract_weaknesses(self, reviews: List[Dict]) -> List[str]:
        """Extract product weaknesses from negative reviews."""
        if not reviews:
            return []
        
        weaknesses = []
        negative_reviews = [r for r in reviews if r.get("rating", 0) <= 2]
        
        for review in negative_reviews[:3]:  # Check top 3 negative reviews
            text = review.get("text", "").lower()
            if "expensive" in text or "price" in text:
                weaknesses.append("Price concerns")
            if "slow" in text or "late" in text:
                weaknesses.append("Shipping delays")
            if "quality" in text:
                weaknesses.append("Quality issues")
            if "size" in text:
                weaknesses.append("Sizing issues")
        
        # Remove duplicates and return top 3
        return list(set(weaknesses))[:3]

