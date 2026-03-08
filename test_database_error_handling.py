"""
Unit tests for database error handling (Task 10.1).

Tests the safe_database_operation decorator and graceful error handling
when the database is unavailable.

Validates Requirements: 10.1, 10.2, 10.3
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from database import (
    safe_database_operation,
    initialize_database,
    create_professor,
    get_professor_by_username,
    save_advising_session,
    get_professor_history,
    load_session
)


@pytest.mark.database
@pytest.mark.unit
class TestSafeDatabaseOperationDecorator:
    """Test suite for safe_database_operation decorator (Task 10.1)."""
    
    def test_decorator_successful_operation(self):
        """Test decorator allows successful operations to proceed normally."""
        @safe_database_operation
        def successful_operation():
            return "success"
        
        result = successful_operation()
        assert result == "success", "Decorator should not interfere with successful operations"
    
    def test_decorator_handles_operational_error(self):
        """Test decorator catches sqlite3.OperationalError and returns None."""
        @safe_database_operation
        def failing_operation():
            raise sqlite3.OperationalError("Database is locked")
        
        result = failing_operation()
        assert result is None, "Decorator should return None for OperationalError"
    
    def test_decorator_handles_integrity_error_for_boolean_functions(self):
        """Test decorator returns False for IntegrityError in boolean-returning functions."""
        @safe_database_operation
        def create_professor():
            raise sqlite3.IntegrityError("UNIQUE constraint failed")
        
        result = create_professor()
        assert result is False, "Decorator should return False for IntegrityError in create functions"
    
    def test_decorator_handles_integrity_error_for_other_functions(self):
        """Test decorator returns None for IntegrityError in non-boolean functions."""
        @safe_database_operation
        def get_data():
            raise sqlite3.IntegrityError("Foreign key constraint failed")
        
        result = get_data()
        assert result is None, "Decorator should return None for IntegrityError in get functions"
    
    def test_decorator_handles_general_exception(self):
        """Test decorator catches general exceptions (but not ValueError)."""
        @safe_database_operation
        def unexpected_error():
            raise RuntimeError("Unexpected error")
        
        result = unexpected_error()
        assert result is None, "Decorator should return None for unexpected exceptions"
    
    def test_decorator_returns_empty_list_for_history_functions(self):
        """Test decorator returns empty list for history-related functions."""
        @safe_database_operation
        def get_professor_history():
            raise sqlite3.OperationalError("Database unavailable")
        
        result = get_professor_history()
        assert result == [], "Decorator should return empty list for history functions"
    
    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function name and docstring."""
        @safe_database_operation
        def test_function():
            """Test docstring"""
            pass
        
        assert test_function.__name__ == "test_function", "Decorator should preserve function name"
        assert test_function.__doc__ == "Test docstring", "Decorator should preserve docstring"
    
    def test_decorator_logs_operational_error(self, caplog):
        """Test decorator logs OperationalError with function name."""
        @safe_database_operation
        def failing_operation():
            raise sqlite3.OperationalError("Connection failed")
        
        with caplog.at_level("ERROR"):
            failing_operation()
        
        assert "Database operation failed" in caplog.text
        assert "failing_operation" in caplog.text
    
    def test_decorator_logs_integrity_error(self, caplog):
        """Test decorator logs IntegrityError with function name."""
        @safe_database_operation
        def integrity_violation():
            raise sqlite3.IntegrityError("Constraint violation")
        
        with caplog.at_level("ERROR"):
            integrity_violation()
        
        assert "Data integrity error" in caplog.text
        assert "integrity_violation" in caplog.text
    
    def test_decorator_logs_unexpected_error(self, caplog):
        """Test decorator logs unexpected exceptions."""
        @safe_database_operation
        def unexpected_error():
            raise RuntimeError("Unexpected error")
        
        with caplog.at_level("ERROR"):
            unexpected_error()
        
        assert "Unexpected error" in caplog.text
        assert "unexpected_error" in caplog.text


@pytest.mark.database
@pytest.mark.unit
class TestDatabaseFunctionsWithErrorHandling:
    """Test database functions handle errors gracefully."""
    
    @patch('database.get_db_connection')
    def test_initialize_database_handles_connection_failure(self, mock_conn):
        """Test initialize_database handles connection failures gracefully."""
        mock_conn.side_effect = sqlite3.OperationalError("Unable to open database")
        
        result = initialize_database()
        
        # Should return None and not raise exception
        assert result is None, "Should return None when database initialization fails"
    
    @patch('database.get_db_connection')
    def test_create_professor_handles_database_unavailable(self, mock_conn):
        """Test create_professor handles database unavailability."""
        mock_conn.side_effect = sqlite3.OperationalError("Database is locked")
        
        result = create_professor("testuser", "password123")
        
        # Should return False (handled by decorator) and not raise exception
        assert result is False, "Should return False when database is unavailable"
    
    @patch('database.get_db_connection')
    def test_get_professor_by_username_handles_connection_failure(self, mock_conn):
        """Test get_professor_by_username handles connection failures."""
        mock_conn.side_effect = sqlite3.OperationalError("Connection failed")
        
        result = get_professor_by_username("testuser")
        
        assert result is None, "Should return None when database connection fails"
    
    @patch('database.get_db_connection')
    def test_save_advising_session_handles_database_error(self, mock_conn):
        """Test save_advising_session handles database errors gracefully."""
        mock_conn.side_effect = sqlite3.OperationalError("Disk I/O error")
        
        result = save_advising_session(
            professor_id=1,
            student_name="John Doe",
            semester="Spring",
            year=2024,
            email_content="Email",
            recommended_schedule="Schedule"
        )
        
        # Should return False (handled by decorator) and not raise exception
        assert result is False, "Should return False when database save fails"
    
    @patch('database.get_db_connection')
    def test_get_professor_history_handles_database_unavailable(self, mock_conn):
        """Test get_professor_history returns empty list when database unavailable."""
        mock_conn.side_effect = sqlite3.OperationalError("Database unavailable")
        
        result = get_professor_history(1)
        
        # Decorator should return empty list for history functions
        assert result == [], "Should return empty list when database is unavailable"
    
    @patch('database.get_db_connection')
    def test_load_session_handles_connection_failure(self, mock_conn):
        """Test load_session handles connection failures."""
        mock_conn.side_effect = sqlite3.OperationalError("Connection timeout")
        
        result = load_session(1, 1)
        
        assert result is None, "Should return None when database connection fails"


