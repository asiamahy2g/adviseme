"""
History Manager for AdviseMe

This module coordinates between UI, database, and session state for history features
including student name extraction, history formatting, and session reloading.

Validates: Requirements 3, 4, 5
"""

import streamlit as st
import logging
from typing import Optional, List
from datetime import datetime
import re
from database import safe_database_operation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_student_name(progress_filename: str) -> str:
    """
    Extract student name from uploaded PDF filename.
    
    Expected format: "StudentName_AcademicProgress.pdf" or similar patterns
    Fallback: "Unknown Student" if parsing fails
    
    Args:
        progress_filename: Name of the uploaded academic progress PDF
        
    Returns:
        Extracted student name or fallback value
    """
    if not progress_filename:
        return "Unnamed Student"
    
    try:
        # Remove .pdf extension
        name_part = progress_filename.replace('.pdf', '').replace('.PDF', '')
        
        # Try to extract name before underscore or parenthesis
        # Common patterns: "FirstName_LastName_...", "FirstName LastName (...)"
        if '_' in name_part:
            # Split by underscore and take first part
            name = name_part.split('_')[0]
        elif '(' in name_part:
            # Split by parenthesis and take first part
            name = name_part.split('(')[0].strip()
        else:
            # Use the whole filename (without extension)
            name = name_part
        
        # Clean up the name
        name = name.strip()
        
        # If name is empty or too short, use fallback
        if len(name) < 2:
            return "Unknown Student"
        
        return name
        
    except Exception as e:
        logger.warning(f"Failed to extract student name from filename: {progress_filename}, error: {e}")
        return "Unknown Student"


def format_history_entry(session: dict) -> str:
    """
    Format a session record for display in dropdown.
    
    Format: "Student Name - Semester Year (MM/DD/YYYY)"
    
    Args:
        session: Session record dictionary from database
        
    Returns:
        Formatted string for dropdown display
    """
    try:
        student_name = session.get('student_name', 'Unknown')
        semester = session.get('semester', '')
        year = session.get('year', '')
        timestamp = session.get('timestamp', '')
        
        # Parse timestamp and format as MM/DD/YYYY
        if timestamp:
            # Handle both string and datetime objects
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp)
            else:
                dt = timestamp
            date_str = dt.strftime('%m/%d/%Y')
        else:
            date_str = 'Unknown Date'
        
        return f"{student_name} - {semester} {year} ({date_str})"
        
    except Exception as e:
        logger.error(f"Error formatting history entry: {e}")
        return "Error formatting entry"


@safe_database_operation
def get_history_dropdown_options(professor_id: int) -> List[tuple]:
    """
    Get formatted history options for dropdown.
    
    Args:
        professor_id: ID of the professor
        
    Returns:
        List of tuples (display_text, session_id)
    """
    from database import get_professor_history
    
    sessions = get_professor_history(professor_id, limit=50)
    
    if not sessions:
        return [("No advising history yet", None)]
    
    options = []
    for session in sessions:
        display_text = format_history_entry(session)
        session_id = session.get('session_id')
        options.append((display_text, session_id))
    
    return options


@safe_database_operation
def reload_session(session_id: int, professor_id: int) -> bool:
    """
    Load a session from database and populate session_state.
    
    Updates: email_content, recommended_schedule, alternative1_schedule,
             alternative2_schedule, semester_info
    
    Args:
        session_id: ID of the session to load
        professor_id: ID of the professor (for security verification)
        
    Returns:
        True if session loaded successfully, False otherwise
    """
    from database import load_session
    
    session = load_session(session_id, professor_id)
    
    if not session:
        logger.warning(f"Session not found or unauthorized: {session_id}")
        st.error("Unable to load session - not found or unauthorized")
        return False
    
    # Populate session state with loaded data
    st.session_state['email_content'] = session.get('email_content', '')
    st.session_state['recommended_schedule'] = session.get('recommended_schedule', '')
    st.session_state['alternative1_schedule'] = session.get('alternative1_schedule', '')
    st.session_state['alternative2_schedule'] = session.get('alternative2_schedule', '')
    
    # Format semester info
    semester = session.get('semester', '')
    year = session.get('year', '')
    st.session_state['semester_info'] = f"{semester} {year}"
    
    # Store the loaded session timestamp for notification
    timestamp = session.get('timestamp', '')
    if timestamp:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = timestamp
        st.session_state['loaded_session_timestamp'] = dt.strftime('%m/%d/%Y %I:%M %p')
    
    logger.info(f"Successfully loaded session {session_id} for professor {professor_id}")
    return True


@safe_database_operation
def save_current_session(professor_id: int, student_name: str, semester: str, year: int) -> bool:
    """
    Save the current session from session_state to database.
    
    Args:
        professor_id: ID of the professor
        student_name: Name of the student
        semester: Semester (Spring, Summer, Fall)
        year: Year
        
    Returns:
        True if save succeeds, False otherwise
    """
    from database import save_advising_session
    
    # Get content from session state
    email_content = st.session_state.get('email_content', '')
    recommended_schedule = st.session_state.get('recommended_schedule', '')
    alternative1_schedule = st.session_state.get('alternative1_schedule', '')
    alternative2_schedule = st.session_state.get('alternative2_schedule', '')
    
    # Validate required fields
    if not email_content or not recommended_schedule:
        logger.warning("Cannot save session - missing required content")
        return False
    
    # Save to database
    success = save_advising_session(
        professor_id=professor_id,
        student_name=student_name,
        semester=semester,
        year=year,
        email_content=email_content,
        recommended_schedule=recommended_schedule,
        alternative1_schedule=alternative1_schedule,
        alternative2_schedule=alternative2_schedule
    )
    
    if success:
        logger.info(f"Saved session for student: {student_name}")
    else:
        logger.warning("Failed to save session to database")
    
    return success
