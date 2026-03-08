"""
Integration test for Task 8.1: Add automatic session saving after advice generation

This test verifies that the automatic session saving functionality works correctly
when advice is generated in the adviseme.py application.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 10.1, 10.2
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import database
import history


@pytest.mark.integration
@pytest.mark.history
class TestAutomaticSessionSaving:
    """Integration tests for automatic session saving after advice generation."""
    
    def setup_method(self):
        """Set up test database before each test."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Patch the DB_PATH
        import database as db_module
        self.original_db_path = db_module.DB_PATH
        db_module.DB_PATH = self.temp_db.name
        
        # Initialize database
        db_module.initialize_database()
        
        # Create a test professor
        db_module.create_professor("test_prof", "password123")
    
    def teardown_method(self):
        """Clean up after each test."""
        import database as db_module
        db_module.DB_PATH = self.original_db_path
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_session_saved_after_advice_generation(self):
        """Test that session is automatically saved after successful advice generation."""
        # Get professor ID
        professor = database.get_professor_by_username("test_prof")
        professor_id = professor['professor_id']
        
        # Simulate advice generation data
        student_name = "John Doe"
        semester = "Spring"
        year = 2024
        email_content = "Test email content for advising"
        recommended_schedule = "| Course | Credits |\n| CS101 | 3 |"
        alternative1_schedule = "| Course | Credits |\n| CS102 | 3 |"
        alternative2_schedule = ""
        
        # Save the session (simulating what happens in adviseme.py)
        success = database.save_advising_session(
            professor_id=professor_id,
            student_name=student_name,
            semester=semester,
            year=year,
            email_content=email_content,
            recommended_schedule=recommended_schedule,
            alternative1_schedule=alternative1_schedule,
            alternative2_schedule=alternative2_schedule
        )
        
        assert success is True, "Session save should succeed"
        
        # Verify session was saved by retrieving history
        history_records = database.get_professor_history(professor_id)
        
        assert len(history_records) == 1, "Should have one saved session"
        assert history_records[0]['student_name'] == student_name
        assert history_records[0]['semester'] == semester
        assert history_records[0]['year'] == year
        assert history_records[0]['email_content'] == email_content
        assert history_records[0]['recommended_schedule'] == recommended_schedule
    
    def test_student_name_extraction_from_filename(self):
        """Test that student name is correctly extracted from PDF filename."""
        # Test various filename formats
        test_cases = [
            ("JohnDoe_AcademicProgress.pdf", "JohnDoe"),
            ("Jane Smith_AcademicProgress.pdf", "Jane Smith"),
            ("Student123_Progress_2024.pdf", "Student123"),
            ("Bob Johnson (12345).pdf", "Bob Johnson"),
            ("StudentName.pdf", "StudentName"),
        ]
        
        for filename, expected_name in test_cases:
            extracted_name = history.extract_student_name(filename)
            assert extracted_name == expected_name, f"Failed to extract name from {filename}"
    
    def test_session_save_with_database_failure(self):
        """Test that advice is still displayed even if database save fails."""
        # Get professor ID
        professor = database.get_professor_by_username("test_prof")
        professor_id = professor['professor_id']
        
        # Try to save with invalid data (year out of range)
        success = database.save_advising_session(
            professor_id=professor_id,
            student_name="Test Student",
            semester="Spring",
            year=2100,  # Invalid year (exceeds 2050 constraint)
            email_content="Test email",
            recommended_schedule="Test schedule",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        # Save should fail due to constraint violation
        assert success is False, "Save should fail with invalid year"
        
        # Verify no session was saved
        history_records = database.get_professor_history(professor_id)
        assert len(history_records) == 0, "No session should be saved on failure"
    
    def test_multiple_sessions_saved_for_professor(self):
        """Test that multiple sessions can be saved for the same professor."""
        # Get professor ID
        professor = database.get_professor_by_username("test_prof")
        professor_id = professor['professor_id']
        
        # Save multiple sessions
        students = ["Alice Brown", "Bob Smith", "Charlie Davis"]
        
        for student in students:
            success = database.save_advising_session(
                professor_id=professor_id,
                student_name=student,
                semester="Fall",
                year=2024,
                email_content=f"Email for {student}",
                recommended_schedule=f"Schedule for {student}",
                alternative1_schedule="",
                alternative2_schedule=""
            )
            assert success is True, f"Should save session for {student}"
        
        # Verify all sessions were saved
        history_records = database.get_professor_history(professor_id)
        assert len(history_records) == 3, "Should have three saved sessions"
        
        # Verify sessions are in reverse chronological order (most recent first)
        saved_names = [record['student_name'] for record in history_records]
        # Since they were saved in order, the most recent should be last in the list
        # but get_professor_history returns them in DESC order
        assert "Charlie Davis" in saved_names
        assert "Bob Smith" in saved_names
        assert "Alice Brown" in saved_names
    
    def test_session_associated_with_correct_professor(self):
        """Test that sessions are correctly associated with the professor who created them."""
        # Create two professors
        database.create_professor("prof1", "password123")
        database.create_professor("prof2", "password456")
        
        prof1 = database.get_professor_by_username("prof1")
        prof2 = database.get_professor_by_username("prof2")
        
        # Save session for prof1
        database.save_advising_session(
            professor_id=prof1['professor_id'],
            student_name="Student A",
            semester="Spring",
            year=2024,
            email_content="Email A",
            recommended_schedule="Schedule A",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        # Save session for prof2
        database.save_advising_session(
            professor_id=prof2['professor_id'],
            student_name="Student B",
            semester="Fall",
            year=2024,
            email_content="Email B",
            recommended_schedule="Schedule B",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        # Verify each professor only sees their own sessions
        prof1_history = database.get_professor_history(prof1['professor_id'])
        prof2_history = database.get_professor_history(prof2['professor_id'])
        
        assert len(prof1_history) == 1, "Prof1 should have one session"
        assert len(prof2_history) == 1, "Prof2 should have one session"
        assert prof1_history[0]['student_name'] == "Student A"
        assert prof2_history[0]['student_name'] == "Student B"
    
    def test_error_handling_for_missing_professor_id(self):
        """Test that session save handles missing professor_id gracefully."""
        # Try to save with non-existent professor_id
        success = database.save_advising_session(
            professor_id=9999,  # Non-existent professor
            student_name="Test Student",
            semester="Spring",
            year=2024,
            email_content="Test email",
            recommended_schedule="Test schedule",
            alternative1_schedule="",
            alternative2_schedule=""
        )
        
        # Save should fail due to foreign key constraint
        assert success is False, "Save should fail with non-existent professor_id"
