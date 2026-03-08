"""
Unit tests for authentication module (auth.py)

Tests session management functions and authentication logic.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import auth
import streamlit as st


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


class TestSessionManagement:
    """Tests for session management functions (Task 4.1)"""
    
    def test_create_session(self, mock_session_state):
        """Test that create_session initializes session_state correctly."""
        professor_id = 123
        username = "test_professor"
        
        auth.create_session(professor_id, username)
        
        assert st.session_state['authenticated'] is True
        assert st.session_state['professor_id'] == professor_id
        assert st.session_state['username'] == username
        assert 'login_timestamp' in st.session_state
        assert isinstance(st.session_state['login_timestamp'], datetime)
    
    def test_is_authenticated_when_not_logged_in(self, mock_session_state):
        """Test is_authenticated returns False when not logged in."""
        assert auth.is_authenticated() is False
    
    def test_is_authenticated_when_logged_in(self, mock_session_state):
        """Test is_authenticated returns True when logged in and not expired."""
        auth.create_session(123, "test_user")
        assert auth.is_authenticated() is True
    
    def test_is_authenticated_with_expired_session(self, mock_session_state):
        """Test is_authenticated returns False and logs out when session expired."""
        # Create session with old timestamp (9 hours ago)
        auth.create_session(123, "test_user")
        st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=9)
        
        assert auth.is_authenticated() is False
        # Should have logged out
        assert 'authenticated' not in st.session_state
    
    def test_check_session_timeout_not_expired(self, mock_session_state):
        """Test check_session_timeout returns False for valid session."""
        st.session_state['login_timestamp'] = datetime.now()
        assert auth.check_session_timeout() is False
    
    def test_check_session_timeout_expired(self, mock_session_state):
        """Test check_session_timeout returns True after 8 hours."""
        st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=8, minutes=1)
        assert auth.check_session_timeout() is True
    
    def test_check_session_timeout_no_timestamp(self, mock_session_state):
        """Test check_session_timeout returns True when no timestamp exists."""
        assert auth.check_session_timeout() is True
    
    def test_logout_clears_session(self, mock_session_state):
        """Test logout clears all authentication-related session state."""
        auth.create_session(123, "test_user")
        
        auth.logout()
        
        assert 'authenticated' not in st.session_state
        assert 'professor_id' not in st.session_state
        assert 'username' not in st.session_state
        assert 'login_timestamp' not in st.session_state
    
    def test_session_timeout_sets_flag_before_logout(self, mock_session_state):
        """Test that session timeout sets session_timeout flag before logout."""
        # Create session with expired timestamp (9 hours ago)
        auth.create_session(123, "test_user")
        st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=9)
        
        # Call is_authenticated which should detect timeout
        result = auth.is_authenticated()
        
        assert result is False
        # Should have set timeout flag
        assert st.session_state.get('session_timeout', False) is True
        # Should have logged out
        assert 'authenticated' not in st.session_state
    
    def test_session_timeout_on_every_page_interaction(self, mock_session_state):
        """Test that session timeout is checked on every call to is_authenticated."""
        # Create session
        auth.create_session(123, "test_user")
        
        # First check - should be authenticated
        assert auth.is_authenticated() is True
        
        # Simulate time passing (9 hours)
        st.session_state['login_timestamp'] = datetime.now() - timedelta(hours=9)
        
        # Second check - should detect timeout and auto-logout
        assert auth.is_authenticated() is False
        assert st.session_state.get('session_timeout', False) is True
    
    def test_logout_preserves_session_timeout_flag(self, mock_session_state):
        """Test that logout doesn't clear the session_timeout flag."""
        auth.create_session(123, "test_user")
        st.session_state['session_timeout'] = True
        
        auth.logout()
        
        # session_timeout flag should still be present
        assert st.session_state.get('session_timeout', False) is True
        # But authentication data should be cleared
        assert 'authenticated' not in st.session_state


