"""
Test suite for sophisticated scoring system components
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scoring import (
    IdeaScore, BreakthroughDetector, SmartFilterer, 
    CrossZoneOptimizer, ConfidenceScorer, FinalSelector, SelectionReporter
)


@pytest.fixture
def sample_idea():
    """Sample idea for testing"""
    return {
        'name': 'AI-Powered Smart Workspace',
        'value_proposition': 'Revolutionary AI system that adapts workspace layout and tools based on user behavior patterns',
        'features': [
            'Machine learning workspace optimization',
            'Real-time environment adaptation', 
            'Predictive tool arrangement',
            'Cross-platform integration'
        ],
        'target_segment': 'B2B knowledge workers and remote teams',
        'differentiation': 'First-ever AI that learns individual work patterns and physically adapts the workspace',
        'viability_score': 7.5,
        'innovation_score': 8.5,
        'viability_details': {
            'technical_feasibility': 7.0,
            'market_readiness': 6.5,
            'resource_requirements': 6.0,
            'time_to_market': 7.5,
            'competitive_moat': 8.0
        }
    }


@pytest.fixture
def sample_breakthrough_idea():
    """Sample breakthrough idea for testing"""
    return {
        'name': 'Quantum Communication Network',
        'value_proposition': 'Breakthrough quantum entanglement communication system enabling instant, unhackable global communications',
        'features': [
            'Quantum entanglement protocols',
            'Zero-latency transmission',
            'Unbreakable encryption',
            'Global network infrastructure'
        ],
        'target_segment': 'Government and enterprise security applications',
        'differentiation': 'Revolutionary quantum physics breakthrough enabling paradigm-shifting communication',
        'viability_score': 5.5,
        'innovation_score': 9.5,
        'viability_details': {
            'technical_feasibility': 4.0,
            'market_readiness': 5.0,
            'resource_requirements': 3.0,
            'time_to_market': 4.0,
            'competitive_moat': 10.0
        }
    }


@pytest.fixture
def sample_zone_results(sample_idea, sample_breakthrough_idea):
    """Sample zone processing results"""
    return [
        {
            'zone': {
                'name': 'Productivity Enhancement',
                'importance_percentage': 60
            },
            'all_ideas': [sample_idea, sample_breakthrough_idea],
            'filtered_ideas': [sample_idea],
            'ideas_kept': 1,
            'ideas_total': 2
        },
        {
            'zone': {
                'name': 'Security Innovation', 
                'importance_percentage': 40
            },
            'all_ideas': [sample_breakthrough_idea],
            'filtered_ideas': [sample_breakthrough_idea],
            'ideas_kept': 1,
            'ideas_total': 1
        }
    ]


class TestIdeaScore:
    """Test IdeaScore functionality"""
    
    def test_idea_score_creation(self, sample_idea):
        """Test creating IdeaScore from idea data"""
        idea_score = IdeaScore.from_idea_data(sample_idea)
        
        assert idea_score.viability_score == 7.5
        assert idea_score.innovation_score == 8.5
        assert idea_score.composite_score > 0
        assert idea_score.confidence_score > 0
        assert idea_score.breakthrough_score > 0
    
    def test_viability_breakdown_parsing(self, sample_idea):
        """Test viability breakdown parsing"""
        idea_score = IdeaScore.from_idea_data(sample_idea)
        
        breakdown = idea_score.viability_breakdown
        assert 'technical_feasibility' in breakdown
        assert 'market_readiness' in breakdown
        assert breakdown['technical_feasibility'] == 7.0
        assert breakdown['market_readiness'] == 6.5
    
    def test_high_potential_detection(self, sample_idea):
        """Test high potential idea detection"""
        idea_score = IdeaScore.from_idea_data(sample_idea)
        
        # Should be high potential due to high innovation + good viability
        assert idea_score.is_high_potential()
    
    def test_composite_score_calculation(self, sample_idea):
        """Test composite score calculation"""
        idea_score = IdeaScore.from_idea_data(sample_idea)
        
        # Composite should be weighted average
        expected_range = (6.0, 9.0)  # Reasonable range given inputs
        assert expected_range[0] <= idea_score.composite_score <= expected_range[1]


class TestBreakthroughDetector:
    """Test BreakthroughDetector functionality"""
    
    def test_breakthrough_detection(self, sample_breakthrough_idea):
        """Test breakthrough detection"""
        detector = BreakthroughDetector()
        analysis = detector.analyze_idea(sample_breakthrough_idea)
        
        assert analysis.is_breakthrough
        assert analysis.breakthrough_score >= 8.0
        assert len(analysis.moonshot_indicators) > 0
    
    def test_moonshot_detection(self, sample_breakthrough_idea):
        """Test moonshot detection"""
        detector = BreakthroughDetector()
        analysis = detector.analyze_idea(sample_breakthrough_idea)
        
        # Should detect as moonshot due to revolutionary language
        assert analysis.is_moonshot
        assert 'revolutionary' in [indicator.lower() for indicator in analysis.moonshot_indicators]
    
    def test_scalability_assessment(self, sample_idea):
        """Test scalability assessment"""
        detector = BreakthroughDetector()
        analysis = detector.analyze_idea(sample_idea)
        
        assert analysis.scalability_score >= 0
        assert analysis.scalability_score <= 10
    
    def test_industry_disruption_potential(self, sample_breakthrough_idea):
        """Test industry disruption potential assessment"""
        detector = BreakthroughDetector()
        analysis = detector.analyze_idea(sample_breakthrough_idea)
        
        disruption = analysis.industry_disruption_potential
        assert isinstance(disruption, dict)
        assert len(disruption) > 0
        
        # Should have high disruption in relevant industries
        assert 'telecommunications' in disruption
        assert disruption['telecommunications'] > 5.0


class TestConfidenceScorer:
    """Test ConfidenceScorer functionality"""
    
    def test_confidence_calculation(self, sample_idea):
        """Test confidence calculation"""
        scorer = ConfidenceScorer()
        analysis = scorer.calculate_confidence(sample_idea)
        
        assert 0 <= analysis.overall_confidence <= 10
        assert analysis.data_quality_score >= 0
        assert analysis.assessment_consistency >= 0
        assert isinstance(analysis.uncertainty_factors, list)
    
    def test_risk_adjustment(self, sample_idea):
        """Test risk adjustment application"""
        scorer = ConfidenceScorer()
        analysis = scorer.calculate_confidence(sample_idea)
        
        adjusted_scores = analysis.adjusted_scores
        assert 'composite_score' in adjusted_scores
        assert 'viability_score' in adjusted_scores
        
        # Adjusted scores should be reasonable
        for score in adjusted_scores.values():
            assert 0 <= score <= 10
    
    def test_confidence_categorization(self, sample_idea):
        """Test confidence categorization"""
        scorer = ConfidenceScorer()
        analysis = scorer.calculate_confidence(sample_idea)
        
        category = scorer.get_confidence_category(analysis.overall_confidence)
        assert category in ['High Confidence', 'Medium Confidence', 'Low Confidence', 'Very Low Confidence']


class TestSmartFilterer:
    """Test SmartFilterer functionality"""
    
    def test_idea_filtering(self, sample_zone_results):
        """Test smart filtering of ideas"""
        filterer = SmartFilterer()
        
        # First, add scoring to ideas (simulate previous pipeline steps)
        for zone_result in sample_zone_results:
            enhanced_ideas = []
            for idea in zone_result['all_ideas']:
                idea['zone_name'] = zone_result['zone']['name']
                idea_score = IdeaScore.from_idea_data(idea)
                breakthrough_detector = BreakthroughDetector()
                breakthrough_analysis = breakthrough_detector.analyze_idea(idea, idea_score)
                
                idea['scoring'] = {
                    'idea_score': idea_score,
                    'breakthrough_analysis': breakthrough_analysis,
                    'composite_score': idea_score.composite_score,
                    'is_excellence': idea_score.is_high_potential(),
                    'is_breakthrough': breakthrough_analysis.is_breakthrough
                }
                enhanced_ideas.append(idea)
            zone_result['all_ideas'] = enhanced_ideas
        
        results = filterer.filter_ideas(sample_zone_results)
        
        assert len(results.selected_ideas) > 0
        assert isinstance(results.filtering_stats, dict)
        assert isinstance(results.warnings, list)
    
    def test_excellence_preservation(self, sample_zone_results):
        """Test excellence idea preservation"""
        filterer = SmartFilterer()
        
        # Ensure at least one idea is marked as excellence
        for zone_result in sample_zone_results:
            for idea in zone_result['all_ideas']:
                idea['zone_name'] = zone_result['zone']['name']
                idea_score = IdeaScore.from_idea_data(idea)
                # Force high scores to ensure excellence
                idea_score.composite_score = 9.0
                idea['scoring'] = {
                    'idea_score': idea_score,
                    'composite_score': 9.0,
                    'is_excellence': True
                }
        
        results = filterer.filter_ideas(sample_zone_results)
        
        # Should preserve excellence ideas
        assert len(results.excellence_preserved) > 0


class TestCrossZoneOptimizer:
    """Test CrossZoneOptimizer functionality"""
    
    def test_portfolio_optimization(self, sample_zone_results):
        """Test portfolio optimization"""
        optimizer = CrossZoneOptimizer()
        
        # Prepare ideas with scoring
        selected_ideas = []
        for zone_result in sample_zone_results:
            for idea in zone_result['all_ideas']:
                idea['zone_name'] = zone_result['zone']['name']
                idea_score = IdeaScore.from_idea_data(idea)
                idea['scoring'] = {
                    'idea_score': idea_score,
                    'composite_score': idea_score.composite_score
                }
                selected_ideas.append(idea)
        
        results = optimizer.optimize_portfolio(selected_ideas)
        
        assert 'baseline_metrics' in results
        assert 'optimized_metrics' in results
        assert 'synergies' in results
        assert 'recommendations' in results
    
    def test_synergy_identification(self, sample_zone_results):
        """Test synergy identification between ideas"""
        optimizer = CrossZoneOptimizer()
        
        selected_ideas = []
        for zone_result in sample_zone_results:
            for idea in zone_result['all_ideas']:
                idea['zone_name'] = zone_result['zone']['name']
                selected_ideas.append(idea)
        
        synergies = optimizer._identify_synergies(selected_ideas)
        
        assert isinstance(synergies, list)
        # Should find some synergies between AI and quantum ideas
        if len(synergies) > 0:
            assert synergies[0].synergy_score >= 0


class TestFinalSelector:
    """Test FinalSelector functionality"""
    
    def test_ensemble_selection(self, sample_zone_results):
        """Test ensemble selection strategies"""
        selector = FinalSelector()
        
        # Mock filtering results
        class MockFilteringResults:
            def __init__(self, selected_ideas):
                self.selected_ideas = selected_ideas
                self.excellence_preserved = []
                self.warnings = []
        
        # Prepare selected ideas
        selected_ideas = []
        for zone_result in sample_zone_results:
            for idea in zone_result['all_ideas']:
                idea['zone_name'] = zone_result['zone']['name']
                idea_score = IdeaScore.from_idea_data(idea)
                breakthrough_detector = BreakthroughDetector()
                breakthrough_analysis = breakthrough_detector.analyze_idea(idea, idea_score)
                
                idea['scoring'] = {
                    'idea_score': idea_score,
                    'breakthrough_analysis': breakthrough_analysis,
                    'composite_score': idea_score.composite_score
                }
                selected_ideas.append(idea)
        
        filtering_results = MockFilteringResults(selected_ideas)
        results = selector.select_final_ideas(filtering_results)
        
        assert len(results.final_selection) > 0
        assert len(results.ensemble_strategies) > 0
        assert 0 <= results.selection_confidence <= 10


class TestSelectionReporter:
    """Test SelectionReporter functionality"""
    
    def test_report_generation(self, sample_zone_results):
        """Test comprehensive report generation"""
        reporter = SelectionReporter()
        
        # Mock other results
        class MockFilteringResults:
            def __init__(self):
                self.selected_ideas = []
                self.dropped_ideas = []
                self.excellence_preserved = []
                self.filtering_stats = {}
                self.warnings = []
        
        class MockFinalResults:
            def __init__(self):
                self.final_selection = []
                self.ensemble_strategies = []
                self.consensus_analysis = {}
                self.safety_checks = {}
                self.warnings = []
                self.selection_confidence = 8.0
                self.dropped_high_value_ideas = []
        
        filtering_results = MockFilteringResults()
        final_results = MockFinalResults()
        
        report = reporter.generate_report(
            sample_zone_results, filtering_results, final_results
        )
        
        assert 'executive_summary' in report
        assert 'zone_analysis' in report
        assert 'breakthrough_metrics' in report
        assert 'recommendations' in report
    
    def test_markdown_export(self, sample_zone_results):
        """Test markdown report export"""
        reporter = SelectionReporter()
        
        # Create minimal report structure
        minimal_report = {
            'metadata': {
                'report_generated': '2024-01-01T00:00:00',
                'report_version': '1.0'
            },
            'executive_summary': {
                'process_overview': {
                    'zones_analyzed': 2,
                    'ideas_processed': 3,
                    'final_selection': 2,
                    'reduction_rate': '33.3%',
                    'quality_improvement': '+1.5'
                },
                'key_achievements': [],
                'risk_assessment': {'overall_risk': 'Low', 'risk_factors': []},
                'breakthrough_performance': {
                    'total_identified': 1,
                    'preservation_rate': '100%',
                    'moonshots_preserved': '1/1'
                },
                'top_performing_zones': [],
                'selection_confidence': 8.5
            },
            'zone_analysis': [],
            'recommendations': []
        }
        
        markdown = reporter.export_report_markdown(minimal_report)
        
        assert isinstance(markdown, str)
        assert '# Product Idea Selection Report' in markdown
        assert 'Executive Summary' in markdown


def test_integration_scoring_pipeline(sample_idea, sample_breakthrough_idea):
    """Test integration of all scoring components"""
    # Test the full pipeline integration
    ideas = [sample_idea, sample_breakthrough_idea]
    
    # Step 1: Apply sophisticated scoring
    enhanced_ideas = []
    for idea in ideas:
        idea['zone_name'] = 'Test Zone'
        
        idea_score = IdeaScore.from_idea_data(idea)
        breakthrough_detector = BreakthroughDetector()
        breakthrough_analysis = breakthrough_detector.analyze_idea(idea, idea_score)
        confidence_scorer = ConfidenceScorer()
        confidence_analysis = confidence_scorer.calculate_confidence(idea, idea_score)
        
        idea['scoring'] = {
            'idea_score': idea_score,
            'breakthrough_analysis': breakthrough_analysis,
            'confidence_analysis': confidence_analysis,
            'composite_score': confidence_analysis.adjusted_scores.get('composite_score', idea_score.composite_score),
            'is_excellence': idea_score.is_high_potential(),
            'is_breakthrough': breakthrough_analysis.is_breakthrough
        }
        
        enhanced_ideas.append(idea)
    
    # Verify all scoring components worked
    assert len(enhanced_ideas) == 2
    for idea in enhanced_ideas:
        assert 'scoring' in idea
        scoring = idea['scoring']
        assert 'idea_score' in scoring
        assert 'breakthrough_analysis' in scoring
        assert 'confidence_analysis' in scoring
        assert isinstance(scoring['composite_score'], (int, float))
        assert isinstance(scoring['is_excellence'], bool)
        assert isinstance(scoring['is_breakthrough'], bool)


if __name__ == "__main__":
    pytest.main([__file__])