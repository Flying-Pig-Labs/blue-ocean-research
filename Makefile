# Multi-Step LLM Pipeline Makefile
# Builds dependencies and runs the pipeline with test fixtures

# Python interpreter
PYTHON := python3

# Virtual environment
VENV := venv
VENV_ACTIVATE := . $(VENV)/bin/activate

# AWS Configuration
AWS_PROFILE := mvp
AWS_REGION := us-east-1
export AWS_PROFILE := $(AWS_PROFILE)
export AWS_REGION := $(AWS_REGION)

# Test input file
TEST_INPUT := tests/fixtures/sample_research.json

# Pipeline script
PIPELINE_SCRIPT := run_pipeline.py

# Default target
.PHONY: all
all: install run

# Help target
.PHONY: help
help:
	@echo "Multi-Step LLM Pipeline Makefile"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make install      - Create venv and install dependencies"
	@echo "  make run          - Run pipeline with cache (fast testing)"
	@echo "  make run-fresh    - Run pipeline with fresh data (no cache)"
	@echo "  make run-verbose  - Run pipeline with verbose output + cache"
	@echo "  make run-interactive - Run pipeline in interactive mode"
	@echo "  make test         - Run test suite"
	@echo "  make clean        - Remove generated files and cache"
	@echo "  make clean-all    - Remove venv, generated files, and cache"
	@echo "  make deps         - Update requirements.txt with current packages"
	@echo "  make check-env    - Verify AWS credentials are configured"
	@echo ""
	@echo "Individual stages (PRAW-based flow):"
	@echo "  make stage1       - Research Analyzer"
	@echo "  make stage2       - JTBD + Reddit (PRAW)"
	@echo "  make stage3       - Opportunity Zone Discovery"
	@echo "  make stage4       - Product Idea Generator"
	@echo "  make stage5       - Idea Consolidator"
	@echo "  make stage6       - GitHub Integration"
	@echo ""
	@echo "Quick start:"
	@echo "  make              - Install dependencies and run pipeline"

# Create virtual environment
$(VENV):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)

# Install dependencies
.PHONY: install
install: $(VENV)
	@echo "Installing dependencies..."
	$(VENV_ACTIVATE) && python3 -m pip install --upgrade pip
	$(VENV_ACTIVATE) && python3 -m pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

# Test AWS secrets access
.PHONY: test-secrets
test-secrets:
	@echo "Testing AWS Secrets Manager access..."
	@echo "Using AWS Profile: $(AWS_PROFILE)"
	@echo "AWS Region: $(AWS_REGION)"
	@echo ""
	@echo "Attempting to list secrets..."
	@aws secretsmanager list-secrets --region $(AWS_REGION) --profile $(AWS_PROFILE) --query "SecretList[?contains(Name, 'key') || contains(Name, 'token')].Name" --output table || (echo "ERROR: Cannot access AWS Secrets Manager. Check your AWS credentials." && exit 1)
	@echo ""
	@echo "✓ AWS Secrets Manager access confirmed!"

# Check if required environment variables are set (now checks AWS instead)
.PHONY: check-env
check-env:
	@echo "Pipeline will load secrets from AWS Secrets Manager"
	@echo "AWS Profile: $(AWS_PROFILE)"
	@echo "AWS Region: $(AWS_REGION)"
	@echo ""
	@echo "Testing AWS access..."
	@aws sts get-caller-identity --profile $(AWS_PROFILE) --region $(AWS_REGION) > /dev/null 2>&1 || (echo "ERROR: Cannot authenticate with AWS. Check your AWS credentials for profile '$(AWS_PROFILE)'" && exit 1)
	@echo "✓ AWS authentication successful"
	@echo ""
	@echo "The pipeline will load these secrets from AWS:"
	@echo "  - ANTHROPIC_API_KEY"
	@echo "  - OPENAI_API_KEY"
	@echo "  - COHERE_API_KEY"
	@echo "  - GITHUB_TOKEN (optional)"
	@echo "  - PERPLEXITY_KEY"
	@echo "  Note: EXA_API_KEY no longer needed (using PRAW for Reddit)"

# Run pipeline with test fixtures (headless mode) - using cache for faster testing
.PHONY: run
run: install check-env
	@echo "=========================================="
	@echo "Running pipeline with test fixtures (cached)"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Headless (automatic) with cache"
	@echo "Note: GitHub repo creation is SKIPPED when using cache"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT) --use-cache

# Run pipeline with fresh data (no cache)
.PHONY: run-fresh
run-fresh: install check-env
	@echo "=========================================="
	@echo "Running pipeline with fresh data (no cache)"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Headless (automatic) - fresh data"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT)

