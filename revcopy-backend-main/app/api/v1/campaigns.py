"""
Campaign management API endpoints with real database operations.
"""

from typing import List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.deps import get_async_session
from app.models.content import Campaign, GeneratedContent, ContentType
from app.schemas.generation import CampaignCreate, CampaignResponse, ContentGenerationResponse

# Configure logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new campaign with real database persistence.
    """
    try:
        logger.info("Creating new campaign", name=campaign_data.name)
        
        # Create campaign instance
        campaign = Campaign(
            name=campaign_data.name,
            description=campaign_data.description,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to database
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        
        logger.info("Campaign created successfully", campaign_id=campaign.id, name=campaign.name)
        
        # Return campaign response
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            is_active=campaign.is_active,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            content=[]
        )
        
    except Exception as e:
        logger.error("Failed to create campaign", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get list of campaigns with real database queries.
    """
    try:
        # Build query
        query = select(Campaign)
        
        if active_only:
            query = query.where(Campaign.is_active == True)
            
        query = query.order_by(Campaign.created_at.desc()).offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        campaigns = result.scalars().all()
        
        # Convert to response format
        campaign_responses = []
        for campaign in campaigns:
            # Get content for this campaign
            content_query = select(GeneratedContent).where(
                GeneratedContent.campaign_id == campaign.id
            )
            content_result = await db.execute(content_query)
            content_items = content_result.scalars().all()
            
            # Convert content to response format
            content_responses = [
                ContentGenerationResponse(
                    id=content.id,
                    content_type=content.content_type,
                    title=content.title or f"{content.content_type.title()} Content",
                    content=content.content,
                    parameters=content.parameters,
                    status=content.status,
                    word_count=len(content.content.split()) if content.content else 0,
                    character_count=len(content.content) if content.content else 0,
                    language=content.language or "en",
                    created_at=content.created_at
                )
                for content in content_items
            ]
            
            campaign_responses.append(CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                is_active=campaign.is_active,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
                content=content_responses
            ))
        
        logger.info("Retrieved campaigns", count=len(campaign_responses))
        return campaign_responses
        
    except Exception as e:
        logger.error("Failed to retrieve campaigns", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaigns: {str(e)}"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get a specific campaign by ID with real database lookup.
    """
    try:
        # Get campaign
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        
        # Get content for this campaign
        content_query = select(GeneratedContent).where(
            GeneratedContent.campaign_id == campaign.id
        )
        content_result = await db.execute(content_query)
        content_items = content_result.scalars().all()
        
        # Convert content to response format
        content_responses = [
            ContentGenerationResponse(
                id=content.id,
                content_type=content.content_type,
                title=content.title or f"{content.content_type.title()} Content",
                content=content.content,
                parameters=content.parameters,
                status=content.status,
                word_count=len(content.content.split()) if content.content else 0,
                character_count=len(content.content) if content.content else 0,
                language=content.language or "en",
                created_at=content.created_at
            )
            for content in content_items
        ]
        
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            is_active=campaign.is_active,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            content=content_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve campaign", campaign_id=campaign_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign: {str(e)}"
        )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update an existing campaign with real database operations.
    """
    try:
        # Get existing campaign
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        
        # Update campaign
        campaign.name = campaign_data.name
        campaign.description = campaign_data.description
        campaign.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(campaign)
        
        logger.info("Campaign updated successfully", campaign_id=campaign.id, name=campaign.name)
        
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            is_active=campaign.is_active,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            content=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update campaign", campaign_id=campaign_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a campaign with real database operations.
    """
    try:
        # Get existing campaign
        query = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        
        # Delete campaign (this will cascade to associated content)
        await db.delete(campaign)
        await db.commit()
        
        logger.info("Campaign deleted successfully", campaign_id=campaign_id)
        
        return {"message": f"Campaign {campaign_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete campaign", campaign_id=campaign_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )


@router.post("/{campaign_id}/content", response_model=ContentGenerationResponse)
async def add_content_to_campaign(
    campaign_id: int,
    content_data: dict,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Add generated content to a campaign with real database operations.
    """
    try:
        # Verify campaign exists
        campaign_query = select(Campaign).where(Campaign.id == campaign_id)
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        
        # Create content instance
        content = GeneratedContent(
            campaign_id=campaign_id,
            content_type=ContentType(content_data["content_type"]),
            title=content_data.get("title", f"{content_data['content_type'].title()} Content"),
            content=content_data["content"],
            parameters=content_data.get("parameters", {}),
            status=content_data.get("status", "completed"),
            language=content_data.get("language", "en"),
            created_at=datetime.utcnow()
        )
        
        # Add to database
        db.add(content)
        
        # Update campaign updated_at
        campaign.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(content)
        
        logger.info("Content added to campaign", campaign_id=campaign_id, content_id=content.id)
        
        return ContentGenerationResponse(
            id=content.id,
            content_type=content.content_type,
            title=content.title,
            content=content.content,
            parameters=content.parameters,
            status=content.status,
            word_count=len(content.content.split()) if content.content else 0,
            character_count=len(content.content) if content.content else 0,
            language=content.language,
            created_at=content.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add content to campaign", campaign_id=campaign_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add content to campaign: {str(e)}"
        ) 