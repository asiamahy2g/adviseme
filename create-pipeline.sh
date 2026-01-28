#!/bin/bash

# Variables - UPDATE THESE
GITHUB_OWNER="YOUR_GITHUB_USERNAME"  # Replace with your GitHub username
GITHUB_REPO="advisor-app"
GITHUB_TOKEN="YOUR_GITHUB_TOKEN"     # Replace with your GitHub personal access token
AWS_ACCOUNT_ID="540738452774"
AWS_REGION="us-east-1"
BUCKET_NAME="advisor-app-pipeline-artifacts-$AWS_ACCOUNT_ID"

echo "Creating complete CodePipeline..."

# Create the pipeline
cat > pipeline.json << EOF
{
  "pipeline": {
    "name": "advisor-app-pipeline",
    "roleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/CodePipelineServiceRole",
    "artifactStore": {
      "type": "S3",
      "location": "$BUCKET_NAME"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [
          {
            "name": "Source",
            "actionTypeId": {
              "category": "Source",
              "owner": "ThirdParty",
              "provider": "GitHub",
              "version": "1"
            },
            "configuration": {
              "Owner": "$GITHUB_OWNER",
              "Repo": "$GITHUB_REPO",
              "Branch": "main",
              "OAuthToken": "$GITHUB_TOKEN"
            },
            "outputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Build",
        "actions": [
          {
            "name": "Build",
            "actionTypeId": {
              "category": "Build",
              "owner": "AWS",
              "provider": "CodeBuild",
              "version": "1"
            },
            "configuration": {
              "ProjectName": "advisor-app-build"
            },
            "inputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ],
            "outputArtifacts": [
              {
                "name": "BuildOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Deploy",
        "actions": [
          {
            "name": "Deploy",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "ECS",
              "version": "1"
            },
            "configuration": {
              "ClusterName": "advisor-app-cluster",
              "ServiceName": "advisor-app-service",
              "FileName": "imagedefinitions.json"
            },
            "inputArtifacts": [
              {
                "name": "BuildOutput"
              }
            ]
          }
        ]
      }
    ]
  }
}
EOF

aws codepipeline create-pipeline --cli-input-json file://pipeline.json

echo "Pipeline created successfully!"
echo ""
echo "IMPORTANT: Update the following in create-pipeline.sh:"
echo "1. GITHUB_OWNER with your GitHub username"
echo "2. GITHUB_TOKEN with your GitHub personal access token"
echo ""
echo "To get a GitHub token:"
echo "1. Go to GitHub Settings > Developer settings > Personal access tokens"
echo "2. Generate new token with 'repo' and 'admin:repo_hook' permissions"
