#!/bin/bash
set -e

# Multi-Step LLM Pipeline - Deployment Script
# Usage: ./scripts/deploy.sh [environment] [options]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
AWS_PROFILE="mvp"
AWS_REGION="us-east-1"
FORCE_DEPLOY=false
SKIP_BUILD=false
SKIP_TESTS=false
DRY_RUN=false

# Help function
show_help() {
    echo -e "${BLUE}Multi-Step LLM Pipeline - Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Environments:"
    echo "  development (default) - Development environment"
    echo "  staging              - Staging environment"
    echo "  production           - Production environment"
    echo ""
    echo "Options:"
    echo "  --aws-profile PROFILE  AWS profile to use (default: mvp)"
    echo "  --aws-region REGION    AWS region (default: us-east-1)"
    echo "  --force-deploy         Deploy even if no changes detected"
    echo "  --skip-build          Skip SAM build step"
    echo "  --skip-tests          Skip running tests"
    echo "  --dry-run             Show what would be deployed without deploying"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy to development"
    echo "  $0 staging                   # Deploy to staging"
    echo "  $0 production --force-deploy # Force deploy to production"
    echo "  $0 staging --dry-run         # Show staging deployment plan"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        development|staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        --aws-profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --aws-region)
            AWS_REGION="$2"
            shift 2
            ;;
        --force-deploy)
            FORCE_DEPLOY=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Set environment variables
export AWS_PROFILE="$AWS_PROFILE"
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_REGION="$AWS_REGION"

# Determine stack name based on environment
case $ENVIRONMENT in
    development)
        STACK_NAME="multi-step-llm-pipeline-dev"
        ;;
    staging)
        STACK_NAME="multi-step-llm-pipeline-staging"
        ;;
    production)
        STACK_NAME="multi-step-llm-pipeline-prod"
        ;;
esac

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Multi-Step LLM Pipeline Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Stack Name:  ${YELLOW}$STACK_NAME${NC}"
echo -e "AWS Profile: ${YELLOW}$AWS_PROFILE${NC}"
echo -e "AWS Region:  ${YELLOW}$AWS_REGION${NC}"
echo -e "Force Deploy: ${YELLOW}$FORCE_DEPLOY${NC}"
echo -e "Dry Run:     ${YELLOW}$DRY_RUN${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}SAM CLI is not installed. Please install it first.${NC}"
    echo "Install with: pip install aws-sam-cli"
    exit 1
fi

# Check AWS credentials
echo "Testing AWS credentials..."
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo -e "${RED}Cannot authenticate with AWS using profile '$AWS_PROFILE'${NC}"
    echo "Please configure your AWS credentials"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
echo -e "AWS Account: ${GREEN}$ACCOUNT_ID${NC}"

# Check if we're in the right directory
if [[ ! -f "run_pipeline.py" ]]; then
    echo -e "${RED}This script must be run from the project root directory${NC}"
    exit 1
fi

# Create infrastructure directory if it doesn't exist
if [[ ! -d "infrastructure" ]]; then
    echo -e "${RED}Infrastructure directory not found${NC}"
    exit 1
fi

cd infrastructure

# Check for changes (unless force deploy is set)
if [[ "$FORCE_DEPLOY" == "false" ]]; then
    echo -e "${BLUE}Checking for changes...${NC}"
    
    # Simple change detection - check if template or source files have changed
    if [[ -f "../.last_deploy_$ENVIRONMENT" ]]; then
        LAST_DEPLOY=$(cat "../.last_deploy_$ENVIRONMENT")
        CURRENT_HASH=$(find ../src ../lambda_handler.py ../requirements.txt template.yaml -type f -exec md5sum {} \; 2>/dev/null | md5sum | cut -d' ' -f1)
        
        if [[ "$LAST_DEPLOY" == "$CURRENT_HASH" ]]; then
            echo -e "${YELLOW}No changes detected since last deployment${NC}"
            echo "Use --force-deploy to deploy anyway"
            exit 0
        fi
    fi
fi

# Run tests unless skipped
if [[ "$SKIP_TESTS" == "false" ]]; then
    echo -e "${BLUE}Running tests...${NC}"
    cd ..
    
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    python -m pytest tests/ -v --tb=short
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Tests failed! Aborting deployment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Tests passed!${NC}"
    cd infrastructure
fi

# Validate SAM template
echo -e "${BLUE}Validating SAM template...${NC}"
if ! sam validate --template template.yaml; then
    echo -e "${RED}SAM template validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}Template is valid${NC}"

