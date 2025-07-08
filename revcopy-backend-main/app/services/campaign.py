"""
Campaign service for managing marketing campaigns.
"""

from typing import Dict, List, Optional
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Campaign, GeneratedContent, ContentType
from app.models.analysis import Analysis

# Configure logging
logger = structlog.get_logger(__name__)


class CampaignService:
    """Service for marketing campaign management."""
    
    async def create_campaign(
        self,
        analysis: Analysis,
        campaign_data: Dict,
        db: AsyncSession
    ) -> Campaign:
        """Create a new marketing campaign."""
        try:
            logger.info("Creating campaign", analysis_id=analysis.id, name=campaign_data.get("name"))
            
            campaign = Campaign(
                analysis_id=analysis.id,
                name=campaign_data["name"],
                description=campaign_data.get("description"),
                campaign_goals=campaign_data.get("goals", []),
                target_platforms=campaign_data.get("platforms", []),
                target_audience=campaign_data.get("target_audience"),
                budget_range=campaign_data.get("budget_range"),
                timeline=campaign_data.get("timeline"),
            )
            
            db.add(campaign)
            await db.commit()
            await db.refresh(campaign)
            
            logger.info("Campaign created successfully", campaign_id=campaign.id)
            return campaign
            
        except Exception as e:
            logger.error("Campaign creation failed", error=str(e))
            await db.rollback()
            raise
    
    async def get_campaign_stats(self, campaign: Campaign) -> Dict:
        """Get campaign statistics."""
        try:
            total_content = len(campaign.generated_contents)
            completed_content = sum(
                1 for content in campaign.generated_contents 
                if content.status.value == "completed"
            )
            
            content_by_type = {}
            for content in campaign.generated_contents:
                content_type = content.content_type.value
                content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
            
            completion_rate = (completed_content / total_content * 100) if total_content > 0 else 0
            
            return {
                "campaign_id": campaign.id,
                "total_content_pieces": total_content,
                "completed_content_pieces": completed_content,
                "completion_rate": completion_rate,
                "content_by_type": content_by_type,
                "created_at": campaign.created_at,
                "last_updated": campaign.updated_at,
            }
            
        except Exception as e:
            logger.error("Failed to get campaign stats", error=str(e), campaign_id=campaign.id)
            raise

