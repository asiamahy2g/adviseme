"""
UI Helper Functions for AdviseMe

This module provides UI utilities including loading indicators for operations
that may take longer than 500ms.

Validates: Requirements 11.4
"""

import streamlit as st
import time
from contextlib import contextmanager
from typing import Callable, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def operation_spinner(message: str, threshold_ms: int = 500):
    """
    Context manager that shows a spinner for potentially slow operations.
    
    This provides user feedback during authentication and database operations
    that may exceed 500ms as specified in requirement 11.4.
    
    Note: Streamlit spinners are synchronous and show for the duration of the
    operation. This context manager ensures spinners are consistently applied
    to operations that may exceed the threshold.
    
    Args:
        message: Message to display with the spinner
        threshold_ms: Expected threshold in milliseconds (default 500ms)
        
    Example:
        with operation_spinner("Authenticating...", threshold_ms=500):
            result = authenticate_user(username, password)
    
    Validates: Requirements 11.4
    """
    start_time = time.time()
    
    with st.spinner(message):
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= threshold_ms:
                logger.debug(f"Operation '{message}' took {elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)")


def timed_operation(operation_name: str, threshold_ms: int = 500):
    """
    Decorator that logs operations exceeding the time threshold.
    
    This helps identify slow database operations and authentication attempts
    for monitoring and optimization purposes.
    
    Args:
        operation_name: Name of the operation for logging
        threshold_ms: Threshold in milliseconds (default 500ms)
        
    Returns:
        Decorated function
        
    Example:
        @timed_operation("database_query", threshold_ms=500)
        def get_professor_history(professor_id):
            return database.query(professor_id)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms >= threshold_ms:
                logger.info(f"{operation_name} took {elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)")
            
            return result
        
        return wrapper
    return decorator
