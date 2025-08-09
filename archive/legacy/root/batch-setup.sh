#!/bin/bash

# AWS Batch Setup Script for Multi-Step LLM Pipeline

PROFILE="mvp"
REGION="us-east-1"
ACCOUNT_ID="984906149037"

echo "Setting up AWS Batch for Multi-Step LLM Pipeline..."

# Create IAM roles for Batch
echo "Creating IAM roles..."

# Create Batch Service Role
aws iam create-role --profile $PROFILE --region $REGION \
  --role-name BatchServiceRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "batch.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || echo "BatchServiceRole already exists"

aws iam attach-role-policy --profile $PROFILE --region $REGION \
  --role-name BatchServiceRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole

# Create ECS Task Execution Role
aws iam create-role --profile $PROFILE --region $REGION \
  --role-name BatchExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || echo "BatchExecutionRole already exists"

aws iam attach-role-policy --profile $PROFILE --region $REGION \
  --role-name BatchExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create Job Role with S3 and Secrets Manager access
aws iam create-role --profile $PROFILE --region $REGION \
  --role-name BatchJobRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || echo "BatchJobRole already exists"

# Create custom policy for job role
aws iam put-role-policy --profile $PROFILE --region $REGION \
  --role-name BatchJobRole \
  --policy-name BatchJobPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::pipeline-data-*/*",
          "arn:aws:s3:::pipeline-data-*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": "secretsmanager:GetSecretValue",
        "Resource": [
          "arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-*",
          "arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-*",
          "arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-*",
          "arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-*",
          "arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-*"
        ]
      }
    ]
  }'

echo "IAM roles created successfully"

# Create Compute Environment
echo "Creating Batch Compute Environment..."
aws batch create-compute-environment --profile $PROFILE --region $REGION \
  --compute-environment-name multi-step-llm-fargate \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type": "FARGATE",
    "maxvCpus": 256,
    "subnets": [
      "subnet-023e0c16f837e81c9",
      "subnet-0e7e33cad2f088743",
      "subnet-01c659c91f652e65a"
    ],
    "securityGroupIds": ["sg-086a073e11cc45e31"]
  }' \
  --service-role arn:aws:iam::${ACCOUNT_ID}:role/BatchServiceRole \
  2>/dev/null || echo "Compute environment already exists"

# Wait for compute environment to be valid
echo "Waiting for compute environment to be ready..."
aws batch describe-compute-environments --profile $PROFILE --region $REGION \
  --compute-environments multi-step-llm-fargate \
  --query 'computeEnvironments[0].status' \
  --output text

# Create Job Queue
echo "Creating Job Queue..."
aws batch create-job-queue --profile $PROFILE --region $REGION \
  --job-queue-name multi-step-llm-queue \
  --state ENABLED \
  --priority 1 \
  --compute-environment-order '[{
    "order": 1,
    "computeEnvironment": "multi-step-llm-fargate"
  }]' \
  2>/dev/null || echo "Job queue already exists"

# Register Job Definition
echo "Registering Job Definition..."
aws batch register-job-definition --profile $PROFILE --region $REGION \
  --job-definition-name multi-step-llm-pipeline \
  --type container \
  --platform-capabilities FARGATE \
  --container-properties file://batch-job-definition.json \
  2>/dev/null || echo "Job definition registered"

echo "AWS Batch setup complete!"
echo ""
echo "To submit a job, run:"
echo "aws batch submit-job --profile $PROFILE --region $REGION \\"
echo "  --job-name test-pipeline-job \\"
echo "  --job-queue multi-step-llm-queue \\"
echo "  --job-definition multi-step-llm-pipeline"