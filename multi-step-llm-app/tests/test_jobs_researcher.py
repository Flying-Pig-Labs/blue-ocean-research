"""
Unit tests for jobs_researcher.py
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs_researcher import JobsResearcher

class TestJobsResearcher:
    """Test suite for JobsResearcher"""
    
    def test_init_with_valid_credentials(self, mock_exa_client, mock_anthropic_client):
        """Test initialization with valid credentials"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                assert researcher.exa_api_key == 'test-exa-key'
                assert researcher.exa is not None
                assert researcher.anthropic_client is not None
    
    def test_init_without_exa_key(self):
        """Test initialization fails without EXA key"""
        with patch.dict(os.environ, {'EXA_API_KEY': ''}):
            with pytest.raises(SystemExit):
                JobsResearcher()
    
    def test_load_analysis_results_success(self, temp_files, mock_exa_client, mock_anthropic_client):
        """Test loading analysis results from file"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                content = researcher.load_analysis_results(temp_files['markdown'])
                assert "# Test Analysis" in content
    
    def test_extract_key_elements(self, sample_analysis_results, mock_exa_client, mock_anthropic_client):
        """Test extracting key elements from analysis"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                elements = researcher.extract_key_elements(sample_analysis_results)
                
                assert len(elements['verticals']) > 0
                assert len(elements['personas']) > 0
                assert len(elements['pain_points']) > 0
                assert len(elements['solution_types']) > 0
    
    def test_construct_search_queries(self, mock_exa_client, mock_anthropic_client):
        """Test construction of search queries"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                elements = {
                    'verticals': ['Healthcare', 'Finance'],
                    'personas': ['Data Scientists', 'Analysts'],
                    'pain_points': ['High costs', 'Complex integration'],
                    'solution_types': ['Cloud ML', 'AutoML']
                }
                
                queries = researcher.construct_search_queries(elements)
                assert len(queries) > 0
                assert any(q['type'] == 'reddit' for q in queries)
                assert any(q['type'] == 'reviews' for q in queries)
                assert any(q['type'] == 'interviews' for q in queries)
    
    def test_search_with_exa_success(self, mock_exa_client, mock_anthropic_client):
        """Test successful EXA search"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                queries = [
                    {"query": "test query", "type": "reddit", "focus": "test"}
                ]
                
                results = researcher.search_with_exa(queries)
                assert 'reddit' in results
                assert len(results['reddit']) > 0
                assert results['reddit'][0]['url'] == "https://example.com"
    
    def test_extract_jobs_to_be_done(self, mock_exa_client, mock_anthropic_client):
        """Test JTBD extraction from search results"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                search_results = {
                    'reddit': [{
                        'snippet': 'I need to find a better way to manage my data',
                        'url': 'https://reddit.com/r/test',
                        'title': 'Test Post',
                        'focus': 'test'
                    }]
                }
                
                jobs = researcher.extract_jobs_to_be_done(search_results, "test context")
                assert len(jobs) > 0
                assert jobs[0]['pattern'] == 'i need to'
    
    def test_synthesize_jtbd_with_claude(self, mock_exa_client, mock_anthropic_client):
        """Test JTBD synthesis with Claude"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="| Job Statement | Source | Frequency | Pain |\n|---|---|---|---|\n| Test job | Reddit | Daily | High |")
        ]
        
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                jobs = [{'job_context': 'test context', 'pattern': 'i need to'}]
                elements = {'verticals': ['Test'], 'personas': ['User'], 'pain_points': ['Pain 1']}
                
                result = researcher._synthesize_jtbd_with_claude(jobs, elements)
                assert "Job Statement" in result
                assert "Test job" in result
    
    def test_structure_jtbd_table(self, mock_exa_client, mock_anthropic_client):
        """Test fallback JTBD table structure"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                jobs = [{
                    'job_context': 'I need to manage data better',
                    'pattern': 'i need to',
                    'source': 'reddit',
                    'focus': 'data_management'
                }]
                elements = {}
                
                result = researcher._structure_jtbd_table(jobs, elements)
                assert "| Job Statement |" in result
                assert "I need to manage data better" in result
    
    def test_generate_jtbd_report(self, mock_exa_client, mock_anthropic_client):
        """Test JTBD report generation"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                jobs = [{
                    'source': 'reddit',
                    'url': 'https://test.com',
                    'title': 'Test',
                    'job_context': 'test context',
                    'focus': 'test',
                    'pattern': 'i need to'
                }]
                search_results = {'reddit': [{'title': 'Test', 'url': 'https://test.com'}]}
                elements = {'verticals': ['Test'], 'personas': ['User'], 'pain_points': ['Pain 1']}
                
                report = researcher.generate_jtbd_report(jobs, search_results, elements)
                assert "# Jobs-to-be-Done Research Report" in report
                assert "Executive Summary" in report
                assert "Key Findings by Source" in report
    
    def test_extract_pain_points(self, mock_exa_client, mock_anthropic_client):
        """Test pain point extraction"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                jobs = [{
                    'job_context': 'I am frustrated with the slow performance'
                }]
                search_results = {
                    'reddit': [{
                        'snippet': 'The system is difficult to use and crashes often'
                    }]
                }
                
                pain_points = researcher.extract_pain_points(jobs, search_results)
                assert len(pain_points) > 0
                assert any('frustrated' in p or 'difficult' in p for p in pain_points)
    
    def test_save_pain_points(self, tmp_path, mock_exa_client, mock_anthropic_client):
        """Test saving pain points to file"""
        with patch('jobs_researcher.Exa', return_value=mock_exa_client):
            with patch('jobs_researcher.anthropic.Anthropic', return_value=mock_anthropic_client):
                researcher = JobsResearcher()
                pain_points = ["Pain 1", "Pain 2", "Pain 3"]
                output_file = tmp_path / "test_pains.txt"
                
                researcher.save_pain_points(pain_points, str(output_file))
                
                assert output_file.exists()
                content = output_file.read_text()
                assert "Pain 1\n" in content
                assert "Pain 2\n" in content
                assert "Pain 3\n" in content