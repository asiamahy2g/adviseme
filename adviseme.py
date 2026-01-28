import streamlit as st
import os, openai, base64, tempfile
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AdviseMe", page_icon="🎓")

st.title("🎓 AdviseMe")
st.subheader("Academic Advisor Assistant")

client = openai.OpenAI(
    api_key=os.getenv("POE_API_KEY"),
    base_url="https://api.poe.com/v1"
)

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
                response = client.chat.completions.create(
                    model="Claude-Sonnet-4",
                    messages=messages
                )
                
                st.success("Analysis complete!")
                st.markdown("### Academic Advice Email")
                st.text_area("Generated Email", response.choices[0].message.content, height=400)
                
            except Exception as e:
                st.error(f"Error generating advice: {str(e)}")
    else:
        st.warning("Please upload both files before generating advice.")

st.markdown("---")
st.markdown("*AdviseMe - AI-powered academic advising assistant*")
