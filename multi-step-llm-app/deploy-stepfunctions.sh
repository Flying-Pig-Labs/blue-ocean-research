#!/bin/bash

# Deploy Multi-Step LLM Pipeline with Step Functions Orchestration
# This script automates the complete deployment process

set -e  # Exit on any error

# Configuration
STACK_NAME="multi-step-llm-pipeline-sf"
ENVIRONMENT="production"
AWS_REGION="us-east-1"
SECRET_NAME="pipeline-secrets"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        log_error "SAM CLI is not installed. Please install SAM CLI first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check required files
    local required_files=(
        "stepfunctions-template.yaml"
        "stepfunctions_api.py"
        "pipeline_metrics.py"
        "requirements.txt"
        "research_analyzer.py"
        "jobs_researcher.py"
        "cluster_jtbd.py"
        "value_curve_mapper.py"
        "product_idea_generator.py"
        "idea_consolidator.py"
        "github_integration.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "All prerequisites satisfied"
}

create_secrets() {
    log_info "Setting up AWS Secrets Manager..."
    
    # Check if secret already exists
    if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" &> /dev/null; then
        log_warning "Secret '$SECRET_NAME' already exists. Skipping creation."
        return 0
    fi
    
    log_info "Creating new secret: $SECRET_NAME"
    echo "Please enter your API keys (press Enter to skip if already set):"
    
    # Collect API keys
    read -p "Anthropic API Key: " ANTHROPIC_KEY
    read -p "OpenAI API Key: " OPENAI_KEY
    read -p "EXA API Key: " EXA_KEY
    read -p "Cohere API Key: " COHERE_KEY
    read -p "GitHub Token: " GITHUB_TOKEN
    read -p "Perplexity API Key (optional): " PERPLEXITY_KEY
    
    # Create secret JSON
    SECRET_JSON=$(cat <<EOF
{
    "ANTHROPIC_API_KEY": "${ANTHROPIC_KEY}",
    "OPENAI_API_KEY": "${OPENAI_KEY}",
    "EXA_API_KEY": "${EXA_KEY}",
    "COHERE_API_KEY": "${COHERE_KEY}",
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "PERPLEXITY_KEY": "${PERPLEXITY_KEY}"
}
EOF
    )
    
    # Create the secret
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "API keys for Multi-Step LLM Pipeline" \
        --secret-string "$SECRET_JSON" \
        --region "$AWS_REGION"
    
    log_success "Secret created successfully"
}

