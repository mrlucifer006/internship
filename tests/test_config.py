"""
Tests for configuration module.
"""
import os
import pytest
from config import Config, DevelopmentConfig, ProductionConfig


def test_config_defaults():
    """Test that configuration has sensible defaults."""
    config = Config()
    
    assert config.HOST == "0.0.0.0"
    assert config.PORT == 5000
    assert config.LOG_LEVEL == "INFO"
    assert config.SESSION_LIFETIME_HOURS == 24


def test_development_config():
    """Test development configuration."""
    config = DevelopmentConfig()
    
    assert config.DEBUG == True
    assert config.LOG_LEVEL==  "DEBUG"


def test_production_config():
    """Test production configuration."""
    config = ProductionConfig()
    
    assert config.DEBUG == False
    assert config.LOG_LEVEL == "WARNING"


def test_config_validation():
    """Test configuration validation."""
    # Should return warnings for missing values
    warnings = Config.validate()
    
    # Should have warnings if not configured
    assert isinstance(warnings, list)
