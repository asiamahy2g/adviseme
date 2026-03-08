"""
Integration test for Task 10.1: Database Error Handling

This test verifies that the safe_database_operation decorator and error handling
work correctly in an end-to-end scenario.

Validates Requirements: 10.1, 10.2, 10.3
"""

import pytest
import sqlite3
import os
import tempfile
from unittest.mock import patch, MagicMock
from database import (
    initialize_database,
    create_professor,
    save_advising_session,
    get_professor_history,
    DB_PATH
)


@pytest.mark.integration
class TestDatabaseErrorHandlingIntegration:
    """Integration tests for database error handling (Task 10.1)."""
    
    def setup_method(self):
        """Set up test database."""
        # Use a temporary database for testing
        self.original_db_path = DB_PATH
        
    def teardown_method(self):
        """Clean up test database."""
        # Remove test database if it exists
        if os.path.exists("test_adviseme.db"):
            os.remove("test_adviseme.db")
    
    @patch('database.DB_PATH', 'test_adviseme.db')
    def test_complete_error_handling_flow(self):
        """Test complete flow with database errors handled gracefully."""
        # Initialize database
        initialize_database()
        
        # Create a professor
        success = create_professor("testprof", "password123")
        assert success is True, "Should create professor successfully"
        
        # Save an advising session
        save_success = save_advising_session(
            professor_id=1,
            student_name="John Doe",
            semester="Spring",
            year=2024,
            email_content="Test email",
            recommended_schedule="Test schedule"
        )
        assert save_success is True, "Should save session successfully"
        
        # Get history
        history = get_professor_history(1)
        assert len(history) == 1, "Should retrieve saved session"
        assert history[0]['student_name'] == "John Doe"
    
    @patch('database.get_db_connection')
    def test_graceful_degradation_on_connection_failure(self, mock_conn):
        """Test application continues when database connection fails."""
        # Simulate connection failure
        mock_conn.side_effect = sqlite3.OperationalError("Unable to open database")
        
        # All operations should return appropriate defaults without raising exceptions
        init_result = initialize_database()
        assert init_result is None, "Should return None on init failure"
        
        create_result = create_professor("testuser", "password123")
        assert create_result is False, "Should return False on create failure"
        
        save_result = save_advising_session(
            professor_id=1,
            student_name="Test",
            semester="Spring",
            year=2024,
            email_content="Email",
            recommended_schedule="Schedule"
        )
        assert save_result is False, "Should return False on save failure"
        
        history_result = get_professor_history(1)
        assert history_result == [], "Should return empty list on history failure"
    
    @patch('database.get_db_connection')
    def test_error_logging_on_database_failure(self, mock_conn, caplog):
        """Test that database errors are properly logged."""
        mock_conn.side_effect = sqlite3.OperationalError("Database locked")
        
        with caplog.at_level("ERROR"):
            initialize_database()
            create_professor("testuser", "password123")
            save_advising_session(
                professor_id=1,
                student_name="Test",
                semester="Spring",
                year=2024,
                email_content="Email",
                recommended_schedule="Schedule"
            )
        
        # Verify errors were logged
        assert "Database operation failed" in caplog.text
        assert "initialize_database" in caplog.text or "create_professor" in caplog.text
    
    @patch('database.DB_PATH', '/invalid/path/adviseme.db')
    def test_app_continues_with_invalid_database_path(self):
        """Test application continues when database path is invalid."""
        # Should not raise exception
        result = initialize_database()
        
        # Decorator should catch the error and return None
        assert result is None, "Should return None when path is invalid"
    
    def test_user_friendly_error_messages(self):
        """Test that error handling provides user-friendly messages."""
        # This test verifies the decorator returns appropriate values
        # that can be used to display user-friendly messages
        
        @patch('database.get_db_connection')
        def test_save_failure_returns_false(mock_conn):
            mock_conn.side_effect = sqlite3.OperationalError("Disk full")
            result = save_advising_session(
                professor_id=1,
                student_name="Test",
                semester="Spring",
                year=2024,
                email_content="Email",
                recommended_schedule="Schedule"
            )
            # False return allows UI to show: "Could not save to history"
            assert result is False
        
        @patch('database.get_db_connection')
        def test_history_failure_returns_empty_list(mock_conn):
            mock_conn.side_effect = sqlite3.OperationalError("Connection timeout")
            result = get_professor_history(1)
            # Empty list allows UI to show: "No history available"
            assert result == []
        
        test_save_failure_returns_false()
        test_history_failure_returns_empty_list()


@pytest.mark.integration
class TestDatabaseRecovery:
    """Test database recovery after errors."""
    
    def teardown_method(self):
        """Clean up test database."""
        if os.path.exists("test_recovery.db"):
            os.remove("test_recovery.db")
    
    @patch('database.DB_PATH', 'test_recovery.db')
    def test_database_operations_resume_after_temporary_failure(self):
        """Test that operations resume normally after temporary database failure."""
        # Initialize database successfully
        initialize_database()
        
        # Create professor successfully
        success = create_professor("testprof", "password123")
        assert success is True
        
        # Simulate temporary failure with mock
        with patch('database.get_db_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.OperationalError("Temporary lock")
            
            # Operation should fail gracefully
            save_result = save_advising_session(
                professor_id=1,
                student_name="Test",
                semester="Spring",
                year=2024,
                email_content="Email",
                recommended_schedule="Schedule"
            )
            assert save_result is False
        
        # After mock is removed, operations should work again
        save_result = save_advising_session(
            professor_id=1,
            student_name="John Doe",
            semester="Spring",
            year=2024,
            email_content="Email",
            recommended_schedule="Schedule"
        )
        assert save_result is True, "Should resume normal operation after temporary failure"
        
        # Verify data was saved
        history = get_professor_history(1)
        assert len(history) == 1
        assert history[0]['student_name'] == "John Doe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
