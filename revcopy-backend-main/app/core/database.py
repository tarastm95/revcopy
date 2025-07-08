"""
Database configuration and connection management.
Handles SQLAlchemy setup, connection pooling, and session management.
"""

import logging
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Configure structured logging
logger = structlog.get_logger(__name__)

# SQLAlchemy metadata with naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Base class for SQLAlchemy models
Base = declarative_base(metadata=metadata)

# Global async engine and session maker
async_engine: Optional[create_async_engine] = None
async_session_maker: Optional[async_sessionmaker] = None

# Sync engine for migrations
sync_engine: Optional[create_engine] = None
sync_session_maker: Optional[sessionmaker] = None


def create_sync_engine():
    """Create synchronous engine for migrations and admin tasks."""
    global sync_engine, sync_session_maker
    
    try:
        # Convert async URL to sync URL for migrations
        sync_url = str(settings.DATABASE_URL).replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        
        sync_engine = create_engine(
            sync_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG,
        )
        
        sync_session_maker = sessionmaker(
            autocommit=False, autoflush=False, bind=sync_engine
        )
        
        logger.info("Synchronous database engine created successfully")
        return sync_engine
        
    except Exception as e:
        logger.error("Failed to create sync database engine", error=str(e))
        raise


async def create_async_engine_instance():
    """Create asynchronous database engine with connection pooling."""
    global async_engine, async_session_maker
    
    try:
        # Engine configuration for optimal performance
        engine_kwargs = {
            "url": str(settings.DATABASE_URL),
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 20,
            "max_overflow": 0,
        }
        
        # Use NullPool for testing to avoid connection issues
        if settings.ENVIRONMENT == "testing":
            engine_kwargs["poolclass"] = NullPool
        
        async_engine = create_async_engine(**engine_kwargs)
        
        async_session_maker = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        
        logger.info("Async database engine created successfully")
        return async_engine
        
    except Exception as e:
        logger.error("Failed to create async database engine", error=str(e))
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    
    Yields:
        AsyncSession: Database session
    """
    if not async_session_maker:
        await create_async_engine_instance()
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


def get_sync_session():
    """
    Get synchronous database session for migrations.
    
    Returns:
        Session: Database session
    """
    if not sync_session_maker:
        create_sync_engine()
    
    db = sync_session_maker()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error("Sync database session error", error=str(e))
        raise
    finally:
        db.close()


async def init_db():
    """Initialize database with all tables."""
    try:
        if not async_engine:
            await create_async_engine_instance()
        
        async with async_engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import user, product, analysis, content  # noqa
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db():
    """Close database connections."""
    try:
        if async_engine:
            await async_engine.dispose()
            logger.info("Async database connections closed")
        
        if sync_engine:
            sync_engine.dispose()
            logger.info("Sync database connections closed")
            
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


async def check_db_connection() -> bool:
    """
    Check database connectivity.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        if not async_engine:
            await create_async_engine_instance()
        
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Database connection check successful")
        return True
        
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False


class DatabaseError(Exception):
    """Custom database-related exception."""
    pass


class TransactionManager:
    """Context manager for database transactions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
            logger.error(
                "Transaction rolled back due to exception",
                exc_type=exc_type.__name__ if exc_type else None,
                exc_val=str(exc_val) if exc_val else None
            )
        else:
            await self.session.commit()
            logger.debug("Transaction committed successfully")


async def create_transaction(session: AsyncSession) -> TransactionManager:
    """
    Create a transaction manager for the given session.
    
    Args:
        session: Database session
        
    Returns:
        TransactionManager: Transaction context manager
    """
    return TransactionManager(session)


async def health_check() -> dict:
    """
    Perform database health check.
    
    Returns:
        dict: Health check result
    """
    try:
        start_time = time.time()
        
        if not async_engine:
            await create_async_engine_instance()
        
        async with async_engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as health_check"))
            result.fetchone()
        
        duration = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": f"{duration:.3f}s",
            "database": "postgresql"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": "postgresql"
        }


# Import time for health check
import time 