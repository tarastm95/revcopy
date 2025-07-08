# RevCopy Test Suite

## Overview

This document describes the comprehensive unit test suite for the RevCopy application. All old test files have been removed and replaced with proper unit tests following industry best practices.

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                    # Test configuration and fixtures
├── test_ai_service.py            # Tests for AI service functionality
├── test_intelligent_prompt_service.py  # Tests for intelligent prompt service
├── test_models.py                # Tests for database models
├── test_api_endpoints.py         # Tests for API endpoints
└── test_prompt_management_api.py # Tests for prompt management API
```

## Test Coverage

The test suite covers:

### AI Service (`test_ai_service.py`)
- ✅ Language detection (English/Hebrew/Mixed content)
- ✅ Product language detection edge cases
- ✅ Prompt formatting with different languages
- ✅ Currency formatting (USD for English, Shekel for Hebrew)
- ✅ Comprehensive content generation
- ✅ Error handling scenarios
- ✅ Template variable handling

### Intelligent Prompt Service (`test_intelligent_prompt_service.py`)
- ✅ Language detection functionality
- ✅ Cultural intelligence loading
- ✅ Template scoring algorithm
- ✅ Cultural adaptation logic
- ✅ Optimized prompt generation

### Database Models (`test_models.py`)
- ✅ PromptTemplate creation and validation
- ✅ CulturalAdaptation model relationships
- ✅ Required field validation
- ✅ Model relationships and foreign keys

### API Endpoints (`test_api_endpoints.py`, `test_prompt_management_api.py`)
- ✅ Template CRUD operations
- ✅ Cultural adaptation endpoints
- ✅ Error handling and validation
- ✅ Authentication and authorization
- ✅ Request/response validation

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r test_requirements.txt
```

### Run All Tests
```bash
# Using the test runner
python run_tests.py

# Or directly with pytest
python -m pytest tests/ -v
```

### Run Specific Test Files
```bash
# Test AI service only
python -m pytest tests/test_ai_service.py -v

# Test models only
python -m pytest tests/test_models.py -v

# Test API endpoints only
python -m pytest tests/test_api_endpoints.py -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

## Test Configuration

### Environment Variables
Tests automatically set up the following environment:
- `POSTGRES_SERVER=localhost`
- `POSTGRES_USER=test`
- `POSTGRES_PASSWORD=test`
- `POSTGRES_DB=test_revcopy`
- `OPENAI_API_KEY=test-key`
- `DEEPSEEK_API_KEY=test-key`
- `TESTING=true`

### Database
Tests use an in-memory SQLite database for speed and isolation.

### Fixtures
Common test fixtures are available in `conftest.py`:
- `test_db_session`: Database session for tests
- `test_client`: HTTP client for API tests
- `sample_product_data`: English product data
- `sample_hebrew_product_data`: Hebrew product data
- `mock_ai_service`: Mocked AI service

## Key Test Features

### 🔍 Language Detection Testing
Comprehensive tests for detecting English vs Hebrew products:
```python
def test_detect_product_language_hebrew(self, ai_service, sample_hebrew_product_data):
    detected_language = ai_service._detect_product_language(sample_hebrew_product_data)
    assert detected_language == "he"
```

### 🌍 Cultural Adaptation Testing
Tests ensure Hebrew products get proper RTL and Shekel formatting:
```python
def test_format_prompt_hebrew_product(self, ai_service, sample_hebrew_product_data):
    # Should use Shekel currency for Hebrew products
    assert "₪99.90" in formatted_prompt
```

### 🚨 Error Handling Testing
All tests include proper error scenarios:
```python
async def test_generate_comprehensive_content_error_handling(self, ai_service):
    with patch.object(ai_service, 'generate_text') as mock_generate:
        mock_generate.side_effect = Exception("AI service error")
        result = await ai_service.generate_comprehensive_content(...)
        assert "error" in result
```

### 📊 Coverage Requirements
- Minimum 70% code coverage enforced
- All public methods must have tests
- Error paths must be tested
- Edge cases must be covered

## Best Practices Implemented

1. **Single Responsibility**: Each test tests one specific functionality
2. **Proper Mocking**: External dependencies are mocked
3. **Meaningful Names**: Test names clearly describe what they test
4. **Error Handling**: All error scenarios are tested
5. **Documentation**: Every test has clear docstrings
6. **Fixtures**: Reusable test data and setups
7. **Isolation**: Tests don't depend on each other
8. **Fast Execution**: In-memory database for speed

## Adding New Tests

When adding new functionality:

1. Create test file: `tests/test_your_module.py`
2. Import the module to test
3. Create test class: `class TestYourModule:`
4. Add test methods: `def test_your_function():`
5. Use fixtures from `conftest.py`
6. Mock external dependencies
7. Test both success and error cases
8. Run tests to ensure they pass

Example:
```python
"""Unit tests for your new module."""

import pytest
from app.your_module import YourClass

class TestYourModule:
    @pytest.fixture
    def your_instance(self):
        return YourClass()
    
    def test_your_function_success(self, your_instance):
        result = your_instance.your_function("test_input")
        assert result == "expected_output"
    
    def test_your_function_error(self, your_instance):
        with pytest.raises(ValueError):
            your_instance.your_function(None)
```

## Continuous Integration

Tests can be integrated into CI/CD pipelines:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r test_requirements.txt
    python run_tests.py
```

The test suite is designed to be fast, reliable, and comprehensive, ensuring the RevCopy application maintains high quality and reliability. 