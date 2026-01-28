#!/bin/bash

# Destroy Advisor Infrastructure Script
# This script will tear down all AWS resources for the advisor app

set -e

echo "🔥 Starting infrastructure destruction..."
echo "⚠️  This will delete ALL advisor app resources!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Destruction cancelled"
    exit 1
fi

REGION="us-east-1"
CLUSTER_NAME="advisor-app-cluster"
SERVICE_NAME="advisor-app-service"
ALB_NAME="advisor-app-alb"
TARGET_GROUP_NAME="advisor-app-targets"
ECR_REPO="advisor-app"
PIPELINE_NAME="advisor-app-pipeline"
BUILD_PROJECT="advisor-app-build"
SECURITY_GROUP_NAME="advisor-app-sg"

echo "🗑️  Deleting DNS record..."
aws route53 change-resource-record-sets \
    --hosted-zone-id Z0995769MLUT7T40EUTT \
    --change-batch '{
        "Changes": [{
            "Action": "DELETE",
            "ResourceRecordSet": {
                "Name": "adviseme.maryvilleinc.org",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "advisor-app-alb-112188915.us-east-1.elb.amazonaws.com",
                    "EvaluateTargetHealth": true,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        }]
    }' || echo "⚠️  DNS record not found or already deleted"

echo "🛑 Stopping ECS service..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --desired-count 0 \
    --region $REGION || echo "⚠️  Service not found"

echo "⏳ Waiting for tasks to stop..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION || echo "⚠️  Service wait failed"

echo "🗑️  Deleting ECS service..."
aws ecs delete-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --region $REGION || echo "⚠️  Service deletion failed"

echo "🗑️  Deleting load balancer listeners..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --names $ALB_NAME \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text 2>/dev/null || echo "None")

if [ "$ALB_ARN" != "None" ]; then
    # Delete HTTPS listener (port 443)
    HTTPS_LISTENER=$(aws elbv2 describe-listeners \
        --load-balancer-arn $ALB_ARN \
        --region $REGION \
        --query 'Listeners[?Port==`443`].ListenerArn' \
        --output text 2>/dev/null || echo "None")
    
    if [ "$HTTPS_LISTENER" != "None" ]; then
        aws elbv2 delete-listener \
            --listener-arn $HTTPS_LISTENER \
            --region $REGION || echo "⚠️  HTTPS listener deletion failed"
    fi
    
    # Delete HTTP listener (port 80)
    HTTP_LISTENER=$(aws elbv2 describe-listeners \
        --load-balancer-arn $ALB_ARN \
        --region $REGION \
        --query 'Listeners[?Port==`80`].ListenerArn' \
        --output text 2>/dev/null || echo "None")
    
    if [ "$HTTP_LISTENER" != "None" ]; then
        aws elbv2 delete-listener \
            --listener-arn $HTTP_LISTENER \
            --region $REGION || echo "⚠️  HTTP listener deletion failed"
    fi
fi

echo "🗑️  Deleting load balancer..."
if [ "$ALB_ARN" != "None" ]; then
    aws elbv2 delete-load-balancer \
        --load-balancer-arn $ALB_ARN \
        --region $REGION
    echo "⏳ Waiting for load balancer to delete..."
    sleep 30
fi

echo "🗑️  Deleting target group..."
TG_ARN=$(aws elbv2 describe-target-groups \
    --names $TARGET_GROUP_NAME \
    --region $REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || echo "None")

if [ "$TG_ARN" != "None" ]; then
    aws elbv2 delete-target-group \
        --target-group-arn $TG_ARN \
        --region $REGION
fi

echo "🗑️  Deleting ECS cluster..."
aws ecs delete-cluster \
    --cluster $CLUSTER_NAME \
    --region $REGION || echo "⚠️  Cluster deletion failed"

echo "🗑️  Deleting task definitions..."
TASK_DEF_ARNS=$(aws ecs list-task-definitions \
    --family-prefix advisor-app-task \
    --region $REGION \
    --query 'taskDefinitionArns' \
    --output text)

for arn in $TASK_DEF_ARNS; do
    aws ecs deregister-task-definition \
        --task-definition $arn \
        --region $REGION || echo "⚠️  Task definition deregistration failed"
done

echo "🗑️  Deleting CodePipeline..."
aws codepipeline delete-pipeline \
    --name $PIPELINE_NAME \
    --region $REGION || echo "⚠️  Pipeline deletion failed"

echo "🗑️  Deleting CodeBuild project..."
aws codebuild delete-project \
    --name $BUILD_PROJECT \
    --region $REGION || echo "⚠️  Build project deletion failed"

echo "🗑️  Deleting ECR repository..."
aws ecr delete-repository \
    --repository-name $ECR_REPO \
    --force \
    --region $REGION || echo "⚠️  ECR repository deletion failed"

echo "🗑️  Deleting S3 artifacts bucket..."
BUCKET_NAME=$(aws s3 ls | grep advisor-app-pipeline-artifacts | awk '{print $3}')
if [ ! -z "$BUCKET_NAME" ]; then
    aws s3 rm s3://$BUCKET_NAME --recursive
    aws s3 rb s3://$BUCKET_NAME
fi

echo "🗑️  Deleting Parameter Store parameter..."
aws ssm delete-parameter \
    --name "/advisor-app/poe-api-key" \
    --region $REGION || echo "⚠️  Parameter deletion failed"

echo "🗑️  Deleting security group rules..."
SG_ID=$(aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" != "None" ]; then
    # Remove port 80 rule
    aws ec2 revoke-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION || echo "⚠️  Port 80 rule removal failed"
    
    # Remove port 443 rule
    aws ec2 revoke-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region $REGION || echo "⚠️  Port 443 rule removal failed"
    
    # Remove port 8501 rule
    aws ec2 revoke-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --region $REGION || echo "⚠️  Port 8501 rule removal failed"
    
    # Delete security group
    aws ec2 delete-security-group \
        --group-id $SG_ID \
        --region $REGION || echo "⚠️  Security group deletion failed"
fi

echo "🗑️  Deleting IAM roles and policies..."
aws iam detach-role-policy \
    --role-name CodeBuildServiceRole \
    --policy-arn arn:aws:iam::540738452774:policy/CodeBuildS3Policy || echo "⚠️  Policy detach failed"

aws iam delete-policy \
    --policy-arn arn:aws:iam::540738452774:policy/CodeBuildS3Policy || echo "⚠️  Policy deletion failed"

aws iam delete-role \
    --role-name CodeBuildServiceRole || echo "⚠️  Role deletion failed"

echo "✅ Infrastructure destruction complete!"
echo "💰 You are no longer being charged for advisor app resources"
echo ""
echo "📝 Summary of deleted resources:"
echo "   - ECS Cluster and Service"
echo "   - Application Load Balancer (with HTTPS/HTTP listeners)"
echo "   - Target Group"
echo "   - Task Definitions"
echo "   - CodePipeline and CodeBuild"
echo "   - ECR Repository"
echo "   - S3 Artifacts Bucket"
echo "   - Parameter Store Parameter"
echo "   - Security Group (with ports 80, 443, 8501)"
echo "   - IAM Roles and Policies"
echo "   - DNS Record (HTTPS-enabled)"
echo ""
echo "🔄 To redeploy, run the setup scripts again"
