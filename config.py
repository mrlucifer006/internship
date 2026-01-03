"""
Configuration management for Visitor Management System.
Loads configuration from environment variables with sensible defaults.
"""
import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Database Configuration
    EMPLOYEE_DB_PATH = os.getenv('EMPLOYEE_DB_PATH', 'employee.db')
    VISITORS_DB_PATH = os.getenv('VISITORS_DB_PATH', 'visitors.db')
    VEHICLE_DB_PATH = os.getenv('VEHICLE_DB_PATH', 'vehicle.db')
    
    # Session Configuration
    SESSION_LIFETIME_HOURS = int(os.getenv('SESSION_LIFETIME_HOURS', 24))
    PERMANENT_SESSION_LIFETIME = timedelta(hours=SESSION_LIFETIME_HOURS)
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # WhatsApp Configuration
    LOGISTICS_PHONE_NUMBER = os.getenv('LOGISTICS_PHONE_NUMBER', '')
    
    # Application Settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        warnings = []
        
        # Warn if using default secret key
        if cls.SECRET_KEY == secrets.token_hex(32) and os.getenv('SECRET_KEY') is None:
            warnings.append(
                "WARNING: Using generated SECRET_KEY. "
                "Set SECRET_KEY in .env for production!"
            )
        
        # Warn if logistics phone number is not set
        if not cls.LOGISTICS_PHONE_NUMBER:
            warnings.append(
                "WARNING: LOGISTICS_PHONE_NUMBER not set. "
                "Logistics WhatsApp notifications will fail."
            )
        
        return warnings


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def validate(cls):
        """Additional validation for production."""
        warnings = super().validate()
        errors = []
        
        # Require SECRET_KEY to be set explicitly in production
        if os.getenv('SECRET_KEY') is None:
            errors.append(
                "ERROR: SECRET_KEY must be explicitly set in production! "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        if errors:
            raise ValueError('\n'.join(errors))
        
        return warnings


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    # Use in-memory databases for testing
    EMPLOYEE_DB_PATH = ':memory:'
    VISITORS_DB_PATH = ':memory:'
    VEHICLE_DB_PATH = ':memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.getenv('FLASK_ENV', 'development').lower()
    return config.get(env, config['default'])
