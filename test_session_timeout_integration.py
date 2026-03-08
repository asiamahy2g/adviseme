"""
Integration test for session timeout handling (Task 10.2)

This test demonstrates the complete session timeout flow:
1. User logs in successfully
2. Session is valid for 8 hours
3. After 8 hours, any page interaction triggers auto-logout
4. User sees timeout message and must log in again

Validates: Requirements 8.3
"""

import pytest
from datetime import datetime, timedelta
import streamlit as st
import auth


@pytest.fixture
def clean_session():
    """Clean session state before and after each test."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    yield
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def test_complete_session_timeout_flow(clean_session):
    """
    Test the complete session timeout flow as it would happen in the application.
    
    Scenario:
    1. Professor logs in at 9:00 AM
    2. Professor uses the app throughout the day
    3. At 5:01 PM (8 hours 1 minute later), professor clicks something
    4. System detects timeout, logs out, and shows message
    5. Professor must log in again
    """
    # Step 1: Professor logs in successfully
    professor_id = 123
    username = "dr_smith"
    auth.create_session(professor_id, username)
    
    # Verify session is active
    assert auth.is_authenticated() is True
    assert st.session_state['authenticated'] is True
    assert st.session_state['professor_id'] == professor_id
    assert st.session_state['username'] == username
    
    # Step 2: Professor uses the app - multiple page interactions within 8 hours
    # Simulate 5 hours passing
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=5)
    assert auth.is_authenticated() is True  # Still valid
    
    # Simulate 7 hours 59 minutes passing
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=7, minutes=59)
    assert auth.is_authenticated() is True  # Still valid
    
    # Step 3: Simulate 8 hours 1 minute passing (session expired)
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=8, minutes=1)
    
    # Step 4: Next page interaction checks authentication
    result = auth.is_authenticated()
    
    # Should return False (not authenticated)
    assert result is False
    
    # Should have logged out the user
    assert 'authenticated' not in st.session_state
    assert 'professor_id' not in st.session_state
    assert 'username' not in st.session_state
    assert 'login_timestamp' not in st.session_state
    
    # Should have set the timeout flag for displaying message
    assert st.session_state.get('session_timeout', False) is True
    
    # Step 5: In the real app, this would trigger the login page with timeout message
    # The timeout message would be displayed and then the flag cleared
    # (This happens in adviseme.py)


def test_session_timeout_exactly_at_8_hours(clean_session):
    """Test that session expires after more than 8 hours."""
    auth.create_session(123, "test_user")
    
    # 7 hours 59 minutes - should be valid
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=7, minutes=59)
    assert auth.is_authenticated() is True
    
    # 8 hours and 1 minute - should expire
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=8, minutes=1)
    assert auth.is_authenticated() is False
    assert st.session_state.get('session_timeout', False) is True


def test_multiple_page_interactions_before_timeout(clean_session):
    """Test that multiple page interactions work correctly before timeout."""
    auth.create_session(123, "test_user")
    login_time = datetime.now()
    st.session_state['login_timestamp'] = login_time
    
    # Simulate 10 page interactions over 7 hours (all should succeed)
    for hours in range(0, 8):
        st.session_state['login_timestamp'] = login_time - timedelta(hours=hours)
        assert auth.is_authenticated() is True, f"Should be authenticated at {hours} hours"
    
    # 9th hour - should fail
    st.session_state['login_timestamp'] = login_time - timedelta(hours=9)
    assert auth.is_authenticated() is False
    assert st.session_state.get('session_timeout', False) is True


def test_session_timeout_message_cleared_after_display(clean_session):
    """Test that timeout message flag can be cleared after display."""
    auth.create_session(123, "test_user")
    st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=9)
    
    # Trigger timeout
    auth.is_authenticated()
    assert st.session_state.get('session_timeout', False) is True
    
    # Simulate the app clearing the flag after displaying the message
    # (This is what happens in adviseme.py)
    del st.session_state['session_timeout']
    assert 'session_timeout' not in st.session_state
    
    # User should still not be authenticated
    assert auth.is_authenticated() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