class TestAuthenticationLogic:
    """Tests for authentication logic (Task 4.3)"""
    
    def test_authenticate_user_valid_credentials(self, mock_session_state):
        """Test authenticate_user returns professor_id for valid credentials."""
        mock_professor = {
            'professor_id': 123,
            'username': 'test_user',
            'password_hash': auth.hash_password('password123')
        }
        
        with patch('database.get_professor_by_username', return_value=mock_professor):
            result = auth.authenticate_user('test_user', 'password123')
            
            assert result == 123
            # Failed attempts should be reset
            assert 'test_user' not in st.session_state.get('failed_attempts', {})
    
    def test_authenticate_user_invalid_password(self, mock_session_state):
        """Test authenticate_user returns None for invalid password."""
        mock_professor = {
            'professor_id': 123,
            'username': 'test_user',
            'password_hash': auth.hash_password('correct_password')
        }
        
        with patch('database.get_professor_by_username', return_value=mock_professor):
            result = auth.authenticate_user('test_user', 'wrong_password')
            
            assert result is None
            # Failed attempt should be recorded
            assert st.session_state['failed_attempts']['test_user'] == 1
    
    def test_authenticate_user_nonexistent_username(self, mock_session_state):
        """Test authenticate_user returns None for non-existent username."""
        with patch('database.get_professor_by_username', return_value=None):
            result = auth.authenticate_user('nonexistent', 'password')
            
            assert result is None
            # Failed attempt should be recorded
            assert st.session_state['failed_attempts']['nonexistent'] == 1
    
    def test_failed_attempt_tracking(self, mock_session_state):
        """Test that failed attempts are tracked correctly."""
        auth.record_failed_attempt('test_user')
        assert st.session_state['failed_attempts']['test_user'] == 1
        
        auth.record_failed_attempt('test_user')
        assert st.session_state['failed_attempts']['test_user'] == 2
    
    def test_lockout_after_three_failed_attempts(self, mock_session_state):
        """Test that account is locked out after 3 failed attempts."""
        # Record 3 failed attempts
        for _ in range(3):
            auth.record_failed_attempt('test_user')
        
        # Should be locked out
        assert auth.check_lockout('test_user') is True
        assert 'test_user' in st.session_state['lockout_until']
    
    def test_lockout_prevents_authentication(self, mock_session_state):
        """Test that locked out users cannot authenticate even with valid credentials."""
        # Lock out the user
        st.session_state['lockout_until'] = {
            'test_user': datetime.now() + timedelta(minutes=5)
        }
        
        mock_professor = {
            'professor_id': 123,
            'username': 'test_user',
            'password_hash': auth.hash_password('password123')
        }
        
        with patch('database.get_professor_by_username', return_value=mock_professor):
            result = auth.authenticate_user('test_user', 'password123')
            
            assert result is None  # Should be rejected due to lockout
    
    def test_lockout_expires_after_five_minutes(self, mock_session_state):
        """Test that lockout expires after 5 minutes."""
        # Set lockout to 6 minutes ago (expired)
        st.session_state['lockout_until'] = {
            'test_user': datetime.now() - timedelta(minutes=1)
        }
        
        # Should not be locked out anymore
        assert auth.check_lockout('test_user') is False
        # Lockout entry should be removed
        assert 'test_user' not in st.session_state['lockout_until']
    
    def test_reset_failed_attempts(self, mock_session_state):
        """Test that failed attempts are reset after successful login."""
        st.session_state['failed_attempts'] = {'test_user': 2}
        
        auth.reset_failed_attempts('test_user')
        
        assert 'test_user' not in st.session_state['failed_attempts']
    
    def test_get_lockout_remaining_time(self, mock_session_state):
        """Test get_lockout_remaining_time returns correct minutes."""
        # Set lockout to 3 minutes from now
        st.session_state['lockout_until'] = {
            'test_user': datetime.now() + timedelta(minutes=3, seconds=30)
        }
        
        remaining = auth.get_lockout_remaining_time('test_user')
        assert remaining == 4  # Should round up to 4 minutes
    
    def test_get_lockout_remaining_time_not_locked(self, mock_session_state):
        """Test get_lockout_remaining_time returns None when not locked out."""
        remaining = auth.get_lockout_remaining_time('test_user')
        assert remaining is None


class TestPasswordHashing:
    """Tests for password hashing functions"""
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = auth.hash_password(password)
        
        # Bcrypt hashes start with $2b$
        assert hashed.startswith('$2b$')
        # Should not equal plain text
        assert hashed != password
    
    def test_hash_password_unique_salts(self):
        """Test that same password produces different hashes (unique salts)."""
        password = "same_password"
        hash1 = auth.hash_password(password)
        hash2 = auth.hash_password(password)
        
        # Should be different due to unique salts
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "correct_password"
        hashed = auth.hash_password(password)
        
        assert auth.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verify_password returns False for incorrect password."""
        password = "correct_password"
        hashed = auth.hash_password(password)
        
        assert auth.verify_password("wrong_password", hashed) is False
    
    def test_verify_password_handles_errors(self):
        """Test verify_password handles invalid hash gracefully."""
        result = auth.verify_password("password", "invalid_hash")
        assert result is False