# Build the application unless skipped
if [[ "$SKIP_BUILD" == "false" ]]; then
    echo -e "${BLUE}Building SAM application...${NC}"
    
    # Prepare Lambda layers
    echo "Preparing Lambda layers..."
    mkdir -p layers/dependencies/python
    mkdir -p layers/utils/python
    
    # Dependencies layer
    pip install -r ../requirements.txt -t layers/dependencies/python/
    
    # Utils layer
    cp -r ../src/ layers/utils/python/
    cp ../llm_config.yaml layers/utils/python/
    cp ../config_loader.py layers/utils/python/
    cp ../prompt_loader.py layers/utils/python/
    
    # Create Lambda source directories
    echo "Preparing Lambda function sources..."
    mkdir -p src/lambda/{starter,status,logs,cancel,stages,cleanup}
    
    # Copy handlers
    cp ../lambda_handler.py src/lambda/starter/handler.py
    cp ../lambda_handler.py src/lambda/status/handler.py
    cp ../lambda_handler.py src/lambda/logs/handler.py
    cp ../lambda_handler.py src/lambda/cancel/handler.py
    cp ../lambda_handler.py src/lambda/cleanup/handler.py
    
    # Create stage-specific handlers
    cp ../research_analyzer.py src/lambda/stages/research_analysis.py
    cp ../jobs_researcher.py src/lambda/stages/jtbd_research.py
    cp ../cluster_jtbd.py src/lambda/stages/clustering.py
    cp ../value_curve_mapper.py src/lambda/stages/value_curve_mapping.py
    cp ../product_idea_generator.py src/lambda/stages/product_idea_generation.py
    cp ../idea_consolidator.py src/lambda/stages/idea_consolidation.py
    cp ../github_integration.py src/lambda/stages/github_integration.py
    
    # Build
    if ! sam build --config-env "$ENVIRONMENT"; then
        echo -e "${RED}SAM build failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Build completed successfully${NC}"
fi

# Deploy or show deployment plan
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${BLUE}Showing deployment plan (dry run)...${NC}"
    
    sam deploy \
        --config-env "$ENVIRONMENT" \
        --no-execute-changeset \
        --parameter-overrides "EnvironmentName=$ENVIRONMENT"
        
    echo -e "${YELLOW}This was a dry run. No resources were actually deployed.${NC}"
else
    echo -e "${BLUE}Deploying to $ENVIRONMENT...${NC}"
    
    # Deploy with appropriate confirmation settings
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Production requires confirmation unless forced
        CONFIRM_FLAG="--confirm-changeset"
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            CONFIRM_FLAG="--no-confirm-changeset"
        fi
    else
        CONFIRM_FLAG="--no-confirm-changeset"
    fi
    
    if sam deploy \
        --config-env "$ENVIRONMENT" \
        $CONFIRM_FLAG \
        --parameter-overrides "EnvironmentName=$ENVIRONMENT"; then
        
        echo -e "${GREEN}Deployment successful!${NC}"
        
        # Update secrets if needed
        echo -e "${BLUE}Updating secrets...${NC}"
        
        SECRET_NAME="$STACK_NAME-secrets"
        
        if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null 2>&1; then
            echo "Secrets Manager secret exists: $SECRET_NAME"
            echo -e "${YELLOW}Please manually update the secret with your API keys:${NC}"
            echo "aws secretsmanager put-secret-value --secret-id $SECRET_NAME --secret-string '{\"ANTHROPIC_API_KEY\":\"your-key\",\"OPENAI_API_KEY\":\"your-key\",\"EXA_API_KEY\":\"your-key\",\"COHERE_API_KEY\":\"your-key\",\"GITHUB_TOKEN\":\"your-token\",\"PERPLEXITY_KEY\":\"your-key\"}'"
        else
            echo -e "${YELLOW}Secret not found. It should be created by the CloudFormation stack.${NC}"
        fi
        
        # Get stack outputs
        echo -e "${BLUE}Deployment Summary:${NC}"
        echo "==================="
        
        aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --profile "$AWS_PROFILE" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[].[OutputKey,OutputValue,Description]' \
            --output table
        
        # Save deployment hash
        CURRENT_HASH=$(find ../src ../lambda_handler.py ../requirements.txt template.yaml -type f -exec md5sum {} \; 2>/dev/null | md5sum | cut -d' ' -f1)
        echo "$CURRENT_HASH" > "../.last_deploy_$ENVIRONMENT"
        
        echo -e "${GREEN}Deployment completed successfully!${NC}"
        
        # Get API endpoint for testing
        API_ENDPOINT=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --profile "$AWS_PROFILE" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
            --output text)
        
        if [[ -n "$API_ENDPOINT" ]]; then
            echo ""
            echo -e "${BLUE}Test your deployment:${NC}"
            echo "API Endpoint: $API_ENDPOINT"
            echo ""
            echo "Test command:"
            echo "curl -X POST '$API_ENDPOINT/pipeline/start' \\"
            echo "  -H 'Content-Type: application/json' \\"
            echo "  -d '{\"researchDocId\":\"test-$(date +%s)\",\"username\":\"testuser\"}'"
            echo ""
            
            # Dashboard URL
            DASHBOARD_URL=$(aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --profile "$AWS_PROFILE" \
                --region "$AWS_REGION" \
                --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
                --output text)
            
            if [[ -n "$DASHBOARD_URL" ]]; then
                echo "Dashboard: $DASHBOARD_URL"
            fi
        fi
        
    else
        echo -e "${RED}Deployment failed!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Script completed successfully!${NC}"