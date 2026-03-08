"""
Unit tests for history manager module.

Tests for Task 5: Implement history manager module (history.py)
Validates Requirements: 3.4, 4.3, 5.1, 5.2, 5.3, 5.4
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from history import (
    extract_student_name,
    format_history_entry,
    get_history_dropdown_options,
    reload_session,
    save_current_session
)


@pytest.mark.history
@pytest.mark.unit
class TestStudentNameExtraction:
    """Test suite for student name extraction functionality (Task 5.1)."""
    
    def test_extract_name_standard_format(self):
        """Test extraction from standard format: StudentName_AcademicProgress.pdf"""
        filename = "JohnDoe_AcademicProgress.pdf"
        result = extract_student_name(filename)
        assert result == "JohnDoe", "Should extract name before underscore"
    
    def test_extract_name_with_spaces(self):
        """Test extraction with spaces in name."""
        filename = "John Doe_AcademicProgress.pdf"
        result = extract_student_name(filename)
        assert result == "John Doe", "Should extract name with spaces"
    
    def test_extract_name_multiple_underscores(self):
        """Test extraction when multiple underscores present."""
        filename = "JohnDoe_AcademicProgress_2024.pdf"
        result = extract_student_name(filename)
        assert result == "JohnDoe", "Should extract first part before underscore"
    
    def test_extract_name_with_parenthesis(self):
        """Test extraction when filename has parenthesis."""
        filename = "John Doe (12345).pdf"
        result = extract_student_name(filename)
        assert result == "John Doe", "Should extract name before parenthesis"
    
    def test_extract_name_uppercase_extension(self):
        """Test extraction with uppercase .PDF extension."""
        filename = "JaneDoe_AcademicProgress.PDF"
        result = extract_student_name(filename)
        assert result == "JaneDoe", "Should handle uppercase PDF extension"
    
    def test_extract_name_no_underscore_or_parenthesis(self):
        """Test extraction when no underscore or parenthesis."""
        filename = "StudentName.pdf"
        result = extract_student_name(filename)
        assert result == "StudentName", "Should use whole filename without extension"
    
    def test_extract_name_empty_filename(self):
        """Test fallback for empty filename."""
        result = extract_student_name("")
        assert result == "Unnamed Student", "Should return 'Unnamed Student' for empty filename"
    
    def test_extract_name_none_filename(self):
        """Test fallback for None filename."""
        result = extract_student_name(None)
        assert result == "Unnamed Student", "Should return 'Unnamed Student' for None"
    
    def test_extract_name_too_short(self):
        """Test fallback when extracted name is too short."""
        filename = "A_AcademicProgress.pdf"
        result = extract_student_name(filename)
        assert result == "Unknown Student", "Should return 'Unknown Student' for single character"
    
    def test_extract_name_only_extension(self):
        """Test fallback when filename is only extension."""
        filename = ".pdf"
        result = extract_student_name(filename)
        assert result == "Unknown Student", "Should return 'Unknown Student' for extension only"
    
    def test_extract_name_with_special_characters(self):
        """Test extraction with special characters in name."""
        filename = "José-García_AcademicProgress.pdf"
        result = extract_student_name(filename)
        assert result == "José-García", "Should preserve special characters"
    
    def test_extract_name_with_numbers(self):
        """Test extraction with numbers in name."""
        filename = "Student123_AcademicProgress.pdf"
        result = extract_student_name(filename)
        assert result == "Student123", "Should preserve numbers in name"


@pytest.mark.history
@pytest.mark.unit
class TestHistoryEntryFormatting:
    """Test suite for history entry formatting functionality (Task 5.3)."""
    
    def test_format_entry_complete_data(self):
        """Test formatting with complete session data."""
        session = {
            'student_name': 'John Doe',
            'semester': 'Spring',
            'year': 2026,
            'timestamp': '2024-01-15 10:30:00'
        }
        result = format_history_entry(session)
        assert result == "John Doe - Spring 2026 (01/15/2024)", "Should format correctly"
    
    def test_format_entry_datetime_object(self):
        """Test formatting when timestamp is datetime object."""
        session = {
            'student_name': 'Jane Smith',
            'semester': 'Fall',
            'year': 2025,
            'timestamp': datetime(2024, 3, 20, 14, 45, 30)
        }
        result = format_history_entry(session)
        assert result == "Jane Smith - Fall 2025 (03/20/2024)", "Should handle datetime object"
    
    def test_format_entry_summer_semester(self):
        """Test formatting for Summer semester."""
        session = {
            'student_name': 'Bob Johnson',
            'semester': 'Summer',
            'year': 2024,
            'timestamp': '2024-06-10 09:00:00'
        }
        result = format_history_entry(session)
        assert result == "Bob Johnson - Summer 2024 (06/10/2024)", "Should format Summer semester correctly" 

    def test_format_entry_missing_timestamp(self):
        """Test formatting when timestamp is missing."""
        session = {
            'student_name': 'Alice Brown',
            'semester': 'Spring',
            'year': 2025,
            'timestamp': None
        }
        result = format_history_entry(session)
        assert result == "Alice Brown - Spring 2025 (Unknown Date)", "Should handle missing timestamp"
    
    def test_format_entry_missing_fields(self):
        """Test formatting when some fields are missing."""
        session = {
            'student_name': 'Test Student',
            'timestamp': '2024-05-15 12:00:00'
        }
        result = format_history_entry(session)
        assert result == "Test Student -   (05/15/2024)", "Should handle missing semester/year"
    
    def test_format_entry_unknown_student(self):
        """Test formatting when student name is missing."""
        session = {
            'semester': 'Fall',
            'year': 2024,
            'timestamp': '2024-09-01 08:00:00'
        }
        result = format_history_entry(session)
        assert result == "Unknown - Fall 2024 (09/01/2024)", "Should use 'Unknown' for missing name"
    
    def test_format_entry_date_formatting(self):
        """Test that date is formatted with leading zeros."""
        session = {
            'student_name': 'Test User',
            'semester': 'Spring',
            'year': 2024,
            'timestamp': '2024-01-05 10:30:00'
        }
        result = format_history_entry(session)
        assert "01/05/2024" in result, "Should format date with leading zeros"


@pytest.mark.history
@pytest.mark.unit
class TestSessionReload:
    """Test suite for session reload functionality (Task 5.3)."""
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_success(self, mock_st, mock_load_session):
        """Test successful session reload populates session_state."""
        # Setup mock session data
        mock_session = {
            'session_id': 1,
            'student_name': 'John Doe',
            'semester': 'Spring',
            'year': 2024,
            'email_content': 'Test email content',
            'recommended_schedule': 'Test recommended schedule',
            'alternative1_schedule': 'Test alt1 schedule',
            'alternative2_schedule': 'Test alt2 schedule',
            'timestamp': '2024-01-15 10:30:00'
        }
        mock_load_session.return_value = mock_session
        
        # Setup mock session_state
        mock_st.session_state = {}
        
        # Call reload_session
        result = reload_session(1, 100)
        
        # Verify load_session was called with correct parameters
        mock_load_session.assert_called_once_with(1, 100)
        
        # Verify session_state was populated
        assert mock_st.session_state['email_content'] == 'Test email content'
        assert mock_st.session_state['recommended_schedule'] == 'Test recommended schedule'
        assert mock_st.session_state['alternative1_schedule'] == 'Test alt1 schedule'
        assert mock_st.session_state['alternative2_schedule'] == 'Test alt2 schedule'
        assert mock_st.session_state['semester_info'] == 'Spring 2024'
        assert 'loaded_session_timestamp' in mock_st.session_state
        assert result is True
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_not_found(self, mock_st, mock_load_session):
        """Test reload when session not found."""
        mock_load_session.return_value = None
        mock_st.session_state = {}
        
        result = reload_session(999, 100)
        
        # Verify error was displayed
        mock_st.error.assert_called_once()
        assert result is False
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_unauthorized(self, mock_st, mock_load_session):
        """Test reload when professor is unauthorized."""
        mock_load_session.return_value = None
        mock_st.session_state = {}
        
        result = reload_session(1, 999)
        
        # Verify error was displayed
        mock_st.error.assert_called_once()
        error_message = mock_st.error.call_args[0][0]
        assert "unauthorized" in error_message.lower()
        assert result is False
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_with_datetime_object(self, mock_st, mock_load_session):
        """Test reload with datetime object timestamp."""
        mock_session = {
            'session_id': 1,
            'student_name': 'Jane Smith',
            'semester': 'Fall',
            'year': 2025,
            'email_content': 'Email content',
            'recommended_schedule': 'Schedule',
            'alternative1_schedule': '',
            'alternative2_schedule': '',
            'timestamp': datetime(2024, 3, 20, 14, 45, 30)
        }
        mock_load_session.return_value = mock_session
        mock_st.session_state = {}
        
        result = reload_session(1, 100)
        
        # Verify timestamp was formatted correctly
        assert mock_st.session_state['loaded_session_timestamp'] == '03/20/2024 02:45 PM'
        assert result is True
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_missing_optional_fields(self, mock_st, mock_load_session):
        """Test reload with missing optional fields."""
        mock_session = {
            'session_id': 1,
            'email_content': 'Email',
            'recommended_schedule': 'Schedule',
            'timestamp': '2024-01-15 10:30:00'
        }
        mock_load_session.return_value = mock_session
        mock_st.session_state = {}
        
        result = reload_session(1, 100)
        
        # Verify optional fields default to empty strings
        assert mock_st.session_state['alternative1_schedule'] == ''
        assert mock_st.session_state['alternative2_schedule'] == ''
        assert mock_st.session_state['semester_info'] == ' '
        assert result is True
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_notification_timestamp(self, mock_st, mock_load_session):
        """Test that reload creates notification timestamp in correct format."""
        mock_session = {
            'session_id': 1,
            'email_content': 'Email',
            'recommended_schedule': 'Schedule',
            'alternative1_schedule': '',
            'alternative2_schedule': '',
            'timestamp': '2024-06-10 09:15:30'
        }
        mock_load_session.return_value = mock_session
        mock_st.session_state = {}
        
        result = reload_session(1, 100)
        
        # Verify notification timestamp format
        timestamp = mock_st.session_state['loaded_session_timestamp']
        assert timestamp == '06/10/2024 09:15 AM'
        assert result is True
    
    @patch('database.load_session')
    @patch('history.st')
    def test_reload_session_exception_handling(self, mock_st, mock_load_session):
        """Test reload handles exceptions gracefully."""
        mock_load_session.side_effect = Exception("Database error")
        mock_st.session_state = {}
        
        result = reload_session(1, 100)
        
        # Decorator should catch the exception and return False (reload_session is a boolean function)
        # No error should be displayed by reload_session itself (decorator handles it)
        assert result is False, "Should return False when exception occurs"


@pytest.mark.history
@pytest.mark.unit
class TestHistoryDropdownOptions:
    """Test suite for history dropdown options functionality."""
    
    @patch('database.get_professor_history')
    def test_get_dropdown_options_with_sessions(self, mock_get_history):
        """Test dropdown options with existing sessions."""
        mock_sessions = [
            {
                'session_id': 1,
                'student_name': 'John Doe',
                'semester': 'Spring',
                'year': 2024,
                'timestamp': '2024-01-15 10:30:00'
            },
            {
                'session_id': 2,
                'student_name': 'Jane Smith',
                'semester': 'Fall',
                'year': 2023,
                'timestamp': '2023-09-20 14:00:00'
            }
        ]
        mock_get_history.return_value = mock_sessions
        
        options = get_history_dropdown_options(100)
        
        assert len(options) == 2
        assert options[0][0] == "John Doe - Spring 2024 (01/15/2024)"
        assert options[0][1] == 1
        assert options[1][0] == "Jane Smith - Fall 2023 (09/20/2023)"
        assert options[1][1] == 2
    
    @patch('database.get_professor_history')
    def test_get_dropdown_options_no_sessions(self, mock_get_history):
        """Test dropdown options when no sessions exist."""
        mock_get_history.return_value = []
        
        options = get_history_dropdown_options(100)
        
        assert len(options) == 1
        assert options[0][0] == "No advising history yet"
        assert options[0][1] is None
    
    @patch('database.get_professor_history')
    def test_get_dropdown_options_error(self, mock_get_history):
        """Test dropdown options when database error occurs."""
        mock_get_history.side_effect = Exception("Database error")
        
        options = get_history_dropdown_options(100)
        
        # Decorator should catch the exception and return empty list
        assert options == [], "Should return empty list when error occurs"


@pytest.mark.history
@pytest.mark.unit
class TestSaveCurrentSession:
    """Test suite for save current session functionality."""
    
    @patch('database.save_advising_session')
    @patch('history.st')
    def test_save_current_session_success(self, mock_st, mock_save):
        """Test successful session save."""
        mock_st.session_state = {
            'email_content': 'Test email',
            'recommended_schedule': 'Test schedule',
            'alternative1_schedule': 'Alt1',
            'alternative2_schedule': 'Alt2'
        }
        mock_save.return_value = True
        
        result = save_current_session(100, 'John Doe', 'Spring', 2024)
        
        mock_save.assert_called_once_with(
            professor_id=100,
            student_name='John Doe',
            semester='Spring',
            year=2024,
            email_content='Test email',
            recommended_schedule='Test schedule',
            alternative1_schedule='Alt1',
            alternative2_schedule='Alt2'
        )
        assert result is True
    
    @patch('database.save_advising_session')
    @patch('history.st')
    def test_save_current_session_missing_content(self, mock_st, mock_save):
        """Test save fails when required content is missing."""
        mock_st.session_state = {
            'email_content': '',
            'recommended_schedule': ''
        }
        
        result = save_current_session(100, 'John Doe', 'Spring', 2024)
        
        # Should not call save_advising_session
        mock_save.assert_not_called()
        assert result is False
    
    @patch('database.save_advising_session')
    @patch('history.st')
    def test_save_current_session_database_failure(self, mock_st, mock_save):
        """Test save handles database failure."""
        mock_st.session_state = {
            'email_content': 'Test email',
            'recommended_schedule': 'Test schedule',
            'alternative1_schedule': '',
            'alternative2_schedule': ''
        }
        mock_save.return_value = False
        
        result = save_current_session(100, 'John Doe', 'Spring', 2024)
        
        assert result is False
    
    @patch('database.save_advising_session')
    @patch('history.st')
    def test_save_current_session_exception(self, mock_st, mock_save):
        """Test save handles exceptions gracefully."""
        mock_st.session_state = {
            'email_content': 'Test email',
            'recommended_schedule': 'Test schedule'
        }
        mock_save.side_effect = Exception("Database error")
        
        result = save_current_session(100, 'John Doe', 'Spring', 2024)
        
        assert result is False
