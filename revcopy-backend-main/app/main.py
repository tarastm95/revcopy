"""
RevCopy Backend Application

Enterprise-grade backend with advanced monitoring, caching, and task management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.core.security import create_access_token

# Import enterprise systems
from app.core.performance import performance_collector, db_query_monitor, cleanup_performance_monitoring
from app.core.cache import initialize_cache, cleanup_cache
from app.core.background_tasks import initialize_task_manager, cleanup_task_manager

# Import API routers
from app.api.v1 import auth, products, campaigns, analysis, content_generation, generation, intelligent_content, admin, prompt_management
from app.api.v1.monitoring import router as monitoring_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring and request tracking.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        logger.info(
            "Request started",
            method=method,
            url=str(request.url),
            remote_addr=client_ip,
            user_agent=user_agent
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                duration=f"{duration:.3f}s",
                method=method,
                status_code=response.status_code,
                url=str(request.url)
            )
            
            # Record performance metric
            from app.core.performance import PerformanceMetric
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                operation=f"http.{method.lower()}.{path}",
                duration_ms=duration * 1000,
                success=response.status_code < 400,
                context={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "client_ip": client_ip
                }
            )
            performance_collector.record_metric(metric)
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            response.headers["X-Timestamp"] = datetime.utcnow().isoformat()
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                duration=f"{duration:.3f}s",
                method=method,
                url=str(request.url),
                error=str(e)
            )
            
            # Record error metric
            from app.core.performance import PerformanceMetric
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                operation=f"http.{method.lower()}.{path}",
                duration_ms=duration * 1000,
                success=False,
                context={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "client_ip": client_ip
                }
            )
            performance_collector.record_metric(metric)
            
            raise


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for headers and basic protection.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # More permissive CSP for Swagger UI functionality
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting RevCopy Backend Application")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize enterprise systems
        await initialize_cache()
        logger.info("Cache system initialized")
        
        await initialize_task_manager()
        logger.info("Task manager initialized")
        
        # Start performance monitoring
        performance_collector.start_monitoring()
        logger.info("Performance monitoring started")
        
        logger.info("All systems initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down RevCopy Backend Application")
        
        try:
            await cleanup_task_manager()
            logger.info("Task manager cleaned up")
            
            await cleanup_cache()
            logger.info("Cache system cleaned up")
            
            await cleanup_performance_monitoring()
            logger.info("Performance monitoring cleaned up")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
        
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="RevCopy API",
    description="Enterprise-grade API for RevCopy - Advanced content generation and product analysis platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "products",
            "description": "Product management and analysis"
        },
        {
            "name": "campaigns",
            "description": "Marketing campaign management"
        },
        {
            "name": "content generation",
            "description": "AI-powered content generation"
        },
        {
            "name": "analysis",
            "description": "Product and review analysis"
        },
        {
            "name": "admin",
            "description": "Administrative functions"
        },
        {
            "name": "monitoring",
            "description": "System monitoring and performance"
        }
    ]
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityMiddleware)
app.add_middleware(PerformanceMiddleware)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(content_generation.router, prefix="/api/v1/content-generation", tags=["content generation"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["content generation"])
app.include_router(intelligent_content.router, prefix="/api/v1/content-generation", tags=["content generation"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(prompt_management.router, prefix="/api/v1/prompts", tags=["admin"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        "Request validation error",
        errors=exc.errors(),
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    logger.error(
        "Starlette HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "Unexpected error",
        error=str(exc),
        url=str(request.url),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }


# System information endpoint
@app.get("/info", tags=["system"])
async def system_info():
    """
    Get system information.
    """
    return {
        "application": "RevCopy Backend",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "features": [
            "Enterprise Performance Monitoring",
            "Advanced Caching System",
            "Background Task Management",
            "Real-time Monitoring",
            "Security Enhancements",
            "Intelligent Content Generation",
            "Product Analysis",
            "Campaign Management"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# Database session error handler
@app.middleware("http")
async def database_session_middleware(request: Request, call_next):
    """
    Middleware to handle database session errors gracefully.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        if "database" in str(e).lower() or "connection" in str(e).lower():
            logger.error(
                "Database session error",
                error=str(e),
                url=str(request.url)
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": "Database connection error",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        raise


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True
    ) 