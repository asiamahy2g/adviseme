"""
Basic infrastructure tests for Task 1.

These tests verify that the project infrastructure is set up correctly:
- Dependencies are installed
- Modules can be imported
- Database can be initialized
- Pytest configuration works
"""

import pytest
import os


def test_bcrypt_installed():
    """Verify bcrypt is installed and can be imported."""
    import bcrypt
    assert bcrypt is not None


def test_hypothesis_installed():
    """Verify hypothesis is installed and can be imported."""
    import hypothesis
    assert hypothesis is not None


def test_auth_module_imports():
    """Verify auth module can be imported."""
    import auth
    assert hasattr(auth, 'hash_password')
    assert hasattr(auth, 'verify_password')
    assert hasattr(auth, 'authenticate_user')
    assert hasattr(auth, 'create_session')
    assert hasattr(auth, 'is_authenticated')
    assert hasattr(auth, 'logout')


def test_database_module_imports():
    """Verify database module can be imported."""
    import database
    assert hasattr(database, 'initialize_database')
    assert hasattr(database, 'create_professor')
    assert hasattr(database, 'save_advising_session')
    assert hasattr(database, 'get_professor_history')
    assert hasattr(database, 'load_session')


def test_history_module_imports():
    """Verify history module can be imported."""
    import history
    assert hasattr(history, 'extract_student_name')
    assert hasattr(history, 'format_history_entry')
    assert hasattr(history, 'reload_session')
    assert hasattr(history, 'save_current_session')


def test_database_initialization(temp_db):
    """Verify database can be initialized with correct schema."""
    import sqlite3
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Check professors table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professors'")
    assert cursor.fetchone() is not None
    
    # Check advising_sessions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='advising_sessions'")
    assert cursor.fetchone() is not None
    
    # Check indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_professors_username'")
    assert cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_sessions_professor'")
    assert cursor.fetchone() is not None
    
    conn.close()


def test_pytest_markers_configured():
    """Verify pytest markers are configured correctly."""
    # This test will fail if markers are not properly configured
    # and --strict-markers is enabled
    pass


@pytest.mark.property_test
def test_property_test_marker():
    """Verify property_test marker works."""
    pass


@pytest.mark.unit
def test_unit_marker():
    """Verify unit marker works."""
    pass


@pytest.mark.auth
def test_auth_marker():
    """Verify auth marker works."""
    pass


@pytest.mark.database
def test_database_marker():
    """Verify database marker works."""
    pass


@pytest.mark.history
def test_history_marker():
    """Verify history marker works."""
    pass
