#!/bin/bash

# Setup script for GitHub OIDC provider and IAM role
# This script creates the necessary AWS resources for GitHub Actions to assume an IAM role

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="github-oidc-flying-pig-labs"
REGION="us-east-1"
GITHUB_ORG="Flying-Pig-Labs"
AWS_PROFILE="${AWS_PROFILE:-mvp}"  # Use mvp profile by default

echo -e "${GREEN}GitHub OIDC Setup for AWS${NC}"
echo "========================================"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "GitHub Organization: $GITHUB_ORG"
echo "Authorized Repositories:"
echo "  - blue-ocean-research (main branch)"
echo "  - blue-ocean-ideation (main branch)"
echo "  - color-code-research-hub (main branch)"
echo "AWS Profile: $AWS_PROFILE"
echo "========================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
    echo -e "${RED}Unable to authenticate with AWS. Please check your credentials.${NC}"
    exit 1
fi

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
echo -e "${GREEN}AWS Account ID: $ACCOUNT_ID${NC}"

# Check if OIDC provider already exists
echo -e "${YELLOW}Checking for existing OIDC provider...${NC}"
OIDC_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn $OIDC_ARN --profile $AWS_PROFILE &> /dev/null; then
    echo -e "${GREEN}OIDC provider already exists${NC}"
    OIDC_EXISTS="true"
else
    echo -e "${YELLOW}OIDC provider does not exist, will be created${NC}"
    OIDC_EXISTS="false"
fi

# Deploy CloudFormation stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"

TEMPLATE_FILE=".github/oidc-setup.yaml"
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}CloudFormation template not found at $TEMPLATE_FILE${NC}"
    exit 1
fi

# Build parameters
PARAMETERS="ParameterKey=GitHubOrg,ParameterValue=$GITHUB_ORG"
if [ "$OIDC_EXISTS" = "true" ]; then
    PARAMETERS="$PARAMETERS ParameterKey=OIDCProviderArn,ParameterValue=$OIDC_ARN"
fi

# Deploy the stack
aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --parameter-overrides $PARAMETERS \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --profile $AWS_PROFILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Stack deployed successfully!${NC}"
else
    echo -e "${RED}Stack deployment failed${NC}"
    exit 1
fi

# Get the role ARN from stack outputs
ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" \
    --output text \
    --region $REGION \
    --profile $AWS_PROFILE)

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "IAM Role ARN: ${ROLE_ARN}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. The OIDC provider and IAM role have been created"
echo "2. GitHub Actions will automatically use the role via OIDC"
echo "3. No need to store AWS credentials in GitHub Secrets!"
echo ""
echo -e "${YELLOW}The workflow is configured to use:${NC}"
echo "   Role: ${ROLE_ARN}"
echo ""
echo -e "${YELLOW}To get your API keys from AWS Secrets Manager:${NC}"
echo "   aws secretsmanager get-secret-value --secret-id your-secret-name --profile $AWS_PROFILE"
echo ""
echo -e "${GREEN}You still need to add these as GitHub Secrets:${NC}"
echo "   - ANTHROPIC_API_KEY (from AWS Secrets Manager)"
echo "   - OPENAI_API_KEY (from AWS Secrets Manager)"
echo "   - GH_PAT (your GitHub Personal Access Token)"
echo ""