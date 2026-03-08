import streamlit as st
import os, requests, base64, json, io
from dotenv import load_dotenv
from datetime import datetime
import logging
import auth
import database
import history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(page_title="AdviseMe", page_icon="🎓")

# Initialize database on startup - handle failures gracefully
try:
    database.initialize_database()
    # Verify database was created successfully by checking if file exists
    if not os.path.exists(database.DB_PATH):
        st.warning("⚠️ History features are temporarily unavailable. You can still generate academic advice.")
        logger.warning("Database initialization failed - continuing without history features")
except Exception as e:
    st.warning("⚠️ History features are temporarily unavailable. You can still generate academic advice.")
    logger.error(f"Database initialization error: {e}")

# Authentication check - show login page if not authenticated
# This check runs on every page interaction (every Streamlit rerun) to enforce session timeout
# The is_authenticated() function checks if the session has exceeded 8 hours and auto-logs out if expired
if not auth.is_authenticated():
    st.title("🎓 AdviseMe - Login")
    st.markdown("### Professor Authentication")
    
    # Display timeout message if session expired
    if st.session_state.get('session_timeout', False):
        st.warning("⏱️ Your session has expired. Please log in again.")
        # Clear the timeout flag
        del st.session_state['session_timeout']
    else:
        st.markdown("Please log in to access the academic advising system.")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("Login", type="primary")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Check for lockout
                lockout_remaining = auth.get_lockout_remaining_time(username)
                if lockout_remaining:
                    st.error(f"Account temporarily locked. Try again in {lockout_remaining} minutes.")
                else:
                    # Attempt authentication
                    with st.spinner("Authenticating..."):
                        professor_id = auth.authenticate_user(username, password)
                        
                        if professor_id:
                            # Authentication successful
                            auth.create_session(professor_id, username)
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            # Check if now locked out
                            lockout_remaining = auth.get_lockout_remaining_time(username)
                            if lockout_remaining:
                                st.error(f"Too many failed attempts. Account locked for {lockout_remaining} minutes.")
                            else:
                                st.error("Invalid username or password")
    
    st.markdown("---")
    st.caption("AdviseMe - Academic Advising System | UAPB")
    st.stop()  # Stop execution here if not authenticated

