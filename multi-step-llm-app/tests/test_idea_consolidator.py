"""
Unit tests for idea_consolidator.py
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from idea_consolidator import IdeaConsolidator


class TestIdeaConsolidator:
    """Test suite for IdeaConsolidator"""
    
    def test_init(self):
        """Test initialization"""
        consolidator = IdeaConsolidator()
        assert consolidator.timestamp is not None
        assert isinstance(consolidator.timestamp, str)
    
    def test_load_product_ideas_success(self, tmp_path, sample_product_ideas):
        """Test successful loading of product ideas"""
        ideas_file = tmp_path / "ideas.json"
        ideas_file.write_text(json.dumps(sample_product_ideas))
        
        consolidator = IdeaConsolidator()
        data = consolidator.load_product_ideas(str(ideas_file))
        
        assert 'metadata' in data
        assert 'results' in data
        assert len(data['results']) > 0
    
    def test_load_product_ideas_file_not_found(self):
        """Test handling of missing file"""
        consolidator = IdeaConsolidator()
        
        with pytest.raises(SystemExit):
            consolidator.load_product_ideas("nonexistent.json")
    
    def test_extract_complete_journey(self, sample_product_ideas):
        """Test journey metadata extraction"""
        consolidator = IdeaConsolidator()
        journey = consolidator.extract_complete_journey(sample_product_ideas)
        
        assert 'pipeline_completion_timestamp' in journey
        assert 'total_zones_analyzed' in journey
        assert 'total_ideas_generated' in journey
        assert 'ideas_after_filtering' in journey
        assert 'pipeline_version' in journey
        assert 'pipeline_steps' in journey
        assert len(journey['pipeline_steps']) == 6
    
    def test_create_exhaustive_idea_details(self, sample_idea, sample_zone):
        """Test creation of exhaustive idea details"""
        consolidator = IdeaConsolidator()
        errc_grid = "ELIMINATE: Feature X\nREDUCE: Cost Y\nRAISE: Quality Z\nCREATE: Innovation A"
        
        details = consolidator.create_exhaustive_idea_details(
            sample_idea, sample_zone, errc_grid, 0, 0
        )
        
        assert details['idea_id'] == 'IDEA-000-000'
        assert 'metadata' in details
        assert 'core_concept' in details
        assert 'scores' in details
        assert 'features' in details
        assert 'errc_foundation' in details
        assert 'market_justification' in details
        assert 'implementation_details' in details
        assert 'risk_assessment' in details
        assert 'growth_potential' in details
    
    def test_extract_errc_section(self):
        """Test ERRC section extraction"""
        consolidator = IdeaConsolidator()
        errc_grid = """
ELIMINATE
- Complex onboarding
- Feature bloat
- High pricing tiers

REDUCE
- Setup time
- Learning curve

RAISE
- User engagement
- Data security

