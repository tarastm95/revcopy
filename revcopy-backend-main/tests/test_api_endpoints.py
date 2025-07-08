"""Unit tests for API endpoints."""

import pytest
from httpx import AsyncClient
import structlog

logger = structlog.get_logger(__name__)


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, test_client: AsyncClient):
        """Test health check endpoint."""
        response = await test_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_template(self, test_client: AsyncClient):
        """Test template creation endpoint."""
        template_data = {
            "title": "Test Template",
            "template_content": "Create a description for {product_title}",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Template"
        logger.info("Template creation test passed")

    @pytest.mark.asyncio
    async def test_get_templates(self, test_client: AsyncClient):
        """Test getting templates list."""
        response = await test_client.get("/api/v1/prompts/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        logger.info("Get templates test passed") 