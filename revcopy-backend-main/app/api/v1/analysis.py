"""
Analysis API endpoints for review processing and NLP analysis.
Handles product analysis, sentiment analysis, and insight generation.
"""

from typing import List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_async_session, check_usage_limits
from app.models.user import User
from app.models.product import Product
from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    SentimentResponse,
    ReviewInsightResponse,
)

# Configure logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Background task imports (will be implemented later)
# from app.tasks.analysis import start_product_analysis, process_review_analysis


@router.post("/start", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    analysis_request: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Start a new product analysis.
    
    Initiates analysis of reviews for a specific product.
    The analysis runs in the background and updates status.
    
    Args:
        analysis_request: Analysis configuration and parameters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        AnalysisResponse: Created analysis with initial status
        
    Raises:
        HTTPException: If product not found or analysis fails to start
    """
    try:
        logger.info(
            "Starting product analysis",
            user_id=current_user.id,
            product_id=analysis_request.product_id,
            analysis_type=analysis_request.analysis_type
        )
        
        # Check if product exists and belongs to user
        result = await db.execute(
            select(Product).where(
                and_(
                    Product.id == analysis_request.product_id,
                    Product.user_id == current_user.id
                )
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning(
                "Analysis requested for non-existent product",
                user_id=current_user.id,
                product_id=analysis_request.product_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check for existing pending/processing analysis
        existing_analysis = await db.execute(
            select(Analysis).where(
                and_(
                    Analysis.product_id == analysis_request.product_id,
                    Analysis.status.in_([AnalysisStatus.PENDING, AnalysisStatus.PROCESSING])
                )
            )
        )
        if existing_analysis.scalar_one_or_none():
            logger.warning(
                "Analysis already in progress for product",
                product_id=analysis_request.product_id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Analysis already in progress for this product"
            )
        
        # Create new analysis
        analysis = Analysis(
            product_id=analysis_request.product_id,
            analysis_type=analysis_request.analysis_type,
            status=AnalysisStatus.PENDING,
            processing_parameters={
                "max_reviews": analysis_request.max_reviews,
            }
        )
        
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # Start background analysis task
        # TODO: Implement background task
        # background_tasks.add_task(start_product_analysis, analysis.id)
        
        logger.info(
            "Analysis created successfully",
            analysis_id=analysis.id,
            product_id=product.id,
            user_id=current_user.id
        )
        
        return AnalysisResponse.from_orm(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to start analysis",
            error=str(e),
            user_id=current_user.id,
            product_id=analysis_request.product_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis"
        )


@router.get("/", response_model=List[AnalysisResponse])
async def list_analyses(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    status: Optional[AnalysisStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of analyses to return"),
    offset: int = Query(0, ge=0, description="Number of analyses to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    ) -> List[AnalysisResponse]:
    """
    List user's analyses with optional filtering.
    
    Args:
        product_id: Optional product ID filter
        status: Optional status filter
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        AnalysisListResponse: List of analyses with metadata
    """
    try:
        logger.info(
            "Listing analyses",
            user_id=current_user.id,
            product_id=product_id,
            status=status
        )
        
        # Build query
        query = select(Analysis).join(Product).where(Product.user_id == current_user.id)
        
        if product_id:
            query = query.where(Analysis.product_id == product_id)
        
        if status:
            query = query.where(Analysis.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Analysis.created_at))
        
        # Add pagination
        query = query.offset(offset).limit(limit)
        
        # Load with relationships
        query = query.options(selectinload(Analysis.product))
        
        # Execute query
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        # Get total count for pagination
        count_query = select(Analysis).join(Product).where(Product.user_id == current_user.id)
        if product_id:
            count_query = count_query.where(Analysis.product_id == product_id)
        if status:
            count_query = count_query.where(Analysis.status == status)
        
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        logger.info(
            "Analyses retrieved successfully",
            user_id=current_user.id,
            count=len(analyses),
            total=total
        )
        
        return AnalysisListResponse(
            analyses=[AnalysisResponse.from_orm(analysis) for analysis in analyses],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(
            "Failed to list analyses",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analyses"
        )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    # TODO: Re-enable authentication after implementing proper auth flow
    # current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Get specific analysis by ID.
    
    Args:
        analysis_id: Analysis ID
        db: Database session
        
    Returns:
        AnalysisResponse: Analysis details
        
    Raises:
        HTTPException: If analysis not found
    """
    try:
        logger.info(
            "Retrieving analysis",
            analysis_id=analysis_id
        )
        
        # Get analysis with all required relationships loaded
        result = await db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(
                selectinload(Analysis.product),
                selectinload(Analysis.review_insights),
                selectinload(Analysis.sentiment_analyses)
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            logger.warning(
                "Analysis not found",
                analysis_id=analysis_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        logger.info(
            "Analysis retrieved successfully",
            analysis_id=analysis_id
        )
        
        return AnalysisResponse.from_orm(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve analysis",
            error=str(e),
            analysis_id=analysis_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )


@router.get("/{analysis_id}/status", response_model=dict)
async def get_analysis_status(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    # TODO: Re-enable authentication after implementing proper auth flow
    # current_user: User = Depends(get_current_user),
    ) -> dict:
    """
    Get analysis status and progress.
    
    Args:
        analysis_id: Analysis ID
        db: Database session
        
    Returns:
        AnalysisStatusResponse: Current status and progress information
        
    Raises:
        HTTPException: If analysis not found
    """
    try:
        result = await db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Calculate progress percentage
        progress_percentage = 0
        if analysis.status == AnalysisStatus.PROCESSING:
            progress_percentage = min(50, analysis.total_reviews_processed * 2)  # Simple calculation
        elif analysis.status == AnalysisStatus.COMPLETED:
            progress_percentage = 100
        
        return {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "progress_percentage": progress_percentage,
            "total_reviews_processed": analysis.total_reviews_processed,
            "started_at": analysis.started_at,
            "completed_at": analysis.completed_at,
            "error_message": analysis.error_message,
            "processing_time_seconds": analysis.processing_time_seconds,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve analysis status",
            error=str(e),
            analysis_id=analysis_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis status"
        )


# @router.post("/quick", response_model=SentimentAnalysisResponse)
# async def quick_sentiment_analysis(
#     quick_analysis: QuickAnalysisRequest,
#     current_user: User = Depends(get_current_user),
#     _: bool = Depends(check_usage_limits),
# ) -> SentimentAnalysisResponse:
# """
# Commented out until missing schemas are implemented
# """
# pass


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an analysis and all related data.
    
    Args:
        analysis_id: Analysis ID to delete
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If analysis not found or cannot be deleted
    """
    try:
        logger.info(
            "Deleting analysis",
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        # Get analysis with ownership check
        result = await db.execute(
            select(Analysis)
            .join(Product)
            .where(
                and_(
                    Analysis.id == analysis_id,
                    Product.user_id == current_user.id
                )
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            logger.warning(
                "Analysis not found for deletion",
                analysis_id=analysis_id,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Check if analysis is currently processing
        if analysis.status == AnalysisStatus.PROCESSING:
            logger.warning(
                "Attempted to delete processing analysis",
                analysis_id=analysis_id,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete analysis that is currently processing"
            )
        
        # Delete analysis (cascade will handle related data)
        await db.delete(analysis)
        await db.commit()
        
        logger.info(
            "Analysis deleted successfully",
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete analysis",
            error=str(e),
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )


@router.post("/{analysis_id}/restart")
async def restart_analysis(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    """
    Restart a failed or completed analysis.
    
    Args:
        analysis_id: Analysis ID to restart
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        AnalysisResponse: Restarted analysis
        
    Raises:
        HTTPException: If analysis cannot be restarted
    """
    try:
        logger.info(
            "Restarting analysis",
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        # Get analysis with ownership check
        result = await db.execute(
            select(Analysis)
            .join(Product)
            .where(
                and_(
                    Analysis.id == analysis_id,
                    Product.user_id == current_user.id
                )
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Check if analysis can be restarted
        if analysis.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Analysis is already running"
            )
        
        # Reset analysis status
        analysis.status = AnalysisStatus.PENDING
        analysis.started_at = None
        analysis.completed_at = None
        analysis.error_message = None
        analysis.processing_time_seconds = None
        
        await db.commit()
        await db.refresh(analysis)
        
        # Start background analysis task
        # TODO: Implement background task
        # background_tasks.add_task(start_product_analysis, analysis.id)
        
        logger.info(
            "Analysis restarted successfully",
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        return AnalysisResponse.from_orm(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to restart analysis",
            error=str(e),
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart analysis"
        )


@router.get("/{analysis_id}/results", response_model=dict)
async def get_analysis_results(
    analysis_id: int,
    db: AsyncSession = Depends(get_async_session),
    # TODO: Re-enable authentication after implementing proper auth flow
    # current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get analysis results for a specific analysis.
    
    Args:
        analysis_id: Analysis ID to get results for
        db: Database session
        
    Returns:
        dict: Analysis results and insights
    """
    try:
        logger.info("Fetching analysis results", analysis_id=analysis_id)
        
        # Get analysis from database
        query = select(Analysis).where(Analysis.id == analysis_id)
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        # Return mock results for now - in production this would include real analysis
        return {
            "analysis_id": analysis_id,
            "status": analysis.status.value if analysis.status else "completed",
            "results": {
                "sentiment_analysis": {
                    "overall_sentiment": "positive",
                    "sentiment_score": 0.75,
                    "positive_reviews": 85,
                    "negative_reviews": 15,
                    "neutral_reviews": 0
                },
                "key_insights": [
                    "Customers love the product quality",
                    "Fast shipping is frequently mentioned",
                    "Great customer service experience",
                    "Value for money is excellent"
                ],
                "pain_points": [
                    "Some packaging issues reported",
                    "Delivery delays in remote areas"
                ],
                "review_summary": {
                    "total_reviews": 100,
                    "average_rating": 4.2,
                    "review_breakdown": {
                        "5_star": 45,
                        "4_star": 30,
                        "3_star": 15,
                        "2_star": 7,
                        "1_star": 3
                    }
                },
                "recommendations": [
                    "Highlight fast shipping in marketing",
                    "Address packaging concerns",
                    "Leverage positive quality feedback"
                ]
            },
            "metadata": {
                "processed_at": "2025-01-05T15:24:05.447932",
                "processing_time_ms": 1500,
                "reviews_analyzed": 100
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch analysis results", analysis_id=analysis_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis results"
        ) 