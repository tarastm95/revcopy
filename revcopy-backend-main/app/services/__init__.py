"""
Services module for business logic and external integrations.

This module contains the core business logic services:
- ProductService: Product management and e-commerce integration
- AnalysisService: Review analysis and NLP processing
- GenerationService: AI-powered content generation
- CampaignService: Marketing campaign management
- ReviewScrapingService: Review collection from e-commerce platforms
- AIService: AI model management and processing
"""

from .product import ProductService
from .analysis import AnalysisService
from .generation import GenerationService
from .campaign import CampaignService
from .review_scraping import ReviewScrapingService
from .ai import AIService
from .amazon_crawler_client import AmazonCrawlerClient

__all__ = [
    "ProductService",
    "AnalysisService", 
    "GenerationService",
    "CampaignService",
    "ReviewScrapingService",
    "AIService",
    "AmazonCrawlerClient",
] 