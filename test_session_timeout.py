"""
Unit tests for session timeout handling.

Tests for Task 10.2: Add session timeout handling
Validates Requirements: 8.3
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import auth


@pytest.mark.auth
@pytest.mark.unit
class TestSessionTimeoutHandling:
    """Test suite for session timeout handling functionality (Task 10.2)."""
    
    @patch('auth.st')
    def test_session_timeout_flag_set_on_expiration(self, mock_st):
        """Test that session_timeout flag is set when session expires."""
        # Setup expired session
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=9)  # Expired (>8 hours)
        }
        
        # Call is_authenticated which should detect timeout
        result = auth.is_authenticated()
        
        # Verify session_timeout flag was set
        assert mock_st.session_state['session_timeout'] is True, "Should set session_timeout flag"
        assert result is False, "Should return False for expired session"
    
    @patch('auth.st')
    def test_session_timeout_flag_not_set_for_valid_session(self, mock_st):
        """Test that session_timeout flag is not set for valid sessions."""
        # Setup valid session
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=2)  # Valid (<8 hours)
        }
        
        # Call is_authenticated
        result = auth.is_authenticated()
        
        # Verify session_timeout flag was not set
        assert 'session_timeout' not in mock_st.session_state, "Should not set session_timeout flag for valid session"
        assert result is True, "Should return True for valid session"
    
    @patch('auth.st')
    def test_session_timeout_exactly_8_hours(self, mock_st):
        """Test session timeout at exactly 8 hours boundary."""
        # Setup session at exactly 8 hours
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=8, seconds=1)  # Just over 8 hours
        }
        
        # Call is_authenticated
        result = auth.is_authenticated()
        
        # Verify timeout occurred
        assert mock_st.session_state['session_timeout'] is True, "Should timeout at 8 hours"
        assert result is False, "Should return False at 8 hours"
    
    @patch('auth.st')
    def test_session_timeout_just_under_8_hours(self, mock_st):
        """Test session remains valid just under 8 hours."""
        # Setup session just under 8 hours
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=7, minutes=59)  # Just under 8 hours
        }
        
        # Call is_authenticated
        result = auth.is_authenticated()
        
        # Verify session is still valid
        assert 'session_timeout' not in mock_st.session_state, "Should not timeout before 8 hours"
        assert result is True, "Should return True before 8 hours"
    
    @patch('auth.st')
    def test_session_timeout_clears_authentication(self, mock_st):
        """Test that timeout clears authentication state."""
        # Setup expired session
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=10)
        }
        
        # Call is_authenticated
        auth.is_authenticated()
        
        # Verify authentication was cleared (logout was called)
        assert 'authenticated' not in mock_st.session_state, "Should clear authenticated flag"
        assert 'professor_id' not in mock_st.session_state, "Should clear professor_id"
        assert 'username' not in mock_st.session_state, "Should clear username"
        assert 'login_timestamp' not in mock_st.session_state, "Should clear login_timestamp"
    
    @patch('auth.st')
    def test_session_timeout_preserves_flag_for_display(self, mock_st):
        """Test that session_timeout flag persists after logout for message display."""
        # Setup expired session
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=9)
        }
        
        # Call is_authenticated
        auth.is_authenticated()
        
        # Verify session_timeout flag still exists after logout
        assert 'session_timeout' in mock_st.session_state, "Should preserve session_timeout flag"
        assert mock_st.session_state['session_timeout'] is True, "Flag should be True"
    
    @patch('auth.st')
    def test_session_timeout_not_authenticated(self, mock_st):
        """Test timeout check when not authenticated."""
        # Setup unauthenticated session
        mock_st.session_state = {
            'authenticated': False
        }
        
        # Call is_authenticated
        result = auth.is_authenticated()
        
        # Verify no timeout flag is set
        assert 'session_timeout' not in mock_st.session_state, "Should not set timeout flag when not authenticated"
        assert result is False, "Should return False when not authenticated"
    
    @patch('auth.st')
    def test_session_timeout_missing_login_timestamp(self, mock_st):
        """Test timeout check when login_timestamp is missing."""
        # Setup session without login_timestamp
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser'
        }
        
        # Call is_authenticated
        result = auth.is_authenticated()
        
        # Verify timeout occurred (missing timestamp treated as expired)
        assert mock_st.session_state['session_timeout'] is True, "Should timeout when login_timestamp missing"
        assert result is False, "Should return False when login_timestamp missing"
    
    @patch('auth.st')
    def test_check_session_timeout_function(self, mock_st):
        """Test check_session_timeout function directly."""
        # Test with expired session
        mock_st.session_state = {
            'login_timestamp': datetime.now() - timedelta(hours=9)
        }
        assert auth.check_session_timeout() is True, "Should return True for expired session"
        
        # Test with valid session
        mock_st.session_state = {
            'login_timestamp': datetime.now() - timedelta(hours=3)
        }
        assert auth.check_session_timeout() is False, "Should return False for valid session"
        
        # Test with missing timestamp
        mock_st.session_state = {}
        assert auth.check_session_timeout() is True, "Should return True when timestamp missing"
    
    @patch('auth.st')
    @patch('auth.logger')
    def test_session_timeout_logging(self, mock_logger, mock_st):
        """Test that logout is logged when session times out."""
        # Setup expired session
        mock_st.session_state = {
            'authenticated': True,
            'professor_id': 1,
            'username': 'testuser',
            'login_timestamp': datetime.now() - timedelta(hours=10)
        }
        
        # Call is_authenticated
        auth.is_authenticated()
        
        # Verify logout was logged
        mock_logger.info.assert_called_with("User logged out")
