"""
Database Manager for AdviseMe

This module handles all database operations including schema creation, professor account
management, and advising session storage using SQLite.

Validates: Requirements 2, 3, 6, 7, 9, 10
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Callable, Any
from datetime import datetime
from contextlib import contextmanager
from functools import wraps
import os
import re
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "adviseme.db"


def safe_database_operation(operation_func: Callable) -> Callable:
    """
    Decorator for graceful database error handling.
    
    This decorator wraps database operations to catch and handle errors gracefully,
    allowing the application to continue functioning even when the database is unavailable.
    
    Error handling:
    - sqlite3.OperationalError: Database connection/access failures
    - sqlite3.IntegrityError: Data integrity violations (unique constraints, foreign keys)
    - General exceptions: Unexpected errors
    
    Args:
        operation_func: The database operation function to wrap
        
    Returns:
        Wrapped function that handles errors gracefully
        
    Validates: Requirements 10.1, 10.2, 10.3
    """
    @wraps(operation_func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return operation_func(*args, **kwargs)
        except ValueError:
            # Let validation errors pass through - these should be handled by the caller
            raise
        except sqlite3.OperationalError as e:
            logger.error(f"Database operation failed in {operation_func.__name__}: {e}")
            # Return appropriate default based on function name
            func_name = operation_func.__name__
            if 'history' in func_name.lower() or func_name == 'get_history_dropdown_options':
                return []
            elif func_name in ['create_professor', 'save_advising_session', 'save_current_session', 'reload_session']:
                return False
            return None
        except sqlite3.IntegrityError as e:
            logger.error(f"Data integrity error in {operation_func.__name__}: {e}")
            # Return False for operations that return boolean success indicators
            func_name = operation_func.__name__
            if func_name in ['create_professor', 'save_advising_session', 'save_current_session', 'reload_session']:
                return False
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {operation_func.__name__}: {e}")
            # Return appropriate default based on function name
            func_name = operation_func.__name__
            if 'history' in func_name.lower() or func_name == 'get_history_dropdown_options':
                return []
            elif func_name in ['create_professor', 'save_advising_session', 'save_current_session', 'reload_session']:
                return False
            return None
    return wrapper


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@safe_database_operation
def initialize_database() -> None:
    """
    Create database file and tables if they don't exist.
    Sets file permissions to 0600 (owner read/write only).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create professors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professors (
                professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT username_format CHECK (
                    username NOT GLOB '*[^A-Za-z0-9_-]*'
                    AND LENGTH(username) > 0
                )
            )
        """)
        
        # Create index on username for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_professors_username 
            ON professors(username)
        """)
        
        # Create advising_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advising_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                semester TEXT NOT NULL,
                year INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_content TEXT NOT NULL,
                recommended_schedule TEXT NOT NULL,
                alternative1_schedule TEXT,
                alternative2_schedule TEXT,
                FOREIGN KEY (professor_id) REFERENCES professors(professor_id)
                    ON DELETE CASCADE,
                CONSTRAINT valid_semester CHECK (
                    semester IN ('Spring', 'Summer', 'Fall')
                ),
                CONSTRAINT valid_year CHECK (
                    year >= 2024 AND year <= 2050
                )
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_professor 
            ON advising_sessions(professor_id, timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_timestamp 
            ON advising_sessions(timestamp DESC)
        """)
        
        logger.info("Database initialized successfully")
    
    # Set file permissions to 0600 (owner read/write only)
    if os.path.exists(DB_PATH):
        os.chmod(DB_PATH, 0o600)
        logger.info(f"Database file permissions set to 0600")


@safe_database_operation
def create_professor(username: str, password: str) -> bool:
    """
    Create a new professor account with bcrypt hashed password.
    
    Validates username format (alphanumeric, hyphens, underscores) and password length
    (minimum 8 characters) before creating the account.
    
    Args:
        username: Unique username (alphanumeric, hyphens, underscores)
        password: Plain text password (minimum 8 characters)
        
    Returns:
        True if creation succeeds, False if validation fails or username exists
        
    Raises:
        ValueError: If username format is invalid or password is too short
    """
    # Validate username format (alphanumeric, hyphens, underscores only)
    if not re.match(r'^[A-Za-z0-9_-]+$', username):
        raise ValueError("Username must contain only alphanumeric characters, hyphens, and underscores")
    
    # Validate password length (minimum 8 characters)
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    # Hash password with bcrypt (automatically generates salt)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO professors (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        logger.info(f"Created professor account: {username}")
        return True


@safe_database_operation
def get_professor_by_username(username: str) -> Optional[Dict]:
    """
    Retrieve professor record by username.
    
    Args:
        username: Professor's username
        
    Returns:
        Dictionary with professor data or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT professor_id, username, password_hash, created_at FROM professors WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


@safe_database_operation
def save_advising_session(
    professor_id: int,
    student_name: str,
    semester: str,
    year: int,
    email_content: str,
    recommended_schedule: str,
    alternative1_schedule: str = "",
    alternative2_schedule: str = ""
) -> bool:
    """
    Save an advising session to the database.
    
    Args:
        professor_id: ID of the professor creating the session
        student_name: Name of the student being advised
        semester: Semester (Spring, Summer, Fall)
        year: Year (2024-2050)
        email_content: Generated email content
        recommended_schedule: Recommended schedule content
        alternative1_schedule: First alternative schedule (optional)
        alternative2_schedule: Second alternative schedule (optional)
        
    Returns:
        True if save succeeds, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO advising_sessions 
            (professor_id, student_name, semester, year, email_content, 
             recommended_schedule, alternative1_schedule, alternative2_schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            professor_id, student_name, semester, year, email_content,
            recommended_schedule, alternative1_schedule, alternative2_schedule
        ))
        logger.info(f"Saved advising session for student: {student_name}")
        return True


@safe_database_operation
def get_professor_history(professor_id: int, limit: int = 50) -> List[Dict]:
    """
    Retrieve advising history for a professor.
    
    Args:
        professor_id: ID of the professor
        limit: Maximum number of sessions to return (default 50)
        
    Returns:
        List of session records ordered by timestamp DESC
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, professor_id, student_name, semester, year, 
                   timestamp, email_content, recommended_schedule, 
                   alternative1_schedule, alternative2_schedule
            FROM advising_sessions
            WHERE professor_id = ?
            ORDER BY timestamp DESC, session_id DESC
            LIMIT ?
        """, (professor_id, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@safe_database_operation
def load_session(session_id: int, professor_id: int) -> Optional[Dict]:
    """
    Load a specific advising session.
    
    Args:
        session_id: Database ID of the session
        professor_id: Must match session owner for security
        
    Returns:
        Session data dict or None if not found/unauthorized
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, professor_id, student_name, semester, year, 
                   timestamp, email_content, recommended_schedule, 
                   alternative1_schedule, alternative2_schedule
            FROM advising_sessions
            WHERE session_id = ? AND professor_id = ?
        """, (session_id, professor_id))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
