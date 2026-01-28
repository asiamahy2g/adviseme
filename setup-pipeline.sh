#!/bin/bash

# Variables
REPO_NAME="advisor-app"
GITHUB_REPO="https://github.com/asiamahy2g/adviseme.git"  # Updated with your GitHub repo
AWS_ACCOUNT_ID="540738452774"
AWS_REGION="us-east-1"

echo "Setting up CI/CD pipeline for $REPO_NAME..."

# 1. Create ECR repository
echo "Creating ECR repository..."
aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION || echo "Repository may already exist"

# 2. Create CodeBuild service role
echo "Creating CodeBuild service role..."
cat > codebuild-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role --role-name CodeBuildServiceRole --assume-role-policy-document file://codebuild-trust-policy.json || echo "Role may already exist"

# Attach policies to CodeBuild role
aws iam attach-role-policy --role-name CodeBuildServiceRole --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
aws iam attach-role-policy --role-name CodeBuildServiceRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# 3. Create CodePipeline service role
echo "Creating CodePipeline service role..."
cat > codepipeline-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codepipeline.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role --role-name CodePipelineServiceRole --assume-role-policy-document file://codepipeline-trust-policy.json || echo "Role may already exist"

# Create custom policy for CodePipeline
cat > codepipeline-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketVersioning",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecs:DescribeServices",
                "ecs:DescribeTaskDefinition",
                "ecs:DescribeTasks",
                "ecs:ListTasks",
                "ecs:RegisterTaskDefinition",
                "ecs:UpdateService"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy --policy-name CodePipelineCustomPolicy --policy-document file://codepipeline-policy.json || echo "Policy may already exist"
aws iam attach-role-policy --role-name CodePipelineServiceRole --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/CodePipelineCustomPolicy

# 4. Create S3 bucket for artifacts
BUCKET_NAME="advisor-app-pipeline-artifacts-$AWS_ACCOUNT_ID"
echo "Creating S3 bucket for artifacts..."
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION || echo "Bucket may already exist"

# 5. Create CodeBuild project
echo "Creating CodeBuild project..."
cat > codebuild-project.json << EOF
{
  "name": "$REPO_NAME-build",
  "source": {
    "type": "GITHUB",
    "location": "$GITHUB_REPO",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "CODEPIPELINE"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
    "computeType": "BUILD_GENERAL1_MEDIUM",
    "privilegedMode": true,
    "environmentVariables": [
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "$AWS_REGION"
      },
      {
        "name": "AWS_ACCOUNT_ID",
        "value": "$AWS_ACCOUNT_ID"
      },
      {
        "name": "IMAGE_REPO_NAME",
        "value": "$REPO_NAME"
      },
      {
        "name": "IMAGE_TAG",
        "value": "latest"
      }
    ]
  },
  "serviceRole": "arn:aws:iam::$AWS_ACCOUNT_ID:role/CodeBuildServiceRole"
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-project.json

echo "Setup complete!"
echo "Next steps:"
echo "1. Create GitHub repository and push your code"
echo "2. Set up GitHub webhook or use CodePipeline with GitHub integration"
echo "3. Create CodePipeline to connect GitHub -> CodeBuild -> ECS"
echo ""
echo "GitHub repo should be: $GITHUB_REPO"
echo "Update the GITHUB_REPO variable in this script with your actual repo URL"
