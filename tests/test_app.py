"""
Basic tests for Flask application routes and functionality.
"""
import pytest


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_login_page_loads(client):
    """Test that login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'login' in response.data.lower()


def test_redirect_to_login(client):
    """Test that unauthenticated users are redirected to login."""
    response = client.get('/home', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


def test_404_error_page(client):
    """Test 404 error handling."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404


def test_api_404(client):
    """Test 404 for API endpoints returns JSON."""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    assert response.is_json
    data = response.get_json()
    assert 'error' in data


def test_unauthorized_api_access(client):
    """Test that API endpoints require authentication."""
    response = client.get('/api/visitors')
    assert response.status_code == 401
    assert response.is_json
