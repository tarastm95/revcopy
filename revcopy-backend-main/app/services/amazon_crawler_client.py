"""
Amazon Crawler Client Service.
Handles communication with the Amazon crawler Go microservice.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

import aiohttp
import structlog
from app.core.config import get_settings

# Configure logging
logger = structlog.get_logger(__name__)

settings = get_settings()


class AmazonCrawlerClient:
    """Client for Amazon crawler Go microservice."""
    
    def __init__(self):
        self.base_url = settings.AMAZON_CRAWLER_URL
        self.timeout = settings.AMAZON_CRAWLER_TIMEOUT
        self.username = settings.AMAZON_CRAWLER_USERNAME
        self.password = settings.AMAZON_CRAWLER_PASSWORD
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'RevCopy-Backend/1.0'
            }
        )
        await self._ensure_authenticated()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._auth_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return
        
        await self._authenticate()
    
    async def _authenticate(self) -> None:
        """Authenticate with the Amazon crawler service."""
        try:
            login_url = f"{self.base_url}/api/v1/auth/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info("Authenticating with Amazon crawler service", url=login_url)
            
            async with self._session.post(login_url, json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self._auth_token = data.get("access_token")
                    
                    # Assume token expires in 1 hour if not specified
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
                    
                    # Update session headers with auth token
                    self._session.headers.update({
                        'Authorization': f'Bearer {self._auth_token}'
                    })
                    
                    logger.info("Amazon crawler authentication successful")
                else:
                    error_data = await response.text()
                    raise Exception(f"Authentication failed: HTTP {response.status} - {error_data}")
        
        except Exception as e:
            logger.error("Amazon crawler authentication failed", error=str(e))
            raise
    
    async def scrape_product(self, product_url: str) -> Optional[Dict]:
        """
        Scrape a single Amazon product.
        
        Args:
            product_url: Amazon product URL to scrape
            
        Returns:
            Product data dictionary or None if failed
        """
        try:
            await self._ensure_authenticated()
            
            scrape_url = f"{self.base_url}/api/v1/amazon/scrape"
            scrape_data = {"url": product_url}
            
            logger.info("Scraping Amazon product", url=product_url)
            
            async with self._session.post(scrape_url, json=scrape_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success") and data.get("data"):
                        product_data = data["data"]
                        logger.info(
                            "Amazon product scraped successfully",
                            asin=product_data.get("asin"),
                            title=product_data.get("title", "")[:50]
                        )
                        return product_data
                    else:
                        logger.error("Amazon scraping failed", response_data=data)
                        return None
                else:
                    error_data = await response.text()
                    logger.error(
                        "Amazon scraping HTTP error",
                        status=response.status,
                        error=error_data,
                        url=product_url
                    )
                    return None
        
        except Exception as e:
            logger.error("Amazon scraping error", error=str(e), url=product_url)
            return None
    
    async def get_targeted_reviews(
        self, 
        product_url: str, 
        positive_count: int = 15, 
        negative_count: int = 15
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Get targeted reviews: specific number of positive and negative reviews.
        
        Args:
            product_url: Amazon product URL
            positive_count: Number of positive reviews (4-5 stars)
            negative_count: Number of negative reviews (1-2 stars)
            
        Returns:
            Tuple of (positive_reviews, negative_reviews)
        """
        try:
            # First scrape the product to get ASIN and basic info
            product_data = await self.scrape_product(product_url)
            
            if not product_data:
                logger.error("Could not get product data for targeted reviews", url=product_url)
                return [], []
            
            asin = product_data.get("asin")
            if not asin:
                logger.error("No ASIN found in product data", product_data=product_data)
                return [], []
            
            # Get product details which should include reviews
            all_reviews = product_data.get("reviews", [])
            
            if not all_reviews:
                logger.warning("No reviews found in product data", asin=asin)
                return [], []
            
            # Filter reviews by rating
            positive_reviews = [
                review for review in all_reviews 
                if review.get("rating", 0) >= 4
            ][:positive_count]
            
            negative_reviews = [
                review for review in all_reviews 
                if review.get("rating", 0) <= 2
            ][:negative_count]
            
            logger.info(
                "Targeted reviews extracted",
                asin=asin,
                positive_count=len(positive_reviews),
                negative_count=len(negative_reviews),
                total_available=len(all_reviews)
            )
            
            return positive_reviews, negative_reviews
        
        except Exception as e:
            logger.error("Targeted reviews extraction failed", error=str(e), url=product_url)
            return [], []
    
    async def bulk_scrape_products(self, product_urls: List[str]) -> List[Dict]:
        """
        Scrape multiple Amazon products in bulk.
        
        Args:
            product_urls: List of Amazon product URLs (max 10)
            
        Returns:
            List of product data dictionaries
        """
        try:
            if len(product_urls) > 10:
                logger.warning("Too many URLs for bulk scraping, limiting to 10", count=len(product_urls))
                product_urls = product_urls[:10]
            
            await self._ensure_authenticated()
            
            bulk_url = f"{self.base_url}/api/v1/amazon/bulk-scrape"
            bulk_data = {"urls": product_urls}
            
            logger.info("Bulk scraping Amazon products", count=len(product_urls))
            
            async with self._session.post(bulk_url, json=bulk_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success") and data.get("data"):
                        results = data["data"]
                        successful = [r for r in results if r.get("success")]
                        
                        logger.info(
                            "Bulk scraping completed",
                            total=len(results),
                            successful=len(successful),
                            failed=len(results) - len(successful)
                        )
                        
                        return [r["data"] for r in successful if r.get("data")]
                    else:
                        logger.error("Bulk scraping failed", response_data=data)
                        return []
                else:
                    error_data = await response.text()
                    logger.error(
                        "Bulk scraping HTTP error",
                        status=response.status,
                        error=error_data
                    )
                    return []
        
        except Exception as e:
            logger.error("Bulk scraping error", error=str(e))
            return []
    
    async def health_check(self) -> bool:
        """
        Check if the Amazon crawler service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            health_url = f"{self.base_url}/health"
            
            async with self._session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    is_healthy = data.get("status") == "healthy"
                    
                    logger.info("Amazon crawler health check", healthy=is_healthy)
                    return is_healthy
                else:
                    logger.error("Amazon crawler health check failed", status=response.status)
                    return False
        
        except Exception as e:
            logger.error("Amazon crawler health check error", error=str(e))
            return False


# Utility function for quick access
async def get_amazon_product_data(product_url: str) -> Optional[Dict]:
    """
    Quick utility to get Amazon product data.
    
    Args:
        product_url: Amazon product URL
        
    Returns:
        Product data dictionary or None
    """
    try:
        async with AmazonCrawlerClient() as client:
            return await client.scrape_product(product_url)
    except Exception as e:
        logger.error("Quick Amazon product fetch failed", error=str(e), url=product_url)
        return None


async def get_targeted_amazon_reviews(
    product_url: str, 
    positive_count: int = 15, 
    negative_count: int = 15
) -> Tuple[List[Dict], List[Dict]]:
    """
    Quick utility to get targeted Amazon reviews.
    
    Args:
        product_url: Amazon product URL
        positive_count: Number of positive reviews needed
        negative_count: Number of negative reviews needed
        
    Returns:
        Tuple of (positive_reviews, negative_reviews)
    """
    try:
        async with AmazonCrawlerClient() as client:
            return await client.get_targeted_reviews(product_url, positive_count, negative_count)
    except Exception as e:
        logger.error("Quick Amazon reviews fetch failed", error=str(e), url=product_url)
        return [], [] 