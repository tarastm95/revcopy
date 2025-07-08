"""
Admin API endpoints for RevCopy administration panel.

Provides comprehensive administrative functionality including:
- Admin authentication and login
- Prompt template management
- User management
- System settings
- Analytics and dashboard data
- Content generation settings
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, update, delete, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.api.deps import get_async_session, get_current_admin_user
from app.models.user import User, UserRole, UserStatus
from app.models.prompts import PromptTemplate
from app.models.content import GeneratedContent
from app.models.product import Product
from app.schemas.prompts import (
    PromptTemplateResponse,
)
from app.schemas.user import UserResponse, UserUpdate, UserLogin, Token
from app.schemas.admin import (
    AdministratorCreate,
    AdministratorUpdate,
    AdministratorResponse,
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentStatsResponse,
    PaymentListResponse,
    PaginationResponse,
    AmazonAccountCreate,
    AmazonAccountUpdate,
    AmazonAccountResponse,
    ProxyServerCreate,
    ProxyServerUpdate,
    ProxyServerResponse,
    CrawlerCreate,
    CrawlerUpdate,
    CrawlerResponse,
    CrawlerStatusUpdate,
)
from app.models.admin import (
    Administrator,
    Payment,
    AmazonAccount,
    ProxyServer,
    Crawler,
    AdminRole,
    AdminStatus,
    PaymentStatus,
    ServerStatus,
    CrawlerStatus,
    CrawlerType,
)
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token
from app.core.config import settings

# Configure logging
logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()

# Create router
router = APIRouter()

# ==================== SIMPLE ADMIN SCHEMAS ====================

class SimplePromptTemplateCreate(BaseModel):
    """Simple schema for creating a prompt template in admin panel."""
    content: str = Field(..., min_length=10, description="Prompt content")
    category: str = Field(..., min_length=1, description="Prompt category")
    is_active: bool = Field(True, description="Is prompt active")


class SimplePromptTemplateUpdate(BaseModel):
    """Simple schema for updating a prompt template in admin panel."""
    content: Optional[str] = Field(None, min_length=10, description="Prompt content")
    category: Optional[str] = Field(None, min_length=1, description="Prompt category")
    is_active: Optional[bool] = Field(None, description="Is prompt active")


class SimplePromptTemplateResponse(BaseModel):
    """Simple schema for prompt template response in admin panel."""
    id: int
    content: str
    category: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== ADMIN AUTHENTICATION ====================

@router.post("/auth/login", response_model=Token)
async def admin_login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session),
) -> Token:
    """
    Authenticate admin user and return JWT tokens.
    Uses regular user authentication but requires admin role.
    
    Args:
        login_data: Admin login credentials
        db: Database session
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid or user is not admin
    """
    try:
        logger.info("Admin login attempt", email=login_data.email)
        
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning("Admin login attempt with non-existent email", email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is admin
        if not user.is_admin:
            logger.warning("Non-admin user attempted admin login", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if account is locked
        if user.is_locked:
            logger.warning("Admin login attempt on locked account", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to multiple failed login attempts"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning("Invalid password attempt", user_id=user.id)
            user.record_failed_login()
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning("Login attempt on inactive admin account", user_id=user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not activated. Please verify your email."
            )
        
        # Record successful login
        user.record_successful_login()
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        logger.info("Admin logged in successfully", user_id=user.id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Admin login failed", error=str(e), email=login_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(
    current_admin: User = Depends(get_current_admin_user),
) -> UserResponse:
    """
    Get current authenticated admin user profile.
    
    Args:
        current_admin: Current authenticated admin user
        
    Returns:
        UserResponse: Current user profile
    """
    return UserResponse.from_orm(current_admin)


# ==================== PROMPT TEMPLATE MANAGEMENT ====================

@router.get("/prompt-templates", response_model=List[SimplePromptTemplateResponse])
async def get_prompt_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> List[SimplePromptTemplateResponse]:
    """
    Get all prompt templates with optional filtering.
    
    Args:
        category: Filter by template category
        is_active: Filter by active status
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_admin: Current admin user
        
    Returns:
        List[PromptTemplateResponse]: List of prompt templates
    """
    try:
        logger.info("Fetching prompt templates", admin_id=current_admin.id)
        
        query = select(PromptTemplate)
        
        # Apply filters
        if category:
            query = query.where(PromptTemplate.category == category)
        if is_active is not None:
            query = query.where(PromptTemplate.is_active == is_active)
        
        # Order by creation date, newest first
        query = query.order_by(desc(PromptTemplate.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        logger.info("Retrieved prompt templates", count=len(templates), admin_id=current_admin.id)
        return [SimplePromptTemplateResponse(
            id=template.id,
            content=template.user_prompt_template or "",
            category=template.category or "",
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        ) for template in templates]
        
    except Exception as e:
        logger.error("Failed to fetch prompt templates", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt templates"
        )


@router.post("/prompt-templates", response_model=SimplePromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_template(
    template_data: SimplePromptTemplateCreate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> SimplePromptTemplateResponse:
    """
    Create a new prompt template.
    
    Args:
        template_data: Prompt template creation data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PromptTemplateResponse: Created prompt template
    """
    try:
        logger.info("Creating prompt template", admin_id=current_admin.id, category=template_data.category)
        
        # Create new template with simple admin schema
        template = PromptTemplate(
            name=f"{template_data.category.replace('_', ' ').title()} Template",  # Generate name from category
            user_prompt_template=template_data.content,
            category=template_data.category,
            is_active=template_data.is_active,
            template_type=template_data.category,  # Use category as template type
            created_by=current_admin.username or current_admin.email,
            updated_by=current_admin.username or current_admin.email,
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info("Prompt template created", template_id=template.id, admin_id=current_admin.id)
        return SimplePromptTemplateResponse(
            id=template.id,
            content=template.user_prompt_template,
            category=template.category,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except Exception as e:
        logger.error("Failed to create prompt template", error=str(e), admin_id=current_admin.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt template"
        )


@router.get("/prompt-templates/{template_id}", response_model=SimplePromptTemplateResponse)
async def get_prompt_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> SimplePromptTemplateResponse:
    """
    Get a specific prompt template by ID.
    
    Args:
        template_id: Template ID
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PromptTemplateResponse: Prompt template data
    """
    try:
        result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found"
            )
        
        return SimplePromptTemplateResponse(
            id=template.id,
            content=template.user_prompt_template,
            category=template.category,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch prompt template", error=str(e), template_id=template_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt template"
        )


@router.put("/prompt-templates/{template_id}", response_model=SimplePromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    template_data: SimplePromptTemplateUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> SimplePromptTemplateResponse:
    """
    Update an existing prompt template.
    
    Args:
        template_id: Template ID to update
        template_data: Updated template data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PromptTemplateResponse: Updated prompt template
    """
    try:
        logger.info("Updating prompt template", template_id=template_id, admin_id=current_admin.id)
        
        # Get existing template
        result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found"
            )
        
        # Update fields with simple admin schema mapping
        update_data = template_data.dict(exclude_unset=True)
        logger.info("Update data received", update_data=update_data, template_id=template_id)
        
        if 'content' in update_data:
            old_content = template.user_prompt_template
            template.user_prompt_template = update_data['content']
            logger.info("Content updated", old_content_length=len(old_content or ""), 
                       new_content_length=len(update_data['content']))
        if 'category' in update_data:
            template.category = update_data['category']
        if 'is_active' in update_data:
            template.is_active = update_data['is_active']
        
        template.updated_by = current_admin.username or current_admin.email
        # Note: updated_at is automatically handled by SQLAlchemy onupdate=func.now()
        
        logger.info("Committing changes to database", template_id=template_id)
        await db.commit()
        await db.refresh(template)
        logger.info("Changes committed and refreshed", template_id=template_id, updated_at=template.updated_at)
        
        logger.info("Prompt template updated", template_id=template_id, admin_id=current_admin.id)
        return SimplePromptTemplateResponse(
            id=template.id,
            content=template.user_prompt_template,
            category=template.category,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update prompt template", error=str(e), template_id=template_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt template"
        )


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Delete a prompt template.
    
    Args:
        template_id: Template ID to delete
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info("Deleting prompt template", template_id=template_id, admin_id=current_admin.id)
        
        # Get existing template
        result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found"
            )
        
        # Delete template
        await db.delete(template)
        await db.commit()
        
        logger.info("Prompt template deleted", template_id=template_id, admin_id=current_admin.id)
        return {"message": "Prompt template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete prompt template", error=str(e), template_id=template_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt template"
        )


# ==================== USER MANAGEMENT ====================

@router.get("/users", response_model=Dict[str, Any])
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of users per page"),
    status_filter: Optional[UserStatus] = Query(None, description="Filter by user status"),
    role_filter: Optional[UserRole] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get paginated list of users with filtering options.
    
    Args:
        page: Page number
        limit: Number of users per page
        status_filter: Filter by user status
        role_filter: Filter by user role
        search: Search term for email or username
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict containing users list and pagination info
    """
    try:
        logger.info("Fetching users", admin_id=current_admin.id, page=page)
        
        # Build query
        query = select(User)
        
        # Apply filters
        if status_filter:
            query = query.where(User.status == status_filter)
        if role_filter:
            query = query.where(User.role == role_filter)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                func.lower(User.email).like(search_term) |
                func.lower(User.username).like(search_term)
            )
        
        # Get total count
        count_query = select(func.count(User.id))
        if status_filter:
            count_query = count_query.where(User.status == status_filter)
        if role_filter:
            count_query = count_query.where(User.role == role_filter)
        if search:
            search_term = f"%{search.lower()}%"
            count_query = count_query.where(
                func.lower(User.email).like(search_term) |
                func.lower(User.username).like(search_term)
            )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(User.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "users": [UserResponse.from_orm(user) for user in users],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        }
        
    except Exception as e:
        logger.error("Failed to fetch users", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> UserResponse:
    """
    Get detailed information about a specific user.
    
    Args:
        user_id: User ID
        db: Database session
        current_admin: Current admin user
        
    Returns:
        UserResponse: User details
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch user details", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_data: Dict[str, str],
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Update user status (activate, deactivate, suspend, etc.).
    
    Args:
        user_id: User ID to update
        status_data: New status data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Status update confirmation
    """
    try:
        logger.info("Updating user status", user_id=user_id, admin_id=current_admin.id)
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from modifying their own status
        if user.id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own status"
            )
        
        # Update status
        new_status = status_data.get("status")
        if new_status:
            try:
                user.status = UserStatus(new_status)
                await db.commit()
                logger.info("User status updated", user_id=user_id, new_status=new_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status value"
                )
        
        return {"message": "User status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user status", error=str(e), user_id=user_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )


