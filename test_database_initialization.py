"""
Unit tests for database initialization and schema creation.

Tests for Task 2.1: Create database initialization and schema creation
Validates Requirements: 6.1, 6.2, 6.3, 6.4, 2.4
"""

import pytest
import sqlite3
import os
import tempfile
from database import initialize_database, get_db_connection
import database


@pytest.mark.database
@pytest.mark.unit
class TestDatabaseInitialization:
    """Test suite for database initialization functionality."""
    
    def test_initialize_database_creates_file(self):
        """Test that initialize_database creates the database file."""
        # Create temporary database path
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.remove(db_path)  # Remove so we can test creation
        
        # Store original and set temp path
        original_db_path = database.DB_PATH
        database.DB_PATH = db_path
        
        try:
            # Initialize database
            initialize_database()
            
            # Verify file exists
            assert os.path.exists(db_path), "Database file should be created"
            
        finally:
            # Cleanup
            database.DB_PATH = original_db_path
            if os.path.exists(db_path):
                os.remove(db_path)
    
    def test_initialize_database_sets_permissions(self):
        """Test that database file permissions are set to 0600 (owner read/write only)."""
        # Create temporary database path
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.remove(db_path)
        
        # Store original and set temp path
        original_db_path = database.DB_PATH
        database.DB_PATH = db_path
        
        try:
            # Initialize database
            initialize_database()
            
            # Check file permissions
            file_stat = os.stat(db_path)
            file_mode = file_stat.st_mode & 0o777
            
            # On Windows, chmod has limited effect, so we check if chmod was called
            # On Unix-like systems, should be 0600 (owner read/write only)
            # On Windows, permissions may be 0666 due to OS limitations
            if os.name == 'posix':
                assert file_mode == 0o600, f"Expected permissions 0600, got {oct(file_mode)}"
            else:
                # On Windows, just verify the file exists and is accessible
                assert os.path.exists(db_path), "Database file should exist"
                assert os.access(db_path, os.R_OK | os.W_OK), "Database should be readable and writable"
            
        finally:
            # Cleanup
            database.DB_PATH = original_db_path
            if os.path.exists(db_path):
                os.remove(db_path)
    
    def test_professors_table_exists(self, temp_db):
        """Test that professors table is created with correct schema."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='professors'
            """)
            result = cursor.fetchone()
            assert result is not None, "professors table should exist"
    
    def test_professors_table_columns(self, temp_db):
        """Test that professors table has all required columns."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("PRAGMA table_info(professors)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # Verify required columns exist with correct types
            assert 'professor_id' in columns, "professor_id column should exist"
            assert 'username' in columns, "username column should exist"
            assert 'password_hash' in columns, "password_hash column should exist"
            assert 'created_at' in columns, "created_at column should exist"
            
            assert columns['professor_id'] == 'INTEGER', "professor_id should be INTEGER"
            assert columns['username'] == 'TEXT', "username should be TEXT"
            assert columns['password_hash'] == 'TEXT', "password_hash should be TEXT"
            assert columns['created_at'] == 'TIMESTAMP', "created_at should be TIMESTAMP"
    
    def test_professors_username_unique_constraint(self, temp_db):
        """Test that username has UNIQUE constraint."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert first professor
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("testuser", "hash123")
            )
            conn.commit()
            
            # Try to insert duplicate username - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                    ("testuser", "hash456")
                )
    
    def test_professors_username_format_constraint(self, temp_db):
        """Test that username format constraint allows only alphanumeric, hyphens, underscores."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Valid usernames should work
            valid_usernames = ["user123", "test-user", "test_user", "User-Name_123"]
            for username in valid_usernames:
                cursor.execute(
                    "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                    (username, "hash123")
                )
            conn.commit()
            
            # Invalid usernames should fail
            invalid_usernames = ["user@test", "user.name", "user name", "user!123"]
            for username in invalid_usernames:
                with pytest.raises(sqlite3.IntegrityError):
                    cursor.execute(
                        "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                        (username, "hash123")
                    )
    
    def test_professors_index_exists(self, temp_db):
        """Test that index on username exists for faster lookups."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check index exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_professors_username'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_professors_username index should exist"
    
    def test_advising_sessions_table_exists(self, temp_db):
        """Test that advising_sessions table is created."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='advising_sessions'
            """)
            result = cursor.fetchone()
            assert result is not None, "advising_sessions table should exist"
    
    def test_advising_sessions_table_columns(self, temp_db):
        """Test that advising_sessions table has all required columns."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("PRAGMA table_info(advising_sessions)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            # Verify required columns
            required_columns = {
                'session_id': 'INTEGER',
                'professor_id': 'INTEGER',
                'student_name': 'TEXT',
                'semester': 'TEXT',
                'year': 'INTEGER',
                'timestamp': 'TIMESTAMP',
                'email_content': 'TEXT',
                'recommended_schedule': 'TEXT',
                'alternative1_schedule': 'TEXT',
                'alternative2_schedule': 'TEXT'
            }
            
            for col_name, col_type in required_columns.items():
                assert col_name in columns, f"{col_name} column should exist"
                assert columns[col_name] == col_type, f"{col_name} should be {col_type}"
    
    def test_advising_sessions_foreign_key_constraint(self, temp_db):
        """Test that foreign key constraint exists between advising_sessions and professors."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign key enforcement
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Try to insert session with non-existent professor_id - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO advising_sessions 
                    (professor_id, student_name, semester, year, email_content, recommended_schedule)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (9999, "John Doe", "Spring", 2026, "Email content", "Schedule"))
    
    def test_advising_sessions_semester_constraint(self, temp_db):
        """Test that semester constraint only allows Spring, Summer, Fall."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create a professor first
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("testprof", "hash123")
            )
            professor_id = cursor.lastrowid
            
            # Valid semesters should work
            valid_semesters = ["Spring", "Summer", "Fall"]
            for semester in valid_semesters:
                cursor.execute("""
                    INSERT INTO advising_sessions 
                    (professor_id, student_name, semester, year, email_content, recommended_schedule)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (professor_id, "John Doe", semester, 2026, "Email", "Schedule"))
            conn.commit()
            
            # Invalid semester should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO advising_sessions 
                    (professor_id, student_name, semester, year, email_content, recommended_schedule)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (professor_id, "Jane Doe", "Winter", 2026, "Email", "Schedule"))
    
    def test_advising_sessions_year_constraint(self, temp_db):
        """Test that year constraint only allows 2024-2050."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create a professor first
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("testprof", "hash123")
            )
            professor_id = cursor.lastrowid
            
            # Valid years should work
            valid_years = [2024, 2030, 2050]
            for year in valid_years:
                cursor.execute("""
                    INSERT INTO advising_sessions 
                    (professor_id, student_name, semester, year, email_content, recommended_schedule)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (professor_id, "John Doe", "Spring", year, "Email", "Schedule"))
            conn.commit()
            
            # Invalid years should fail
            invalid_years = [2023, 2051, 2000, 2100]
            for year in invalid_years:
                with pytest.raises(sqlite3.IntegrityError):
                    cursor.execute("""
                        INSERT INTO advising_sessions 
                        (professor_id, student_name, semester, year, email_content, recommended_schedule)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (professor_id, "Jane Doe", "Spring", year, "Email", "Schedule"))
    
    def test_advising_sessions_indexes_exist(self, temp_db):
        """Test that required indexes exist on advising_sessions table."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='advising_sessions'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert 'idx_sessions_professor' in indexes, "idx_sessions_professor index should exist"
            assert 'idx_sessions_timestamp' in indexes, "idx_sessions_timestamp index should exist"
    
    def test_connection_context_manager_commits_on_success(self, temp_db):
        """Test that connection context manager commits changes on success."""
        # Insert data using context manager
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("contexttest", "hash123")
            )
        
        # Verify data was committed
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM professors WHERE username = ?", ("contexttest",))
            result = cursor.fetchone()
            assert result is not None, "Data should be committed"
            assert result[0] == "contexttest"
    
    def test_connection_context_manager_rollback_on_error(self, temp_db):
        """Test that connection context manager rolls back on error."""
        # Insert initial data
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("rollbacktest", "hash123")
            )
        
        # Try to insert duplicate (should fail and rollback)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                    ("rollbacktest", "hash456")
                )
        except sqlite3.IntegrityError:
            pass  # Expected
        
        # Verify only one record exists
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM professors WHERE username = ?", ("rollbacktest",))
            count = cursor.fetchone()[0]
            assert count == 1, "Should only have one record after rollback"
    
    def test_connection_context_manager_closes_connection(self, temp_db):
        """Test that connection context manager closes connection after use."""
        conn_ref = None
        with get_db_connection() as conn:
            conn_ref = conn
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        
        # Connection should be closed after context
        # Attempting to use it should raise an error
        with pytest.raises(sqlite3.ProgrammingError):
            conn_ref.execute("SELECT 1")
    
    def test_initialize_database_idempotent(self, temp_db):
        """Test that calling initialize_database multiple times is safe."""
        # Initialize again (already initialized by temp_db fixture)
        initialize_database()
        
        # Verify tables still exist and are functional
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check professors table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professors'")
            assert cursor.fetchone() is not None
            
            # Check advising_sessions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='advising_sessions'")
            assert cursor.fetchone() is not None
            
            # Verify we can still insert data
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("idempotenttest", "hash123")
            )
            conn.commit()
    
    def test_utf8_encoding_support(self, temp_db):
        """Test that database supports UTF-8 encoding for text content."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create professor
            cursor.execute(
                "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
                ("testprof", "hash123")
            )
            professor_id = cursor.lastrowid
            
            # Insert session with UTF-8 characters
            utf8_content = "Hello 世界 🌍 Café résumé"
            cursor.execute("""
                INSERT INTO advising_sessions 
                (professor_id, student_name, semester, year, email_content, recommended_schedule)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (professor_id, "José García", "Spring", 2026, utf8_content, "Schedule"))
            conn.commit()
            
            # Retrieve and verify
            cursor.execute("SELECT student_name, email_content FROM advising_sessions WHERE professor_id = ?", (professor_id,))
            row = cursor.fetchone()
            assert row[0] == "José García", "UTF-8 student name should be preserved"
            assert row[1] == utf8_content, "UTF-8 email content should be preserved"
