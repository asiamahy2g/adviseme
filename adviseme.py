import streamlit as st
import os, requests, base64, json, io
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="AdviseMe", page_icon="🎓")

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

st.markdown("**Course Schedule**")
schedule_file = st.file_uploader("Upload course schedule PDF", type="pdf", key="schedule")
if schedule_file:
    st.caption(f"✓ {schedule_file.name} ({schedule_file.size / 1024:.1f} KB)")

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
                    
                    st.success("Analysis complete! Multiple schedule options generated.")
                    
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
