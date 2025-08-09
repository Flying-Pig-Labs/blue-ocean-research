#!/bin/bash
"""
Lambda Deployment Script for Multi-Step LLM Pipeline
Builds and deploys all Lambda functions with proper layer management
"""

set -e  # Exit on any error

# Configuration
STACK_NAME="multi-step-llm-pipeline"
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
ENVIRONMENT="${ENVIRONMENT:-production}"
SECRETS_ARN="${SECRETS_ARN:-arn:aws:secretsmanager:us-east-1:*:secret:pipeline-secrets*}"

echo "🚀 Starting Lambda deployment for Multi-Step LLM Pipeline"
echo "   Stack: $STACK_NAME"
echo "   Region: $REGION"
echo "   Profile: $PROFILE"
echo "   Environment: $ENVIRONMENT"
echo ""

# Create layers directory structure
mkdir -p layers/common/python/lib/python3.11/site-packages

echo "📦 Building Lambda layer with dependencies..."

# Install dependencies to layer
pip install -r layers/common/requirements.txt -t layers/common/python/lib/python3.11/site-packages/ --quiet

# Remove unnecessary files to reduce layer size
echo "🧹 Optimizing layer size..."
find layers/common/python -name "*.pyc" -delete
find layers/common/python -name "__pycache__" -type d -exec rm -rf {} +
find layers/common/python -name "*.dist-info" -type d -exec rm -rf {} +
find layers/common/python -name "tests" -type d -exec rm -rf {} +
find layers/common/python -name "test" -type d -exec rm -rf {} +

# Check layer size
layer_size=$(du -sh layers/common/python | cut -f1)
echo "   Layer size: $layer_size"

# Validate SAM template
echo "✅ Validating SAM template..."
sam validate --template lambda-template.yaml

# Build the application
echo "🔨 Building Lambda functions..."
sam build --template lambda-template.yaml --parallel

# Deploy the stack
echo "🚢 Deploying to AWS..."
sam deploy \
    --template-file lambda-template.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --profile $PROFILE \
    --parameter-overrides \
        EnvironmentName=$ENVIRONMENT \
        SecretsManagerArn=$SECRETS_ARN \
    --resolve-s3 \
    --no-confirm-changeset

# Get outputs
echo "📋 Deployment completed! Getting outputs..."
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "✅ Lambda deployment complete!"
echo ""
echo "🔗 API Endpoints:"
api_endpoint=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo "   API Base URL: $api_endpoint"
echo "   Start Pipeline: POST $api_endpoint/start-pipeline"
echo "   Job Status: GET $api_endpoint/status/{jobId}"
echo "   Job Logs: GET $api_endpoint/logs/{jobId}"
echo ""

echo "📝 Example API Usage:"
echo "   # Start a pipeline"
echo "   curl -X POST $api_endpoint/start-pipeline \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{"
echo "       \"input_data\": {"
echo "         \"title\": \"Sample Research\","
echo "         \"content\": \"Market analysis data...\""
echo "       },"
echo "       \"max_jtbds\": 20,"
echo "       \"target_ideas\": 12"
echo "     }'"
echo ""
echo "   # Check job status"
echo "   curl $api_endpoint/status/\$JOB_ID"
echo ""

echo "🎯 Next Steps:"
echo "1. Test the API endpoints with sample data"
echo "2. Monitor CloudWatch logs for execution details"
echo "3. Check S3 bucket for generated pipeline outputs"
echo "4. Review DynamoDB for job tracking data"
echo ""

echo "📊 Resource Summary:"
bucket_name=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
    --output text)

table_name=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --profile $PROFILE \
    --query 'Stacks[0].Outputs[?OutputKey==`JobsTableName`].OutputValue' \
    --output text)

echo "   S3 Bucket: $bucket_name"
echo "   DynamoDB Table: $table_name"
echo "   Lambda Functions: 9 functions deployed"
echo ""

# Optional: Run a quick test
read -p "🧪 Run a quick API test? (y/N): " test_api
if [[ $test_api =~ ^[Yy]$ ]]; then
    echo "🧪 Testing API endpoint..."
    
    test_payload='{
        "input_data": {
            "title": "Test Research Document",
            "content": "This is a test market research document for validating the pipeline deployment. It contains sample data about market trends, customer needs, and competitive landscape analysis.",
            "source": "deployment_test"
        },
        "max_jtbds": 5,
        "target_ideas": 3
    }'
    
    response=$(curl -s -X POST "$api_endpoint/start-pipeline" \
        -H 'Content-Type: application/json' \
        -d "$test_payload")
    
    job_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', 'ERROR'))")
    
    if [[ $job_id != "ERROR" ]]; then
        echo "✅ Pipeline started successfully!"
        echo "   Job ID: $job_id"
        echo "   Check status: curl $api_endpoint/status/$job_id"
        echo "   View logs: curl $api_endpoint/logs/$job_id"
    else
        echo "❌ Test failed. Response:"
        echo "$response"
    fi
fi

echo ""
echo "🎉 Deployment script complete!"