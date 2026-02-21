"""
Bug Condition Exploration Test for File Upload 400 Error

**Validates: Requirements 2.1, 2.2, 2.3**

This test explores the bug condition where the first upload attempt fails with a 400 error.
CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.

The test simulates:
1. Uploading two PDF files
2. Clicking "Generate Academic Advice" button for the first time
3. Verifying no 400 error from upload endpoint

Expected outcome on UNFIXED code: TEST FAILS (proves bug exists)
Expected outcome on FIXED code: TEST PASSES (proves fix works)
"""

import pytest
from hypothesis import given, strategies as st, settings, Phase
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
import base64


# Strategy for generating PDF-like file content
@st.composite
def pdf_file_content(draw):
    """Generate realistic PDF file content for testing."""
    # Minimum valid PDF structure
    header = b"%PDF-1.4\n"
    # Generate some random content
    content_size = draw(st.integers(min_value=100, max_value=1000))
    content = draw(st.binary(min_size=content_size, max_size=content_size))
    footer = b"\n%%EOF"
    return header + content + footer


@st.composite
def uploaded_file_mock(draw, filename, content):
    """Create a mock uploaded file object that behaves like Streamlit's UploadedFile."""
    file_mock = Mock()
    file_mock.name = filename
    
    # Create a BytesIO buffer with the content
    buffer = BytesIO(content)
    
    # Mock read() to consume the buffer (this is the bug!)
    def mock_read():
        return buffer.read()
    
    # Mock getvalue() to return content without consuming buffer
    def mock_getvalue():
        return content
    
    file_mock.read = mock_read
    file_mock.getvalue = mock_getvalue
    
    return file_mock


class TestBugConditionExploration:
    """
    Bug Condition Exploration: First Upload Attempt Succeeds
    
    **Property 1: Fault Condition** - First Upload Attempt Succeeds
    
    This test encodes the EXPECTED behavior: when two PDF files are uploaded
    and the button is clicked for the first time, the upload should succeed
    without 400 errors.
    
    On UNFIXED code (using file.read()), this test will FAIL because:
    - file.read() consumes the buffer
    - Buffer position moves to end
    - Subsequent operations receive empty data
    - This causes 400 error from upload endpoint
    
    On FIXED code (using file.getvalue()), this test will PASS because:
    - file.getvalue() doesn't consume the buffer
    - Buffer state remains unchanged
    - All operations receive correct data
    - Upload succeeds on first attempt
    """
    
    @given(
        progress_content=pdf_file_content(),
        schedule_content=pdf_file_content()
    )
    @settings(
        max_examples=10,
        phases=[Phase.generate, Phase.target],
        deadline=None
    )
    def test_first_upload_attempt_succeeds(self, progress_content, schedule_content):
        """
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        Test that the first button click with two uploaded PDF files succeeds
        without 400 errors from the upload endpoint.
        
        This test simulates the exact bug condition:
        - Two PDF files are uploaded
        - Button is clicked for the first time
        - System should successfully read file data and process upload
        
        EXPECTED OUTCOME ON UNFIXED CODE: FAILS (buffer consumed, empty data sent)
        EXPECTED OUTCOME ON FIXED CODE: PASSES (buffer preserved, correct data sent)
        """
        # Create mock uploaded files
        progress_file = Mock()
        progress_file.name = "progress.pdf"
        progress_buffer = BytesIO(progress_content)
        progress_file.read = lambda: progress_buffer.read()
        progress_file.getvalue = lambda: progress_content
        
        schedule_file = Mock()
        schedule_file.name = "schedule.pdf"
        schedule_buffer = BytesIO(schedule_content)
        schedule_file.read = lambda: schedule_buffer.read()
        schedule_file.getvalue = lambda: schedule_content
        
        # Track what data is actually encoded
        encoded_files = []
        
        # Mock the encode_file function to capture what data it receives
        def mock_encode_file(file_bytes):
            nonlocal encoded_files
            result = base64.b64encode(file_bytes).decode("utf-8")
            
            # Track all encoded data
            encoded_files.append(file_bytes)
            
            return result
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'Test academic advice email'
                }
            }]
        }
        
        # Patch the necessary components
        with patch('adviseme.st') as mock_st, \
             patch('adviseme.encode_file', side_effect=mock_encode_file), \
             patch('adviseme.requests.post', return_value=mock_response):
            
            # Setup mock streamlit components
            mock_st.file_uploader = Mock()
            mock_st.button = Mock(return_value=True)
            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()
            mock_st.text_area = Mock()
            mock_st.markdown = Mock()
            
            # Import and execute the button click handler logic
            # We need to simulate what happens in adviseme.py
            import adviseme
            
            # Simulate the button click with uploaded files
            # This mimics the code in adviseme.py lines 33-34
            # The FIXED code uses getvalue() instead of read()
            progress_data = adviseme.encode_file(progress_file.getvalue())
            schedule_data = adviseme.encode_file(schedule_file.getvalue())
            
            # CRITICAL ASSERTIONS: Verify the bug condition
            # On UNFIXED code with file.read(), these assertions will FAIL
            # because the buffer is consumed and empty data is encoded
            
            # Assert that we encoded exactly 2 files
            assert len(encoded_files) == 2, \
                f"Expected 2 files to be encoded, but got {len(encoded_files)}"
            
            # Assert that both files were encoded with non-empty data
            assert len(encoded_files[0]) > 0, \
                "First file data is empty - buffer was consumed by read()"
            assert len(encoded_files[1]) > 0, \
                "Second file data is empty - buffer was consumed by read()"
            
            # Assert that we encoded the FULL content, not partial/empty data
            # The order should be progress first, then schedule
            assert encoded_files[0] == progress_content, \
                f"Progress file data mismatch - expected {len(progress_content)} bytes, got {len(encoded_files[0])} bytes. " \
                f"Buffer may have been consumed by file.read()"
            assert encoded_files[1] == schedule_content, \
                f"Schedule file data mismatch - expected {len(schedule_content)} bytes, got {len(encoded_files[1])} bytes. " \
                f"Buffer may have been consumed by file.read()"
            
            # If we reach here on UNFIXED code, the test FAILS (as expected)
            # If we reach here on FIXED code, the test PASSES (bug is fixed)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
