"""
Tests for configuration module.
"""

import unittest
from unittest.mock import patch
from src.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    @patch.dict('os.environ', {
        'GCP_PROJECT_ID': 'test-project',
        'GCS_BUCKET_NAME': 'test-bucket',
        'GEMINI_API_KEY': 'test-key'
    })
    def test_config_validation(self):
        """Test configuration validation."""
        # Reload config to pick up mocked env vars
        from importlib import reload
        import src.config
        reload(src.config)
        from src.config import Config as ReloadedConfig
        
        self.assertTrue(ReloadedConfig.validate())
    
    @patch.dict('os.environ', {})
    def test_config_validation_fails(self):
        """Test configuration validation fails when values are missing."""
        from importlib import reload
        import src.config
        reload(src.config)
        from src.config import Config as ReloadedConfig
        
        self.assertFalse(ReloadedConfig.validate())
        self.assertGreater(len(ReloadedConfig.get_missing_configs()), 0)


if __name__ == '__main__':
    unittest.main()

