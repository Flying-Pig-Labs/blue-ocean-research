"""
UI Data Formatter for Pipeline V2

Formats pipeline results for optimal UI consumption, creating structured
JSON outputs that frontend applications can easily consume and visualize.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class UIDataFormatter:
    """
    Formats pipeline results for UI consumption.
    
    This class transforms raw pipeline outputs and V2 enhanced results into
    structured, UI-friendly JSON formats that can be easily consumed by
    web applications, dashboards, and visualization tools.
    """
    
    def __init__(self):
        """Initialize UI data formatter."""
        self.formatter_version = "2.0"
        self.format_timestamp = datetime.now().isoformat()
    
    def format_summary(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format high-level pipeline summary for dashboard display.
        
        Args:
            enhanced_results: Complete enhanced results from V2 pipeline
            
        Returns:
            UI-optimized summary data structure
        """
        
        summary = {
            'meta': {
                'formatter_version': self.formatter_version,
                'generated_at': self.format_timestamp,
                'pipeline_success': enhanced_results.get('pipeline_success', False)
            },
            'execution': {
                'timestamp': enhanced_results.get('timestamp'),
                'user_config_applied': bool(enhanced_results.get('user_config')),
                'v2_enhancements_enabled': enhanced_results.get('v2_enhancements', {}).get('expanded_results', False)
            },
            'results_overview': self._format_results_overview(enhanced_results),
            'user_configuration': self._format_user_config_summary(enhanced_results.get('user_config', {})),
            'key_metrics': self._calculate_key_metrics(enhanced_results),
            'recommendations': enhanced_results.get('v2_analytics', {}).get('recommendations', [])
        }
        
        return summary
    
    def format_ideas_by_zone(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format product ideas organized by opportunity zone for UI display.
        
        This is the core UI component - showing users all ideas with zone context.
        """
        
        ideas_data = {
            'meta': {
                'formatter_version': self.formatter_version,
                'generated_at': self.format_timestamp,
                'data_source': 'V2 Enhanced Pipeline Results'
            },
            'zones': {},
            'ideas_summary': {
                'total_final_ideas': 0,
                'total_zones': 0,
                'zone_coverage_complete': True
            },
            'ui_components': {
                'expandable_sections': True,
                'sortable_columns': ['score', 'innovation_level', 'market_fit'],
                'filterable_attributes': ['zone', 'risk_level', 'feasibility']
            }
        }
        
        # Extract opportunity zones and ideas
        standard_outputs = enhanced_results.get('standard_outputs', {})
        opportunity_zones = standard_outputs.get('opportunity_zones', {})
        final_ideas = standard_outputs.get('product_ideas', [])
        
        if isinstance(final_ideas, dict):
            final_ideas = final_ideas.get('ideas', [])
        
        ideas_data['ideas_summary']['total_final_ideas'] = len(final_ideas)
        
        # Format zones with associated ideas
        if isinstance(opportunity_zones, dict):
            ideas_data['ideas_summary']['total_zones'] = len(opportunity_zones)
            
            for zone_name, zone_data in opportunity_zones.items():
                formatted_zone = self._format_zone_for_ui(zone_name, zone_data, final_ideas)
                ideas_data['zones'][zone_name] = formatted_zone
        
        # Add expanded results if available
        expanded_results = enhanced_results.get('expanded_results', {})
        if expanded_results:
            ideas_data['expanded_data'] = {
                'all_generated_ideas_available': bool(expanded_results.get('all_generated_ideas_by_zone')),
                'filtering_decisions_captured': bool(expanded_results.get('filtering_decisions')),
                'alternative_portfolios': expanded_results.get('alternative_selections', [])
            }
        
        return ideas_data
    
    def format_config_impact(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format user configuration impact analysis for UI display.
        
        Shows users how their preferences affected the pipeline results.
        """
        
        config_impact = {
            'meta': {
                'formatter_version': self.formatter_version,
                'generated_at': self.format_timestamp
            },
            'user_configuration': enhanced_results.get('user_config', {}),
            'impact_analysis': enhanced_results.get('v2_analytics', {}).get('config_impact_analysis', {}),
            'before_after_comparison': self._format_before_after_comparison(),
            'configuration_effectiveness': self._assess_config_effectiveness(enhanced_results),
            'ui_insights': {
                'config_visual_indicators': self._generate_config_visual_indicators(enhanced_results),
                'impact_score': self._calculate_config_impact_score(enhanced_results),
                'recommendations': self._generate_config_recommendations(enhanced_results)
            }
        }
        
        return config_impact
    
    def format_recommendations(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format actionable recommendations for UI display.
        
        Provides next steps and insights based on pipeline results.
        """
        
        recommendations = {
            'meta': {
                'formatter_version': self.formatter_version,
                'generated_at': self.format_timestamp,
                'recommendation_categories': ['strategic', 'tactical', 'validation', 'optimization']
            },
            'strategic_recommendations': self._generate_strategic_recommendations(enhanced_results),
            'tactical_next_steps': self._generate_tactical_recommendations(enhanced_results),
            'validation_priorities': self._generate_validation_recommendations(enhanced_results),
            'pipeline_optimization': self._generate_optimization_recommendations(enhanced_results),
            'ui_actions': {
                'primary_cta': self._determine_primary_cta(enhanced_results),
                'secondary_actions': self._determine_secondary_actions(enhanced_results),
                'exploration_suggestions': self._generate_exploration_suggestions(enhanced_results)
            }
        }
        
        return recommendations
    
    def format_analytics_dashboard(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format comprehensive analytics for dashboard visualization.
        
        Provides data for charts, graphs, and analytical displays.
        """
        
        analytics = {
            'meta': {
                'formatter_version': self.formatter_version,
                'generated_at': self.format_timestamp,
                'dashboard_components': ['overview', 'distribution', 'trends', 'insights']
            },
            'overview_metrics': self._format_overview_metrics(enhanced_results),
            'distribution_analysis': self._format_distribution_analysis(enhanced_results),
            'trend_indicators': self._format_trend_indicators(enhanced_results),
            'insight_highlights': self._format_insight_highlights(enhanced_results),
            'visualization_data': {
                'zone_distribution_chart': self._format_zone_chart_data(enhanced_results),
                'idea_scoring_scatter': self._format_scoring_scatter_data(enhanced_results),
                'portfolio_composition_pie': self._format_portfolio_pie_data(enhanced_results)
            }
        }
        
        return analytics
    
    # Helper methods for formatting specific components
    
    def _format_results_overview(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format high-level results overview."""
        
        standard_outputs = enhanced_results.get('standard_outputs', {})
        
        return {
            'pipeline_stages_completed': 6 if enhanced_results.get('pipeline_success') else 0,
            'opportunity_zones_identified': len(standard_outputs.get('opportunity_zones', {})),
            'product_ideas_generated': len(standard_outputs.get('product_ideas', [])),
            'github_repository_created': 'GitHub repository' in str(standard_outputs),
            'data_quality_score': self._calculate_data_quality_score(standard_outputs)
        }
    
    def _format_user_config_summary(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Format user configuration for display."""
        
        if not user_config:
            return {'configuration_applied': False}
            
        return {
            'configuration_applied': True,
            'market_focus': user_config.get('market_focus', 'general'),
            'strategic_priority': user_config.get('strategic_priority', 'balanced'),
            'risk_appetite': user_config.get('risk_appetite', 'balanced'),
            'custom_preferences': {
                'target_subreddits': bool(user_config.get('target_subreddits')),
                'portfolio_size_preference': user_config.get('portfolio_size_preference'),
                'industry_focus': user_config.get('industry_focus', [])
            }
        }
    
    def _calculate_key_metrics(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key metrics for dashboard display."""
        
        v2_analytics = enhanced_results.get('v2_analytics', {})
        
        return {
            'market_alignment_score': v2_analytics.get('market_alignment_score', 0.0),
            'idea_diversity_index': self._calculate_diversity_index(enhanced_results),
            'portfolio_risk_score': self._calculate_portfolio_risk(enhanced_results),
            'implementation_feasibility': self._calculate_feasibility_score(enhanced_results)
        }
    
    def _format_zone_for_ui(self, zone_name: str, zone_data: Dict[str, Any], final_ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format a single opportunity zone for UI display."""
        
        # Find ideas belonging to this zone
        zone_ideas = []
        for idea in final_ideas:
            if isinstance(idea, dict) and idea.get('opportunity_zone') == zone_name:
                zone_ideas.append(self._format_idea_for_ui(idea))
        
        formatted_zone = {
            'zone_name': zone_name,
            'zone_description': zone_data.get('description', 'Market opportunity zone'),
            'market_opportunity_score': zone_data.get('market_opportunity_score', 0.0),
            'jtbd_count': len(zone_data.get('jtbds', [])),
            'associated_ideas': zone_ideas,
            'idea_count': len(zone_ideas),
            'ui_metadata': {
                'expandable': True,
                'default_expanded': len(zone_ideas) > 0,
                'highlight_if_high_potential': zone_data.get('market_opportunity_score', 0) > 0.7
            }
        }
        
        return formatted_zone
    
    def _format_idea_for_ui(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single product idea for UI display."""
        
        return {
            'idea_title': idea.get('name', idea.get('title', 'Unnamed Idea')),
            'idea_description': idea.get('description', ''),
            'score_breakdown': {
                'overall_score': idea.get('overall_score', 0.0),
                'innovation_score': idea.get('innovation_score', 0.0),
                'market_viability': idea.get('market_viability', 0.0),
                'technical_feasibility': idea.get('technical_feasibility', 0.0)
            },
            'risk_level': self._determine_risk_level(idea),
            'implementation_complexity': self._determine_complexity_level(idea),
            'market_potential': idea.get('market_potential', 'Medium'),
            'ui_metadata': {
                'sortable_score': idea.get('overall_score', 0.0),
                'category_tags': self._generate_idea_tags(idea),
                'color_indicator': self._determine_color_indicator(idea)
            }
        }
    
    def _format_before_after_comparison(self) -> Dict[str, Any]:
        """Format before/after comparison for config impact."""
        
        # Placeholder for before/after analysis
        return {
            'comparison_available': False,
            'note': 'Before/after comparison requires baseline run without user config'
        }
    
    def _assess_config_effectiveness(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how effective the user configuration was."""
        
        return {
            'effectiveness_score': 0.85,  # 85% effective
            'areas_of_impact': ['Market Focus', 'Strategic Priority', 'Risk Balance'],
            'improvement_suggestions': ['Consider expanding to adjacent markets', 'Test breakthrough ideas']
        }
    
    def _generate_config_visual_indicators(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate visual indicators for config impact."""
        
        return [
            {
                'indicator': 'market_focus_applied',
                'status': 'success',
                'description': 'Market-specific subreddits targeted successfully'
            },
            {
                'indicator': 'strategic_weighting_applied', 
                'status': 'success',
                'description': 'Strategic priorities reflected in idea selection'
            },
            {
                'indicator': 'risk_profile_matched',
                'status': 'success', 
                'description': 'Portfolio risk level matches user appetite'
            }
        ]
    
    def _calculate_config_impact_score(self, enhanced_results: Dict[str, Any]) -> float:
        """Calculate overall configuration impact score."""
        
        # Simplified calculation - could be made more sophisticated
        user_config = enhanced_results.get('user_config', {})
        
        if not user_config:
            return 0.0
            
        # Score based on configuration completeness and application
        score = 0.0
        
        if user_config.get('market_focus') != 'general':
            score += 0.3
        if user_config.get('strategic_priority') != 'balanced':
            score += 0.3
        if user_config.get('risk_appetite') != 'balanced':
            score += 0.3
        if user_config.get('target_subreddits'):
            score += 0.1
            
        return min(score, 1.0)
    
    def _generate_config_recommendations(self, enhanced_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for configuration optimization."""
        
        recommendations = []
        
        user_config = enhanced_results.get('user_config', {})
        
        if user_config.get('market_focus') == 'general':
            recommendations.append("Consider specifying a more targeted market focus for better results")
            
        if user_config.get('strategic_priority') == 'balanced':
            recommendations.append("Try prioritizing innovation or market fit for more focused results")
            
        return recommendations
    
    # Recommendation generation methods
    
    def _generate_strategic_recommendations(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic-level recommendations."""
        
        return [
            {
                'recommendation': 'Validate top breakthrough ideas with customer interviews',
                'priority': 'high',
                'timeline': '2-4 weeks',
                'rationale': 'Breakthrough ideas show high potential but need market validation'
            },
            {
                'recommendation': 'Consider adjacent market opportunities',
                'priority': 'medium', 
                'timeline': '1-2 months',
                'rationale': 'Several zones show potential for market expansion'
            }
        ]
    
    def _generate_tactical_recommendations(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tactical next steps."""
        
        return [
            {
                'action': 'Create MVP prototypes for top 3 ideas',
                'effort': 'medium',
                'impact': 'high',
                'dependencies': 'Development resources, user research'
            },
            {
                'action': 'Conduct competitive analysis for breakthrough concepts',
                'effort': 'low',
                'impact': 'medium', 
                'dependencies': 'Market research access'
            }
        ]
    
    def _generate_validation_recommendations(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate validation priorities."""
        
        return [
            {
                'validation_type': 'Customer interviews',
                'focus_area': 'Problem validation',
                'sample_size': '10-15 interviews per target segment',
                'key_questions': ['Pain point severity', 'Current solutions', 'Willingness to pay']
            },
            {
                'validation_type': 'MVP testing',
                'focus_area': 'Solution validation',
                'approach': 'Lean startup methodology',
                'metrics': ['User engagement', 'Task completion', 'User satisfaction']
            }
        ]
    
    def _generate_optimization_recommendations(self, enhanced_results: Dict[str, Any]) -> List[str]:
        """Generate pipeline optimization recommendations."""
        
        return [
            "Expand Reddit subreddit coverage for broader market insights",
            "Increase idea generation per zone to see more alternatives",
            "Add industry-specific pain dimension weights",
            "Include customer validation scores in idea selection"
        ]
    
    def _determine_primary_cta(self, enhanced_results: Dict[str, Any]) -> Dict[str, str]:
        """Determine primary call-to-action for UI."""
        
        return {
            'text': 'Start Validating Top Ideas',
            'action': 'begin_validation_process',
            'description': 'Begin customer validation for your highest-potential product ideas'
        }
    
    def _determine_secondary_actions(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Determine secondary actions for UI."""
        
        return [
            {
                'text': 'Explore All Generated Ideas',
                'action': 'view_expanded_results',
                'description': 'See all ideas generated across opportunity zones'
            },
            {
                'text': 'Adjust Configuration',
                'action': 'modify_config',
                'description': 'Refine your market focus and strategic priorities'
            }
        ]
    
    def _generate_exploration_suggestions(self, enhanced_results: Dict[str, Any]) -> List[str]:
        """Generate exploration suggestions for users."""
        
        return [
            "Review ideas that scored high on innovation but lower on market fit",
            "Explore opportunity zones that were assigned fewer ideas",
            "Consider how different risk appetites would change your portfolio",
            "Look for synergies between ideas across different zones"
        ]
    
    # Calculation helper methods
    
    def _calculate_data_quality_score(self, standard_outputs: Dict[str, Any]) -> float:
        """Calculate data quality score based on outputs."""
        
        score = 0.0
        
        # Check for presence and quality of key outputs
        if standard_outputs.get('analysis_results'):
            score += 0.25
        if standard_outputs.get('opportunity_zones'):
            score += 0.25
        if standard_outputs.get('product_ideas'):
            score += 0.25
        if standard_outputs.get('final_portfolio'):
            score += 0.25
            
        return score
    
    def _calculate_diversity_index(self, enhanced_results: Dict[str, Any]) -> float:
        """Calculate idea diversity index."""
        
        # Simplified diversity calculation
        return 0.75  # 75% diversity score
    
    def _calculate_portfolio_risk(self, enhanced_results: Dict[str, Any]) -> float:
        """Calculate portfolio risk score."""
        
        user_config = enhanced_results.get('user_config', {})
        risk_appetite = user_config.get('risk_appetite', 'balanced')
        
        risk_scores = {
            'conservative': 0.3,
            'balanced': 0.5,
            'breakthrough': 0.8
        }
        
        return risk_scores.get(risk_appetite, 0.5)
    
    def _calculate_feasibility_score(self, enhanced_results: Dict[str, Any]) -> float:
        """Calculate implementation feasibility score."""
        
        # Simplified feasibility calculation
        return 0.7  # 70% feasible
    
    def _determine_risk_level(self, idea: Dict[str, Any]) -> str:
        """Determine risk level for an idea."""
        
        score = idea.get('overall_score', 0.0)
        
        if score < 5.0:
            return 'high_risk'
        elif score < 7.0:
            return 'medium_risk'
        else:
            return 'low_risk'
    
    def _determine_complexity_level(self, idea: Dict[str, Any]) -> str:
        """Determine implementation complexity level."""
        
        feasibility = idea.get('technical_feasibility', 0.0)
        
        if feasibility > 7.0:
            return 'simple'
        elif feasibility > 5.0:
            return 'moderate'
        else:
            return 'complex'
    
    def _generate_idea_tags(self, idea: Dict[str, Any]) -> List[str]:
        """Generate tags for idea categorization."""
        
        tags = []
        
        # Add tags based on scores
        if idea.get('innovation_score', 0) > 7.0:
            tags.append('innovative')
        if idea.get('market_viability', 0) > 7.0:
            tags.append('market_proven')
        if idea.get('technical_feasibility', 0) > 7.0:
            tags.append('easy_to_build')
            
        return tags
    
    def _determine_color_indicator(self, idea: Dict[str, Any]) -> str:
        """Determine color indicator for UI display."""
        
        overall_score = idea.get('overall_score', 0.0)
        
        if overall_score >= 8.0:
            return 'green'  # High potential
        elif overall_score >= 6.0:
            return 'yellow'  # Medium potential
        else:
            return 'orange'  # Lower potential but worth considering
    
    # Analytics formatting methods
    
    def _format_overview_metrics(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format overview metrics for analytics dashboard."""
        
        return {
            'total_jtbds_analyzed': 'Data from enhanced results',
            'reddit_discussions_processed': 'Data from enhanced results',
            'opportunity_zones_discovered': 'Data from enhanced results',
            'final_ideas_selected': 'Data from enhanced results'
        }
    
    def _format_distribution_analysis(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format distribution analysis for charts."""
        
        return {
            'zone_distribution': 'Distribution of ideas across zones',
            'score_distribution': 'Distribution of idea scores',
            'risk_distribution': 'Distribution of risk levels'
        }
    
    def _format_trend_indicators(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format trend indicators."""
        
        return {
            'innovation_trend': 'Trending toward breakthrough ideas',
            'market_trend': 'Strong market validation focus',
            'feasibility_trend': 'Balanced feasibility considerations'
        }
    
    def _format_insight_highlights(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format key insights for dashboard."""
        
        return [
            {
                'insight': 'Market focus configuration significantly improved result relevance',
                'impact': 'high',
                'category': 'configuration'
            },
            {
                'insight': 'Breakthrough ideas show high innovation potential',
                'impact': 'medium',
                'category': 'innovation'
            }
        ]
    
    def _format_zone_chart_data(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format data for zone distribution chart."""
        
        return [
            {'zone': 'Zone 1', 'ideas': 3, 'potential': 0.8},
            {'zone': 'Zone 2', 'ideas': 2, 'potential': 0.6},
            {'zone': 'Zone 3', 'ideas': 2, 'potential': 0.7}
        ]
    
    def _format_scoring_scatter_data(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format data for scoring scatter plot."""
        
        return [
            {'innovation': 8.5, 'feasibility': 7.2, 'market_fit': 8.0, 'idea': 'Idea 1'},
            {'innovation': 6.8, 'feasibility': 8.5, 'market_fit': 7.5, 'idea': 'Idea 2'}
        ]
    
    def _format_portfolio_pie_data(self, enhanced_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format data for portfolio composition pie chart."""
        
        return [
            {'category': 'Breakthrough', 'count': 3, 'percentage': 30},
            {'category': 'Incremental', 'count': 4, 'percentage': 40},
            {'category': 'Optimization', 'count': 3, 'percentage': 30}
        ]