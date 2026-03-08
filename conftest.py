"""
Pytest configuration and shared fixtures for AdviseMe tests.

This module provides:
- Hypothesis profile configuration for property-based testing
- Shared test fixtures for database, authentication, and session management
- Custom test strategies for domain objects
"""

import pytest
import os
import tempfile
import sqlite3
from hypothesis import settings, Verbosity

# Configure Hypothesis profiles
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.normal)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)
settings.register_profile("thorough", max_examples=1000, verbosity=Verbosity.normal)

# Load profile from environment variable or use default
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)


@pytest.fixture
def temp_db():
    """
    Create a temporary database for testing.
    
    Yields:
        str: Path to temporary database file
    """
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Store original DB_PATH
    import database
    original_db_path = database.DB_PATH
    
    # Replace with temp path
    database.DB_PATH = db_path
    
    # Initialize database
    database.initialize_database()
    
    yield db_path
    
    # Cleanup
    database.DB_PATH = original_db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_connection(temp_db):
    """
    Provide a database connection for testing.
    
    Args:
        temp_db: Temporary database fixture
        
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_professor(temp_db):
    """
    Create a sample professor account for testing.
    
    Args:
        temp_db: Temporary database fixture
        
    Returns:
        dict: Professor data (username, password, professor_id)
    """
    from database import create_professor, get_professor_by_username
    
    username = "test_professor"
    password = "testpass123"
    
    create_professor(username, password)
    professor = get_professor_by_username(username)
    
    return {
        'username': username,
        'password': password,
        'professor_id': professor['professor_id'],
        'password_hash': professor['password_hash']
    }


@pytest.fixture
def sample_session_data():
    """
    Provide sample advising session data for testing.
    
    Returns:
        dict: Sample session data
    """
    return {
        'student_name': 'John Doe',
        'semester': 'Spring',
        'year': 2026,
        'email_content': 'Sample email content for academic advising.',
        'recommended_schedule': '| Course | Credits |\n|--------|--------|\n| CS 101 | 3 |',
        'alternative1_schedule': '| Course | Credits |\n|--------|--------|\n| CS 102 | 3 |',
        'alternative2_schedule': '| Course | Credits |\n|--------|--------|\n| CS 103 | 3 |'
    }


@pytest.fixture
def mock_streamlit_session():
    """
    Mock Streamlit session_state for testing.
    
    Returns:
        dict: Mock session state dictionary
    """
    return {}


# Custom Hypothesis strategies for domain objects
from hypothesis import strategies as st

# Username strategy: alphanumeric, hyphens, underscores, 3-50 chars
usernames = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    ),
    min_size=3,
    max_size=50
).filter(lambda x: len(x) > 0 and x[0].isalnum())  # Must start with alphanumeric

# Password strategy: min 8 chars, max 100 chars
passwords = st.text(min_size=8, max_size=100)

# Semester strategy
semesters = st.sampled_from(['Spring', 'Summer', 'Fall'])

# Year strategy: 2024-2050
years = st.integers(min_value=2024, max_value=2050)

# Student name strategy
student_names = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')),
    min_size=1,
    max_size=100
).filter(lambda x: len(x.strip()) > 0)

# Session data strategy
session_data_strategy = st.fixed_dictionaries({
    'student_name': student_names,
    'semester': semesters,
    'year': years,
    'email_content': st.text(min_size=10, max_size=1000),
    'recommended_schedule': st.text(min_size=10, max_size=1000),
    'alternative1_schedule': st.text(max_size=1000),
    'alternative2_schedule': st.text(max_size=1000)
})
