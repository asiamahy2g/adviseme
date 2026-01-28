#!/bin/bash

# AWS ECS Deployment Script for Advisor App

set -e

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="advisor-app-cluster"
SERVICE_NAME="advisor-app-service"
TASK_DEFINITION="advisor-app-task"
ECR_REPOSITORY="advisor-app"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Deploying Advisor App to ECS..."
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Build and push Docker image
echo "Building and pushing Docker image..."
make deploy AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID

# Update task definition with correct account ID
sed "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" ecs-task-definition.json > ecs-task-definition-updated.json

# Register new task definition
echo "Registering task definition..."
aws ecs register-task-definition --cli-input-json file://ecs-task-definition-updated.json --region $AWS_REGION

# Create ECS cluster if it doesn't exist
echo "Creating ECS cluster..."
aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION || \
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION

# Update service or create if it doesn't exist
echo "Updating ECS service..."
aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION && \
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_DEFINITION --region $AWS_REGION || \
echo "Service doesn't exist. Create it manually through AWS Console with the registered task definition."

echo "Deployment completed!"
echo "Task Definition: $TASK_DEFINITION"
echo "ECR Repository: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

# Cleanup
rm -f ecs-task-definition-updated.json
