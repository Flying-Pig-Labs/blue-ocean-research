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
	@echo "  make run          - Run pipeline with test fixtures (headless)"
	@echo "  make run-verbose  - Run pipeline with verbose output"
	@echo "  make run-interactive - Run pipeline in interactive mode"
	@echo "  make test         - Run test suite"
	@echo "  make clean        - Remove generated files and cache"
	@echo "  make clean-all    - Remove venv, generated files, and cache"
	@echo "  make deps         - Update requirements.txt with current packages"
	@echo "  make check-env    - Verify environment variables are set"
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
	$(VENV_ACTIVATE) && pip install --upgrade pip
	$(VENV_ACTIVATE) && pip install -r requirements.txt
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
	@echo "  - EXA_API_KEY"
	@echo "  - COHERE_API_KEY"
	@echo "  - GITHUB_TOKEN (optional)"
	@echo "  - PERPLEXITY_KEY"

# Run pipeline with test fixtures (headless mode)
.PHONY: run
run: install check-env
	@echo "=========================================="
	@echo "Running pipeline with test fixtures"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Headless (automatic)"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT)

# Run pipeline with verbose output
.PHONY: run-verbose
run-verbose: install check-env
	@echo "=========================================="
	@echo "Running pipeline with verbose output"
	@echo "Input: $(TEST_INPUT)"
	@echo "Mode: Headless with verbose logging"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT) --verbose

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
	$(VENV_ACTIVATE) && pip freeze > requirements.txt
	@echo "requirements.txt updated!"

# Run individual pipeline stages
.PHONY: stage1
stage1: install check-env
	@echo "Running Stage 1: Research Analyzer..."
	$(VENV_ACTIVATE) && $(PYTHON) research_analyzer.py --input $(TEST_INPUT)

.PHONY: stage2
stage2: install check-env
	@echo "Running Stage 2: Jobs Researcher..."
	$(VENV_ACTIVATE) && $(PYTHON) jobs_researcher.py

.PHONY: stage3
stage3: install check-env
	@echo "Running Stage 3: Cluster JTBD..."
	$(VENV_ACTIVATE) && $(PYTHON) cluster_jtbd.py pain_points.txt

.PHONY: stage4
stage4: install check-env
	@echo "Running Stage 4: Value Curve Mapper..."
	$(VENV_ACTIVATE) && $(PYTHON) value_curve_mapper.py opportunity_zones.json

.PHONY: stage5
stage5: install check-env
	@echo "Running Stage 5: Product Idea Generator..."
	$(VENV_ACTIVATE) && $(PYTHON) product_idea_generator.py

.PHONY: stage6
stage6: install check-env
	@echo "Running Stage 6: Idea Consolidator..."
	$(VENV_ACTIVATE) && $(PYTHON) idea_consolidator.py

# Run pipeline with GitHub integration
.PHONY: run-github
run-github: install check-env
	@test -n "$$GITHUB_TOKEN" || (echo "ERROR: GITHUB_TOKEN required for GitHub integration" && exit 1)
	@echo "=========================================="
	@echo "Running pipeline with GitHub integration"
	@echo "Input: $(TEST_INPUT)"
	@echo "Output: GitHub repository will be created"
	@echo "=========================================="
	$(VENV_ACTIVATE) && $(PYTHON) $(PIPELINE_SCRIPT) --input $(TEST_INPUT) --github --repo-name "innovation-$$(date +%Y%m%d-%H%M%S)"

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
.PHONY: deploy
deploy:
	@echo "Building and deploying to AWS..."
	sam build
	sam deploy --guided

.PHONY: deploy-no-confirm
deploy-no-confirm:
	@echo "Building and deploying to AWS (no confirmation)..."
	sam build
	sam deploy --no-confirm-changeset

# Default is to install and run
.DEFAULT_GOAL := all