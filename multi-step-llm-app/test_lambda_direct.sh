#!/bin/bash

# Test Lambda function directly with AWS CLI
FUNCTION_NAME="pipeline-research-analyzer-dev"
PAYLOAD='{
  "jobId": "test-direct-123",
  "s3Bucket": "multi-step-llm-dev-984906149037", 
  "s3InputKey": "test/research_data.json",
  "s3OutputKey": "test/output.json"
}'

echo "Testing Lambda function: $FUNCTION_NAME"
echo "Payload: $PAYLOAD"
echo ""

# First, create a test file in S3
echo '{"content": "Test research content about technology."}' > /tmp/test_research.json
aws s3 cp /tmp/test_research.json s3://multi-step-llm-dev-984906149037/test/research_data.json

# Invoke the Lambda function
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload "$PAYLOAD" \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda_response.json

echo "Lambda response:"
cat /tmp/lambda_response.json | python -m json.tool

# Check if output was created in S3
echo ""
echo "Checking S3 for output..."
aws s3 ls s3://multi-step-llm-dev-984906149037/test/