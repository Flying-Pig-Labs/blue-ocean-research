"""
Pytest Configuration and Shared Fixtures - Test Infrastructure Module

Purpose: Provides reusable test fixtures, mock objects, and configuration for the
         entire test suite, ensuring consistent and isolated test environments.

This module serves as the central configuration hub for all pytest tests in the
innovation pipeline. It provides mock implementations of external services,
sample data fixtures, and environment setup to enable fast, reliable unit testing
without requiring real API keys or network access.

Key Components:
1. Environment Variables - Set test API keys and AWS credentials
2. Sample Data Fixtures - Realistic test data for each pipeline stage
3. Mock API Clients - Simulated responses from LLM and cloud services
4. Temporary Files - File system fixtures for I/O testing
5. Test Isolation - Ensures tests don't interfere with each other

Mocking Strategy:
- All external API calls are mocked (Anthropic, OpenAI, Cohere, AWS)
- Mock responses match real API response structures
- Fixtures return consistent, predictable data
- No real network calls or API costs during testing

Fixture Categories:
- Data Fixtures: sample_research_json, sample_analysis_results, etc.
- Mock Clients: mock_anthropic_client, mock_openai_client, etc.
- File System: temp_files for testing I/O operations
- Environment: Automatic setup of required environment variables

Usage:
    @pytest.mark.usefixtures("mock_anthropic_client")
    def test_my_function(mock_anthropic_client):
        # Test code using mocked Anthropic client
        pass

Testing Philosophy:
- Fast execution (no network I/O)
- Deterministic results (no randomness)
- Complete isolation (no side effects)
- Realistic data (matches production formats)

Author: Multi-Step LLM Pipeline Team
Date: January 2025
Version: 2.0.0
"""

import pytest
import json
import os
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Set test environment variables to avoid real API calls
# These are fake keys that allow the code to initialize without errors
# All actual API calls are mocked via fixtures below
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"  # Mock Claude API key
os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"        # Mock AWS access key
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"  # Mock AWS secret
os.environ["S3_BUCKET_NAME"] = "test-bucket"            # Mock S3 bucket name
os.environ["S3_FILE_KEY"] = "test-key.json"             # Mock S3 object key
os.environ["EXA_API_KEY"] = "test-exa-key"              # Mock Exa API key (deprecated)
os.environ["COHERE_API_KEY"] = "test-cohere-key"        # Mock Cohere API key
os.environ["OPENAI_API_KEY"] = "test-openai-key"        # Mock OpenAI API key
os.environ["GITHUB_TOKEN"] = "test-github-token"        # Mock GitHub PAT


@pytest.fixture
def sample_research_json():
    """
    Sample research JSON data matching Color Code Research Hub format.
    Represents the input to Stage 1 (Research Analysis).
    
    Returns:
        dict: Research document with metadata and content sections
    """
    return {
        "metadata": {"title": "Test Research", "date": "2024-08-01"},
        "content": "This is test research content about AI and machine learning trends.",
    }


@pytest.fixture
def sample_analysis_results():
    """
    Sample analysis results from Stage 1 output.
    This markdown format is consumed by Stage 2 (JTBD Research).
    
    Returns:
        str: Markdown-formatted analysis with verticals, personas, and pain points
    """
    return """# Research Analysis Results

## Industry Verticals

- Healthcare AI
- Financial Services
- E-commerce platforms

## User Personas

- Data Scientists
- Business Analysts
- Software Engineers

## Pain Points

- Complex integration processes
- High computational costs
- Lack of explainability

## Solution Types

- Cloud-based ML platforms
- AutoML solutions
- Edge computing
"""


@pytest.fixture
def sample_pain_points():
    """
    Sample pain points extracted from Reddit discussions.
    Input for Stage 3 (Opportunity Zone Clustering).
    
    Returns:
        list: User pain points in first-person format
    """
    return [
        "I can't integrate our ML models with existing systems",
        "The training costs are too high for our budget",
        "We need better model explainability for compliance",
        "Setting up the infrastructure takes too long",
        "Our team lacks ML expertise",
    ]


