"""
Unit tests for research_analyzer.py
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research_analyzer import ResearchAnalyzer, AnalysisTask

class TestResearchAnalyzer:
    """Test suite for ResearchAnalyzer"""
    
    def test_init_with_valid_credentials(self, mock_anthropic_client, mock_s3_client):
        """Test initialization with valid credentials"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                assert analyzer.api_key == 'test-anthropic-key'
                assert analyzer.client is not None
                assert analyzer.s3_client is not None
    
    def test_init_without_anthropic_key(self):
        """Test initialization fails without Anthropic key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            with pytest.raises(SystemExit):
                ResearchAnalyzer()
    
    def test_pull_from_s3_success(self, mock_s3_client, sample_research_json):
        """Test successful S3 file pull"""
        mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(sample_research_json).encode('utf-8'))
        }
        
        with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
            with patch('research_analyzer.anthropic.Anthropic'):
                analyzer = ResearchAnalyzer()
                result = analyzer.pull_from_s3('test-bucket', 'test-key')
                
                assert result == sample_research_json
                mock_s3_client.get_object.assert_called_once_with(
                    Bucket='test-bucket',
                    Key='test-key'
                )
    
    def test_extract_content_direct(self, mock_anthropic_client, mock_s3_client):
        """Test content extraction from direct content field"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                data = {"content": "Test content"}
                result = analyzer.extract_content(data)
                assert result == "Test content"
    
    def test_extract_content_nested(self, mock_anthropic_client, mock_s3_client):
        """Test content extraction from nested structure"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                data = {"research": {"content": "Nested content"}}
                result = analyzer.extract_content(data)
                assert result == "Nested content"
    
    def test_create_analysis_tasks(self, mock_anthropic_client, mock_s3_client):
        """Test creation of analysis tasks"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                tasks = analyzer.create_analysis_tasks()
                
                assert len(tasks) == 4
                assert tasks[0].name == "Industry Verticals"
                assert tasks[0].model == "sonnet"
                assert tasks[2].name == "Pain Points"
                assert tasks[2].model == "opus"
    
    def test_analyze_with_llm_success(self, mock_anthropic_client, mock_s3_client):
        """Test successful LLM analysis"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis result")]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                task = AnalysisTask(
                    name="Test Task",
                    prompt="Test prompt",
                    model="sonnet"
                )
                
                name, result = analyzer.analyze_with_llm(task, "Test content")
                assert name == "Test Task"
                assert result == "Analysis result"
    
    def test_combine_results(self, mock_anthropic_client, mock_s3_client):
        """Test combining analysis results"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                results = {
                    "Task 1": "Result 1",
                    "Task 2": "Result 2"
                }
                
                combined = analyzer.combine_results(results)
                assert "# Research Analysis Results" in combined
                assert "## Task 1" in combined
                assert "Result 1" in combined
                assert "## Task 2" in combined
                assert "Result 2" in combined
    
    @patch('research_analyzer.ThreadPoolExecutor')
    def test_run_parallel_analysis(self, mock_executor, mock_anthropic_client, mock_s3_client):
        """Test parallel analysis execution"""
        # Mock the executor context manager
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Mock futures
        mock_future = MagicMock()
        mock_future.result.return_value = ("Test Task", "Test Result")
        mock_executor_instance.submit.return_value = mock_future
        
        # Mock as_completed
        with patch('research_analyzer.as_completed', return_value=[mock_future]):
            with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
                with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                    analyzer = ResearchAnalyzer()
                    results = analyzer.run_parallel_analysis("Test content")
                    
                    assert "Test Task" in results
                    assert results["Test Task"] == "Test Result"
    
    def test_save_results(self, tmp_path, mock_anthropic_client, mock_s3_client):
        """Test saving results to file"""
        with patch('research_analyzer.anthropic.Anthropic', return_value=mock_anthropic_client):
            with patch('research_analyzer.boto3.client', return_value=mock_s3_client):
                analyzer = ResearchAnalyzer()
                output_file = tmp_path / "test_results.md"
                
                analyzer.save_results("Test results", str(output_file))
                
                assert output_file.exists()
                assert output_file.read_text() == "Test results"