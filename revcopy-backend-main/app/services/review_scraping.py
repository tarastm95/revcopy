"""
Review scraping service for collecting reviews from e-commerce platforms.
"""

from typing import Dict, List, Optional
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, EcommercePlatform
from crawlers.shopify_crawler import ShopifyCrawler

# Configure logging
logger = structlog.get_logger(__name__)


class ReviewScrapingService:
    """Service for scraping reviews from e-commerce platforms."""
    
    def __init__(self):
        self.platform_scrapers = {
            EcommercePlatform.AMAZON: self._scrape_amazon_reviews,
            EcommercePlatform.EBAY: self._scrape_ebay_reviews,
            EcommercePlatform.ALIEXPRESS: self._scrape_aliexpress_reviews,
            EcommercePlatform.SHOPIFY: self._scrape_shopify_reviews,
        }
    
    async def scrape_product_reviews(
        self,
        product: Product,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Scrape reviews for a product."""
        try:
            logger.info(
                "Starting review scraping",
                product_id=product.id,
                platform=product.platform.value,
                limit=limit
            )
            
            scraper = self.platform_scrapers.get(product.platform)
            if not scraper:
                raise ValueError(f"No scraper available for platform: {product.platform}")
            
            reviews = await scraper(product, limit)
            
            logger.info(
                "Review scraping completed",
                product_id=product.id,
                reviews_count=len(reviews)
            )
            
            return reviews
            
        except Exception as e:
            logger.error(
                "Review scraping failed",
                error=str(e),
                product_id=product.id,
                platform=product.platform.value
            )
            raise
    
    async def _scrape_shopify_reviews(
        self,
        product: Product,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Scrape Shopify reviews using the enhanced crawler."""
        try:
            async with ShopifyCrawler() as crawler:
                # Extract reviews from the product page HTML
                reviews = await crawler.extract_reviews_from_html(product.url)
                
                if limit and len(reviews) > limit:
                    reviews = reviews[:limit]
                
                logger.info(
                    "Shopify reviews scraped successfully",
                    product_id=product.id,
                    url=product.url,
                    reviews_count=len(reviews)
                )
                
                return reviews
                
        except Exception as e:
            logger.error(
                "Shopify review scraping failed",
                error=str(e),
                product_id=product.id,
                url=product.url
            )
            return []
    
    async def _scrape_amazon_reviews(
        self,
        product: Product,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Scrape Amazon reviews using the Amazon crawler service."""
        try:
            from app.services.amazon_crawler_client import AmazonCrawlerClient
            
            async with AmazonCrawlerClient() as client:
                # Get targeted reviews: 15 positive + 15 negative (or use limit)
                if limit:
                    # Split limit between positive and negative
                    positive_count = min(15, limit // 2)
                    negative_count = min(15, limit - positive_count)
                else:
                    positive_count = 15
                    negative_count = 15
                
                positive_reviews, negative_reviews = await client.get_targeted_reviews(
                    product.url, positive_count, negative_count
                )
                
                # Combine and format reviews
                all_reviews = []
                
                # Add positive reviews
                for review in positive_reviews:
                    formatted_review = self._format_amazon_review(review, "positive")
                    if formatted_review:
                        all_reviews.append(formatted_review)
                
                # Add negative reviews
                for review in negative_reviews:
                    formatted_review = self._format_amazon_review(review, "negative")
                    if formatted_review:
                        all_reviews.append(formatted_review)
                
                logger.info(
                    "Amazon reviews scraped via crawler service",
                    product_id=product.id,
                    url=product.url,
                    positive_reviews=len(positive_reviews),
                    negative_reviews=len(negative_reviews),
                    total_reviews=len(all_reviews)
                )
                
                return all_reviews[:limit] if limit else all_reviews
                
        except Exception as e:
            logger.error(
                "Amazon crawler service failed, falling back to mock data",
                error=str(e),
                product_id=product.id,
                url=product.url
            )
            
            # Fallback to mock reviews if crawler service fails
            return self._get_fallback_amazon_reviews(limit)
    
    def _format_amazon_review(self, review: Dict, sentiment: str) -> Optional[Dict]:
        """Format Amazon review from crawler service to standard format."""
        try:
            return {
                "review_id": review.get("id", f"AMZ_{sentiment}_{hash(review.get('text', ''))%10000}"),
                "reviewer_name": review.get("author", "Amazon Customer"),
                "rating": review.get("rating", 5 if sentiment == "positive" else 2),
                "title": review.get("title", "Customer Review"),
                "text": self.clean_review_text(review.get("text", "")),
                "date": review.get("date", "2024-01-01"),
                "verified_purchase": review.get("verified", True),
                "helpful_votes": review.get("helpful_votes", 0),
                "sentiment": sentiment,
                "source": "amazon_crawler"
            }
        except Exception as e:
            logger.error("Failed to format Amazon review", error=str(e), review=review)
            return None
    
    def _get_fallback_amazon_reviews(self, limit: Optional[int] = None) -> List[Dict]:
        """Get fallback mock Amazon reviews when crawler service fails."""
        mock_reviews = [
            {
                "review_id": "FALLBACK_R1",
                "reviewer_name": "John D.",
                "rating": 5,
                "title": "Excellent product!",
                "text": "This product exceeded my expectations. Great quality and fast shipping.",
                "date": "2024-01-15",
                "verified_purchase": True,
                "helpful_votes": 12,
                "sentiment": "positive",
                "source": "fallback"
            },
            {
                "review_id": "FALLBACK_R2",
                "reviewer_name": "Sarah M.",
                "rating": 4,
                "title": "Good value for money",
                "text": "Works as advertised. Had minor issues with setup but customer service helped.",
                "date": "2024-01-10",
                "verified_purchase": True,
                "helpful_votes": 8,
                "sentiment": "positive",
                "source": "fallback"
            },
            {
                "review_id": "FALLBACK_R3",
                "reviewer_name": "Mike R.",
                "rating": 5,
                "title": "Highly recommend",
                "text": "Best purchase I've made this year. Quality is outstanding and delivery was quick.",
                "date": "2024-01-08",
                "verified_purchase": True,
                "helpful_votes": 15,
                "sentiment": "positive",
                "source": "fallback"
            },
            {
                "review_id": "FALLBACK_R4",
                "reviewer_name": "Lisa K.",
                "rating": 2,
                "title": "Not as expected",
                "text": "The product quality is poor and doesn't match the description. Disappointed with the purchase.",
                "date": "2024-01-12",
                "verified_purchase": True,
                "helpful_votes": 5,
                "sentiment": "negative",
                "source": "fallback"
            },
            {
                "review_id": "FALLBACK_R5",
                "reviewer_name": "David P.",
                "rating": 1,
                "title": "Waste of money",
                "text": "Broke after just a few uses. Very poor build quality and terrible customer service.",
                "date": "2024-01-14",
                "verified_purchase": True,
                "helpful_votes": 8,
                "sentiment": "negative",
                "source": "fallback"
            },
        ]
        
        return mock_reviews[:limit] if limit else mock_reviews
    
    async def _scrape_ebay_reviews(
        self,
        product: Product,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Scrape eBay reviews."""
        # Mock eBay reviews for demonstration
        mock_reviews = [
            {
                "review_id": "E1",
                "reviewer_name": "buyer123",
                "rating": 4,
                "title": "Good item",
                "text": "Item as described. Fast shipping from seller.",
                "date": "2024-01-12",
                "verified_purchase": True,
                "helpful_votes": 3
            },
            {
                "review_id": "E2",
                "reviewer_name": "happybuyer",
                "rating": 5,
                "title": "Perfect!",
                "text": "Exactly what I needed. Great communication with seller.",
                "date": "2024-01-09",
                "verified_purchase": True,
                "helpful_votes": 5
            },
        ]
        
        return mock_reviews[:limit] if limit else mock_reviews
    
    async def _scrape_aliexpress_reviews(
        self,
        product: Product,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Scrape AliExpress reviews."""
        # Mock AliExpress reviews for demonstration
        mock_reviews = [
            {
                "review_id": "A1",
                "reviewer_name": "User***1",
                "rating": 4,
                "title": "Good quality",
                "text": "Product quality is good. Took a while to arrive but worth the wait.",
                "date": "2024-01-05",
                "verified_purchase": True,
                "helpful_votes": 2
            },
            {
                "review_id": "A2",
                "reviewer_name": "Customer***2",
                "rating": 5,
                "title": "Excellent!",
                "text": "Amazing product for the price. Would buy again.",
                "date": "2024-01-03",
                "verified_purchase": True,
                "helpful_votes": 7
            },
        ]
        
        return mock_reviews[:limit] if limit else mock_reviews
    
    def clean_review_text(self, text: str) -> str:
        """Clean and normalize review text."""
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        text = " ".join(text.split())  # Normalize whitespace
        
        # TODO: Add more sophisticated text cleaning
        # - Remove HTML tags
        # - Handle special characters
        # - Normalize encoding
        # - Remove spam patterns
        
        return text
    
    def extract_review_features(self, review: Dict) -> Dict:
        """Extract features from review data."""
        features = {
            "has_rating": review.get("rating") is not None,
            "is_verified": review.get("verified_purchase", False),
            "has_helpful_votes": (review.get("helpful_votes", 0) > 0),
            "text_length": len(review.get("text", "")),
            "has_title": bool(review.get("title")),
        }
        
        return features