# ==================== DASHBOARD & ANALYTICS ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get dashboard statistics for admin panel.
    
    Args:
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict containing various statistics
    """
    try:
        logger.info("Fetching dashboard stats", admin_id=current_admin.id)
        
        # Get current date ranges
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Active users (last 30 days)
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.last_login >= thirty_days_ago)
        )
        active_users = active_users_result.scalar() or 0
        
        # New users (last 7 days)
        new_users_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= seven_days_ago)
        )
        new_users = new_users_result.scalar() or 0
        
        # Total products analyzed
        total_products_result = await db.execute(select(func.count(Product.id)))
        total_products = total_products_result.scalar() or 0
        
        # Products analyzed (last 30 days)
        recent_products_result = await db.execute(
            select(func.count(Product.id)).where(Product.created_at >= thirty_days_ago)
        )
        recent_products = recent_products_result.scalar() or 0
        
        # Total content generated
        total_content_result = await db.execute(select(func.count(GeneratedContent.id)))
        total_content = total_content_result.scalar() or 0
        
        # Content generated (last 30 days)
        recent_content_result = await db.execute(
            select(func.count(GeneratedContent.id)).where(GeneratedContent.created_at >= thirty_days_ago)
        )
        recent_content = recent_content_result.scalar() or 0
        
        # Active prompt templates
        active_templates_result = await db.execute(
            select(func.count(PromptTemplate.id)).where(PromptTemplate.is_active == True)
        )
        active_templates = active_templates_result.scalar() or 0
        
        return {
            "users": {
                "total": total_users,
                "active_30d": active_users,
                "new_7d": new_users,
            },
            "products": {
                "total": total_products,
                "analyzed_30d": recent_products,
            },
            "content": {
                "total": total_content,
                "generated_30d": recent_content,
            },
            "templates": {
                "active": active_templates,
            },
            "last_updated": now.isoformat(),
        }
        
    except Exception as e:
        logger.error("Failed to fetch dashboard stats", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )


@router.get("/analytics/usage")
async def get_usage_analytics(
    period: str = Query("7d", regex="^(7d|30d|90d)$", description="Time period: 7d, 30d, or 90d"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get usage analytics for the specified period.
    
    Args:
        period: Time period (7d, 30d, 90d)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict containing usage analytics data
    """
    try:
        logger.info("Fetching usage analytics", period=period, admin_id=current_admin.id)
        
        # Calculate date range
        days = int(period[:-1])  # Remove 'd' suffix
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily user registrations
        daily_registrations = await db.execute(
            select(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            )
            .where(User.created_at >= start_date)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )
        
        # Daily content generation
        daily_content = await db.execute(
            select(
                func.date(GeneratedContent.created_at).label('date'),
                func.count(GeneratedContent.id).label('count')
            )
            .where(GeneratedContent.created_at >= start_date)
            .group_by(func.date(GeneratedContent.created_at))
            .order_by(func.date(GeneratedContent.created_at))
        )
        
        # Content by type
        content_by_type = await db.execute(
            select(
                GeneratedContent.content_type,
                func.count(GeneratedContent.id).label('count')
            )
            .where(GeneratedContent.created_at >= start_date)
            .group_by(GeneratedContent.content_type)
        )
        
        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "daily_registrations": [
                {"date": str(row.date), "count": row.count}
                for row in daily_registrations
            ],
            "daily_content": [
                {"date": str(row.date), "count": row.count}
                for row in daily_content
            ],
            "content_by_type": [
                {"type": row.content_type, "count": row.count}
                for row in content_by_type
            ],
        }
        
    except Exception as e:
        logger.error("Failed to fetch usage analytics", error=str(e), period=period)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )


