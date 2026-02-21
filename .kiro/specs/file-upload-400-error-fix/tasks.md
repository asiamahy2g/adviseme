# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - First Upload Attempt Succeeds
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to the concrete failing case - first button click with two uploaded PDF files
  - Test that when two PDF files are uploaded and the button is clicked for the first time, the upload succeeds without 400 errors
  - The test should simulate: uploading two PDF files, clicking "Generate Academic Advice" button for the first time, and verifying no 400 error from /_stcore/upload_file endpoint
  - Mock Streamlit's file uploader and upload endpoint to observe buffer state and data being sent
  - Run test on UNFIXED code (with file.read())
  - **EXPECTED OUTCOME**: Test FAILS with 400 error from upload endpoint (this is correct - it proves the bug exists)
  - Document counterexamples found: buffer consumption by file.read(), buffer position state, empty data sent to upload endpoint
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Upload Flow Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (subsequent clicks, missing files, API errors)
  - Write property-based tests capturing observed behavior patterns:
    - Subsequent button clicks (2nd, 3rd click) work correctly and generate advice
    - Missing file validation shows warning when 0 or 1 files uploaded
    - API error responses display error messages correctly
    - Successful API responses display advice in text area correctly
    - Spinner displays during processing
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for file upload 400 error on first attempt

  - [x] 3.1 Implement the fix in adviseme.py
    - Locate the button click handler (code block under `if st.button("Generate Academic Advice"):`)
    - Replace all instances of `file.read()` with `file.getvalue()` when accessing uploaded file data
    - Verify base64 encoding receives the same byte data format from `file.getvalue()`
    - Ensure no other logic changes (validation, error handling, API calls, UI updates remain identical)
    - _Bug_Condition: isBugCondition(input) where input.filesUploaded == 2 AND input.isFirstClick == true AND fileReadMethod == 'file.read()' AND NOT uploadSuccessful(input)_
    - _Expected_Behavior: For any button click event where two PDF files are uploaded and the button is clicked for the first time, the fixed function SHALL successfully read the file data using file.getvalue() and process the upload without 400 errors_
    - _Preservation: For any button click event that is NOT the first upload attempt (subsequent clicks, missing files, API errors), the fixed code SHALL produce exactly the same behavior as the original code_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - First Upload Attempt Succeeds
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed - first upload attempt succeeds without 400 error)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Upload Flow Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions in subsequent clicks, validation, error handling, success flow)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
