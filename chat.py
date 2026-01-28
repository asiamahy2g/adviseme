# pip install openai python-dotenv
import os, openai, base64
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(
    api_key=os.getenv("POE_API_KEY"),
    base_url="https://api.poe.com/v1",
)

def encode_file(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Academic advisor prompt
system_prompt = """You are a seasoned professor and an animal science professor at UAPB. A student sent you an email inquiring about their academic progress and the courses they need to complete in Spring 2026. I have attached his academic progress. Go through it and make a list of the courses she/he needs to take. I have attached the course schedule for spring 2026. Based on the student's needs, schedule their classes for him. She/he will need 15 - 18 credits. Let's assume she/he passes all current courses in the Fall 2025. Prepare an email for her/him, first telling him about his academic progress and also the classes he needs to register for in the spring semester. Make it clear, concise and straight to the point."""

# Check for required files
progress_file = "Michai_Tate_(100293224) (1).pdf"
schedule_file = "Class_Schedule_UAPB SPRING 2026.pdf"

if not os.path.exists(progress_file):
    print(f"Error: {progress_file} not found. Please add the student's academic progress file.")
    exit(1)

if not os.path.exists(schedule_file):
    print(f"Error: {schedule_file} not found. Please add the Spring 2026 course schedule file.")
    exit(1)

# Encode files
progress_data = encode_file(progress_file)
schedule_data = encode_file(schedule_file)

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
                    "filename": "academic_progress.pdf",
                    "file_data": f"data:application/pdf;base64,{progress_data}"
                }
            },
            {
                "type": "file",
                "file": {
                    "filename": "spring_2026_schedule.pdf",
                    "file_data": f"data:application/pdf;base64,{schedule_data}"
                }
            }
        ]
    }
]

print("Analyzing student's academic progress and generating course recommendations...\n")

response = client.chat.completions.create(
    model="Claude-Sonnet-4",
    messages=messages,
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