@pytest.mark.database
@pytest.mark.unit
class TestApplicationContinuesWithoutDatabase:
    """Test that application can continue functioning without database."""
    
    @patch('database.get_db_connection')
    def test_app_continues_when_database_init_fails(self, mock_conn):
        """Test application can start even if database initialization fails."""
        mock_conn.side_effect = sqlite3.OperationalError("Cannot create database")
        
        # Should not raise exception
        result = initialize_database()
        
        assert result is None, "App should continue even if database init fails"
    
    @patch('database.get_professor_history')
    def test_history_dropdown_handles_database_unavailable(self, mock_get_history):
        """Test history dropdown handles database unavailability."""
        from history import get_history_dropdown_options
        
        mock_get_history.side_effect = sqlite3.OperationalError("Database unavailable")
        
        # Should return empty list, not raise exception
        result = get_history_dropdown_options(1)
        
        assert result == [], "Should return empty list when database unavailable"
    
    @patch('database.save_advising_session')
    def test_advice_generation_continues_when_save_fails(self, mock_save):
        """Test advice generation continues even if database save fails."""
        mock_save.side_effect = sqlite3.OperationalError("Write failed")
        
        # Should return False (handled by decorator), not raise exception
        result = save_advising_session(
            professor_id=1,
            student_name="Test Student",
            semester="Spring",
            year=2024,
            email_content="Email content",
            recommended_schedule="Schedule"
        )
        
        assert result is False, "Should return False and allow app to continue"


@pytest.mark.database
@pytest.mark.unit
class TestErrorLogging:
    """Test that errors are properly logged."""
    
    @patch('database.get_db_connection')
    def test_connection_failure_is_logged(self, mock_conn, caplog):
        """Test connection failures are logged with details."""
        mock_conn.side_effect = sqlite3.OperationalError("Connection refused")
        
        with caplog.at_level("ERROR"):
            initialize_database()
        
        assert "Database operation failed" in caplog.text
        assert "initialize_database" in caplog.text
    
    @patch('database.get_db_connection')
    def test_integrity_error_is_logged(self, mock_conn, caplog):
        """Test integrity errors are logged."""
        mock_context = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        mock_context.__enter__.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_context
        
        with caplog.at_level("ERROR"):
            create_professor("testuser", "password123")
        
        # Check that error was logged
        assert len(caplog.records) > 0, "Should log integrity errors"
    
    @patch('database.get_db_connection')
    def test_write_failure_is_logged(self, mock_conn, caplog):
        """Test write failures are logged."""
        mock_conn.side_effect = sqlite3.OperationalError("Disk full")
        
        with caplog.at_level("ERROR"):
            save_advising_session(
                professor_id=1,
                student_name="Test",
                semester="Spring",
                year=2024,
                email_content="Email",
                recommended_schedule="Schedule"
            )
        
        assert "Database operation failed" in caplog.text
        assert "save_advising_session" in caplog.text


@pytest.mark.database
@pytest.mark.integration
class TestGracefulDegradation:
    """Test graceful degradation when database is unavailable."""
    
    @patch('database.get_db_connection')
    def test_authentication_fails_gracefully_without_database(self, mock_conn):
        """Test authentication fails gracefully when database unavailable."""
        mock_conn.side_effect = sqlite3.OperationalError("Database unavailable")
        
        result = get_professor_by_username("testuser")
        
        # Should return None, allowing auth module to handle as invalid credentials
        assert result is None, "Should return None when database unavailable"
    
    @patch('database.get_professor_history')
    def test_history_features_disabled_without_database(self, mock_get_history):
        """Test history features are disabled when database unavailable."""
        from history import get_history_dropdown_options
        
        mock_get_history.return_value = []
        
        result = get_history_dropdown_options(1)
        
        # Should return list with "No history" message when database returns empty list
        assert result == [("No advising history yet", None)], "Should return 'No history' message when database returns empty list"
    
    @patch('database.save_advising_session')
    def test_advice_displayed_even_when_save_fails(self, mock_save):
        """Test advice is displayed even when database save fails."""
        mock_save.return_value = False  # Simulates decorator returning False on error
        
        result = save_advising_session(
            professor_id=1,
            student_name="Test",
            semester="Spring",
            year=2024,
            email_content="Generated email",
            recommended_schedule="Generated schedule"
        )
        
        # Should return False (error handled), allowing UI to show warning but display advice
        assert result is False, "Should return False and allow advice to be displayed"