# ==================== SYSTEM SETTINGS ====================

@router.get("/settings")
async def get_system_settings(
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get system settings and configuration.
    
    Args:
        current_admin: Current admin user
        
    Returns:
        Dict containing system settings
    """
    try:
        logger.info("Fetching system settings", admin_id=current_admin.id)
        
        # Mock system settings - in a real implementation, these would come from a settings table or config
        return {
            "ai_provider": {
                "current": "deepseek",
                "available": ["deepseek", "openai", "anthropic"],
                "api_key_configured": True,
            },
            "content_generation": {
                "max_tokens_default": 500,
                "temperature_default": 0.7,
                "enabled_types": [
                    "facebook_ad",
                    "google_ad", 
                    "instagram_caption",
                    "email_campaign",
                    "product_description"
                ],
            },
            "rate_limiting": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "enabled": True,
            },
            "email": {
                "smtp_configured": False,
                "verification_enabled": False,
                "notifications_enabled": True,
            },
            "analytics": {
                "tracking_enabled": True,
                "retention_days": 90,
            },
        }
        
    except Exception as e:
        logger.error("Failed to fetch system settings", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system settings"
        )


@router.put("/settings")
async def update_system_settings(
    settings_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Update system settings.
    
    Args:
        settings_data: Updated settings data
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Update confirmation message
    """
    try:
        logger.info("Updating system settings", admin_id=current_admin.id)
        
        # In a real implementation, you would:
        # 1. Validate the settings data
        # 2. Update the settings in database/config
        # 3. Apply the changes to the running system
        
        logger.info("System settings updated", admin_id=current_admin.id, settings=settings_data.keys())
        
        return {"message": "System settings updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update system settings", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system settings"
        )


# ==================== ADMINISTRATOR MANAGEMENT ====================

@router.get("/administrators", response_model=List[AdministratorResponse])
async def get_administrators(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of administrators per page"),
    status_filter: Optional[AdminStatus] = Query(None, description="Filter by status"),
    role_filter: Optional[AdminRole] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> List[AdministratorResponse]:
    """
    Get all administrators with optional filtering and pagination.
    
    Args:
        page: Page number for pagination
        limit: Number of administrators per page
        status_filter: Filter by administrator status
        role_filter: Filter by administrator role
        search: Search term for name or email
        db: Database session
        current_admin: Current admin user
        
    Returns:
        List[AdministratorResponse]: List of administrators
    """
    try:
        logger.info("Fetching administrators", admin_id=current_admin.id)
        
        query = select(Administrator)
        
        # Apply filters
        if status_filter:
            query = query.where(Administrator.status == status_filter)
        if role_filter:
            query = query.where(Administrator.role == role_filter)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Administrator.name.ilike(search_term)) |
                (Administrator.email.ilike(search_term))
            )
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(Administrator.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        administrators = result.scalars().all()
        
        logger.info("Retrieved administrators", count=len(administrators), admin_id=current_admin.id)
        return [AdministratorResponse.from_orm(admin) for admin in administrators]
        
    except Exception as e:
        logger.error("Failed to fetch administrators", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve administrators"
        )


@router.post("/administrators", response_model=AdministratorResponse, status_code=status.HTTP_201_CREATED)
async def create_administrator(
    admin_data: AdministratorCreate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdministratorResponse:
    """
    Create a new administrator.
    
    Args:
        admin_data: Administrator creation data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        AdministratorResponse: Created administrator
    """
    try:
        logger.info("Creating administrator", admin_id=current_admin.id, email=admin_data.email)
        
        # Check if email already exists
        existing_admin = await db.execute(
            select(Administrator).where(Administrator.email == admin_data.email)
        )
        if existing_admin.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrator with this email already exists"
            )
        
        # Create new administrator
        admin = Administrator(
            name=admin_data.name,
            email=admin_data.email,
            password_hash=get_password_hash(admin_data.password),
            role=admin_data.role,
            status=admin_data.status,
            created_by=current_admin.email,
            updated_by=current_admin.email,
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        logger.info("Administrator created", admin_id=admin.id, created_by=current_admin.id)
        return AdministratorResponse.from_orm(admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create administrator", error=str(e), admin_id=current_admin.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create administrator"
        )


@router.put("/administrators/{admin_id}", response_model=AdministratorResponse)
async def update_administrator(
    admin_id: int,
    admin_data: AdministratorUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdministratorResponse:
    """
    Update an existing administrator.
    
    Args:
        admin_id: Administrator ID to update
        admin_data: Updated administrator data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        AdministratorResponse: Updated administrator
    """
    try:
        logger.info("Updating administrator", target_admin_id=admin_id, admin_id=current_admin.id)
        
        # Get existing administrator
        result = await db.execute(select(Administrator).where(Administrator.id == admin_id))
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrator not found"
            )
        
        # Update fields
        update_data = admin_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password" and value:
                admin.password_hash = get_password_hash(value)
            else:
                setattr(admin, field, value)
        
        admin.updated_by = current_admin.email
        
        await db.commit()
        await db.refresh(admin)
        
        logger.info("Administrator updated", target_admin_id=admin_id, updated_by=current_admin.id)
        return AdministratorResponse.from_orm(admin)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update administrator", error=str(e), target_admin_id=admin_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update administrator"
        )


@router.delete("/administrators/{admin_id}")
async def delete_administrator(
    admin_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Delete an administrator.
    
    Args:
        admin_id: Administrator ID to delete
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info("Deleting administrator", target_admin_id=admin_id, admin_id=current_admin.id)
        
        # Prevent self-deletion
        if admin_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own administrator account"
            )
        
        # Get administrator
        result = await db.execute(select(Administrator).where(Administrator.id == admin_id))
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrator not found"
            )
        
        # Delete administrator
        await db.delete(admin)
        await db.commit()
        
        logger.info("Administrator deleted", target_admin_id=admin_id, deleted_by=current_admin.id)
        return {"message": f"Administrator {admin.name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete administrator", error=str(e), target_admin_id=admin_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete administrator"
        )


