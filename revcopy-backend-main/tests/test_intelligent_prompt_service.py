"""Unit tests for the IntelligentPromptService class."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import structlog

from app.services.intelligent_prompt_service import IntelligentPromptService
from app.models.prompts import PromptTemplate, CulturalAdaptation
from app.schemas.prompts import IntelligentPromptRequest

logger = structlog.get_logger(__name__)


class TestIntelligentPromptService:
    """Test suite for IntelligentPromptService class."""

    @pytest.fixture
    def prompt_service(self):
        """Create an IntelligentPromptService instance for testing."""
        return IntelligentPromptService()

    @pytest.fixture
    def sample_prompt_request(self, sample_product_data):
        """Create a sample prompt request."""
        return IntelligentPromptRequest(
            content_type="product_description",
            language="en",
            cultural_region="north_america",
            product_data=sample_product_data,
            target_audience="general",
            context_tags=["ecommerce", "retail"]
        )

    def test_detect_product_language_english(self, prompt_service, sample_product_data):
        """Test language detection for English products."""
        detected_language = prompt_service._detect_product_language(sample_product_data)
        assert detected_language == "en"
        logger.info("English language detection test passed")

    def test_detect_product_language_hebrew(self, prompt_service, sample_hebrew_product_data):
        """Test language detection for Hebrew products."""
        detected_language = prompt_service._detect_product_language(sample_hebrew_product_data)
        assert detected_language == "he"
        logger.info("Hebrew language detection test passed")

    def test_calculate_template_score_high_match(self, prompt_service, sample_prompt_request):
        """Test template scoring with high relevance match."""
        mock_template = Mock()
        mock_template.content_type = "product_description"
        mock_template.primary_language = "en"
        mock_template.supported_languages = ["en", "es"]
        mock_template.context_tags = ["ecommerce", "retail"]
        mock_template.target_audience = ["general", "millennials"]
        mock_template.success_rate = 0.85
        mock_template.average_user_rating = 4.5
        mock_template.conversion_rate = 0.12

        score = prompt_service._calculate_template_score(mock_template, sample_prompt_request)
        
        # Should have high score due to perfect matches
        assert score > 0.8
        logger.info("High match template scoring test passed")

    def test_calculate_template_score_low_match(self, prompt_service, sample_prompt_request):
        """Test template scoring with low relevance match."""
        mock_template = Mock()
        mock_template.content_type = "social_media"  # Different type
        mock_template.primary_language = "fr"  # Different language
        mock_template.supported_languages = ["fr", "de"]
        mock_template.context_tags = ["fashion", "luxury"]  # Different context
        mock_template.target_audience = ["teenagers"]  # Different audience
        mock_template.success_rate = 0.45
        mock_template.average_user_rating = 2.5
        mock_template.conversion_rate = 0.03

        score = prompt_service._calculate_template_score(mock_template, sample_prompt_request)
        
        # Should have low score due to mismatches
        assert score < 0.5
        logger.info("Low match template scoring test passed")

    @pytest.mark.asyncio
    async def test_get_optimized_prompt_english_product(self, prompt_service, sample_prompt_request, test_db_session):
        """Test getting optimized prompt for English product."""
        with patch.object(prompt_service, '_find_best_template', new_callable=AsyncMock) as mock_find:
            mock_template = Mock()
            mock_template.id = 1
            mock_template.template_content = "Create a description for {product_title}"
            mock_template.primary_language = "en"
            mock_find.return_value = mock_template

            with patch.object(prompt_service, '_get_cultural_adaptation', new_callable=AsyncMock) as mock_adaptation:
                mock_adaptation.return_value = None

                result = await prompt_service.get_optimized_prompt(sample_prompt_request, test_db_session)
                
                assert "prompt" in result
                assert "template_id" in result
                assert result["template_id"] == 1
                assert "Test Product" in result["prompt"]
                logger.info("English optimized prompt test passed")

    @pytest.mark.asyncio
    async def test_get_optimized_prompt_with_cultural_adaptation(self, prompt_service, test_db_session):
        """Test getting optimized prompt with cultural adaptation."""
        hebrew_request = IntelligentPromptRequest(
            content_type="product_description",
            language="he",
            cultural_region="middle_east",
            product_data={"title": "מוצר טסט", "description": "תיאור מוצר"},
            target_audience="general",
            context_tags=["ecommerce"]
        )

        with patch.object(prompt_service, '_find_best_template', new_callable=AsyncMock) as mock_find:
            mock_template = Mock()
            mock_template.id = 1
            mock_template.template_content = "Create a description for {product_title}"
            mock_template.primary_language = "en"
            mock_find.return_value = mock_template

            with patch.object(prompt_service, '_get_cultural_adaptation', new_callable=AsyncMock) as mock_adaptation:
                mock_cultural_adaptation = Mock()
                mock_cultural_adaptation.adapted_prompt = "צור תיאור עבור {product_title}"
                mock_adaptation.return_value = mock_cultural_adaptation

                result = await prompt_service.get_optimized_prompt(hebrew_request, test_db_session)
                
                assert "prompt" in result
                assert "cultural_adaptation" in result
                assert "מוצר טסט" in result["prompt"]
                logger.info("Cultural adaptation test passed")

    @pytest.mark.asyncio
    async def test_get_cultural_adaptation_auto_create(self, prompt_service, test_db_session):
        """Test automatic creation of cultural adaptation."""
        mock_template = Mock()
        mock_template.id = 1
        mock_template.primary_language = "en"
        mock_template.template_content = "Create description for {product_title}"

        hebrew_request = IntelligentPromptRequest(
            content_type="product_description",
            language="he",
            cultural_region="middle_east",
            product_data={"title": "מוצר טסט"},
            target_audience="general"
        )

        with patch.object(prompt_service, '_create_cultural_adaptation', new_callable=AsyncMock) as mock_create:
            mock_adaptation = Mock()
            mock_adaptation.adapted_prompt = "צור תיאור עבור {product_title}"
            mock_create.return_value = mock_adaptation

            result = await prompt_service._get_cultural_adaptation(mock_template, hebrew_request, test_db_session)
            
            assert result is not None
            mock_create.assert_called_once()
            logger.info("Auto-create cultural adaptation test passed")

    def test_load_cultural_intelligence(self, prompt_service):
        """Test loading of cultural intelligence data."""
        assert hasattr(prompt_service, 'cultural_intelligence')
        assert "middle_east" in prompt_service.cultural_intelligence
        
        hebrew_culture = prompt_service.cultural_intelligence["middle_east"]["hebrew"]
        assert hebrew_culture["text_direction"] == "rtl"
        assert hebrew_culture["currency_symbol"] == "₪"
        logger.info("Cultural intelligence loading test passed")

    @pytest.mark.asyncio
    async def test_error_handling_no_template_found(self, prompt_service, sample_prompt_request, test_db_session):
        """Test error handling when no suitable template is found."""
        with patch.object(prompt_service, '_find_best_template', new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None

            result = await prompt_service.get_optimized_prompt(sample_prompt_request, test_db_session)
            
            assert "error" in result
            assert "No suitable template found" in result["error"]
            logger.info("No template found error handling test passed")

    def test_detect_product_language_edge_cases(self, prompt_service):
        """Test language detection with edge cases."""
        # Empty data
        empty_data = {}
        assert prompt_service._detect_product_language(empty_data) == "en"
        
        # Mixed content (should default to English)
        mixed_data = {
            "title": "Product מוצר",
            "description": "Mixed content with עברית and English"
        }
        assert prompt_service._detect_product_language(mixed_data) == "en"
        
        # Only Hebrew
        hebrew_data = {
            "title": "מוצר מעולה",
            "description": "תיאור מפורט של מוצר איכותי"
        }
        assert prompt_service._detect_product_language(hebrew_data) == "he"
        
        logger.info("Language detection edge cases test passed") 