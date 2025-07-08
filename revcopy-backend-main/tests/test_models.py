"""Unit tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import structlog

from app.models.prompts import PromptTemplate, CulturalAdaptation, ABTestExperiment

logger = structlog.get_logger(__name__)


class TestPromptModels:
    """Test suite for prompt-related models."""

    @pytest.mark.asyncio
    async def test_create_prompt_template(self, test_db_session):
        """Test creating a prompt template."""
        template = PromptTemplate(
            title="Test Template",
            template_content="Create a description for {product_title}",
            content_type="product_description",
            primary_language="en",
            is_active=True
        )

        test_db_session.add(template)
        await test_db_session.commit()
        await test_db_session.refresh(template)

        assert template.id is not None
        assert template.title == "Test Template"
        assert template.primary_language == "en"

    @pytest.mark.asyncio
    async def test_create_cultural_adaptation(self, test_db_session):
        """Test creating a cultural adaptation."""
        template = PromptTemplate(
            title="Base Template",
            template_content="Base content",
            content_type="product_description",
            primary_language="en",
            is_active=True
        )
        test_db_session.add(template)
        await test_db_session.commit()
        await test_db_session.refresh(template)

        adaptation = CulturalAdaptation(
            template_id=template.id,
            target_language="he",
            cultural_region="middle_east",
            adapted_prompt="Hebrew content"
        )

        test_db_session.add(adaptation)
        await test_db_session.commit()
        await test_db_session.refresh(adaptation)

        assert adaptation.id is not None
        assert adaptation.template_id == template.id
        assert adaptation.target_language == "he"

    @pytest.mark.asyncio
    async def test_create_ab_test_experiment(self, test_db_session):
        """Test creating an A/B test experiment."""
        experiment = ABTestExperiment(
            name="Test Experiment",
            description="Testing template performance",
            status="active",
            traffic_allocation=0.5,
            start_date=datetime.utcnow(),
            confidence_level=0.95,
            minimum_sample_size=1000,
            control_group_performance=0.15,
            test_group_performance=0.18,
            statistical_significance=0.03
        )

        test_db_session.add(experiment)
        await test_db_session.commit()
        await test_db_session.refresh(experiment)

        assert experiment.id is not None
        assert experiment.name == "Test Experiment"
        assert experiment.status == "active"
        assert experiment.traffic_allocation == 0.5
        logger.info("AB test experiment creation test passed")

    @pytest.mark.asyncio
    async def test_template_required_fields(self, test_db_session):
        """Test that required fields are enforced."""
        # Try to create template without required fields
        template = PromptTemplate()  # Missing required fields

        test_db_session.add(template)
        
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        
        await test_db_session.rollback()
        logger.info("Required fields validation test passed")

    @pytest.mark.asyncio
    async def test_template_relationships(self, test_db_session):
        """Test model relationships."""
        # Create template
        template = PromptTemplate(
            title="Template with Relations",
            template_content="Content",
            content_type="product_description",
            primary_language="en",
            is_active=True
        )
        test_db_session.add(template)
        await test_db_session.commit()
        await test_db_session.refresh(template)

        # Create cultural adaptation linked to template
        adaptation = CulturalAdaptation(
            template_id=template.id,
            target_language="he",
            cultural_region="middle_east",
            adapted_prompt="Hebrew content"
        )
        test_db_session.add(adaptation)
        await test_db_session.commit()

        # Test relationship
        await test_db_session.refresh(template)
        assert len(template.cultural_adaptations) == 1
        assert template.cultural_adaptations[0].target_language == "he"
        logger.info("Model relationships test passed")

    def test_template_default_values(self):
        """Test model default values."""
        template = PromptTemplate(
            title="Test Defaults",
            template_content="Content",
            content_type="product_description",
            primary_language="en"
        )

        # Test default values
        assert template.is_active is True
        assert template.success_rate == 0.0
        assert template.average_user_rating == 0.0
        assert template.conversion_rate == 0.0
        assert template.supported_languages == []
        assert template.cultural_regions == []
        logger.info("Default values test passed") 