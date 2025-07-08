"""Unit tests for the prompt management API endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import structlog

logger = structlog.get_logger(__name__)


class TestPromptManagementAPI:
    """Test suite for prompt management API endpoints."""

    @pytest.mark.asyncio
    async def test_create_template_success(self, test_client: AsyncClient):
        """Test successful template creation."""
        template_data = {
            "title": "Test Template",
            "template_content": "Create a description for {product_title}",
            "content_type": "product_description",
            "primary_language": "en",
            "supported_languages": ["en", "es"],
            "cultural_regions": ["north_america"],
            "context_tags": ["ecommerce"],
            "target_audience": ["general"],
            "is_active": True
        }

        response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Template"
        assert data["content_type"] == "product_description"
        logger.info("Template creation test passed")

    @pytest.mark.asyncio
    async def test_get_templates_list(self, test_client: AsyncClient):
        """Test retrieving templates list."""
        response = await test_client.get("/api/v1/prompts/templates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        logger.info("Templates list retrieval test passed")

    @pytest.mark.asyncio
    async def test_get_template_by_id(self, test_client: AsyncClient):
        """Test retrieving a specific template by ID."""
        # First create a template
        template_data = {
            "title": "Test Template for ID",
            "template_content": "Test content",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        create_response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )
        created_template = create_response.json()
        template_id = created_template["id"]

        # Now retrieve it
        response = await test_client.get(f"/api/v1/prompts/templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["title"] == "Test Template for ID"
        logger.info("Template retrieval by ID test passed")

    @pytest.mark.asyncio
    async def test_update_template(self, test_client: AsyncClient):
        """Test updating an existing template."""
        # First create a template
        template_data = {
            "title": "Original Title",
            "template_content": "Original content",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        create_response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )
        created_template = create_response.json()
        template_id = created_template["id"]

        # Update the template
        update_data = {
            "title": "Updated Title",
            "template_content": "Updated content"
        }

        response = await test_client.put(
            f"/api/v1/prompts/templates/{template_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["template_content"] == "Updated content"
        logger.info("Template update test passed")

    @pytest.mark.asyncio
    async def test_delete_template(self, test_client: AsyncClient):
        """Test deleting a template."""
        # First create a template
        template_data = {
            "title": "Template to Delete",
            "template_content": "Content to delete",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        create_response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )
        created_template = create_response.json()
        template_id = created_template["id"]

        # Delete the template
        response = await test_client.delete(f"/api/v1/prompts/templates/{template_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = await test_client.get(f"/api/v1/prompts/templates/{template_id}")
        assert get_response.status_code == 404
        logger.info("Template deletion test passed")

    @pytest.mark.asyncio
    async def test_create_template_validation_error(self, test_client: AsyncClient):
        """Test template creation with validation errors."""
        invalid_template_data = {
            "title": "",  # Empty title should fail validation
            "template_content": "Content"
        }

        response = await test_client.post(
            "/api/v1/prompts/templates",
            json=invalid_template_data
        )

        assert response.status_code == 422  # Validation error
        logger.info("Template validation error test passed")

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, test_client: AsyncClient):
        """Test retrieving a non-existent template."""
        response = await test_client.get("/api/v1/prompts/templates/99999")

        assert response.status_code == 404
        logger.info("Non-existent template test passed")

    @pytest.mark.asyncio
    async def test_filter_templates_by_language(self, test_client: AsyncClient):
        """Test filtering templates by language."""
        # Create templates with different languages
        english_template = {
            "title": "English Template",
            "template_content": "English content",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        hebrew_template = {
            "title": "Hebrew Template",
            "template_content": "Hebrew content",
            "content_type": "product_description",
            "primary_language": "he",
            "is_active": True
        }

        await test_client.post("/api/v1/prompts/templates", json=english_template)
        await test_client.post("/api/v1/prompts/templates", json=hebrew_template)

        # Filter by English
        response = await test_client.get("/api/v1/prompts/templates?language=en")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # All returned templates should have English as primary language
        for template in data:
            assert template["primary_language"] == "en"
        logger.info("Template language filtering test passed")

    @pytest.mark.asyncio
    async def test_cultural_adaptation_endpoints(self, test_client: AsyncClient):
        """Test cultural adaptation CRUD operations."""
        # First create a template
        template_data = {
            "title": "Base Template",
            "template_content": "Base content",
            "content_type": "product_description",
            "primary_language": "en",
            "is_active": True
        }

        template_response = await test_client.post(
            "/api/v1/prompts/templates",
            json=template_data
        )
        template_id = template_response.json()["id"]

        # Create cultural adaptation
        adaptation_data = {
            "template_id": template_id,
            "target_language": "he",
            "cultural_region": "middle_east",
            "adapted_prompt": "Adapted Hebrew content",
            "cultural_modifications": {"text_direction": "rtl"}
        }

        response = await test_client.post(
            "/api/v1/prompts/cultural-adaptations",
            json=adaptation_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["target_language"] == "he"
        assert data["cultural_region"] == "middle_east"
        logger.info("Cultural adaptation creation test passed") 