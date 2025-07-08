#!/usr/bin/env python3
"""
Test runner for the RevCopy application.

This script runs all unit tests with proper setup and teardown.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test_revcopy",
        "OPENAI_API_KEY": "test-key",
        "DEEPSEEK_API_KEY": "test-key",
        "SECRET_KEY": "test-secret-key",
        "TESTING": "true"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    logger.info("Test environment configured")


def run_tests():
    """Run the test suite."""
    try:
        setup_test_environment()
        
        logger.info("Starting test suite...")
        
        # Run pytest with coverage
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            logger.info("All tests passed!")
        else:
            logger.error("Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        logger.error(f"Test run failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code) 