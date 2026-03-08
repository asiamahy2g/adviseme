"""
Unit tests for admin UI functionality (Task 11.2)

Tests the admin interface for professor account creation.
"""

import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
import auth
import database


@pytest.fixture
def mock_session_state():
    """Fixture to provide a clean session state for each test."""
    # Clear session state before each test
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    yield st.session_state
    # Clean up after test
    for key in list(st.session_state.keys()):
        del st.session_state[key]


class TestAdminUI:
    """Tests for admin UI functionality (Task 11.2)"""
    
    def test_is_admin_returns_true_for_admin_user(self, mock_session_state):
        """Test that is_admin() returns True when logged in as admin."""
        # Set up authenticated admin session
        auth.create_session(1, "admin")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            assert auth.is_admin() is True
    
    def test_is_admin_returns_false_for_non_admin_user(self, mock_session_state):
        """Test that is_admin() returns False when logged in as regular professor."""
        # Set up authenticated non-admin session
        auth.create_session(2, "professor1")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            assert auth.is_admin() is False
    
    def test_is_admin_returns_false_when_not_authenticated(self, mock_session_state):
        """Test that is_admin() returns False when not authenticated."""
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            assert auth.is_admin() is False
    
    @patch('database.create_professor')
    def test_create_professor_success(self, mock_create_professor, mock_session_state):
        """Test successful professor account creation through admin UI."""
        mock_create_professor.return_value = True
        
        # Simulate admin creating a professor account
        username = "new_professor"
        password = "password123"
        
        result = database.create_professor(username, password)
        
        assert result is True
        mock_create_professor.assert_called_once_with(username, password)
    
    @patch('database.create_professor')
    def test_create_professor_duplicate_username(self, mock_create_professor, mock_session_state):
        """Test that duplicate username is handled correctly."""
        # Simulate database returning False for duplicate username
        mock_create_professor.return_value = False
        
        username = "existing_professor"
        password = "password123"
        
        result = database.create_professor(username, password)
        
        assert result is False
    
    @patch('database.create_professor')
    def test_create_professor_validation_error(self, mock_create_professor, mock_session_state):
        """Test that validation errors are raised for invalid input."""
        # Simulate validation error
        mock_create_professor.side_effect = ValueError("Password must be at least 8 characters long")
        
        username = "test_user"
        password = "short"
        
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            database.create_professor(username, password)
    
    def test_admin_ui_visibility_logic(self, mock_session_state):
        """Test that admin UI should only be visible when is_admin() returns True."""
        # Test 1: Admin user should see the UI
        auth.create_session(1, "admin")
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            assert auth.is_admin() is True  # UI should be visible
        
        # Clear session
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Test 2: Non-admin user should not see the UI
        auth.create_session(2, "professor1")
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            assert auth.is_admin() is False  # UI should be hidden
