import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os, requests, base64, json
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AdviseMe", page_icon="🎓")

# Load authentication config
config_path = os.path.join(os.path.dirname(__file__), "auth_config.yaml")

with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('preauthorized', {})
)

# Render login form
name, authentication_status, username = authenticator.login("Sign in to AdviseMe", "main")

if authentication_status is False:
    st.error("Username/password is incorrect")
    st.stop()

if authentication_status is None:
    st.warning("Please enter your username and password")
    st.stop()

# User is authenticated - show logout in sidebar
with st.sidebar:
    st.write(f"Welcome, **{name}**")
    authenticator.logout("Sign Out", "sidebar")
    st.markdown("---")

st.title("🎓 AdviseMe")
st.subheader("Academic Advisor Assistant")

# POE API configuration
POE_API_KEY = os.getenv("POE_API_KEY")
POE_BASE_URL = "https://api.poe.com/v1"

def encode_file(file_bytes):
    return base64.b64encode(file_bytes).decode("utf-8")

# File upload section
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Student Academic Progress**")
    progress_file = st.file_uploader("Upload academic progress PDF", type="pdf", key="progress")

with col2:
    st.markdown("**Course Schedule**")
    schedule_file = st.file_uploader("Upload course schedule PDF", type="pdf", key="schedule")

if st.button("Generate Academic Advice", type="primary"):
    if progress_file and schedule_file:
        with st.spinner("Analyzing documents and generating advice..."):
            # Encode files
            progress_data = encode_file(progress_file.read())
            schedule_data = encode_file(schedule_file.read())

            # Academic advisor prompt
            system_prompt = """You are a seasoned professor and an animal science professor at UAPB. A student sent you an email inquiring about their academic progress and the courses they need to complete in Spring 2026. I have attached his academic progress. Go through it and make a list of the courses she/he needs to take. I have attached the course schedule for spring 2026. Based on the student's needs, schedule their classes for him. She/he will need 15 - 18 credits. Let's assume she/he passes all current courses in the Fall 2025. Prepare an email for her/him, first telling him about his academic progress and also the classes he needs to register for in the spring semester. Make it clear, concise and straight to the point."""

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
                    st.success("Analysis complete!")
                    st.markdown("### Academic Advice Email")
                    st.text_area("Generated Email", result['choices'][0]['message']['content'], height=400)
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Error generating advice: {str(e)}")
    else:
        st.warning("Please upload both files before generating advice.")

st.markdown("---")
st.markdown("*AdviseMe - AI-powered academic advising assistant*")