# Run pipeline with verbose output
.PHONY: run-verbose
run-verbose: install check-env
	@echo "=========================================="
	@echo "Running pipeline with verbose output (cached)"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Headless with verbose logging + cache"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT) --verbose --use-cache

# Run pipeline in interactive mode
.PHONY: run-interactive
run-interactive: install check-env
	@echo "=========================================="
	@echo "Running pipeline in interactive mode"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Interactive (requires user input)"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT) --interactive

# Run tests
.PHONY: test
test: install
	@echo "Running test suite..."
	$(VENV_ACTIVATE) && $(PYTHON) -m pytest tests/ -v

# Run tests with coverage
.PHONY: test-coverage
test-coverage: install
	@echo "Running tests with coverage..."
	$(VENV_ACTIVATE) && $(PYTHON) -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@rm -f *.json *.txt *.md 2>/dev/null || true
	@rm -f lambda_function.zip 2>/dev/null || true
	@rm -rf __pycache__ .pytest_cache htmlcov 2>/dev/null || true
	@rm -rf logs/* 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

# Clean everything including venv
.PHONY: clean-all
clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@rm -rf .aws-sam 2>/dev/null || true
	@echo "Full clean complete!"

# Update requirements.txt with current packages
.PHONY: deps
deps: $(VENV)
	@echo "Updating requirements.txt..."
	$(VENV_ACTIVATE) && python3 -m pip freeze > requirements.txt
	@echo "requirements.txt updated!"

# Run individual pipeline stages (PRAW-based flow)
.PHONY: stage1
stage1: install check-env
	@echo "Running Stage 1: Research Analyzer..."
	$(VENV_ACTIVATE) && $(PYTHON) research_analyzer.py --local $(TEST_INPUT)

.PHONY: stage2
stage2: install check-env
	@echo "Running Stage 2: JTBD + Reddit (PRAW)..."
	$(VENV_ACTIVATE) && $(PYTHON) jobs_to_reddit.py

.PHONY: stage3
stage3: install check-env
	@echo "Running Stage 3: Opportunity Zone Discovery..."
	$(VENV_ACTIVATE) && $(PYTHON) opportunity_zone_analyzer.py

.PHONY: stage4
stage4: install check-env
	@echo "Running Stage 4: Product Idea Generator..."
	$(VENV_ACTIVATE) && $(PYTHON) product_idea_generator.py --input opportunity_zones.json

.PHONY: stage5
stage5: install check-env
	@echo "Running Stage 5: Idea Consolidator..."
	$(VENV_ACTIVATE) && $(PYTHON) idea_consolidator.py

.PHONY: stage6
stage6: install check-env
	@echo "Running Stage 6: GitHub Integration..."
	$(VENV_ACTIVATE) && $(PYTHON) product_idea_generator.py --github

# Run pipeline with GitHub integration (fresh data + repo creation)
.PHONY: run-github
run-github: install check-env
	@echo "=========================================="
	@echo "Running FULL pipeline with GitHub repository creation"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Fresh data generation + GitHub repo"
	@echo "Output: GitHub repository will be created"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT)

# Run cleanup script
.PHONY: cleanup
cleanup: install
	@echo "Running pipeline cleanup..."
	$(VENV_ACTIVATE) && $(PYTHON) cleanup_pipeline.py --force

# Display pipeline status
.PHONY: status
status:
	@echo "Pipeline Output Files:"
	@echo "======================"
	@ls -la *.json *.txt *.md 2>/dev/null || echo "No output files found"
	@echo ""
	@echo "Log Files:"
	@echo "=========="
	@ls -la logs/ 2>/dev/null || echo "No log files found"

# Development shortcuts
.PHONY: dev
dev: install
	@echo "Entering development shell..."
	@$(VENV_ACTIVATE) && exec $$SHELL

.PHONY: format
format: install
	@echo "Formatting code..."
	$(VENV_ACTIVATE) && black *.py tests/ src/ --line-length 120

.PHONY: lint
lint: install
	@echo "Linting code..."
	$(VENV_ACTIVATE) && flake8 *.py tests/ src/ --max-line-length 120

# AWS Lambda deployment
.PHONY: deploy-sam
deploy-sam:
	@echo "Building and deploying to AWS..."
	sam build
	sam deploy --guided

.PHONY: deploy-no-confirm
deploy-no-confirm:
	@echo "Building and deploying to AWS (no confirmation)..."
	sam build
	sam deploy --no-confirm-changeset

# ==========================================
# AWS Batch Deployment Commands
# ==========================================

# AWS Account configuration
AWS_ACCOUNT_ID := 984906149037
AWS_REGION := us-east-1
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPOSITORY := multi-step-llm-pipeline
IMAGE_TAG := latest
FULL_IMAGE_NAME := $(ECR_REGISTRY)/$(ECR_REPOSITORY):$(IMAGE_TAG)

# Build Docker image for Batch
.PHONY: docker-build
docker-build:
	@echo "=========================================="
	@echo "Building Docker image for AWS Batch"
	@echo "Image: $(ECR_REPOSITORY):$(IMAGE_TAG)"
	@echo "=========================================="
	docker build --platform linux/amd64 --progress=plain -t $(ECR_REPOSITORY):$(IMAGE_TAG) .
	@echo "✅ Docker image built successfully"

# Login to ECR
.PHONY: docker-login
docker-login:
	@echo "=========================================="
	@echo "Logging into AWS ECR"
	@echo "Registry: $(ECR_REGISTRY)"
	@echo "=========================================="
	@# Create temporary Docker config to avoid macOS credential store issues
	@mkdir -p ./docker-tmp
	@echo '{"auths":{}}' > ./docker-tmp/config.json
	@aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) | \
		docker --config ./docker-tmp login --username AWS --password-stdin $(ECR_REGISTRY)
	@echo "✅ Successfully logged into ECR"

# Create ECR repository if it doesn't exist
.PHONY: ecr-create
ecr-create:
	@echo "=========================================="
	@echo "Creating ECR repository (if needed)"
	@echo "Repository: $(ECR_REPOSITORY)"
	@echo "=========================================="
	@aws ecr describe-repositories --repository-names $(ECR_REPOSITORY) --region $(AWS_REGION) --profile $(AWS_PROFILE) 2>/dev/null || \
		aws ecr create-repository --repository-name $(ECR_REPOSITORY) --region $(AWS_REGION) --profile $(AWS_PROFILE)
	@echo "✅ ECR repository ready"

# Push Docker image to ECR
.PHONY: docker-push
docker-push: docker-login
	@echo "=========================================="
	@echo "Pushing Docker image to ECR"
	@echo "Image: $(FULL_IMAGE_NAME)"
	@echo "=========================================="
	docker tag $(ECR_REPOSITORY):$(IMAGE_TAG) $(FULL_IMAGE_NAME)
	docker --config ./docker-tmp push $(FULL_IMAGE_NAME)
	@echo "✅ Docker image pushed successfully"
	@echo "Image URI: $(FULL_IMAGE_NAME)"
	@# Clean up temporary Docker config
	@rm -rf ./docker-tmp

# Complete Docker workflow: build and push (VERBOSE)
.PHONY: docker
docker: ecr-create docker-build docker-push
	@echo "=========================================="
	@echo "✅ Docker image built and pushed to ECR"
	@echo "Image: $(FULL_IMAGE_NAME)"
	@echo "=========================================="

# Install CDK dependencies
.PHONY: cdk-install
cdk-install:
	@echo "=========================================="
	@echo "Installing CDK dependencies"
	@echo "=========================================="
	@if [ ! -d "infrastructure/.venv" ]; then \
		cd infrastructure && python3 -m venv .venv; \
	fi
	@cd infrastructure && \
		. .venv/bin/activate && \
		.venv/bin/python -m pip install --upgrade pip && \
		.venv/bin/python -m pip install -r requirements-cdk.txt
	@echo "✅ CDK dependencies installed"

# Bootstrap CDK (first time only)
.PHONY: cdk-bootstrap
cdk-bootstrap: cdk-install
	@echo "=========================================="
	@echo "Bootstrapping CDK"
	@echo "Account: $(AWS_ACCOUNT_ID)"
	@echo "Region: $(AWS_REGION)"
	@echo "=========================================="
	@cd infrastructure && \
		. .venv/bin/activate && \
		cdk bootstrap aws://$(AWS_ACCOUNT_ID)/$(AWS_REGION) --profile $(AWS_PROFILE)
	@echo "✅ CDK bootstrap complete"

# Preview CDK changes
.PHONY: cdk-diff
cdk-diff: cdk-install
	@echo "=========================================="
	@echo "Previewing CDK stack changes"
	@echo "=========================================="
	@cd infrastructure && \
		. .venv/bin/activate && \
		CDK_DEFAULT_ACCOUNT=$(AWS_ACCOUNT_ID) \
		CDK_DEFAULT_REGION=$(AWS_REGION) \
		cdk diff --profile $(AWS_PROFILE)

# Deploy CDK stack
.PHONY: cdk-deploy
cdk-deploy: cdk-install
	@echo "=========================================="
	@echo "Deploying CDK stack"
	@echo "Account: $(AWS_ACCOUNT_ID)"
	@echo "Region: $(AWS_REGION)"
	@echo "=========================================="
	@cd infrastructure && \
		. .venv/bin/activate && \
		CDK_DEFAULT_ACCOUNT=$(AWS_ACCOUNT_ID) \
		CDK_DEFAULT_REGION=$(AWS_REGION) \
		cdk deploy --require-approval never --profile $(AWS_PROFILE)
	@echo "✅ CDK stack deployed successfully"

# Complete deployment: Docker + CDK
.PHONY: deploy
deploy: docker cdk-deploy
	@echo "=========================================="
	@echo "✅ Complete deployment successful!"
	@echo "Docker image: $(FULL_IMAGE_NAME)"
	@echo "CDK stack: MultiStepLLMBatch-dev"
	@echo "=========================================="
	@echo ""
	@echo "Next steps:"
	@echo "1. Upload research to S3 and register in DynamoDB"
	@echo "2. Call API Gateway /submit endpoint with research ID"
	@echo "3. Monitor logs via /logs/{researchId} endpoint"

# Destroy CDK stack
.PHONY: cdk-destroy
cdk-destroy: cdk-install
	@echo "=========================================="
	@echo "⚠️  DESTROYING CDK stack"
	@echo "This will delete all AWS resources!"
	@echo "=========================================="
	@read -p "Are you sure? Type 'yes' to continue: " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		cd infrastructure && \
		. .venv/bin/activate && \
		CDK_DEFAULT_ACCOUNT=$(AWS_ACCOUNT_ID) \
		CDK_DEFAULT_REGION=$(AWS_REGION) \
		cdk destroy --force --profile $(AWS_PROFILE); \
		echo "✅ CDK stack destroyed"; \
	else \
		echo "❌ Destruction cancelled"; \
	fi

# Show current Docker image info
.PHONY: docker-info
docker-info:
	@echo "=========================================="
	@echo "Docker Image Information"
	@echo "=========================================="
	@echo "Local image: $(ECR_REPOSITORY):$(IMAGE_TAG)"
	@echo "ECR URI: $(FULL_IMAGE_NAME)"
	@echo ""
	@echo "Local images:"
	@docker images $(ECR_REPOSITORY) --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
	@echo ""
	@echo "ECR images:"
	@aws ecr describe-images --repository-name $(ECR_REPOSITORY) \
		--region $(AWS_REGION) --profile $(AWS_PROFILE) \
		--query 'imageDetails[*].[imageTags[0],imageSizeInBytes,imagePushedAt]' \
		--output table 2>/dev/null || echo "No images in ECR yet"

# Test Batch job locally with Docker
.PHONY: docker-test
docker-test: docker-build
	@echo "=========================================="
	@echo "Testing Docker container locally"
	@echo "=========================================="
	docker run --rm \
		-e ANTHROPIC_API_KEY \
		-e OPENAI_API_KEY \
		-e COHERE_API_KEY \
		-e GITHUB_TOKEN \
		-e PERPLEXITY_KEY \
		-e AWS_PROFILE=$(AWS_PROFILE) \
		-v ~/.aws:/root/.aws:ro \
		$(ECR_REPOSITORY):$(IMAGE_TAG) \
		--input tests/fixtures/sample_research.json \
		--skip-github

# View Batch job logs
.PHONY: batch-logs
batch-logs:
	@echo "=========================================="
	@echo "Viewing recent Batch job logs"
	@echo "=========================================="
	@aws logs tail /aws/batch/job/multi-step-llm \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--since 10m \
		--follow

# Submit a test Batch job
.PHONY: batch-submit
batch-submit:
	@echo "=========================================="
	@echo "Submitting test Batch job"
	@echo "=========================================="
	@aws batch submit-job \
		--job-name "test-pipeline-$$(date +%Y%m%d-%H%M%S)" \
		--job-queue multi-step-llm-queue \
		--job-definition multi-step-llm-pipeline \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--container-overrides '{"environment":[{"name":"S3_INPUT_KEY","value":"tests/fixtures/sample_research.json"}]}'

# Show Batch job status
.PHONY: batch-status
batch-status:
	@echo "=========================================="
	@echo "Recent Batch jobs"
	@echo "=========================================="
	@aws batch list-jobs \
		--job-queue multi-step-llm-queue \
		--job-status RUNNABLE \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--output table
	@aws batch list-jobs \
		--job-queue multi-step-llm-queue \
		--job-status RUNNING \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--output table
	@aws batch list-jobs \
		--job-queue multi-step-llm-queue \
		--job-status SUCCEEDED \
		--max-results 5 \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--output table
	@aws batch list-jobs \
		--job-queue multi-step-llm-queue \
		--job-status FAILED \
		--max-results 5 \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--output table

# Default is to install and run
.DEFAULT_GOAL := all