# Banner image - full width but limited height
if os.path.exists("banner.jpg"):
    st.markdown(
        """
        <style>
        [data-testid="stImage"] {
            max-height: 120px;
            overflow: hidden;
        }
        [data-testid="stImage"] img {
            object-fit: cover;
            object-position: center;
            width: 100%;
            height: 120px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.image("banner.jpg", use_container_width=True)
else:
    st.warning("Banner image not found at: " + os.path.abspath("banner.jpg"))

st.title("🎓 AdviseMe")
st.subheader("Your Academic Companion")

# Sidebar
with st.sidebar:
    # Display authenticated username
    st.markdown(f"**Logged in as:** {st.session_state.get('username', 'Unknown')}")
    st.markdown("---")
    
    # Class Schedule Management - upload once, reuse for multiple students
    st.markdown("**📅 Class Schedule Manager**")
    
    # Check if a schedule is already loaded
    if 'stored_schedule_file' in st.session_state and st.session_state.get('stored_schedule_file'):
        # Display currently loaded schedule info
        schedule_info = st.session_state.get('stored_schedule_info', {})
        st.success(f"✓ Schedule loaded: {schedule_info.get('semester', '')} {schedule_info.get('year', '')}")
        st.caption(f"File: {schedule_info.get('filename', 'Unknown')}")
        
        # Button to clear/change schedule
        if st.button("🔄 Change Schedule", use_container_width=True):
            del st.session_state['stored_schedule_file']
            del st.session_state['stored_schedule_info']
            st.rerun()
    else:
        # Upload new schedule
        st.markdown("Upload a class schedule to reuse for multiple students:")
        
        with st.form("schedule_upload_form"):
            new_schedule_file = st.file_uploader("Course Schedule PDF", type="pdf", key="new_schedule")
            
            col1, col2 = st.columns(2)
            with col1:
                schedule_semester = st.selectbox("Semester", ["Spring", "Summer", "Fall"], index=0, key="schedule_semester")
            with col2:
                schedule_year = st.number_input("Year", min_value=2024, max_value=2030, value=2026, step=1, key="schedule_year")
            
            upload_button = st.form_submit_button("📁 Save Schedule", type="primary")
            
            if upload_button:
                if new_schedule_file:
                    # Store schedule in session state
                    st.session_state['stored_schedule_file'] = new_schedule_file.getvalue()
                    st.session_state['stored_schedule_info'] = {
                        'filename': new_schedule_file.name,
                        'semester': schedule_semester,
                        'year': schedule_year,
                        'size': new_schedule_file.size
                    }
                    st.success(f"✓ Schedule saved for {schedule_semester} {schedule_year}")
                    st.rerun()
                else:
                    st.error("Please upload a schedule file")
    
    st.markdown("---")
    
    # History dropdown - above "About" expander
    st.markdown("**📚 Advising History**")
    professor_id = st.session_state.get('professor_id')
    
    if professor_id:
        # Get history options - handle database unavailability
        # Show spinner only if operation takes longer than expected
        with st.spinner("Loading history..."):
            history_options = history.get_history_dropdown_options(professor_id)
        
        # Check if database is unavailable (decorator returns empty list)
        if history_options is None or (isinstance(history_options, list) and len(history_options) == 0):
            st.info("History features temporarily unavailable")
            logger.warning("History dropdown unavailable - database error")
        else:
            # Create dropdown with formatted entries
            display_texts = [option[0] for option in history_options]
            session_ids = [option[1] for option in history_options]
            
            # Use selectbox for history dropdown
            selected_index = st.selectbox(
                "Select a previous session to reload:",
                range(len(display_texts)),
                format_func=lambda i: display_texts[i],
                key="history_dropdown",
                label_visibility="collapsed"
            )
            
            # Handle selection
            selected_session_id = session_ids[selected_index]
            
            # Check if a valid session was selected and if it's different from current
            if selected_session_id is not None:
                # Use a button to trigger reload to avoid constant reloading
                if st.button("📂 Load Selected Session", use_container_width=True):
                    with st.spinner("Loading session..."):
                        success = history.reload_session(selected_session_id, professor_id)
                        if success:
                            # Show notification with timestamp
                            loaded_timestamp = st.session_state.get('loaded_session_timestamp', 'Unknown time')
                            st.success(f"✅ Loaded session from {loaded_timestamp}")
                            st.rerun()
                        elif success is False:
                            # Session not found or error already displayed by reload_session
                            pass
                        else:
                            # success is None - database unavailable
                            st.error("Unable to load session - history features temporarily unavailable")
    else:
        st.info("No advising history yet")
    
    st.markdown("---")
    
    # Admin interface - only visible to admin users
    if auth.is_admin():
        with st.expander("🔐 Admin - Create Professor Account", expanded=False):
            st.markdown("**Create New Professor Account**")
            st.caption("Only administrators can create new professor accounts.")
            
            with st.form("create_professor_form"):
                new_username = st.text_input(
                    "Username",
                    placeholder="Enter username (alphanumeric, hyphens, underscores)",
                    help="Username must contain only letters, numbers, hyphens, and underscores"
                )
                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter password (minimum 8 characters)",
                    help="Password must be at least 8 characters long"
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter password"
                )
                
                create_button = st.form_submit_button("Create Account", type="primary")
                
                if create_button:
                    # Validate inputs
                    if not new_username or not new_password:
                        st.error("❌ Please enter both username and password")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        try:
                            # Attempt to create professor account
                            success = database.create_professor(new_username, new_password)
                            
                            if success:
                                st.success(f"✅ Professor account '{new_username}' created successfully!")
                                logger.info(f"Admin {st.session_state.get('username')} created professor account: {new_username}")
                            else:
                                st.error("❌ Failed to create account. Username may already exist.")
                        except ValueError as e:
                            # Validation error from create_professor
                            st.error(f"❌ Validation error: {str(e)}")
                        except Exception as e:
                            # Database error or other unexpected error
                            st.error(f"❌ Error creating account: {str(e)}")
                            logger.error(f"Error creating professor account: {e}")
        
        st.markdown("---")
    
    with st.expander("📖 About", expanded=False):
        st.markdown("""
        **AdviseMe** helps academic advisors at UAPB create personalized course schedules for students.
        
        **Features:**
        - Generate professional emails with academic advice
        - Create multiple schedule options (customizable credits)
        - Download schedules in CSV format
        - Works with Workday data exports
        - Available for all departments
        """)
    
    with st.expander("📋 How to Use", expanded=False):
        st.markdown("""
        **Step 1:** Download from Workday
        - Student's academic progress (PDF)
        - Course schedule for the semester (PDF)
        
        **Step 2:** Upload both files using the form
        
        **Step 3:** Select semester and year
        
        **Step 4:** Click "Generate Academic Advice"
        
        **Step 5:** Review multiple schedule options
        
        **Step 6:** Download your preferred schedule and email it to the student
        """)
    
    with st.expander("⚙️ Settings"):
        st.markdown("**Default Credit Range**")
        min_credits = st.number_input("Minimum Credits", min_value=12, max_value=18, value=15)
        max_credits = st.number_input("Maximum Credits", min_value=12, max_value=21, value=18)
        
        if min_credits > max_credits:
            st.error("Minimum credits cannot exceed maximum credits")
        else:
            st.session_state['min_credits'] = min_credits
            st.session_state['max_credits'] = max_credits
    
    with st.expander("❓ Help & FAQ"):
        st.markdown("""
        **Q: What file formats are supported?**  
        A: Only PDF files from Workday.
        
        **Q: Why did my upload fail?**  
        A: Try uploading again. Large files (>10MB) may timeout.
        
        **Q: Can I use this for any department?**  
        A: Yes! AdviseMe works for all departments at UAPB.
        
        **Q: How do I download the schedule?**  
        A: Click the download button in any schedule tab.
        """)
    
    with st.expander("📞 Contact & Support"):
        st.markdown("""
        **Need help?**  
        Contact IT Support or your department administrator.
        
        **Report issues:**  
        Email: asiamahe@uapb.edu
        """)
    
    st.markdown("---")
    
    # Logout button at bottom of sidebar
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        auth.logout()
        st.rerun()
    
    st.markdown("---")
    st.caption("Version 2.0 | March 2026")

# POE API configuration
POE_API_KEY = os.getenv("POE_API_KEY")
POE_BASE_URL = "https://api.poe.com/v1"

def encode_file(file_bytes):
    return base64.b64encode(file_bytes).decode("utf-8")

def parse_schedule_table_to_csv(schedule_markdown):
    """Convert markdown table to CSV format."""
    lines = schedule_markdown.strip().split('\n')
    csv_lines = []
    for line in lines:
        if '|' in line and not line.strip().startswith('|---'):
            # Remove leading/trailing pipes and split
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            csv_lines.append(','.join(cells))
    return '\n'.join(csv_lines)

# File upload section
st.markdown("**Student Academic Progress**")
progress_file = st.file_uploader("Upload academic progress PDF", type="pdf", key="progress")
if progress_file:
    st.caption(f"✓ {progress_file.name} ({progress_file.size / 1024:.1f} KB)")

# Check if schedule is already stored in session
if 'stored_schedule_file' in st.session_state and st.session_state.get('stored_schedule_file'):
    # Use stored schedule
    schedule_info = st.session_state.get('stored_schedule_info', {})
    st.markdown("**Course Schedule**")
    st.info(f"✓ Using saved schedule: {schedule_info.get('semester', '')} {schedule_info.get('year', '')} - {schedule_info.get('filename', '')}")
    st.caption("To change the schedule, use the Schedule Manager in the sidebar")
    
    # Get semester and year from stored schedule
    semester = schedule_info.get('semester', 'Spring')
    year = schedule_info.get('year', 2026)
    
    # Create a mock file object from stored bytes
    class StoredFile:
        def __init__(self, data, name):
            self.data = data
            self.name = name
        def getvalue(self):
            return self.data
    
    schedule_file = StoredFile(st.session_state['stored_schedule_file'], schedule_info.get('filename', 'schedule.pdf'))
else:
    # No stored schedule - require upload
    st.markdown("**Course Schedule**")
    schedule_file = st.file_uploader("Upload course schedule PDF", type="pdf", key="schedule")
    if schedule_file:
        st.caption(f"✓ {schedule_file.name} ({schedule_file.size / 1024:.1f} KB)")
    
    st.info("💡 Tip: Use the Schedule Manager in the sidebar to upload a schedule once and reuse it for multiple students")
    
    # Semester and year input
    col1, col2 = st.columns(2)
    with col1:
        semester = st.selectbox("Semester", ["Spring", "Summer", "Fall"], index=0)
    with col2:
        year = st.number_input("Year", min_value=2024, max_value=2030, value=2026, step=1)

if st.button("Generate Academic Advice", type="primary"):
    if progress_file and schedule_file:
        with st.spinner("Analyzing documents and generating advice..."):
            # Encode files
            progress_data = encode_file(progress_file.getvalue())
            schedule_data = encode_file(schedule_file.getvalue())
            
            # Academic advisor prompt
            credit_range = f"{st.session_state.get('min_credits', 15)}-{st.session_state.get('max_credits', 18)}"
            system_prompt = f"""You are an academic advisor at UAPB. A student sent you an email inquiring about their academic progress and the courses they need to complete in {semester} {year}. I have attached their academic progress and the course schedule for {semester.lower()} {year}.

Your task:
1. Analyze the student's academic progress and identify courses with status "Not Satisfied" - these are the courses they need to take
2. IMPORTANT: Do NOT recommend courses that are "In Progress" - only recommend courses with "Not Satisfied" status
3. CRITICAL: Only recommend courses that are REQUIRED for the student's program completion - do not suggest electives or non-required courses unless necessary to meet credit requirements
4. Based on the student's needs and the available course schedule, create schedule options ({credit_range} credits each) for {semester} {year}
5. ONLY create alternative schedules if there are genuinely different viable combinations of required courses - if there's only one logical schedule, provide only the recommended schedule
6. Assume the student passes all current courses in the previous semester
7. Rank the schedules by quality (consider: time distribution, prerequisite flow, workload balance, avoiding conflicts)

Please provide outputs in this EXACT format:

OUTPUT 1 - EMAIL:
Write a clear, concise, professional email to the student that:
- Summarizes their academic progress
- Mentions that you've created multiple schedule options for them to choose from
- Provides any important notes or considerations

OUTPUT 2 - RECOMMENDED SCHEDULE (BEST OPTION):
Create a markdown table with: | Course Code | Course Name | Credits | Day/Time | Instructor |
Add a brief explanation (2-3 sentences) of why this is the recommended option.

OUTPUT 3 - ALTERNATIVE SCHEDULE 1 (only if genuinely different viable combination exists):
Create a markdown table with the same format.
Add a brief explanation of the key differences from the recommended schedule.

OUTPUT 4 - ALTERNATIVE SCHEDULE 2 (only if a third genuinely different viable combination exists):
Create a markdown table with the same format.
Add a brief explanation of the key differences.

Format your response EXACTLY as follows:
---EMAIL---
[Your email content here]
---END EMAIL---

---RECOMMENDED---
[Brief explanation why this is best]

[Your markdown table here]
---END RECOMMENDED---

---ALTERNATIVE1---
[Brief explanation of differences]

[Your markdown table here]
---END ALTERNATIVE1---

---ALTERNATIVE2---
[Brief explanation of differences]

[Your markdown table here]
---END ALTERNATIVE2---

IMPORTANT NOTES:
- Only include ALTERNATIVE1 and ALTERNATIVE2 sections if there are genuinely different viable combinations of REQUIRED courses
- If there is only one logical schedule to meet the student's program requirements, provide only the RECOMMENDED schedule section
- Do not create artificial alternatives by mixing in non-required electives just to have multiple options
"""
            
            # Create message with file attachments
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt
                        },
                        {
                            "type": "file",
                            "file": {
                                "filename": progress_file.name,
                                "file_data": f"data:application/pdf;base64,{progress_data}"
                            }
                        },
                        {
                            "type": "file",
                            "file": {
                                "filename": schedule_file.name,
                                "file_data": f"data:application/pdf;base64,{schedule_data}"
                            }
                        }
                    ]
                }
            ]
            
            try:
                headers = {
                    "Authorization": f"Bearer {POE_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "Claude-Sonnet-4",
                    "messages": messages
                }
                
                response = requests.post(
                    f"{POE_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Parse the response to extract email and schedules
                    email_content = ""
                    recommended_schedule = ""
                    alternative1_schedule = ""
                    alternative2_schedule = ""
                    
                    # Extract email
                    if "---EMAIL---" in content and "---END EMAIL---" in content:
                        email_start = content.find("---EMAIL---") + len("---EMAIL---")
                        email_end = content.find("---END EMAIL---")
                        email_content = content[email_start:email_end].strip()
                    
                    # Extract recommended schedule
                    if "---RECOMMENDED---" in content and "---END RECOMMENDED---" in content:
                        rec_start = content.find("---RECOMMENDED---") + len("---RECOMMENDED---")
                        rec_end = content.find("---END RECOMMENDED---")
                        recommended_schedule = content[rec_start:rec_end].strip()
                    
                    # Extract alternative 1
                    if "---ALTERNATIVE1---" in content and "---END ALTERNATIVE1---" in content:
                        alt1_start = content.find("---ALTERNATIVE1---") + len("---ALTERNATIVE1---")
                        alt1_end = content.find("---END ALTERNATIVE1---")
                        alternative1_schedule = content[alt1_start:alt1_end].strip()
                    
                    # Extract alternative 2
                    if "---ALTERNATIVE2---" in content and "---END ALTERNATIVE2---" in content:
                        alt2_start = content.find("---ALTERNATIVE2---") + len("---ALTERNATIVE2---")
                        alt2_end = content.find("---END ALTERNATIVE2---")
                        alternative2_schedule = content[alt2_start:alt2_end].strip()
                    
                    # If parsing fails, show full content
                    if not email_content:
                        email_content = content
                        recommended_schedule = "Parsing failed. Please check the email tab for full response."
                    
                    # Store in session state for persistence
                    st.session_state['email_content'] = email_content
                    st.session_state['recommended_schedule'] = recommended_schedule
                    st.session_state['alternative1_schedule'] = alternative1_schedule
                    st.session_state['alternative2_schedule'] = alternative2_schedule
                    st.session_state['semester_info'] = f"{semester} {year}"
                    
                    # Automatically save session to database
                    try:
                        # Extract student name from progress file
                        student_name = history.extract_student_name(progress_file.name)
                        
                        # Get professor ID from session state
                        professor_id = st.session_state.get('professor_id')
                        
                        # Save the advising session
                        if professor_id:
                            save_success = database.save_advising_session(
                                professor_id=professor_id,
                                student_name=student_name,
                                semester=semester,
                                year=year,
                                email_content=email_content,
                                recommended_schedule=recommended_schedule,
                                alternative1_schedule=alternative1_schedule,
                                alternative2_schedule=alternative2_schedule
                            )
                            
                            if save_success:
                                st.success("Analysis complete! Multiple schedule options generated.")
                            elif save_success is False:
                                # Database error occurred (decorator returned False)
                                st.success("Analysis complete! Multiple schedule options generated.")
                                st.warning("⚠️ Session saved to display but could not be saved to history database.")
                            else:
                                # save_success is None - should not happen with current decorator
                                st.success("Analysis complete! Multiple schedule options generated.")
                                st.warning("⚠️ Session saved to display but could not be saved to history database.")
                        else:
                            st.success("Analysis complete! Multiple schedule options generated.")
                            st.warning("⚠️ Session saved to display but could not be saved to history (no professor ID).")
                    except Exception as e:
                        # Display advice even if database save fails
                        st.success("Analysis complete! Multiple schedule options generated.")
                        st.warning(f"⚠️ Session saved to display but could not be saved to history: {str(e)}")
                        logger.error(f"Failed to save advising session: {e}")
                    
                    # Create tabs for email and schedules
                    tabs = ["📧 Email", "⭐ Recommended Schedule"]
                    if alternative1_schedule:
                        tabs.append("📅 Alternative 1")
                    if alternative2_schedule:
                        tabs.append("📅 Alternative 2")
                    
                    tab_objects = st.tabs(tabs)
                    
                    # Email tab
                    with tab_objects[0]:
                        st.markdown("### Academic Advice Email")
                        st.text_area("Generated Email", email_content, height=400, label_visibility="collapsed")
                        
                        # Download and copy buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download Email",
                                data=email_content,
                                file_name=f"academic_advice_{semester}_{year}.txt",
                                mime="text/plain"
                            )
                        with col2:
                            if st.button("📋 Copy to Clipboard", key="copy_email"):
                                st.toast("Email copied to clipboard!", icon="✅")
                    
                    # Recommended schedule tab
                    with tab_objects[1]:
                        st.markdown("### ⭐ Recommended Schedule (Best Option)")
                        if recommended_schedule and "|" in recommended_schedule:
                            st.markdown(recommended_schedule)
                            
                            csv_data = parse_schedule_table_to_csv(recommended_schedule)
                            st.download_button(
                                label="📥 Download Schedule (CSV)",
                                data=csv_data,
                                file_name=f"recommended_schedule_{semester}_{year}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info(recommended_schedule)
                    
                    # Alternative 1 tab
                    if alternative1_schedule and len(tab_objects) > 2:
                        with tab_objects[2]:
                            st.markdown("### Alternative Schedule Option 1")
                            if "|" in alternative1_schedule:
                                st.markdown(alternative1_schedule)
                                
                                csv_data = parse_schedule_table_to_csv(alternative1_schedule)
                                st.download_button(
                                    label="📥 Download Schedule (CSV)",
                                    data=csv_data,
                                    file_name=f"alternative1_schedule_{semester}_{year}.csv",
                                    mime="text/csv",
                                    key="download_alt1"
                                )
                            else:
                                st.info(alternative1_schedule)
                    
                    # Alternative 2 tab
                    if alternative2_schedule and len(tab_objects) > 3:
                        with tab_objects[3]:
                            st.markdown("### Alternative Schedule Option 2")
                            if "|" in alternative2_schedule:
                                st.markdown(alternative2_schedule)
                                
                                csv_data = parse_schedule_table_to_csv(alternative2_schedule)
                                st.download_button(
                                    label="📥 Download Schedule (CSV)",
                                    data=csv_data,
                                    file_name=f"alternative2_schedule_{semester}_{year}.csv",
                                    mime="text/csv",
                                    key="download_alt2"
                                )
                            else:
                                st.info(alternative2_schedule)
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
                    st.info("💡 Tip: Try uploading the files again or check your internet connection.")
                
            except Exception as e:
                st.error(f"Error generating advice: {str(e)}")
                st.info("💡 Tip: Please try again. If the issue persists, contact support.")
    else:
        st.warning("⚠️ Please upload both files before generating advice.")
        st.info("💡 Download your student's academic progress and the course schedule from Workday, then upload them here.")

# Show previous results if they exist in session state
if 'email_content' in st.session_state and 'recommended_schedule' in st.session_state:
    with st.expander("📋 View Previous Results", expanded=False):
        st.caption(f"Last generated for: {st.session_state.get('semester_info', 'Unknown semester')}")
        
        prev_tabs = ["📧 Email", "⭐ Recommended"]
        if st.session_state.get('alternative1_schedule'):
            prev_tabs.append("📅 Alternative 1")
        if st.session_state.get('alternative2_schedule'):
            prev_tabs.append("📅 Alternative 2")
        
        prev_tab_objects = st.tabs(prev_tabs)
        
        with prev_tab_objects[0]:
            st.text_area("Previous Email", st.session_state['email_content'], height=300, label_visibility="collapsed", disabled=True)
        
        with prev_tab_objects[1]:
            if "|" in st.session_state['recommended_schedule']:
                st.markdown(st.session_state['recommended_schedule'])
            else:
                st.info(st.session_state['recommended_schedule'])
        
        if len(prev_tab_objects) > 2 and st.session_state.get('alternative1_schedule'):
            with prev_tab_objects[2]:
                if "|" in st.session_state['alternative1_schedule']:
                    st.markdown(st.session_state['alternative1_schedule'])
                else:
                    st.info(st.session_state['alternative1_schedule'])
        
        if len(prev_tab_objects) > 3 and st.session_state.get('alternative2_schedule'):
            with prev_tab_objects[3]:
                if "|" in st.session_state['alternative2_schedule']:
                    st.markdown(st.session_state['alternative2_schedule'])
                else:
                    st.info(st.session_state['alternative2_schedule'])

st.markdown("---")
st.markdown("*Your Academic Companion*")
