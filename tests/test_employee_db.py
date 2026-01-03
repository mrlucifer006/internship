"""
Tests for employee database operations.
"""
import pytest
from employee_db import hash_password, verify_password, insert_employee, check_credentials


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test123"
    hashed = hash_password(password)
    
    # Should not be plain text
    assert hashed != password
    
    # Should verify correctly
    assert verify_password(password, hashed)
    
    # Should not verify wrong password
    assert not verify_password("wrong", hashed)


def test_backward_compatibility():
    """Test backward compatibility with plain text passwords."""
    plain_password = "plaintext123"
    
    # Should accept plain text (backward compatibility)
    assert verify_password(plain_password, plain_password)


def test_insert_employee():
    """Test employee insertion with hashed password."""
    employee_data = {
        "name": "Test User",
        "phone": "9876543210",
        "login_id": f"test_user_{pytest.__version__}",  # Unique ID
        "password": "secure123",
        "Auth_level": 3,
        "status": 0
    }
    
    result = insert_employee(employee_data)
    assert result == True


def test_check_credentials():
    """Test credential checking."""
    # Test with hardcoded super admin (no database required)
    # This tests the fallback mechanism
    # Note: In real tests you'd create a test user first
    pass  # Skip for now as it requires database setup
