"""
Unit tests for advising session storage functionality.

Tests for Task 2.8: Implement advising session storage
Validates Requirements: 3.1, 3.2, 3.3, 4.5, 9.4
"""

import pytest
from database import (
    save_advising_session,
    get_professor_history,
    load_session,
    get_db_connection
)


@pytest.mark.database
@pytest.mark.unit
class TestAdvisingSessionStorage:
    """Test suite for advising session storage functionality."""
    
    def test_save_advising_session_with_all_fields(self, temp_db, sample_professor, sample_session_data):
        """Test saving a complete advising session with all fields."""
        result = save_advising_session(
            professor_id=sample_professor['professor_id'],
            student_name=sample_session_data['student_name'],
            semester=sample_session_data['semester'],
            year=sample_session_data['year'],
            email_content=sample_session_data['email_content'],
            recommended_schedule=sample_session_data['recommended_schedule'],
            alternative1_schedule=sample_session_data['alternative1_schedule'],
            alternative2_schedule=sample_session_data['alternative2_schedule']
        )
        
        assert result is True, "Should successfully save advising session"
        
        # Verify session was saved
        history = get_professor_history(sample_professor['professor_id'])
        assert len(history) == 1, "Should have one session in history"
        assert history[0]['student_name'] == sample_session_data['student_name']
    
    def test_save_advising_session_with_optional_fields_empty(self, temp_db, sample_professor):
        """Test saving session with optional alternative schedules as empty strings."""
        result = save_advising_session(
            professor_id=sample_professor['professor_id'],
            student_name="Jane Smith",
            semester="Fall",
            year=2025,
            email_content="Email content",
            recommended_schedule="Schedule content",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        assert result is True, "Should save session with empty alternative schedules"
        
        # Verify session was saved
        history = get_professor_history(sample_professor['professor_id'])
        assert len(history) == 1
        assert history[0]['alternative1_schedule'] == ""
        assert history[0]['alternative2_schedule'] == ""
    
    def test_save_advising_session_returns_true_on_success(self, temp_db, sample_professor, sample_session_data):
        """Test that save_advising_session returns True on successful save."""
        result = save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        assert result is True, "Should return True on success"
    
    def test_save_advising_session_stores_timestamp(self, temp_db, sample_professor, sample_session_data):
        """Test that session timestamp is automatically stored."""
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        history = get_professor_history(sample_professor['professor_id'])
        assert history[0]['timestamp'] is not None, "Timestamp should be stored"
    
    def test_save_advising_session_associates_with_professor(self, temp_db, sample_professor, sample_session_data):
        """Test that session is correctly associated with professor_id."""
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        history = get_professor_history(sample_professor['professor_id'])
        assert history[0]['professor_id'] == sample_professor['professor_id'], \
            "Session should be associated with correct professor"
    
    def test_save_advising_session_with_utf8_content(self, temp_db, sample_professor):
        """Test saving session with UTF-8 characters in content."""
        utf8_content = "Hello 世界 🌍 Café résumé"
        
        result = save_advising_session(
            professor_id=sample_professor['professor_id'],
            student_name="José García",
            semester="Spring",
            year=2026,
            email_content=utf8_content,
            recommended_schedule="Schedule with émojis 📚",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        assert result is True
        
        # Verify UTF-8 content is preserved
        history = get_professor_history(sample_professor['professor_id'])
        assert history[0]['student_name'] == "José García"
        assert history[0]['email_content'] == utf8_content
        assert history[0]['recommended_schedule'] == "Schedule with émojis 📚"
    
    def test_save_advising_session_handles_invalid_professor_id(self, temp_db):
        """Test that saving with non-existent professor_id fails gracefully."""
        result = save_advising_session(
            professor_id=99999,  # Non-existent
            student_name="Test Student",
            semester="Spring",
            year=2026,
            email_content="Email",
            recommended_schedule="Schedule"
        )
        
        assert result is False, "Should return False for invalid professor_id"
    
    def test_get_professor_history_returns_empty_for_new_professor(self, temp_db, sample_professor):
        """Test that new professor with no sessions returns empty history."""
        history = get_professor_history(sample_professor['professor_id'])
        
        assert history == [], "New professor should have empty history"
    
    def test_get_professor_history_returns_all_sessions(self, temp_db, sample_professor):
        """Test that get_professor_history returns all sessions for a professor."""
        # Create multiple sessions
        for i in range(5):
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=f"Student {i}",
                semester="Spring",
                year=2026,
                email_content=f"Email {i}",
                recommended_schedule=f"Schedule {i}"
            )
        
        history = get_professor_history(sample_professor['professor_id'])
        
        assert len(history) == 5, "Should return all 5 sessions"
    
    def test_get_professor_history_ordered_by_timestamp_desc(self, temp_db, sample_professor):
        """Test that history is returned in reverse chronological order (most recent first)."""
        import time
        
        # Create sessions with different student names
        student_names = ["Alice", "Bob", "Charlie"]
        for name in student_names:
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=name,
                semester="Spring",
                year=2026,
                email_content="Email",
                recommended_schedule="Schedule"
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        history = get_professor_history(sample_professor['professor_id'])
        
        # Most recent should be first (Charlie was added last)
        assert history[0]['student_name'] == "Charlie", "Most recent session should be first"
        assert history[1]['student_name'] == "Bob"
        assert history[2]['student_name'] == "Alice"
    
    def test_get_professor_history_respects_limit(self, temp_db, sample_professor):
        """Test that get_professor_history respects the limit parameter."""
        # Create 10 sessions
        for i in range(10):
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=f"Student {i}",
                semester="Spring",
                year=2026,
                email_content="Email",
                recommended_schedule="Schedule"
            )
        
        # Request only 5
        history = get_professor_history(sample_professor['professor_id'], limit=5)
        
        assert len(history) == 5, "Should return only 5 sessions when limit=5"
    
    def test_get_professor_history_default_limit_50(self, temp_db, sample_professor):
        """Test that default limit is 50 sessions."""
        # Create 60 sessions
        for i in range(60):
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=f"Student {i}",
                semester="Spring",
                year=2026,
                email_content="Email",
                recommended_schedule="Schedule"
            )
        
        # Get history without specifying limit
        history = get_professor_history(sample_professor['professor_id'])
        
        assert len(history) == 50, "Should return maximum 50 sessions by default"
    
    def test_get_professor_history_returns_most_recent_when_limited(self, temp_db, sample_professor):
        """Test that when limited, the most recent sessions are returned."""
        import time
        
        # Create 60 sessions
        for i in range(60):
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=f"Student {i}",
                semester="Spring",
                year=2026,
                email_content="Email",
                recommended_schedule="Schedule"
            )
            if i % 10 == 0:  # Add delay every 10 records to ensure different timestamps
                time.sleep(0.01)
        
        history = get_professor_history(sample_professor['professor_id'], limit=50)
        
        # Should have the most recent 50 (Student 59 down to Student 10)
        assert history[0]['student_name'] == "Student 59", "Should have most recent session"
        assert history[49]['student_name'] == "Student 10", "Should have 50th most recent"
    
    def test_get_professor_history_isolates_professors(self, temp_db):
        """Test that professors can only see their own sessions."""
        from database import create_professor
        
        # Create two professors
        create_professor("prof1", "password123")
        create_professor("prof2", "password456")
        
        from database import get_professor_by_username
        prof1 = get_professor_by_username("prof1")
        prof2 = get_professor_by_username("prof2")
        
        # Create sessions for each professor
        save_advising_session(
            professor_id=prof1['professor_id'],
            student_name="Student A",
            semester="Spring",
            year=2026,
            email_content="Email A",
            recommended_schedule="Schedule A"
        )
        
        save_advising_session(
            professor_id=prof2['professor_id'],
            student_name="Student B",
            semester="Fall",
            year=2026,
            email_content="Email B",
            recommended_schedule="Schedule B"
        )
        
        # Each professor should only see their own session
        history1 = get_professor_history(prof1['professor_id'])
        history2 = get_professor_history(prof2['professor_id'])
        
        assert len(history1) == 1, "Prof1 should have 1 session"
        assert len(history2) == 1, "Prof2 should have 1 session"
        assert history1[0]['student_name'] == "Student A"
        assert history2[0]['student_name'] == "Student B"
    
    def test_get_professor_history_returns_all_fields(self, temp_db, sample_professor, sample_session_data):
        """Test that get_professor_history returns all session fields."""
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        history = get_professor_history(sample_professor['professor_id'])
        session = history[0]
        
        # Verify all fields are present
        assert 'session_id' in session
        assert 'professor_id' in session
        assert 'student_name' in session
        assert 'semester' in session
        assert 'year' in session
        assert 'timestamp' in session
        assert 'email_content' in session
        assert 'recommended_schedule' in session
        assert 'alternative1_schedule' in session
        assert 'alternative2_schedule' in session
    
    def test_load_session_with_valid_session_id(self, temp_db, sample_professor, sample_session_data):
        """Test loading a session with valid session_id and professor_id."""
        # Save a session
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        # Get the session_id
        history = get_professor_history(sample_professor['professor_id'])
        session_id = history[0]['session_id']
        
        # Load the session
        loaded_session = load_session(session_id, sample_professor['professor_id'])
        
        assert loaded_session is not None, "Should load session successfully"
        assert loaded_session['student_name'] == sample_session_data['student_name']
        assert loaded_session['email_content'] == sample_session_data['email_content']
    
    def test_load_session_returns_all_fields(self, temp_db, sample_professor, sample_session_data):
        """Test that load_session returns all session fields."""
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            **sample_session_data
        )
        
        history = get_professor_history(sample_professor['professor_id'])
        session_id = history[0]['session_id']
        
        loaded_session = load_session(session_id, sample_professor['professor_id'])
        
        # Verify all fields
        assert loaded_session['session_id'] == session_id
        assert loaded_session['professor_id'] == sample_professor['professor_id']
        assert loaded_session['student_name'] == sample_session_data['student_name']
        assert loaded_session['semester'] == sample_session_data['semester']
        assert loaded_session['year'] == sample_session_data['year']
        assert loaded_session['email_content'] == sample_session_data['email_content']
        assert loaded_session['recommended_schedule'] == sample_session_data['recommended_schedule']
        assert loaded_session['alternative1_schedule'] == sample_session_data['alternative1_schedule']
        assert loaded_session['alternative2_schedule'] == sample_session_data['alternative2_schedule']
    
    def test_load_session_verifies_professor_id(self, temp_db):
        """Test that load_session enforces professor_id verification for security."""
        from database import create_professor, get_professor_by_username
        
        # Create two professors
        create_professor("prof1", "password123")
        create_professor("prof2", "password456")
        
        prof1 = get_professor_by_username("prof1")
        prof2 = get_professor_by_username("prof2")
        
        # Prof1 creates a session
        save_advising_session(
            professor_id=prof1['professor_id'],
            student_name="Student A",
            semester="Spring",
            year=2026,
            email_content="Email A",
            recommended_schedule="Schedule A"
        )
        
        # Get the session_id
        history = get_professor_history(prof1['professor_id'])
        session_id = history[0]['session_id']
        
        # Prof2 tries to load Prof1's session - should fail
        loaded_session = load_session(session_id, prof2['professor_id'])
        
        assert loaded_session is None, "Should not allow loading another professor's session"
    
    def test_load_session_with_invalid_session_id(self, temp_db, sample_professor):
        """Test that load_session returns None for non-existent session_id."""
        loaded_session = load_session(99999, sample_professor['professor_id'])
        
        assert loaded_session is None, "Should return None for invalid session_id"
    
    def test_load_session_preserves_utf8_content(self, temp_db, sample_professor):
        """Test that load_session preserves UTF-8 content."""
        utf8_content = "Hello 世界 🌍 Café résumé"
        
        save_advising_session(
            professor_id=sample_professor['professor_id'],
            student_name="José García",
            semester="Spring",
            year=2026,
            email_content=utf8_content,
            recommended_schedule="Schedule with émojis 📚"
        )
        
        history = get_professor_history(sample_professor['professor_id'])
        session_id = history[0]['session_id']
        
        loaded_session = load_session(session_id, sample_professor['professor_id'])
        
        assert loaded_session['student_name'] == "José García"
        assert loaded_session['email_content'] == utf8_content
        assert loaded_session['recommended_schedule'] == "Schedule with émojis 📚"
    
    def test_save_advising_session_handles_database_write_failure(self, temp_db, sample_professor):
        """Test error handling when database write fails."""
        # This test verifies the function returns False on error
        # We can't easily simulate a write failure without mocking,
        # but we can test with invalid data that violates constraints
        
        result = save_advising_session(
            professor_id=sample_professor['professor_id'],
            student_name="Test Student",
            semester="InvalidSemester",  # Violates CHECK constraint
            year=2026,
            email_content="Email",
            recommended_schedule="Schedule"
        )
        
        assert result is False, "Should return False when constraint is violated"
    
    def test_get_professor_history_handles_invalid_professor_id(self, temp_db):
        """Test that get_professor_history handles invalid professor_id gracefully."""
        history = get_professor_history(99999)
        
        assert history == [], "Should return empty list for invalid professor_id"
    
    def test_multiple_sessions_same_student(self, temp_db, sample_professor):
        """Test that multiple sessions can be saved for the same student."""
        student_name = "John Doe"
        
        # Save multiple sessions for same student
        for i in range(3):
            save_advising_session(
                professor_id=sample_professor['professor_id'],
                student_name=student_name,
                semester="Spring",
                year=2026 + i,
                email_content=f"Email {i}",
                recommended_schedule=f"Schedule {i}"
            )
        
        history = get_professor_history(sample_professor['professor_id'])
        
        assert len(history) == 3, "Should have 3 sessions for same student"
        assert all(s['student_name'] == student_name for s in history)
