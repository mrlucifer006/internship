"""
Test configuration and fixtures for pytest.
"""
import pytest
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TestingConfig
from app import app as flask_app
from db import init_db


@pytest.fixture
def app():
    """Create and configure a test Flask app instance."""
    flask_app.config.from_object(TestingConfig)
    
    # Initialize test database
    init_db()
    
    # Create application context  
    ctx = flask_app.app_context()
    ctx.push()
    
    yield flask_app
    
    ctx.pop()


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()