@pytest.fixture
def sample_opportunity_zones():
    """
    Sample opportunity zones from Stage 3 output.
    Shows clustered pain points with weighted importance.
    Used as input for Stage 4 (Product Idea Generation).
    
    Returns:
        dict: Opportunity zones with clusters and market percentages
    """
    return {
        "metadata": {"timestamp": "2024-08-01T10:00:00", "n_clusters": 3},
        "clusters": {
            "0": {
                "label": "Integration Complexity",
                "job_to_be_done": "When I need to deploy ML, I want seamless integration, so I can focus on business value",
                "severity": "High",
                "size": 15,
            }
        },
        "opportunity_zones": {
            "opportunity_zones": [
                {
                    "name": "Seamless ML Integration",
                    "description": "Eliminate integration friction for ML deployment",
                    "clusters_addressed": ["Integration Complexity"],
                    "importance_percentage": 40,
                    "potential_impact": "High",
                    "implementation_complexity": "Medium",
                },
                {
                    "name": "Cost-Effective Training",
                    "description": "Reduce ML training costs by 80%",
                    "clusters_addressed": ["High Costs"],
                    "importance_percentage": 35,
                    "potential_impact": "High",
                    "implementation_complexity": "High",
                },
            ],
            "rationale": "Focus on integration and cost reduction",
        },
    }


@pytest.fixture
def mock_anthropic_client():
    """
    Mock Anthropic (Claude) API client.
    Simulates responses from Claude Sonnet/Opus models.
    
    Returns:
        MagicMock: Mocked client with create() method returning test content
    """
    mock = MagicMock()
    mock.messages.create.return_value.content = [
        MagicMock(text="This is a mock response from Claude")
    ]
    return mock


@pytest.fixture
def mock_s3_client():
    """
    Mock AWS S3 client for storage operations.
    Simulates reading research documents from S3.
    
    Returns:
        MagicMock: Mocked boto3 S3 client with get_object() method
    """
    mock = MagicMock()
    mock.get_object.return_value = {
        "Body": MagicMock(
            read=lambda: json.dumps({"content": "Test research content"}).encode(
                "utf-8"
            )
        )
    }
    return mock


@pytest.fixture
def mock_exa_client():
    """
    Mock EXA API client (deprecated - replaced by PRAW).
    Kept for backward compatibility with older tests.
    
    Returns:
        MagicMock: Mocked EXA client with search_and_contents() method
    """
    mock = MagicMock()
    mock_result = MagicMock()
    mock_result.url = "https://example.com"
    mock_result.title = "Test Result"
    mock_result.text = "Test content"
    mock_result.highlights = ["highlight 1", "highlight 2"]
    mock.search_and_contents.return_value.results = [mock_result]
    return mock


@pytest.fixture
def mock_cohere_client():
    """
    Mock Cohere API client for embeddings.
    Used in Stage 3 for clustering pain points.
    
    Returns:
        MagicMock: Mocked client with embed() method returning test vectors
    """
    mock = MagicMock()
    # Mock embeddings - returns 3D vectors for clustering
    mock.embed.return_value.embeddings = [[0.1, 0.2, 0.3] for _ in range(5)]
    return mock


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI API client (GPT-4o, GPT-5, o1).
    Simulates responses for idea generation and README creation.
    
    Returns:
        MagicMock: Mocked client with chat.completions.create() method
    """
    mock = MagicMock()
    mock.chat.completions.create.return_value.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {
                        "label": "Test Cluster",
                        "summary": "Test summary",
                        "job_to_be_done": "Test JTBD",
                        "severity": "High",
                    }
                )
            )
        )
    ]
    return mock


@pytest.fixture
def temp_files(tmp_path):
    """
    Create temporary files for I/O testing.
    Provides isolated file system for each test.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        dict: Paths to temporary test files (json, pain_points, markdown)
    """
    files = {}

    # Create test JSON file
    json_file = tmp_path / "test_research.json"
    json_file.write_text(json.dumps({"content": "Test research content"}))
    files["json"] = str(json_file)

    # Create test pain points file
    pain_file = tmp_path / "pain_points.txt"
    pain_file.write_text(
        "\n".join(["I can't do X", "Y is too complex", "Z takes too long"])
    )
    files["pain_points"] = str(pain_file)

    # Create test markdown file
    md_file = tmp_path / "analysis.md"
    md_file.write_text("# Test Analysis\n\nTest content")
    files["markdown"] = str(md_file)

    return files
