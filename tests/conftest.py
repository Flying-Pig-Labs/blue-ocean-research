"""
Shared pytest fixtures and configuration
"""

import pytest
import json
import os
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["S3_FILE_KEY"] = "test-key.json"
os.environ["EXA_API_KEY"] = "test-exa-key"
os.environ["COHERE_API_KEY"] = "test-cohere-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"


@pytest.fixture
def sample_research_json():
    """Sample research JSON data"""
    return {
        "metadata": {"title": "Test Research", "date": "2024-08-01"},
        "content": "This is test research content about AI and machine learning trends.",
    }


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results markdown"""
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
    """Sample pain points for clustering"""
    return [
        "I can't integrate our ML models with existing systems",
        "The training costs are too high for our budget",
        "We need better model explainability for compliance",
        "Setting up the infrastructure takes too long",
        "Our team lacks ML expertise",
    ]


@pytest.fixture
def sample_opportunity_zones():
    """Sample opportunity zones from clustering"""
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
    """Mock Anthropic client"""
    mock = MagicMock()
    mock.messages.create.return_value.content = [
        MagicMock(text="This is a mock response from Claude")
    ]
    return mock


@pytest.fixture
def mock_s3_client():
    """Mock S3 client"""
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
    """Mock EXA client"""
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
    """Mock Cohere client"""
    mock = MagicMock()
    # Mock embeddings
    mock.embed.return_value.embeddings = [[0.1, 0.2, 0.3] for _ in range(5)]
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
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
    """Create temporary files for testing"""
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
