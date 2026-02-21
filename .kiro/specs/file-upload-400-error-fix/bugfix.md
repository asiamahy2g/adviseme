# Bugfix Requirements Document

## Introduction

The advisor app (adviseme.py) experiences a 400 error from Streamlit's upload endpoint when users attempt to upload PDF files for the first time. The upload succeeds on subsequent attempts, indicating a file buffer state issue in the button click handler. This bug prevents users from successfully uploading their academic progress and course schedule PDFs on the first try, creating a poor user experience and requiring multiple attempts to use the application.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user uploads two PDF files and clicks "Generate Academic Advice" for the first time THEN the system triggers a 400 error from the Streamlit upload endpoint (/_stcore/upload_file/...)

1.2 WHEN the file buffer is read via `file.read()` in the button click handler without proper buffer management THEN the system fails to properly access the file data on the first attempt

1.3 WHEN the user clicks the button again after the initial failure THEN the system successfully reads the file data and processes the upload

### Expected Behavior (Correct)

2.1 WHEN a user uploads two PDF files and clicks "Generate Academic Advice" for the first time THEN the system SHALL successfully read the file data and process the upload without errors

2.2 WHEN the file buffer is accessed in the button click handler THEN the system SHALL properly manage the buffer state to ensure reliable file reading on the first attempt

2.3 WHEN the file data is encoded to base64 THEN the system SHALL use a method that doesn't consume or depend on the buffer position state

### Unchanged Behavior (Regression Prevention)

3.1 WHEN files are successfully uploaded and processed THEN the system SHALL CONTINUE TO encode them as base64 and send them to the POE API with the correct format

3.2 WHEN the POE API returns a successful response THEN the system SHALL CONTINUE TO display the generated academic advice email in the text area

3.3 WHEN either file is missing THEN the system SHALL CONTINUE TO display the warning message "Please upload both files before generating advice"

3.4 WHEN an API error occurs THEN the system SHALL CONTINUE TO display the appropriate error message with status code and details

3.5 WHEN the button is clicked with valid files THEN the system SHALL CONTINUE TO show the spinner with message "Analyzing documents and generating advice..."