prepare_lambda_code() {
    log_info "Preparing Lambda function code..."
    
    # Create a temporary build directory
    BUILD_DIR="./build"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Copy Python files
    cp *.py "$BUILD_DIR/"
    
    # Copy requirements and other necessary files
    if [[ -f "requirements.txt" ]]; then
        cp requirements.txt "$BUILD_DIR/"
    fi
    
    # Copy prompts directory if it exists
    if [[ -d "prompts" ]]; then
        cp -r prompts "$BUILD_DIR/"
    fi
    
    # Install dependencies in the build directory
    if [[ -f "$BUILD_DIR/requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        pip install -r "$BUILD_DIR/requirements.txt" -t "$BUILD_DIR/" --quiet
    fi
    
    log_success "Lambda code prepared"
}

validate_template() {
    log_info "Validating CloudFormation template..."
    
    aws cloudformation validate-template \
        --template-body file://stepfunctions-template.yaml \
        --region "$AWS_REGION" > /dev/null
    
    log_success "Template validation passed"
}

deploy_infrastructure() {
    log_info "Building and deploying infrastructure with SAM..."
    
    # Build the SAM application
    sam build \
        --template-file stepfunctions-template.yaml \
        --build-dir .aws-sam/build \
        --source-dir .
    
    log_info "Deploying CloudFormation stack: $STACK_NAME"
    
    # Deploy with SAM
    sam deploy \
        --template-file stepfunctions-template.yaml \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --parameter-overrides EnvironmentName="$ENVIRONMENT" \
        --region "$AWS_REGION" \
        --resolve-s3 \
        --no-fail-on-empty-changeset
    
    log_success "Infrastructure deployed successfully"
}

get_stack_outputs() {
    log_info "Retrieving stack outputs..."
    
    local outputs
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output json 2>/dev/null || echo "[]")
    
    if [[ "$outputs" == "[]" ]]; then
        log_warning "No stack outputs found or stack doesn't exist yet"
        return 1
    fi
    
    echo "$outputs" | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"'
    return 0
}

test_deployment() {
    log_info "Testing deployment..."
    
    # Get API endpoint from stack outputs
    local api_endpoint
    api_endpoint=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`PipelineApiEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$api_endpoint" ]]; then
        log_warning "Could not retrieve API endpoint for testing"
        return 1
    fi
    
    log_info "Testing API endpoint: $api_endpoint"
    
    # Create a test payload
    local test_payload=$(cat <<EOF
{
    "input": {
        "researchData": "This is a test research document for deployment validation.",
        "createGitHubRepo": false,
        "testMode": true
    },
    "name": "deployment-test-$(date +%s)"
}
EOF
    )
    
    # Test the API endpoint
    local response
    response=$(curl -s -X POST "$api_endpoint/pipeline/start" \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        -w "%{http_code}" \
        -o /tmp/api_response.json)
    
    local http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        log_success "API test successful"
        cat /tmp/api_response.json | jq .
        return 0
    else
        log_error "API test failed with HTTP code: $http_code"
        cat /tmp/api_response.json
        return 1
    fi
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create CloudWatch dashboard
    local dashboard_body=$(cat <<EOF
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "MultiStepLLMPipeline", "PipelineStarted" ],
                    [ ".", "PipelineCompleted" ],
                    [ ".", "PipelineFailed" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "Pipeline Executions",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "MultiStepLLMPipeline", "StageCompleted", "Stage", "1" ],
                    [ "...", "2" ],
                    [ "...", "3" ],
                    [ "...", "4" ],
                    [ "...", "5" ],
                    [ "...", "6" ],
                    [ "...", "7" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "Stage Completions",
                "period": 300
            }
        }
    ]
}
EOF
    )
    
    aws cloudwatch put-dashboard \
        --dashboard-name "MultiStepLLMPipeline-$ENVIRONMENT" \
        --dashboard-body "$dashboard_body" \
        --region "$AWS_REGION" &> /dev/null || log_warning "Failed to create CloudWatch dashboard"
    
    log_success "Monitoring setup complete"
}

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."
    
    rm -rf ./build
    rm -f /tmp/api_response.json
    
    log_success "Cleanup complete"
}

print_summary() {
    echo ""
    echo "=================================="
    echo "🚀 DEPLOYMENT COMPLETE"
    echo "=================================="
    echo ""
    
    log_info "Stack Name: $STACK_NAME"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $AWS_REGION"
    echo ""
    
    log_info "Stack Outputs:"
    if get_stack_outputs; then
        echo ""
    fi
    
    echo "📊 Next Steps:"
    echo "1. Check CloudWatch dashboard: MultiStepLLMPipeline-$ENVIRONMENT"
    echo "2. Monitor EventBridge events in the custom bus: pipeline-events-$ENVIRONMENT"
    echo "3. Test pipeline execution using the API endpoint"
    echo "4. Review Step Functions console for execution visualization"
    echo ""
    
    echo "📚 Resources:"
    echo "- CloudFormation Stack: https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/stackinfo?stackId=$STACK_NAME"
    echo "- Step Functions: https://console.aws.amazon.com/states/home?region=$AWS_REGION#/statemachines"
    echo "- API Gateway: https://console.aws.amazon.com/apigateway/home?region=$AWS_REGION"
    echo "- CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=MultiStepLLMPipeline-$ENVIRONMENT"
    echo ""
}

main() {
    echo "🚀 Multi-Step LLM Pipeline Deployment Script"
    echo "============================================="
    echo ""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --stack-name)
                STACK_NAME="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --region)
                AWS_REGION="$2"
                shift 2
                ;;
            --secret-name)
                SECRET_NAME="$2"
                shift 2
                ;;
            --skip-secrets)
                SKIP_SECRETS=true
                shift
                ;;
            --skip-test)
                SKIP_TEST=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --stack-name NAME     CloudFormation stack name (default: multi-step-llm-pipeline-sf)"
                echo "  --environment ENV     Environment name (default: production)"
                echo "  --region REGION       AWS region (default: us-east-1)"
                echo "  --secret-name NAME    Secrets Manager secret name (default: pipeline-secrets)"
                echo "  --skip-secrets        Skip secrets creation"
                echo "  --skip-test           Skip deployment test"
                echo "  --help                Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_prerequisites
    
    if [[ "$SKIP_SECRETS" != "true" ]]; then
        create_secrets
    fi
    
    prepare_lambda_code
    validate_template
    deploy_infrastructure
    setup_monitoring
    
    if [[ "$SKIP_TEST" != "true" ]]; then
        test_deployment
    fi
    
    cleanup_temp_files
    print_summary
    
    log_success "Deployment completed successfully! 🎉"
}

# Handle script interruption
trap cleanup_temp_files EXIT

# Run main function
main "$@"