# ==================== PAYMENT MANAGEMENT ====================

@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of payments per page"),
    status_filter: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    search: Optional[str] = Query(None, description="Search by user email or payment ID"),
    start_date: Optional[datetime] = Query(None, description="Filter payments from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter payments until this date"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> PaymentListResponse:
    """
    Get all payments with filtering and pagination.
    
    Args:
        page: Page number for pagination
        limit: Number of payments per page
        status_filter: Filter by payment status
        search: Search term for user email or payment ID
        start_date: Filter payments from this date
        end_date: Filter payments until this date
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PaymentListResponse: Paginated payment list with metadata
    """
    try:
        logger.info("Fetching payments", admin_id=current_admin.id)
        
        query = select(Payment)
        
        # Apply filters
        if status_filter:
            query = query.where(Payment.status == status_filter)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Payment.user_email.ilike(search_term)) |
                (Payment.id.ilike(search_term))
            )
        if start_date:
            query = query.where(Payment.created_at >= start_date)
        if end_date:
            query = query.where(Payment.created_at <= end_date)
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(desc(Payment.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        payments = result.scalars().all()
        
        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = PaginationResponse(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        logger.info("Retrieved payments", count=len(payments), total=total, admin_id=current_admin.id)
        
        return PaymentListResponse(
            payments=[PaymentResponse.from_orm(payment) for payment in payments],
            pagination=pagination
        )
        
    except Exception as e:
        logger.error("Failed to fetch payments", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments"
        )


@router.get("/payments/stats", response_model=PaymentStatsResponse)
async def get_payment_stats(
    period: str = Query("30d", regex="^(7d|30d|90d|1y|all)$", description="Time period: 7d, 30d, 90d, 1y, all"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> PaymentStatsResponse:
    """
    Get payment statistics for the specified period.
    
    Args:
        period: Time period for statistics (7d, 30d, 90d, 1y, all)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PaymentStatsResponse: Payment statistics
    """
    try:
        logger.info("Fetching payment stats", period=period, admin_id=current_admin.id)
        
        # Calculate date range
        start_date = None
        if period != "all":
            if period == "1y":
                days = 365
            else:
                days = int(period[:-1])
            start_date = datetime.utcnow() - timedelta(days=days)
        
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Build base queries with optional date filtering
        def apply_date_filter(query, date_field=Payment.created_at):
            if start_date:
                return query.where(date_field >= start_date)
            return query
        
        # Total revenue
        revenue_query = select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
        revenue_query = apply_date_filter(revenue_query)
        total_revenue_result = await db.execute(revenue_query)
        total_revenue = total_revenue_result.scalar()
        
        # Monthly revenue
        monthly_revenue_result = await db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                and_(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.created_at >= month_start
                )
            )
        )
        monthly_revenue = monthly_revenue_result.scalar()
        
        # Average payment
        avg_query = select(func.coalesce(func.avg(Payment.amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
        avg_query = apply_date_filter(avg_query)
        avg_payment_result = await db.execute(avg_query)
        average_payment = avg_payment_result.scalar()
        
        # Success rate
        total_query = select(func.count(Payment.id))
        total_query = apply_date_filter(total_query)
        total_payments_result = await db.execute(total_query)
        total_payments = total_payments_result.scalar()
        
        successful_query = select(func.count(Payment.id)).where(Payment.status == PaymentStatus.COMPLETED)
        successful_query = apply_date_filter(successful_query)
        successful_payments_result = await db.execute(successful_query)
        successful_payments = successful_payments_result.scalar()
        
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Monthly payment count
        monthly_payments_result = await db.execute(
            select(func.count(Payment.id))
            .where(Payment.created_at >= month_start)
        )
        monthly_payments = monthly_payments_result.scalar()
        
        # Payment method breakdown
        method_query = select(Payment.payment_method, func.count(Payment.id)).group_by(Payment.payment_method)
        method_query = apply_date_filter(method_query)
        payment_methods_result = await db.execute(method_query)
        payment_method_breakdown = {method: count for method, count in payment_methods_result}
        
        # Status breakdown
        status_query = select(Payment.status, func.count(Payment.id)).group_by(Payment.status)
        status_query = apply_date_filter(status_query)
        status_result = await db.execute(status_query)
        status_breakdown = {status: count for status, count in status_result}
        
        return PaymentStatsResponse(
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            average_payment=average_payment,
            success_rate=success_rate,
            total_payments=total_payments,
            monthly_payments=monthly_payments,
            payment_method_breakdown=payment_method_breakdown,
            status_breakdown=status_breakdown
        )
        
    except Exception as e:
        logger.error("Failed to fetch payment stats", error=str(e), period=period)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment statistics"
        )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment_details(
    payment_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> PaymentResponse:
    """
    Get detailed information about a specific payment.
    
    Args:
        payment_id: Payment ID
        db: Database session
        current_admin: Current admin user
        
    Returns:
        PaymentResponse: Payment details
    """
    try:
        result = await db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return PaymentResponse.from_orm(payment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch payment details", error=str(e), payment_id=payment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment details"
        )


# ==================== AMAZON ACCOUNT MANAGEMENT ====================

@router.get("/amazon-accounts", response_model=List[AmazonAccountResponse])
async def get_amazon_accounts(
    status_filter: Optional[ServerStatus] = Query(None, description="Filter by account status"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> List[AmazonAccountResponse]:
    """
    Get all Amazon accounts with optional filtering.
    
    Args:
        status_filter: Filter by account status
        db: Database session
        current_admin: Current admin user
        
    Returns:
        List[AmazonAccountResponse]: List of Amazon accounts
    """
    try:
        logger.info("Fetching Amazon accounts", admin_id=current_admin.id)
        
        query = select(AmazonAccount)
        
        if status_filter:
            query = query.where(AmazonAccount.status == status_filter)
        
        query = query.order_by(desc(AmazonAccount.created_at))
        
        result = await db.execute(query)
        accounts = result.scalars().all()
        
        # Mask passwords for security
        response_accounts = []
        for account in accounts:
            account_dict = account.__dict__.copy()
            account_dict['password_masked'] = '*' * 8  # Mask password
            response_accounts.append(AmazonAccountResponse(**account_dict))
        
        logger.info("Retrieved Amazon accounts", count=len(accounts), admin_id=current_admin.id)
        return response_accounts
        
    except Exception as e:
        logger.error("Failed to fetch Amazon accounts", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Amazon accounts"
        )


@router.post("/amazon-accounts", response_model=AmazonAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_amazon_account(
    account_data: AmazonAccountCreate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AmazonAccountResponse:
    """
    Create a new Amazon account.
    
    Args:
        account_data: Amazon account creation data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        AmazonAccountResponse: Created Amazon account
    """
    try:
        logger.info("Creating Amazon account", admin_id=current_admin.id, username=account_data.username)
        
        # Check if username already exists
        existing_account = await db.execute(
            select(AmazonAccount).where(AmazonAccount.username == account_data.username)
        )
        if existing_account.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amazon account with this username already exists"
            )
        
        # Create new Amazon account
        account = AmazonAccount(
            username=account_data.username,
            password_hash=get_password_hash(account_data.password),  # Encrypt password
            status=account_data.status,
            avatar_url=account_data.avatar_url,
            created_by=current_admin.email,
            updated_by=current_admin.email,
        )
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
        
        # Prepare response with masked password
        account_dict = account.__dict__.copy()
        account_dict['password_masked'] = '*' * 8
        
        logger.info("Amazon account created", account_id=account.id, created_by=current_admin.id)
        return AmazonAccountResponse(**account_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create Amazon account", error=str(e), admin_id=current_admin.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Amazon account"
        )


@router.put("/amazon-accounts/{account_id}", response_model=AmazonAccountResponse)
async def update_amazon_account(
    account_id: int,
    account_data: AmazonAccountUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AmazonAccountResponse:
    """
    Update an existing Amazon account.
    
    Args:
        account_id: Amazon account ID to update
        account_data: Updated account data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        AmazonAccountResponse: Updated Amazon account
    """
    try:
        logger.info("Updating Amazon account", account_id=account_id, admin_id=current_admin.id)
        
        # Get existing account
        result = await db.execute(select(AmazonAccount).where(AmazonAccount.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amazon account not found"
            )
        
        # Update fields
        update_data = account_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password" and value:
                account.password_hash = get_password_hash(value)
            else:
                setattr(account, field, value)
        
        account.updated_by = current_admin.email
        
        await db.commit()
        await db.refresh(account)
        
        # Prepare response with masked password
        account_dict = account.__dict__.copy()
        account_dict['password_masked'] = '*' * 8
        
        logger.info("Amazon account updated", account_id=account_id, updated_by=current_admin.id)
        return AmazonAccountResponse(**account_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update Amazon account", error=str(e), account_id=account_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Amazon account"
        )


@router.delete("/amazon-accounts/{account_id}")
async def delete_amazon_account(
    account_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Delete an Amazon account.
    
    Args:
        account_id: Amazon account ID to delete
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info("Deleting Amazon account", account_id=account_id, admin_id=current_admin.id)
        
        # Get account
        result = await db.execute(select(AmazonAccount).where(AmazonAccount.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amazon account not found"
            )
        
        # Delete account
        await db.delete(account)
        await db.commit()
        
        logger.info("Amazon account deleted", account_id=account_id, deleted_by=current_admin.id)
        return {"message": f"Amazon account {account.username} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete Amazon account", error=str(e), account_id=account_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete Amazon account"
        )


# ==================== PROXY SERVER MANAGEMENT ====================

@router.get("/proxy-servers", response_model=List[ProxyServerResponse])
async def get_proxy_servers(
    status_filter: Optional[ServerStatus] = Query(None, description="Filter by server status"),
    location_filter: Optional[str] = Query(None, description="Filter by location"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> List[ProxyServerResponse]:
    """
    Get all proxy servers with optional filtering.
    
    Args:
        status_filter: Filter by server status
        location_filter: Filter by geographic location
        db: Database session
        current_admin: Current admin user
        
    Returns:
        List[ProxyServerResponse]: List of proxy servers
    """
    try:
        logger.info("Fetching proxy servers", admin_id=current_admin.id)
        
        query = select(ProxyServer)
        
        if status_filter:
            query = query.where(ProxyServer.status == status_filter)
        if location_filter:
            query = query.where(ProxyServer.location.ilike(f"%{location_filter}%"))
        
        query = query.order_by(desc(ProxyServer.created_at))
        
        result = await db.execute(query)
        servers = result.scalars().all()
        
        logger.info("Retrieved proxy servers", count=len(servers), admin_id=current_admin.id)
        return [ProxyServerResponse.from_orm(server) for server in servers]
        
    except Exception as e:
        logger.error("Failed to fetch proxy servers", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve proxy servers"
        )


@router.post("/proxy-servers", response_model=ProxyServerResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy_server(
    server_data: ProxyServerCreate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> ProxyServerResponse:
    """
    Create a new proxy server.
    
    Args:
        server_data: Proxy server creation data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        ProxyServerResponse: Created proxy server
    """
    try:
        logger.info("Creating proxy server", admin_id=current_admin.id, name=server_data.name)
        
        # Create new proxy server
        server = ProxyServer(
            name=server_data.name,
            address=server_data.address,
            location=server_data.location,
            status=server_data.status,
            rate_limit_per_hour=server_data.rate_limit_per_hour,
            created_by=current_admin.email,
            updated_by=current_admin.email,
        )
        
        db.add(server)
        await db.commit()
        await db.refresh(server)
        
        logger.info("Proxy server created", server_id=server.id, created_by=current_admin.id)
        return ProxyServerResponse.from_orm(server)
        
    except Exception as e:
        logger.error("Failed to create proxy server", error=str(e), admin_id=current_admin.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proxy server"
        )


@router.put("/proxy-servers/{server_id}", response_model=ProxyServerResponse)
async def update_proxy_server(
    server_id: int,
    server_data: ProxyServerUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> ProxyServerResponse:
    """
    Update an existing proxy server.
    
    Args:
        server_id: Proxy server ID to update
        server_data: Updated server data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        ProxyServerResponse: Updated proxy server
    """
    try:
        logger.info("Updating proxy server", server_id=server_id, admin_id=current_admin.id)
        
        # Get existing server
        result = await db.execute(select(ProxyServer).where(ProxyServer.id == server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proxy server not found"
            )
        
        # Update fields
        update_data = server_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(server, field, value)
        
        server.updated_by = current_admin.email
        
        await db.commit()
        await db.refresh(server)
        
        logger.info("Proxy server updated", server_id=server_id, updated_by=current_admin.id)
        return ProxyServerResponse.from_orm(server)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update proxy server", error=str(e), server_id=server_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update proxy server"
        )


@router.delete("/proxy-servers/{server_id}")
async def delete_proxy_server(
    server_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Delete a proxy server.
    
    Args:
        server_id: Proxy server ID to delete
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info("Deleting proxy server", server_id=server_id, admin_id=current_admin.id)
        
        # Get server
        result = await db.execute(select(ProxyServer).where(ProxyServer.id == server_id))
        server = result.scalar_one_or_none()
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proxy server not found"
            )
        
        # Delete server
        await db.delete(server)
        await db.commit()
        
        logger.info("Proxy server deleted", server_id=server_id, deleted_by=current_admin.id)
        return {"message": f"Proxy server {server.name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete proxy server", error=str(e), server_id=server_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete proxy server"
        )


# ==================== CRAWLER MANAGEMENT ====================

@router.get("/crawlers", response_model=List[CrawlerResponse])
async def get_crawlers(
    status_filter: Optional[CrawlerStatus] = Query(None, description="Filter by crawler status"),
    crawler_type_filter: Optional[CrawlerType] = Query(None, description="Filter by crawler type"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> List[CrawlerResponse]:
    """
    Get all crawlers with optional filtering.
    
    Args:
        status_filter: Filter by crawler status
        crawler_type_filter: Filter by crawler type
        db: Database session
        current_admin: Current admin user
        
    Returns:
        List[CrawlerResponse]: List of crawlers
    """
    try:
        logger.info("Fetching crawlers", admin_id=current_admin.id)
        
        query = select(Crawler)
        
        if status_filter:
            query = query.where(Crawler.status == status_filter)
        if crawler_type_filter:
            query = query.where(Crawler.crawler_type == crawler_type_filter)
        
        query = query.order_by(desc(Crawler.created_at))
        
        result = await db.execute(query)
        crawlers = result.scalars().all()
        
        logger.info("Retrieved crawlers", count=len(crawlers), admin_id=current_admin.id)
        return [CrawlerResponse.from_orm(crawler) for crawler in crawlers]
        
    except Exception as e:
        logger.error("Failed to fetch crawlers", error=str(e), admin_id=current_admin.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve crawlers"
        )


@router.post("/crawlers", response_model=CrawlerResponse, status_code=status.HTTP_201_CREATED)
async def create_crawler(
    crawler_data: CrawlerCreate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> CrawlerResponse:
    """
    Create a new crawler.
    
    Args:
        crawler_data: Crawler creation data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        CrawlerResponse: Created crawler
    """
    try:
        logger.info("Creating crawler", admin_id=current_admin.id, name=crawler_data.name)
        
        # Create new crawler
        crawler = Crawler(
            name=crawler_data.name,
            crawler_type=crawler_data.crawler_type,
            target_url=crawler_data.target_url,
            css_selector=crawler_data.css_selector,
            user_agent=crawler_data.user_agent,
            interval_minutes=crawler_data.interval_minutes,
            created_by=current_admin.email,
            updated_by=current_admin.email,
        )
        
        db.add(crawler)
        await db.commit()
        await db.refresh(crawler)
        
        logger.info("Crawler created", crawler_id=crawler.id, created_by=current_admin.id)
        return CrawlerResponse.from_orm(crawler)
        
    except Exception as e:
        logger.error("Failed to create crawler", error=str(e), admin_id=current_admin.id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create crawler"
        )


@router.put("/crawlers/{crawler_id}", response_model=CrawlerResponse)
async def update_crawler(
    crawler_id: int,
    crawler_data: CrawlerUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> CrawlerResponse:
    """
    Update an existing crawler.
    
    Args:
        crawler_id: Crawler ID to update
        crawler_data: Updated crawler data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        CrawlerResponse: Updated crawler
    """
    try:
        logger.info("Updating crawler", crawler_id=crawler_id, admin_id=current_admin.id)
        
        # Get existing crawler
        result = await db.execute(select(Crawler).where(Crawler.id == crawler_id))
        crawler = result.scalar_one_or_none()
        
        if not crawler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawler not found"
            )
        
        # Update fields
        update_data = crawler_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(crawler, field, value)
        
        crawler.updated_by = current_admin.email
        
        await db.commit()
        await db.refresh(crawler)
        
        logger.info("Crawler updated", crawler_id=crawler_id, updated_by=current_admin.id)
        return CrawlerResponse.from_orm(crawler)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update crawler", error=str(e), crawler_id=crawler_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update crawler"
        )


@router.put("/crawlers/{crawler_id}/status", response_model=CrawlerResponse)
async def update_crawler_status(
    crawler_id: int,
    status_data: CrawlerStatusUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> CrawlerResponse:
    """
    Update crawler status (start, pause, stop).
    
    Args:
        crawler_id: Crawler ID to update
        status_data: New status data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        CrawlerResponse: Updated crawler
    """
    try:
        logger.info("Updating crawler status", crawler_id=crawler_id, new_status=status_data.status, admin_id=current_admin.id)
        
        # Get existing crawler
        result = await db.execute(select(Crawler).where(Crawler.id == crawler_id))
        crawler = result.scalar_one_or_none()
        
        if not crawler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawler not found"
            )
        
        # Update status and related fields
        old_status = crawler.status
        crawler.status = status_data.status
        crawler.updated_by = current_admin.email
        
        # If starting the crawler, calculate next run time
        if status_data.status == CrawlerStatus.RUNNING and old_status != CrawlerStatus.RUNNING:
            from datetime import timedelta
            crawler.next_run_at = datetime.utcnow() + timedelta(minutes=crawler.interval_minutes)
        
        # If stopping/pausing, clear next run time
        elif status_data.status in [CrawlerStatus.STOPPED, CrawlerStatus.PAUSED]:
            crawler.next_run_at = None
        
        await db.commit()
        await db.refresh(crawler)
        
        logger.info("Crawler status updated", crawler_id=crawler_id, old_status=old_status, new_status=status_data.status, updated_by=current_admin.id)
        return CrawlerResponse.from_orm(crawler)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update crawler status", error=str(e), crawler_id=crawler_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update crawler status"
        )


@router.delete("/crawlers/{crawler_id}")
async def delete_crawler(
    crawler_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user),
) -> Dict[str, str]:
    """
    Delete a crawler.
    
    Args:
        crawler_id: Crawler ID to delete
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info("Deleting crawler", crawler_id=crawler_id, admin_id=current_admin.id)
        
        # Get crawler
        result = await db.execute(select(Crawler).where(Crawler.id == crawler_id))
        crawler = result.scalar_one_or_none()
        
        if not crawler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawler not found"
            )
        
        # Don't delete running crawlers
        if crawler.status == CrawlerStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a running crawler. Stop it first."
            )
        
        # Delete crawler
        await db.delete(crawler)
        await db.commit()
        
        logger.info("Crawler deleted", crawler_id=crawler_id, deleted_by=current_admin.id)
        return {"message": f"Crawler {crawler.name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete crawler", error=str(e), crawler_id=crawler_id)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete crawler"
        ) 