CREATE
- AI assistance
- Real-time collaboration
"""
        
        eliminate_factors = consolidator._extract_errc_section(errc_grid, "ELIMINATE")
        assert len(eliminate_factors) >= 3
        assert "Complex onboarding" in eliminate_factors[0]
        
        create_factors = consolidator._extract_errc_section(errc_grid, "CREATE")
        assert len(create_factors) >= 2
        assert "AI assistance" in create_factors[0]
    
    def test_estimate_dev_time(self, sample_idea):
        """Test development time estimation"""
        consolidator = IdeaConsolidator()
        
        # High viability
        sample_idea['viability_score'] = 9
        assert consolidator._estimate_dev_time(sample_idea) == "3-6 months"
        
        # Medium viability
        sample_idea['viability_score'] = 7
        assert consolidator._estimate_dev_time(sample_idea) == "6-12 months"
        
        # Low viability
        sample_idea['viability_score'] = 4
        assert consolidator._estimate_dev_time(sample_idea) == "12-18 months"
    
    def test_estimate_market_size(self, sample_zone):
        """Test market size estimation"""
        consolidator = IdeaConsolidator()
        
        # High importance
        sample_zone['importance_percentage'] = 50
        assert consolidator._estimate_market_size(sample_zone) == "$1B+ TAM"
        
        # Medium importance
        sample_zone['importance_percentage'] = 30
        assert consolidator._estimate_market_size(sample_zone) == "$500M-$1B TAM"
        
        # Low importance
        sample_zone['importance_percentage'] = 15
        assert consolidator._estimate_market_size(sample_zone) == "$100M-$500M TAM"
    
    def test_assess_network_effects(self, sample_idea):
        """Test network effects assessment"""
        consolidator = IdeaConsolidator()
        
        # High innovation
        sample_idea['innovation_score'] = 9
        result = consolidator._assess_network_effects(sample_idea)
        assert "Strong network effects" in result
        
        # Medium innovation
        sample_idea['innovation_score'] = 6
        result = consolidator._assess_network_effects(sample_idea)
        assert "Moderate network effects" in result
        
        # Low innovation
        sample_idea['innovation_score'] = 3
        result = consolidator._assess_network_effects(sample_idea)
        assert "Limited network effects" in result
    
    def test_create_final_output(self, sample_product_ideas):
        """Test final output creation"""
        consolidator = IdeaConsolidator()
        final_output = consolidator.create_final_output(sample_product_ideas)
        
        assert 'pipeline_metadata' in final_output
        assert 'executive_summary' in final_output
        assert 'zone_summaries' in final_output
        assert 'all_filtered_ideas' in final_output
        assert 'implementation_roadmap' in final_output
        assert 'resource_allocation' in final_output
        assert 'success_metrics' in final_output
        
        # Check executive summary
        exec_summary = final_output['executive_summary']
        assert 'total_opportunity_zones' in exec_summary
        assert 'total_filtered_ideas' in exec_summary
        assert 'highest_scoring_idea' in exec_summary
        assert 'most_innovative_idea' in exec_summary
        assert 'quickest_to_market' in exec_summary
        assert 'recommendation' in exec_summary
    
    def test_calculate_zone_value(self, sample_ideas):
        """Test zone value calculation"""
        consolidator = IdeaConsolidator()
        
        # With ideas
        value = consolidator._calculate_zone_value(sample_ideas)
        assert value > 0
        
        # Empty list
        value = consolidator._calculate_zone_value([])
        assert value == 0.0
    
    def test_find_highest_scoring(self, sample_ideas):
        """Test finding highest scoring idea"""
        consolidator = IdeaConsolidator()
        
        # Prepare test data with scores
        ideas = []
        for i, idea in enumerate(sample_ideas):
            idea_data = {
                'idea_id': f'IDEA-{i}',
                'scores': {
                    'viability_score': 5 + i,
                    'innovation_score': 6 + i
                }
            }
            ideas.append(idea_data)
        
        highest = consolidator._find_highest_scoring(ideas)
        assert highest['scores']['viability_score'] == 7  # 5 + 2 for the third idea
        
        # Empty list
        highest = consolidator._find_highest_scoring([])
        assert highest == {}
    
    def test_create_roadmap(self, sample_ideas):
        """Test implementation roadmap creation"""
        consolidator = IdeaConsolidator()
        
        # Create test ideas with IDs
        ideas = []
        for i in range(6):
            ideas.append({
                'idea_id': f'IDEA-00{i}',
                'scores': {'viability_score': 8 - i}
            })
        
        roadmap = consolidator._create_roadmap(ideas)
        
        assert 'phase_1' in roadmap
        assert 'phase_2' in roadmap
        assert 'phase_3' in roadmap
        
        assert roadmap['phase_1']['duration'] == "0-3 months"
        assert len(roadmap['phase_1']['ideas']) <= 2
        assert roadmap['phase_2']['duration'] == "3-9 months"
        assert roadmap['phase_3']['duration'] == "9-18 months"
    
    def test_suggest_resource_allocation(self, sample_ideas):
        """Test resource allocation suggestions"""
        consolidator = IdeaConsolidator()
        
        # Create test ideas with scores
        ideas = []
        for i in range(3):
            ideas.append({
                'idea_id': f'IDEA-00{i}',
                'scores': {
                    'viability_score': 8 - i,
                    'innovation_score': 7 - i
                }
            })
        
        allocation = consolidator._suggest_resource_allocation(ideas)
        
        assert 'allocation_strategy' in allocation
        assert 'allocations' in allocation
        assert 'total_budget_recommendation' in allocation
        
        # Check allocations are sorted by percentage
        allocations = allocation['allocations']
        assert allocations[0]['resource_percentage'] >= allocations[1]['resource_percentage']
        
        # Empty list
        allocation = consolidator._suggest_resource_allocation([])
        assert allocation == {}
    
    def test_save_final_output(self, tmp_path, sample_final_output):
        """Test saving final output"""
        consolidator = IdeaConsolidator()
        
        json_file = tmp_path / "portfolio.json"
        consolidator.save_final_output(sample_final_output, str(json_file))
        
        assert json_file.exists()
        
        # Check summary file was created
        summary_file = tmp_path / "portfolio_summary.md"
        assert summary_file.exists()
        
        # Verify JSON content
        with open(json_file) as f:
            saved_data = json.load(f)
        assert saved_data == sample_final_output
    
    def test_create_summary_report(self, tmp_path, sample_final_output):
        """Test summary report creation"""
        consolidator = IdeaConsolidator()
        
        report_file = tmp_path / "summary.md"
        consolidator.create_summary_report(sample_final_output, str(report_file))
        
        assert report_file.exists()
        
        content = report_file.read_text()
        assert "# Innovation Portfolio Summary" in content
        assert "## Executive Summary" in content
        assert "## Top 3 Ideas" in content
        assert "Total Opportunity Zones" in content
        assert "Total Filtered Ideas" in content


@pytest.fixture
def sample_zone():
    """Sample opportunity zone for testing"""
    return {
        'name': 'Test Zone',
        'description': 'A test opportunity zone',
        'importance_percentage': 30,
        'potential_impact': 'High'
    }


@pytest.fixture
def sample_idea():
    """Sample product idea for testing"""
    return {
        'name': 'Test Product',
        'value_proposition': 'Revolutionary solution for testing',
        'viability_score': 7.5,
        'innovation_score': 8,
        'features': ['Feature 1', 'Feature 2', 'Feature 3'],
        'target_segment': 'Developers',
        'differentiation': 'First of its kind',
        'viability_details': {
            'technical_feasibility': 8,
            'market_readiness': 7,
            'resource_requirements': 6,
            'time_to_market': 7,
            'competitive_moat': 8
        }
    }


@pytest.fixture
def sample_ideas():
    """Sample list of ideas for testing"""
    return [
        {
            'name': 'Product A',
            'viability_score': 8,
            'innovation_score': 7
        },
        {
            'name': 'Product B',
            'viability_score': 6,
            'innovation_score': 9
        },
        {
            'name': 'Product C',
            'viability_score': 7,
            'innovation_score': 8
        }
    ]


@pytest.fixture
def sample_product_ideas():
    """Sample product ideas data structure"""
    return {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'zones_processed': 2,
            'total_ideas': 20,
            'filtered_ideas': 5
        },
        'results': [
            {
                'zone': {
                    'name': 'Zone 1',
                    'importance_percentage': 50,
                    'description': 'Primary opportunity'
                },
                'errc_grid': 'ELIMINATE: X\nREDUCE: Y\nRAISE: Z\nCREATE: A',
                'all_ideas': [
                    {
                        'name': 'Idea 1',
                        'value_proposition': 'Test value prop',
                        'viability_score': 8,
                        'innovation_score': 7
                    }
                ],
                'filtered_ideas': [
                    {
                        'name': 'Idea 1',
                        'value_proposition': 'Test value prop',
                        'viability_score': 8,
                        'innovation_score': 7
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_final_output():
    """Sample final output structure"""
    return {
        'pipeline_metadata': {
            'pipeline_completion_timestamp': datetime.now().isoformat(),
            'total_zones_analyzed': 2,
            'total_ideas_generated': 20,
            'ideas_after_filtering': 5
        },
        'executive_summary': {
            'total_opportunity_zones': 2,
            'total_filtered_ideas': 5,
            'highest_scoring_idea': {'idea_id': 'IDEA-001'},
            'most_innovative_idea': {'idea_id': 'IDEA-002'},
            'quickest_to_market': {'idea_id': 'IDEA-003'},
            'recommendation': 'Focus on top 3 ideas'
        },
        'zone_summaries': [],
        'all_filtered_ideas': [
            {
                'idea_id': 'IDEA-001',
                'core_concept': {'name': 'Test Idea 1'},
                'scores': {'viability_score': 8, 'innovation_score': 7}
            }
        ],
        'implementation_roadmap': {},
        'resource_allocation': {},
        'success_metrics': {}
    }