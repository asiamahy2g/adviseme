"""
Integration test for admin UI functionality (Task 11.2)

Tests the complete flow of admin account creation through the UI.
"""

import pytest
import os
import tempfile
import sqlite3
from unittest.mock import patch
import streamlit as st
import auth
import database


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    # Create a temporary file for the database
    temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_fd)
    
    # Patch the database path
    with patch('database.DB_PATH', temp_path):
        # Initialize the database
        database.initialize_database()
        yield temp_path
    
    # Clean up
    try:
        os.unlink(temp_path)
    except:
        pass


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


class TestAdminIntegration:
    """Integration tests for admin UI (Task 11.2)"""
    
    def test_admin_can_create_professor_account(self, temp_database, mock_session_state):
        """Test that admin can successfully create a professor account."""
        # Set up admin session
        auth.create_session(1, "admin")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            # Verify admin status
            assert auth.is_admin() is True
            
            # Create a professor account
            with patch('database.DB_PATH', temp_database):
                success = database.create_professor("test_professor", "password123")
                assert success is True
                
                # Verify the account was created in the database
                conn = sqlite3.connect(temp_database)
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM professors WHERE username = ?", ("test_professor",))
                result = cursor.fetchone()
                conn.close()
                
                assert result is not None
                assert result[0] == "test_professor"
    
    def test_non_admin_cannot_see_admin_ui(self, mock_session_state):
        """Test that non-admin users cannot access admin functionality."""
        # Set up non-admin session
        auth.create_session(2, "regular_professor")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            # Verify non-admin status
            assert auth.is_admin() is False
            # In the actual UI, the admin expander would not be rendered
    
    def test_admin_ui_handles_duplicate_username(self, temp_database, mock_session_state):
        """Test that admin UI properly handles duplicate username errors."""
        # Set up admin session
        auth.create_session(1, "admin")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            with patch('database.DB_PATH', temp_database):
                # Create first account
                success1 = database.create_professor("duplicate_user", "password123")
                assert success1 is True
                
                # Try to create duplicate account - should return False due to decorator
                success2 = database.create_professor("duplicate_user", "password456")
                assert success2 is False
    
    def test_admin_ui_validates_password_length(self, temp_database, mock_session_state):
        """Test that admin UI validates password length (minimum 8 characters)."""
        # Set up admin session
        auth.create_session(1, "admin")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            with patch('database.DB_PATH', temp_database):
                # Try to create account with short password - should raise ValueError
                with pytest.raises(ValueError, match="at least 8 characters"):
                    database.create_professor("test_user", "short")
    
    def test_admin_ui_validates_username_format(self, temp_database, mock_session_state):
        """Test that admin UI validates username format."""
        # Set up admin session
        auth.create_session(1, "admin")
        
        with patch.dict('os.environ', {'ADMIN_USERNAME': 'admin'}):
            with patch('database.DB_PATH', temp_database):
                # Try to create account with invalid username (contains spaces) - should raise ValueError
                with pytest.raises(ValueError, match="alphanumeric characters"):
                    database.create_professor("invalid user", "password123")
                
                # Try to create account with invalid username (contains special chars) - should raise ValueError
                with pytest.raises(ValueError, match="alphanumeric characters"):
                    database.create_professor("user@domain", "password123")
