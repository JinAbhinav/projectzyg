"""
Test the configuration module.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seer.utils.config import settings


class TestConfig(unittest.TestCase):
    """Test cases for the configuration module."""
    
    def test_settings_exist(self):
        """Test that settings object exists."""
        self.assertIsNotNone(settings)
    
    def test_app_name(self):
        """Test app name setting."""
        self.assertEqual(settings.APP_NAME, "SEER")
    
    def test_app_version(self):
        """Test app version setting."""
        self.assertEqual(settings.APP_VERSION, "0.1.0")
    
    def test_database_settings(self):
        """Test database settings."""
        self.assertIsNotNone(settings.database)
        self.assertIsNotNone(settings.database.DB_URL)
    
    def test_api_settings(self):
        """Test API settings."""
        self.assertIsNotNone(settings.api)
        self.assertIsInstance(settings.api.API_PORT, int)
    
    def test_crawler_settings(self):
        """Test crawler settings."""
        self.assertIsNotNone(settings.crawler)
        self.assertIsInstance(settings.crawler.MAX_RECURSION_DEPTH, int)
    
    def test_nlp_settings(self):
        """Test NLP settings."""
        self.assertIsNotNone(settings.nlp)
        self.assertIsNotNone(settings.nlp.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main() 