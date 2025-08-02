"""
Unit tests for value_curve_mapper.py
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from concurrent.futures import Future

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from value_curve_mapper import ValueCurveMapper

class TestValueCurveMapper:
    """Test suite for ValueCurveMapper"""
    
    def test_init_with_valid_credentials(self, mock_exa_client, mock_anthropic_client):
        """Test initialization with valid credentials"""
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                assert mapper.exa_api_key == 'test-exa-key'
                assert mapper.anthropic_api_key == 'test-anthropic-key'
                assert mapper.exa is not None
                assert mapper.anthropic_client is not None
                assert mapper.model_opus == 'claude-3-opus-20240229'
    
    def test_init_without_exa_key(self):
        """Test initialization fails without EXA key"""
        with patch.dict(os.environ, {'EXA_API_KEY': ''}):
            with pytest.raises(SystemExit):
                ValueCurveMapper()
    
    def test_init_without_anthropic_key(self):
        """Test initialization fails without Anthropic key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            with pytest.raises(SystemExit):
                ValueCurveMapper()
    
    def test_load_opportunity_zones_success(self, tmp_path, sample_opportunity_zones, 
                                          mock_exa_client, mock_anthropic_client):
        """Test loading opportunity zones from JSON"""
        zones_file = tmp_path / "zones.json"
        zones_file.write_text(json.dumps(sample_opportunity_zones))
        
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                data = mapper.load_opportunity_zones(str(zones_file))
                
                assert 'opportunity_zones' in data
                assert 'metadata' in data
    
    def test_search_strategy_canvas(self, mock_exa_client, mock_anthropic_client):
        """Test EXA search for competitive strategy"""
        mock_result = MagicMock()
        mock_result.url = "https://example.com/strategy"
        mock_result.title = "Competitive Analysis"
        mock_result.text = "Market leader analysis..."
        mock_result.highlights = ["key insight 1", "key insight 2"]
        mock_exa_client.search_and_contents.return_value.results = [mock_result]
        
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                zone = {
                    'name': 'Test Zone',
                    'description': 'Test description',
                    'clusters_addressed': ['Cluster 1']
                }
                
                result = mapper.search_strategy_canvas(zone)
                
                assert result['zone_name'] == 'Test Zone'
                assert len(result['search_results']) == 1
                assert result['search_results'][0]['url'] == "https://example.com/strategy"
    
    def test_analyze_industry_norms(self, mock_exa_client, mock_anthropic_client):
        """Test industry norms analysis with Opus"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="**Industry Norms**: Everyone uses SaaS\n**Sacred Cows**: Must have enterprise features")
        ]
        
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                competitive_data = {
                    'zone_name': 'Test Zone',
                    'zone_description': 'Test',
                    'search_results': [{
                        'title': 'Market Analysis',
                        'text': 'Industry insights...',
                        'highlights': ['insight 1']
                    }]
                }
                
                result = mapper.analyze_industry_norms(competitive_data)
                
                assert "Industry Norms" in result
                assert "Sacred Cows" in result
                assert mock_anthropic_client.messages.create.called
    
    def test_analyze_engineering_spectrum(self, mock_exa_client, mock_anthropic_client):
        """Test engineering spectrum analysis with Opus"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="**OVER-ENGINEERED**: Complex dashboards\n**UNDER-ENGINEERED**: Basic auth")
        ]
        
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                competitive_data = {
                    'zone_name': 'Test Zone',
                    'zone_description': 'Test',
                    'search_results': [{
                        'title': 'Product Review',
                        'text': 'Feature analysis...'
                    }]
                }
                
                result = mapper.analyze_engineering_spectrum(competitive_data)
                
                assert "OVER-ENGINEERED" in result
                assert "UNDER-ENGINEERED" in result
    
    @patch('value_curve_mapper.ThreadPoolExecutor')
    def test_analyze_zone_sequential_then_parallel(self, mock_executor, 
                                                  mock_exa_client, mock_anthropic_client):
        """Test that EXA runs first, then Opus calls run in parallel"""
        # Mock EXA results
        mock_exa_client.search_and_contents.return_value.results = [MagicMock()]
        
        # Mock futures
        mock_future1 = MagicMock(spec=Future)
        mock_future1.result.return_value = "Norms analysis"
        mock_future2 = MagicMock(spec=Future)
        mock_future2.result.return_value = "Engineering analysis"
        
        # Mock executor
        mock_executor_instance = MagicMock()
        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Mock as_completed
        with patch('value_curve_mapper.as_completed', return_value=[mock_future1, mock_future2]):
            with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
                with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                    mapper = ValueCurveMapper()
                    zone = {
                        'name': 'Test Zone',
                        'description': 'Test',
                        'importance_percentage': 50
                    }
                    
                    result = mapper.analyze_zone(zone, 0, 1)
                    
                    # Verify EXA was called
                    assert mock_exa_client.search_and_contents.called
                    
                    # Verify parallel execution setup
                    assert mock_executor_instance.submit.call_count == 2
                    
                    # Verify results
                    assert result['zone'] == zone
                    assert 'competitive_data' in result
                    assert result['industry_norms'] == "Norms analysis"
                    assert result['engineering_spectrum'] == "Engineering analysis"
    
    def test_generate_value_curve_report(self, mock_exa_client, mock_anthropic_client):
        """Test report generation"""
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                analyses = [{
                    'zone': {
                        'name': 'Test Zone',
                        'importance_percentage': 50,
                        'description': 'Test description'
                    },
                    'competitive_data': {
                        'search_results': []
                    },
                    'industry_norms': 'Test norms analysis',
                    'engineering_spectrum': 'Test engineering analysis'
                }]
                
                report = mapper.generate_value_curve_report(analyses)
                
                assert "# Value Curve Mapping Report" in report
                assert "Test Zone" in report
                assert "50%" in report
                assert "Industry Norms & Sacred Cows" in report
                assert "Engineering Spectrum Analysis" in report
    
    def test_save_results(self, tmp_path, mock_exa_client, mock_anthropic_client):
        """Test saving results to files"""
        with patch('value_curve_mapper.Exa', return_value=mock_exa_client):
            with patch('value_curve_mapper.anthropic.Anthropic', return_value=mock_anthropic_client):
                mapper = ValueCurveMapper()
                
                analyses = [{
                    'zone': {'name': 'Test'},
                    'competitive_data': {},
                    'industry_norms': 'norms',
                    'engineering_spectrum': 'spectrum'
                }]
                report = "# Test Report"
                
                json_file = tmp_path / "results.json"
                report_file = tmp_path / "report.md"
                
                mapper.save_results(analyses, report, str(json_file), str(report_file))
                
                assert json_file.exists()
                assert report_file.exists()
                assert report_file.read_text() == "# Test Report"
                
                json_data = json.loads(json_file.read_text())
                assert 'metadata' in json_data
                assert 'analyses' in json_data