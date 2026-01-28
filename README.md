# Advisor App

AI-powered academic advisor application built with Streamlit and deployed on AWS ECS.

## Features
- Academic advising using AI (POE API)
- Streamlit web interface
- PDF file upload and analysis
- AWS ECS deployment with Fargate
- CI/CD pipeline with CodePipeline
- Auto-scaling with 2 replicas

## Authentication

The app uses Streamlit-Authenticator for user authentication.

### Default Login Credentials

| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

### Adding New Users

1. Generate a password hash:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('YOUR_PASSWORD'.encode(), bcrypt.gensalt()).decode())"
```

2. Add the user to `auth_config.yaml`:
```yaml
credentials:
  usernames:
    newuser:
      email: newuser@example.com
      name: New User
      password: <paste_hash_here>
```

### Changing Passwords

1. Generate a new hash using the command above
2. Replace the password hash in `auth_config.yaml`
3. Restart the app

## Local Development

### Prerequisites
- Python 3.9+
- POE API key from https://poe.com/api_key

### Setup
1. Clone the repository:
```bash
git clone https://github.com/asiamahy2g/adviseme.git
cd adviseme
```

2. Create a `.env` file with your POE API key:
```bash
echo "POE_API_KEY=your_poe_api_key_here" > .env
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
streamlit run adviseme.py
```

The app will be available at http://localhost:8501

### Testing Locally
1. Sign in with username `admin` and password `admin123`
2. Upload a student academic progress PDF
3. Upload a course schedule PDF
4. Click "Generate Academic Advice"
5. The AI will analyze both documents and provide personalized recommendations

## AWS ECS Deployment

### Production URLs
- http://54.198.108.158:8501 (Primary)
- Additional replicas available via load balancing

### Architecture
- **GitHub**: Source code repository
- **CodePipeline**: CI/CD automation (Source → Build → Deploy)
- **CodeBuild**: Docker image building and ECR push
- **ECR**: Container image registry
- **ECS Fargate**: Serverless container hosting
- **Parameter Store**: Secure API key storage

### Deployment Process
The app automatically deploys when changes are pushed to the main branch:

1. **Push changes**:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

2. **Pipeline stages**:
   - **Source**: Pulls code from GitHub
   - **Build**: Creates Docker image and pushes to ECR
   - **Deploy**: Updates ECS service with new image

3. **Monitor deployment**:
   - Pipeline: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/advisor-app-pipeline/view
   - ECS Service: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/advisor-app-cluster/services

### Manual ECS Deployment (if needed)
```bash
# Build and push Docker image
make deploy

# Or run individual commands
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 540738452774.dkr.ecr.us-east-1.amazonaws.com
docker build -t advisor-app .
docker tag advisor-app:latest 540738452774.dkr.ecr.us-east-1.amazonaws.com/advisor-app:latest
docker push 540738452774.dkr.ecr.us-east-1.amazonaws.com/advisor-app:latest
```

## Configuration

### Environment Variables
- `POE_API_KEY`: Your POE API key for AI functionality

### AWS Resources
- **ECS Cluster**: advisor-app-cluster
- **ECS Service**: advisor-app-service (2 replicas)
- **ECR Repository**: advisor-app
- **Parameter Store**: /advisor-app/poe-api-key
- **Security Group**: advisor-app-sg (port 8501)

## Usage
1. Access the app via the production URLs or run locally
2. Upload student's academic progress PDF
3. Upload course schedule PDF for the target semester
4. Click "Generate Academic Advice"
5. Receive AI-generated email with course recommendations

The AI acts as a seasoned Animal Science professor at UAPB, analyzing academic progress and recommending 15-18 credit hours for the Spring 2026 semester.

## Development
- **Framework**: Streamlit
- **AI Integration**: POE API with direct HTTP requests
- **File Processing**: Base64 encoding for PDF uploads
- **Deployment**: Docker containerization with AWS ECS Fargate
