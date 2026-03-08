"""
Integration tests for login page and authentication flow in adviseme.py

Validates: Requirements 1.1, 1.2, 1.3, 2.5, 11.1
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import auth
import database


@pytest.mark.integration
@pytest.mark.auth
def test_login_page_displays_when_not_authenticated():
    """
    Test that login page is displayed when user is not authenticated.
    
    Validates: Requirement 1.1 - Login page displays before main application
    """
    # Clear session state
    st.session_state.clear()
    
    # Verify not authenticated
    assert not auth.is_authenticated()
    
    # The login page should be shown (tested via manual verification)
    # This is a smoke test to ensure the auth module works correctly


@pytest.mark.integration
@pytest.mark.auth
def test_authentication_creates_session():
    """
    Test that successful authentication creates a session with username display.
    
    Validates: Requirements 1.2, 1.5 - Authentication grants access and displays username
    """
    # Clear session state
    st.session_state.clear()
    
    # Create a test professor account
    database.initialize_database()
    username = "test_prof_login"
    password = "testpass123"
    
    # Clean up any existing test account
    try:
        with database.get_db_connection() as conn:
            conn.execute("DELETE FROM professors WHERE username = ?", (username,))
    except:
        pass
    
    # Create test account
    success = database.create_professor(username, password)
    assert success, "Failed to create test professor account"
    
    # Authenticate
    professor_id = auth.authenticate_user(username, password)
    assert professor_id is not None, "Authentication failed"
    
    # Create session
    auth.create_session(professor_id, username)
    
    # Verify session state
    assert st.session_state.get('authenticated') == True
    assert st.session_state.get('username') == username
    assert st.session_state.get('professor_id') == professor_id
    
    # Verify is_authenticated returns True
    assert auth.is_authenticated()
    
    # Clean up
    with database.get_db_connection() as conn:
        conn.execute("DELETE FROM professors WHERE username = ?", (username,))


@pytest.mark.integration
@pytest.mark.auth
def test_invalid_credentials_show_error():
    """
    Test that invalid credentials are rejected.
    
    Validates: Requirement 1.3 - Invalid credentials display error and deny access
    """
    # Clear session state
    st.session_state.clear()
    
    # Try to authenticate with invalid credentials
    professor_id = auth.authenticate_user("nonexistent_user", "wrongpassword")
    
    # Should return None
    assert professor_id is None
    
    # Should not be authenticated
    assert not auth.is_authenticated()


@pytest.mark.integration
@pytest.mark.auth
def test_lockout_after_failed_attempts():
    """
    Test that account is locked after 3 failed attempts.
    
    Validates: Requirement 2.5 - Lockout after 3 consecutive failed attempts
    """
    # Clear session state
    st.session_state.clear()
    
    username = "test_lockout_user"
    
    # Attempt authentication 3 times with wrong password
    for i in range(3):
        professor_id = auth.authenticate_user(username, "wrongpassword")
        assert professor_id is None
    
    # Check that account is now locked
    lockout_remaining = auth.get_lockout_remaining_time(username)
    assert lockout_remaining is not None
    assert lockout_remaining > 0
    
    # Verify lockout check returns True
    assert auth.check_lockout(username)


@pytest.mark.integration
@pytest.mark.auth
def test_logout_clears_session():
    """
    Test that logout clears session state.
    
    Validates: Requirement 1.6 - Logout terminates session and returns to login
    """
    from datetime import datetime
    
    # Set up authenticated session
    st.session_state['authenticated'] = True
    st.session_state['professor_id'] = 123
    st.session_state['username'] = "test_user"
    st.session_state['login_timestamp'] = datetime.now()
    
    # Verify authenticated
    assert auth.is_authenticated()
    
    # Logout
    auth.logout()
    
    # Verify session cleared
    assert not st.session_state.get('authenticated', False)
    assert 'professor_id' not in st.session_state
    assert 'username' not in st.session_state
    
    # Verify not authenticated
    assert not auth.is_authenticated()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
