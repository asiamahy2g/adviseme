"""
Authentication Module for AdviseMe

This module handles professor authentication, session management, and security features
including password hashing with bcrypt and account lockout after failed attempts.

Validates: Requirements 1, 2, 8
"""

import bcrypt
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with work factor 12.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hash string
    """
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def authenticate_user(username: str, password: str) -> Optional[int]:
    """
    Authenticate a professor and return their professor_id.
    
    Implements:
    - Database lookup for username
    - Bcrypt password verification
    - Failed attempt tracking
    - 5-minute lockout after 3 failed attempts
    - Authentication failure logging
    
    Args:
        username: Professor's username
        password: Plain text password to verify
        
    Returns:
        professor_id if authentication succeeds, None otherwise
        
    Validates: Requirements 1.2, 1.3, 2.5, 10.5
    """
    from database import get_professor_by_username
    
    # Check if account is locked out
    if check_lockout(username):
        lockout_until = st.session_state['lockout_until'][username]
        remaining = (lockout_until - datetime.now()).total_seconds() / 60
        logger.warning(f"Login attempt for locked account: {username}")
        return None
    
    # Get professor from database
    professor = get_professor_by_username(username)
    
    if professor is None:
        # Username doesn't exist
        logger.warning(f"Login attempt with non-existent username: {username}")
        record_failed_attempt(username)
        return None
    
    # Verify password
    if verify_password(password, professor['password_hash']):
        # Authentication successful
        logger.info(f"Successful authentication for user: {username}")
        reset_failed_attempts(username)
        return professor['professor_id']
    else:
        # Invalid password
        logger.warning(f"Failed authentication attempt for user: {username} (invalid password)")
        record_failed_attempt(username)
        return None


def create_session(professor_id: int, username: str) -> None:
    """
    Create an authenticated session in Streamlit session_state.
    
    Args:
        professor_id: Database ID of the professor
        username: Professor's username for display
    """
    st.session_state['authenticated'] = True
    st.session_state['professor_id'] = professor_id
    st.session_state['username'] = username
    st.session_state['login_timestamp'] = datetime.now()


def is_authenticated() -> bool:
    """
    Check if current session is authenticated and not expired.
    
    This function is called on every page interaction to enforce session timeout.
    If the session has exceeded 8 hours, it automatically logs out the user
    and sets a flag to display a timeout message.
    
    Returns:
        True if authenticated and session valid, False otherwise
        
    Validates: Requirements 8.2, 8.3
    """
    if not st.session_state.get('authenticated', False):
        return False
    
    # Check session timeout (8 hours) on every page interaction
    if check_session_timeout():
        # Set timeout flag before logout to display message
        st.session_state['session_timeout'] = True
        logout()
        return False
    
    return True


def logout() -> None:
    """Clear session state and return to login page."""
    # Clear all authentication-related session state
    for key in ['authenticated', 'professor_id', 'username', 'login_timestamp']:
        if key in st.session_state:
            del st.session_state[key]
    
    logger.info("User logged out")


def check_session_timeout() -> bool:
    """
    Check if session has exceeded 8-hour timeout.
    
    Returns:
        True if session expired, False otherwise
    """
    if 'login_timestamp' not in st.session_state:
        return True
    
    login_time = st.session_state['login_timestamp']
    elapsed = datetime.now() - login_time
    
    # 8 hour timeout
    return elapsed > timedelta(hours=8)


def check_lockout(username: str) -> bool:
    """
    Check if username is currently locked out.
    
    Args:
        username: Username to check
        
    Returns:
        True if locked out, False otherwise
    """
    if 'lockout_until' not in st.session_state:
        st.session_state['lockout_until'] = {}
    
    if username in st.session_state['lockout_until']:
        unlock_time = st.session_state['lockout_until'][username]
        if datetime.now() < unlock_time:
            return True
        else:
            # Lockout expired, remove it
            del st.session_state['lockout_until'][username]
    
    return False


def record_failed_attempt(username: str) -> None:
    """
    Record a failed login attempt and implement lockout if needed.
    
    Args:
        username: Username that failed authentication
    """
    if 'failed_attempts' not in st.session_state:
        st.session_state['failed_attempts'] = {}
    
    if username not in st.session_state['failed_attempts']:
        st.session_state['failed_attempts'][username] = 0
    
    st.session_state['failed_attempts'][username] += 1
    
    # Log the failed attempt
    logger.warning(f"Failed login attempt for username: {username}")
    
    # Implement lockout after 3 failed attempts
    if st.session_state['failed_attempts'][username] >= 3:
        if 'lockout_until' not in st.session_state:
            st.session_state['lockout_until'] = {}
        
        lockout_time = datetime.now() + timedelta(minutes=5)
        st.session_state['lockout_until'][username] = lockout_time
        logger.warning(f"Account locked out: {username} until {lockout_time}")


def reset_failed_attempts(username: str) -> None:
    """
    Reset failed attempt counter for a username.
    
    Args:
        username: Username to reset
    """
    if 'failed_attempts' in st.session_state and username in st.session_state['failed_attempts']:
        del st.session_state['failed_attempts'][username]


def get_lockout_remaining_time(username: str) -> Optional[int]:
    """
    Get remaining lockout time in minutes for a username.
    
    Args:
        username: Username to check
        
    Returns:
        Remaining minutes until unlock, or None if not locked out
    """
    if 'lockout_until' not in st.session_state:
        return None
    
    if username in st.session_state['lockout_until']:
        lockout_until = st.session_state['lockout_until'][username]
        remaining_seconds = (lockout_until - datetime.now()).total_seconds()
        if remaining_seconds > 0:
            return int(remaining_seconds / 60) + 1  # Round up to next minute
    
    return None


def is_admin() -> bool:
    """
    Check if the currently authenticated user is an admin.
    
    This function checks if the logged-in user's username matches the admin
    username stored in environment variables. Admin credentials are stored
    in the .env file for security.
    
    Returns:
        True if the current user is an admin, False otherwise
        
    Validates: Requirements 7.5
    """
    if not is_authenticated():
        return False
    
    admin_username = os.getenv('ADMIN_USERNAME')
    current_username = st.session_state.get('username')
    
    if not admin_username:
        logger.warning("ADMIN_USERNAME not configured in environment variables")
        return False
    
    return current_username == admin_username


def authenticate_admin(username: str, password: str) -> bool:
    """
    Authenticate admin credentials against environment variables.
    
    This function verifies admin credentials stored in environment variables
    without using the database. This allows admin access even if the database
    is unavailable or not yet initialized.
    
    Args:
        username: Admin username to verify
        password: Admin password to verify
        
    Returns:
        True if credentials match admin credentials in .env, False otherwise
        
    Validates: Requirements 7.5
    """
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_username or not admin_password:
        logger.error("Admin credentials not configured in environment variables")
        return False
    
    return username == admin_username and password == admin_password
