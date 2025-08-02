"""
Unit tests for product_idea_generator.py
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_idea_generator import ProductIdeaGenerator

class TestProductIdeaGenerator:
    """Test suite for ProductIdeaGenerator"""
    
    def test_init_with_valid_credentials(self, mock_openai_client, mock_anthropic_client):
        """Test initialization with valid credentials"""
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                assert generator.openai_api_key == 'test-openai-key'
                assert generator.anthropic_api_key == 'test-anthropic-key'
                assert generator.model_o1 == 'o1-preview'
                assert generator.model_opus == 'claude-3-opus-20240229'
    
    def test_init_without_openai_key(self):
        """Test initialization fails without OpenAI key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with pytest.raises(SystemExit):
                ProductIdeaGenerator()
    
    def test_init_without_anthropic_key(self):
        """Test initialization fails without Anthropic key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            with pytest.raises(SystemExit):
                ProductIdeaGenerator()
    
    def test_load_value_curves_success(self, tmp_path, sample_value_curves, 
                                     mock_openai_client, mock_anthropic_client):
        """Test loading value curves from JSON"""
        curves_file = tmp_path / "curves.json"
        curves_file.write_text(json.dumps(sample_value_curves))
        
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                data = generator.load_value_curves(str(curves_file))
                
                assert 'analyses' in data
                assert len(data['analyses']) > 0
    
    def test_generate_errc_grid(self, mock_openai_client, mock_anthropic_client):
        """Test ERRC grid generation with OpenAI o1"""
        mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ELIMINATE: Feature X\nREDUCE: Cost Y\nRAISE: Quality Z\nCREATE: Innovation A"))
        ]
        
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                zone_analysis = {
                    'zone': {'name': 'Test Zone', 'importance_percentage': 50},
                    'industry_norms': 'Test norms',
                    'engineering_spectrum': 'Test spectrum',
                    'competitive_data': {'search_results': []}
                }
                
                errc = generator.generate_errc_grid(zone_analysis)
                
                assert "ELIMINATE" in errc
                assert "REDUCE" in errc
                assert "RAISE" in errc
                assert "CREATE" in errc
    
    def test_generate_product_ideas(self, mock_openai_client, mock_anthropic_client):
        """Test product idea generation with Claude Opus"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="1. Product Alpha: Revolutionary solution\n2. Product Beta: Next-gen platform")
        ]
        
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                errc_grid = "Test ERRC grid"
                
                ideas = generator.generate_product_ideas("Test Zone", errc_grid)
                
                assert isinstance(ideas, list)
                assert len(ideas) == 10  # Should always return 10 ideas
    
    def test_scope_viability(self, mock_openai_client, mock_anthropic_client):
        """Test viability assessment with Claude Opus"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="1. Product Alpha: Overall Viability Score: 8/10\n2. Product Beta: Overall Viability Score: 6/10")
        ]
        
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                ideas = [
                    {'name': 'Product Alpha', 'value_proposition': 'Test'},
                    {'name': 'Product Beta', 'value_proposition': 'Test'}
                ]
                
                scored_ideas = generator.scope_viability(ideas, "Test Zone")
                
                assert len(scored_ideas) == 2
                assert all('viability_score' in idea for idea in scored_ideas)
                assert scored_ideas[0]['viability_score'] >= 1
                assert scored_ideas[0]['viability_score'] <= 10
    
    def test_filter_ideas_by_percentage(self, mock_openai_client, mock_anthropic_client):
        """Test percentage-based idea filtering"""
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                ideas = [
                    {'name': 'Idea 1', 'viability_score': 9},
                    {'name': 'Idea 2', 'viability_score': 7},
                    {'name': 'Idea 3', 'viability_score': 5},
                    {'name': 'Idea 4', 'viability_score': 3},
                    {'name': 'Idea 5', 'viability_score': 8},
                    {'name': 'Idea 6', 'viability_score': 6},
                    {'name': 'Idea 7', 'viability_score': 4},
                    {'name': 'Idea 8', 'viability_score': 2},
                    {'name': 'Idea 9', 'viability_score': 10},
                    {'name': 'Idea 10', 'viability_score': 1}
                ]
                
                # Test 30% filtering (should keep top 3)
                filtered = generator.filter_ideas_by_percentage(ideas, 30)
                assert len(filtered) == 3
                assert filtered[0]['name'] == 'Idea 9'  # Highest score
                assert filtered[1]['name'] == 'Idea 1'  # Second highest
                assert filtered[2]['name'] == 'Idea 5'  # Third highest
                
                # Test 100% filtering (should keep all)
                filtered = generator.filter_ideas_by_percentage(ideas, 100)
                assert len(filtered) == 10
                
                # Test 10% filtering (should keep 1)
                filtered = generator.filter_ideas_by_percentage(ideas, 10)
                assert len(filtered) == 1
                assert filtered[0]['name'] == 'Idea 9'
    
    def test_process_opportunity_zone(self, mock_openai_client, mock_anthropic_client):
        """Test complete processing of an opportunity zone"""
        # Mock responses
        mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="ERRC Grid content"))
        ]
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="Product ideas and viability scores")
        ]
        
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                zone_analysis = {
                    'zone': {'name': 'Test Zone', 'importance_percentage': 20},
                    'industry_norms': 'Norms',
                    'engineering_spectrum': 'Spectrum'
                }
                
                result = generator.process_opportunity_zone(zone_analysis)
                
                assert 'zone' in result
                assert 'errc_grid' in result
                assert 'all_ideas' in result
                assert 'filtered_ideas' in result
                assert result['ideas_total'] == 10
                assert result['ideas_kept'] == 2  # 20% of 10
    
    def test_generate_final_report(self, mock_openai_client, mock_anthropic_client):
        """Test final report generation"""
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                results = [{
                    'zone': {'name': 'Zone 1', 'importance_percentage': 50},
                    'errc_grid': 'ERRC content',
                    'all_ideas': [
                        {'name': 'Idea 1', 'viability_score': 8, 'innovation_score': 7}
                    ],
                    'filtered_ideas': [
                        {'name': 'Idea 1', 'viability_score': 8, 'innovation_score': 7}
                    ],
                    'ideas_kept': 1,
                    'ideas_total': 2
                }]
                
                report = generator.generate_final_report(results)
                
                assert "# Product Innovation Pipeline Results" in report
                assert "Executive Summary" in report
                assert "Zone 1" in report
                assert "ERRC Grid" in report
                assert "Idea 1" in report
    
    def test_save_results(self, tmp_path, mock_openai_client, mock_anthropic_client):
        """Test saving results to files"""
        with patch('product_idea_generator.openai.OpenAI', return_value=mock_openai_client):
            with patch('product_idea_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
                generator = ProductIdeaGenerator()
                results = [{'test': 'data'}]
                report = "Test report"
                
                json_file = tmp_path / "test.json"
                report_file = tmp_path / "test.md"
                
                generator.save_results(results, report, str(json_file), str(report_file))
                
                assert json_file.exists()
                assert report_file.exists()
                assert report_file.read_text() == "Test report"
                
                json_data = json.loads(json_file.read_text())
                assert 'metadata' in json_data
                assert 'results' in json_data

@pytest.fixture
def sample_value_curves():
    """Sample value curves data for testing"""
    return {
        "analyses": [{
            "zone": {
                "name": "Test Zone",
                "importance_percentage": 30,
                "description": "Test opportunity zone"
            },
            "industry_norms": "Industry follows X patterns",
            "engineering_spectrum": "Over-engineered in Y, under in Z",
            "competitive_data": {
                "search_results": [
                    {"title": "Competitor Analysis", "highlights": ["insight 1"]}
                ]
            }
        }]
    }