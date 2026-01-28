# Advisor App

AI-powered academic advisor application built with Streamlit and deployed on AWS ECS.

## Features
- Academic advising using AI
- Streamlit web interface
- AWS ECS deployment
- CI/CD pipeline with CodePipeline
- Auto-scaling with 2 replicas

## Local Development
```bash
pip install -r requirements.txt
streamlit run adviseme.py
```

## Deployment
The app is automatically deployed to AWS ECS via CodePipeline when changes are pushed to main branch.
