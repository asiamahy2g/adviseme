"""
Unit tests for admin authentication functionality.

Tests the admin authentication check and admin credential verification
against environment variables.
"""

import pytest
import os
from unittest.mock import patch
import auth


def test_is_admin_not_authenticated():
    """Test that is_admin returns False when user is not authenticated."""
    with patch('auth.is_authenticated', return_value=False):
        assert auth.is_admin() is False


def test_is_admin_no_admin_username_configured():
    """Test that is_admin returns False when ADMIN_USERNAME is not configured."""
    with patch('auth.is_authenticated', return_value=True), \
         patch('os.getenv', return_value=None), \
         patch('streamlit.session_state', {'username': 'testuser'}):
        assert auth.is_admin() is False


def test_is_admin_user_is_admin():
    """Test that is_admin returns True when current user matches admin username."""
    with patch('auth.is_authenticated', return_value=True), \
         patch('os.getenv', return_value='admin'), \
         patch('streamlit.session_state', {'username': 'admin'}):
        assert auth.is_admin() is True


def test_is_admin_user_is_not_admin():
    """Test that is_admin returns False when current user does not match admin username."""
    with patch('auth.is_authenticated', return_value=True), \
         patch('os.getenv', return_value='admin'), \
         patch('streamlit.session_state', {'username': 'professor1'}):
        assert auth.is_admin() is False


def test_authenticate_admin_valid_credentials():
    """Test that authenticate_admin returns True with valid admin credentials."""
    with patch.dict(os.environ, {'ADMIN_USERNAME': 'admin', 'ADMIN_PASSWORD': 'admin123'}):
        assert auth.authenticate_admin('admin', 'admin123') is True


def test_authenticate_admin_invalid_username():
    """Test that authenticate_admin returns False with invalid username."""
    with patch.dict(os.environ, {'ADMIN_USERNAME': 'admin', 'ADMIN_PASSWORD': 'admin123'}):
        assert auth.authenticate_admin('wronguser', 'admin123') is False


def test_authenticate_admin_invalid_password():
    """Test that authenticate_admin returns False with invalid password."""
    with patch.dict(os.environ, {'ADMIN_USERNAME': 'admin', 'ADMIN_PASSWORD': 'admin123'}):
        assert auth.authenticate_admin('admin', 'wrongpassword') is False


def test_authenticate_admin_no_credentials_configured():
    """Test that authenticate_admin returns False when admin credentials are not configured."""
    with patch.dict(os.environ, {}, clear=True):
        assert auth.authenticate_admin('admin', 'admin123') is False


def test_authenticate_admin_missing_username():
    """Test that authenticate_admin returns False when ADMIN_USERNAME is missing."""
    with patch.dict(os.environ, {'ADMIN_PASSWORD': 'admin123'}, clear=True):
        assert auth.authenticate_admin('admin', 'admin123') is False


def test_authenticate_admin_missing_password():
    """Test that authenticate_admin returns False when ADMIN_PASSWORD is missing."""
    with patch.dict(os.environ, {'ADMIN_USERNAME': 'admin'}, clear=True):
        assert auth.authenticate_admin('admin', 'admin123') is False
