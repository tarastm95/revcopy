"""Test configuration and fixtures for the RevCopy application."""

import asyncio
import pytest
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

from app.core.database import Base, get_async_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session") 
def event_loop():
    """Create event loop for test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        
    await engine.dispose()


@pytest.fixture
async def test_client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def sample_product_data() -> Dict[str, Any]:
    """Sample English product data for testing."""
    return {
        "id": 123456789,
        "title": "Test Product",
        "description": "This is a high-quality test product for testing purposes.",
        "vendor": "Test Vendor",
        "price": "99.90",
        "url": "https://example.com/products/test-product"
    }


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock_service = Mock()
    mock_service.generate_text = AsyncMock(return_value="Mock generated text")
    mock_service.generate_comprehensive_content = AsyncMock(return_value={
        "product_description": "Mock product description"
    })
    mock_service._detect_product_language = Mock(return_value="en")
    return mock_service
