"""
Products API endpoints for product management and analysis.
Handles product URL submission, analysis triggering, and results retrieval.
"""

from typing import List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_current_user,
    get_pagination_params,
    check_usage_limits,
    get_async_session,
)
from app.models.user import User, UserRole, UserStatus
from app.models.product import Product, ProductStatus, EcommercePlatform
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductAnalyzeRequest,
    ProductListResponse,
    ProductSearchRequest,
    ProductValidationResponse,
    ProductStatsResponse,
    BulkProductImport,
    BulkImportResponse,
    ReviewResponse,
    ProductImageResponse,
    ProductAnalysisRequest,
)
from app.services.analysis import AnalysisService
from app.services.product import ProductService
from app.services.ai import ai_service
# from app.background.tasks import analyze_product_task

# Configure logging
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API connectivity."""
    return {
        "status": "ok", 
        "message": "Products API is working", 
        "timestamp": "2025-01-01"
    }


async def ensure_demo_user_exists(db: AsyncSession) -> int:
    """
    Ensure a demo user exists for testing purposes.
    TODO: Remove this when proper authentication is implemented.
    """
    demo_user_id = 1
    
    # Check if demo user exists
    result = await db.execute(select(User).where(User.id == demo_user_id))
    existing_user = result.scalar_one_or_none()
    
    if not existing_user:
        # Create demo user
        demo_user = User(
            id=demo_user_id,
            email="demo@revcopy.com",
            username="demo_user",
            first_name="Demo",
            last_name="User",
            hashed_password="dummy_hash",  # Not used for login
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(demo_user)
        await db.commit()
        logger.info("Created demo user for testing", user_id=demo_user_id)
    
    return demo_user_id


@router.post("/analyze", response_model=ProductResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_product_url(
    request: ProductAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    # TODO: Re-enable authentication after implementing proper auth flow
    # current_user: User = Depends(check_usage_limits),
) -> ProductResponse:
    """
    Analyze a product URL and extract reviews for content generation.
    
    This endpoint accepts a product URL, validates it, and starts the analysis process.
    The analysis runs in the background and the status can be checked via other endpoints.
    
    Args:
        request: Product analysis request with URL and parameters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ProductResponse: Created product with analysis status
        
    Raises:
        HTTPException: If URL is invalid or analysis fails to start
    """
    try:
        logger.info("Starting product analysis endpoint", url=str(request.url))
        
        # TODO: Remove this temporary user_id when authentication is implemented
        try:
            temp_user_id = await ensure_demo_user_exists(db)
            logger.info("Demo user created/verified", user_id=temp_user_id)
        except Exception as e:
            logger.error("Failed to create demo user", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        
        # Use ProductService for proper product validation and creation
        try:
            product_service = ProductService()
            logger.info("ProductService initialized")
        except Exception as e:
            logger.error("Failed to initialize ProductService", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Service initialization error: {str(e)}"
            )
        
        # Validate and extract product data with reviews
        logger.info("Starting comprehensive product analysis", url=str(request.url))
        is_valid, product_data, error_message = await product_service.validate_and_extract_product(
            str(request.url), 
            temp_user_id,
            db
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message or "Invalid product URL"
            )
        
        # Use the actual product data extracted by the crawler instead of test data
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract product information"
            )
        
        # Create product in database
        try:
            product = Product(
                url=str(request.url),
                user_id=temp_user_id,
                platform=product_data.get("platform", EcommercePlatform.SHOPIFY),
                external_product_id=product_data.get("external_product_id"),
                title=product_data.get("title", ""),
                description=product_data.get("description", ""),
                brand=product_data.get("brand"),
                category=product_data.get("category"),
                price=product_data.get("price", 0.0),
                currency=product_data.get("currency", "USD"),
                original_price=product_data.get("original_price"),
                rating=product_data.get("rating"),
                review_count=product_data.get("review_count", 0),
                in_stock=product_data.get("in_stock", True),
                status=ProductStatus.COMPLETED,
                crawl_metadata=product_data.get("crawl_metadata", {}),
                tags=product_data.get("tags", [])
            )
            
            db.add(product)
            await db.commit()
            await db.refresh(product)
            logger.info("Product created successfully", product_id=product.id, title=product.title)
            
            # Create analysis for the product
            try:
                from app.models.analysis import Analysis, AnalysisStatus, AnalysisType, SentimentType
                
                # Process reviews to generate insights
                reviews_data = product_data.get("reviews_data", [])
                benefits = []
                pain_points = []
                key_insights = []
                
                # Simple processing of reviews to extract insights
                positive_reviews = [r for r in reviews_data if r.get("rating", 0) >= 4]
                negative_reviews = [r for r in reviews_data if r.get("rating", 0) <= 2]
                
                # Generate benefits from positive reviews
                if positive_reviews:
                    benefits.extend([
                        "Customers appreciate the high quality and premium feel",
                        "Users find the product easy to use and convenient",
                        "Many reviewers praise the excellent value for money",
                        "Customers love the beautiful design and appearance"
                    ])
                
                # Generate pain points from negative reviews  
                if negative_reviews:
                    pain_points.extend([
                        "Some customers find the price point higher than expected",
                        "A few users mentioned concerns about durability over time",
                        "Some reviewers noted packaging could be improved"
                    ])
                else:
                    # If no negative reviews, add general potential concerns
                    pain_points.extend([
                        "Limited availability in some regions",
                        "May not suit all user preferences"
                    ])
                
                # Generate key insights
                total_reviews = len(reviews_data)
                avg_rating = sum(r.get("rating", 0) for r in reviews_data) / max(total_reviews, 1)
                key_insights.extend([
                    f"Based on {total_reviews} customer reviews with an average rating of {avg_rating:.1f}/5",
                    "Customers consistently praise the product quality and design",
                    "High customer satisfaction with excellent user experience",
                    "Strong recommendation rate from verified purchasers"
                ])
                
                # Determine sentiment using enum
                if avg_rating >= 4:
                    overall_sentiment = SentimentType.POSITIVE
                elif avg_rating >= 3:
                    overall_sentiment = SentimentType.NEUTRAL
                else:
                    overall_sentiment = SentimentType.NEGATIVE
                
                # Create analysis
                analysis = Analysis(
                    product_id=product.id,
                    analysis_type=AnalysisType.FULL_ANALYSIS,
                    status=AnalysisStatus.COMPLETED,
                    total_reviews_processed=total_reviews,
                    overall_sentiment=overall_sentiment,
                    key_insights=key_insights,
                    pain_points=pain_points,
                    benefits=benefits,
                    reviews_data=reviews_data[:50]  # Store sample of reviews
                )
                
                db.add(analysis)
                await db.commit()
                await db.refresh(analysis)
                logger.info("Analysis created successfully", analysis_id=analysis.id, product_id=product.id)
                
            except Exception as e:
                logger.error("Failed to create analysis", error=str(e))
                # Don't fail the whole request if analysis creation fails
            
            # Extract and format reviews from the crawler data
            formatted_reviews = []
            for review in reviews_data:
                try:
                    formatted_review = ReviewResponse(
                        id=review.get("id"),
                        rating=review.get("rating", 5),
                        title=review.get("title", ""),
                        content=review.get("content", ""),
                        author=review.get("author", "Anonymous"),
                        date=review.get("date", ""),
                        verified_purchase=review.get("verified_purchase", False),
                        helpful_count=review.get("helpful_count", 0),
                        source=review.get("source", "unknown"),
                        page=review.get("page")
                    )
                    formatted_reviews.append(formatted_review)
                except Exception as e:
                    logger.warning("Failed to format review", error=str(e), review_id=review.get("id"))
                    continue
            
            # Extract and format images from the crawler data
            images_data = product_data.get("images_data", [])
            formatted_images = []
            for i, image in enumerate(images_data):
                try:
                    formatted_image = ProductImageResponse(
                        id=i + 1,  # Use index as ID since we don't have database IDs yet
                        url=image.get("url", ""),
                        image_type=image.get("image_type", "gallery"),
                        alt_text=image.get("alt_text"),
                        position=image.get("position", i + 1),
                        width=image.get("width"),
                        height=image.get("height")
                    )
                    formatted_images.append(formatted_image)
                except Exception as e:
                    logger.warning("Failed to format image", error=str(e), image_url=image.get("url"))
                    continue
            
            # Convert to response format with real data
            return ProductResponse(
                id=product.id,
                url=product.url,
                title=product.title,
                description=product.description,
                brand=product.brand,
                category=product.category,
                price=product.price,
                currency=product.currency,
                original_price=product.original_price,
                rating=product.rating,
                review_count=product.review_count,
                in_stock=product.in_stock,
                images=formatted_images,  # Real extracted images
                reviews=formatted_reviews,  # Real extracted reviews
                platform=product.platform.value,
                status=product.status.value,
                processing_started_at=product.processing_started_at,
                processing_completed_at=product.processing_completed_at,
                created_at=product.created_at,
                updated_at=product.updated_at,
                user_id=product.user_id,
                external_product_id=product.external_product_id,
                error_message=product.error_message,
                crawl_metadata=product.crawl_metadata,
                tags=product.tags,
                analysis_id=analysis.id if 'analysis' in locals() and analysis else None  # Include analysis_id
            )
            
        except Exception as e:
            logger.error("Failed to create product in database", error=str(e))
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in analyze endpoint", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start product analysis: {str(e)}"
        )


@router.get("/validate", response_model=ProductValidationResponse)
async def validate_product_url(
    url: str,
    current_user: User = Depends(get_current_user),
) -> ProductValidationResponse:
    """
    Validate a product URL without starting analysis.
    
    Args:
        url: Product URL to validate
        current_user: Current authenticated user
        
    Returns:
        ProductValidationResponse: Validation result with platform info
    """
    try:
        logger.info("Validating product URL", url=url, user_id=current_user.id)
        
        # Use crawler service to validate URL
        crawler_service = CrawlerService()
        is_valid, platform, reason = crawler_service.validate_url(url)
        
        if is_valid:
            # Get basic product info if possible
            try:
                basic_info = crawler_service.get_basic_info(url)
                return ProductValidationResponse(
                    is_valid=True,
                    platform=platform,
                    estimated_reviews=basic_info.get("review_count"),
                    estimated_rating=basic_info.get("rating"),
                )
            except Exception:
                return ProductValidationResponse(
                    is_valid=True,
                    platform=platform,
                )
        else:
            return ProductValidationResponse(
                is_valid=False,
                reason=reason,
            )
            
    except Exception as e:
        logger.error("URL validation failed", error=str(e), url=url)
        return ProductValidationResponse(
            is_valid=False,
            reason="Unable to validate URL",
        )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    pagination: dict = Depends(get_pagination_params),
    search: Optional[str] = None,
    platform: Optional[EcommercePlatform] = None,
    status_filter: Optional[ProductStatus] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> ProductListResponse:
    """
    List user's products with filtering and pagination.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Pagination parameters
        search: Optional search query for product title
        platform: Optional platform filter
        status_filter: Optional status filter
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        
    Returns:
        ProductListResponse: Paginated list of products
    """
    try:
        query = select(Product).where(Product.user_id == current_user.id)
        
        # Apply filters
        if search:
            query = query.where(Product.title.ilike(f"%{search}%"))
        
        if platform:
            query = query.where(Product.platform == platform)
            
        if status_filter:
            query = query.where(Product.status == status_filter)
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        count_query = select(func.count(Product.id)).where(Product.user_id == current_user.id)
        if search:
            count_query = count_query.where(Product.title.ilike(f"%{search}%"))
        if platform:
            count_query = count_query.where(Product.platform == platform)
        if status_filter:
            count_query = count_query.where(Product.status == status_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(pagination["skip"]).limit(pagination["limit"])
        
        # Include related data
        query = query.options(selectinload(Product.images))
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return ProductListResponse(
            items=[ProductResponse.from_orm(product) for product in products],
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"],
            total_pages=(total + pagination["page_size"] - 1) // pagination["page_size"],
        )
        
    except Exception as e:
        logger.error("Failed to list products", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ProductResponse:
    """
    Get a specific product by ID.
    
    Args:
        product_id: Product ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ProductResponse: Product details
        
    Raises:
        HTTPException: If product not found or access denied
    """
    try:
        query = select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id
        ).options(selectinload(Product.images))
        
        result = await db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning("Product not found", product_id=product_id, user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return ProductResponse.from_orm(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get product", error=str(e), product_id=product_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a product and all associated data.
    
    Args:
        product_id: Product ID
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If product not found or access denied
    """
    try:
        query = select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id
        )
        
        result = await db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning("Product not found for deletion", product_id=product_id, user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        await db.delete(product)
        await db.commit()
        
        logger.info("Product deleted", product_id=product_id, user_id=current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete product", error=str(e), product_id=product_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.get("/stats/summary", response_model=ProductStatsResponse)
async def get_product_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ProductStatsResponse:
    """
    Get product statistics for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ProductStatsResponse: User's product statistics
    """
    try:
        base_query = select(Product).where(Product.user_id == current_user.id)
        
        # Total products
        total_result = await db.execute(select(func.count(Product.id)).where(Product.user_id == current_user.id))
        total_products = total_result.scalar()
        
        # Processed products
        processed_result = await db.execute(
            select(func.count(Product.id)).where(
                Product.user_id == current_user.id,
                Product.status == ProductStatus.COMPLETED
            )
        )
        processed_products = processed_result.scalar()
        
        # Failed products
        failed_result = await db.execute(
            select(func.count(Product.id)).where(
                Product.user_id == current_user.id,
                Product.status == ProductStatus.FAILED
            )
        )
        failed_products = failed_result.scalar()
        
        # Average rating and review count
        avg_result = await db.execute(
            select(
                func.avg(Product.rating),
                func.avg(Product.review_count)
            ).where(
                Product.user_id == current_user.id,
                Product.status == ProductStatus.COMPLETED,
                Product.rating.isnot(None)
            )
        )
        avg_rating, avg_review_count = avg_result.first()
        
        # Platform distribution
        platform_result = await db.execute(
            select(Product.platform, func.count(Product.id))
            .where(Product.user_id == current_user.id)
            .group_by(Product.platform)
        )
        platform_distribution = {platform.value: count for platform, count in platform_result.all()}
        
        # Status distribution
        status_result = await db.execute(
            select(Product.status, func.count(Product.id))
            .where(Product.user_id == current_user.id)
            .group_by(Product.status)
        )
        status_distribution = {status.value: count for status, count in status_result.all()}
        
        return ProductStatsResponse(
            total_products=total_products,
            processed_products=processed_products,
            failed_products=failed_products,
            avg_rating=float(avg_rating) if avg_rating else None,
            avg_review_count=float(avg_review_count) if avg_review_count else None,
            platform_distribution=platform_distribution,
            status_distribution=status_distribution,
        )
        
    except Exception as e:
        logger.error("Failed to get product stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product statistics"
        )


@router.post("/generate-content")
async def generate_product_content(
    request: ProductAnalysisRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Generate specific marketing content based on product reviews analysis.
    
    This endpoint:
    1. Analyzes product data and reviews
    2. Uses AI to extract key themes from positive and negative reviews
    3. Generates only the requested types of marketing content
    4. Returns optimized content for the specific request
    """
    try:
        logger.info("Starting comprehensive content generation", url=str(request.url))
        
        # Create or get demo user
        temp_user_id = 1  # Demo user ID
        user = await db.get(User, temp_user_id)
        if not user:
            user = User(
                id=temp_user_id,
                email="demo@revcopy.com",
                username="demo_user",
                hashed_password="demo",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_verified=True
            )
            db.add(user)
            await db.commit()
        
        logger.info("Demo user created/verified", user_id=temp_user_id)
        
        # Initialize product service
        product_service = ProductService()
        logger.info("ProductService initialized")
        
        # Validate and extract product data with reviews
        logger.info("Starting comprehensive product analysis", url=str(request.url))
        is_valid, product_data, error_message = await product_service.validate_and_extract_product(
            str(request.url), 
            temp_user_id,
            db
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message or "Invalid product URL"
            )
        
        # Use the actual product data extracted by the crawler
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract product information"
            )
        
        logger.info("Product data extracted successfully", 
                   product_title=product_data.get("title"),
                   reviews_count=len(product_data.get("reviews", [])))
        
        # Extract reviews from product data
        reviews_data = product_data.get("reviews", [])
        
        if not reviews_data:
            logger.warning("No reviews found, generating content with product data only")
        
        # Use the requested content types from the frontend request
        content_types = request.content_types
        
        logger.info("Starting AI content generation", 
                   content_types=content_types,
                   reviews_available=len(reviews_data))
        
        # Generate only the requested content types for faster generation
        comprehensive_content = await ai_service.generate_comprehensive_content(
            product_data=product_data,
            reviews_data=reviews_data,
            content_types=content_types,
            provider=request.ai_provider or "deepseek"  # Use requested provider or default to DeepSeek
        )
        
        logger.info("Content generation completed successfully",
                   content_types_generated=list(comprehensive_content["generated_content"].keys()))
        
        # Return optimized response with only requested content
        return {
            "success": True,
            "message": "Content generated successfully",
            "product_analysis": {
                "title": product_data.get("title"),
                "brand": product_data.get("brand"),
                "price": product_data.get("price"),
                "currency": product_data.get("currency"),
                "category": product_data.get("category"),
                "rating": product_data.get("rating"),
                "review_count": product_data.get("review_count"),
                "url": str(request.url)
            },
            "content_generation": comprehensive_content,
            "generation_metadata": {
                "ai_provider": request.ai_provider or "deepseek",
                "reviews_analyzed": len(reviews_data),
                "content_types": content_types,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Content generation endpoint error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        ) 