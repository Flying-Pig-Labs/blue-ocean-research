"""
Selection Reporting System
========================

Generates comprehensive reports on the selection process with zone-by-zone
analysis and breakthrough preservation metrics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from .idea_score import IdeaScore


@dataclass
class ZoneAnalysis:
    """Analysis results for a single opportunity zone"""
    zone_name: str
    total_ideas: int
    selected_ideas: int
    selection_rate: float
    avg_composite_score: float
    breakthrough_count: int
    moonshot_count: int
    risk_distribution: Dict[str, int]
    top_idea: Optional[Dict[str, Any]]


@dataclass
class BreakthroughMetrics:
    """Metrics for breakthrough idea preservation"""
    total_breakthroughs: int
    preserved_breakthroughs: int
    preservation_rate: float
    total_moonshots: int
    preserved_moonshots: int
    moonshot_preservation_rate: float
    dropped_breakthroughs: List[Dict[str, Any]]


class SelectionReporter:
    """
    Comprehensive reporting system for selection process analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize selection reporter"""
        if config is None:
            config = IdeaScore.load_config()
        
        self.config = config
    
    def generate_report(self, original_zone_results: List[Dict[str, Any]],
                       filtering_results,
                       final_selection_results,
                       optimization_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate comprehensive selection report
        
        Args:
            original_zone_results: Original zone processing results
            filtering_results: Smart filtering results
            final_selection_results: Final selection results
            optimization_results: Optional cross-zone optimization results
            
        Returns:
            Comprehensive report dictionary
        """
        
        # Generate zone-by-zone analysis
        zone_analysis = self._analyze_zones(original_zone_results, final_selection_results)
        
        # Calculate breakthrough preservation metrics
        breakthrough_metrics = self._calculate_breakthrough_metrics(
            original_zone_results, final_selection_results
        )
        
        # Generate selection summary
        selection_summary = self._generate_selection_summary(
            original_zone_results, filtering_results, final_selection_results
        )
        
        # Analyze selection quality
        quality_analysis = self._analyze_selection_quality(final_selection_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            zone_analysis, breakthrough_metrics, quality_analysis
        )
        
        # Create executive summary
        executive_summary = self._create_executive_summary(
            zone_analysis, breakthrough_metrics, selection_summary, quality_analysis
        )
        
        report = {
            'metadata': {
                'report_generated': datetime.now().isoformat(),
                'report_version': '1.0',
                'configuration': self._get_config_summary()
            },
            'executive_summary': executive_summary,
            'selection_summary': selection_summary,
            'zone_analysis': zone_analysis,
            'breakthrough_metrics': breakthrough_metrics,
            'quality_analysis': quality_analysis,
            'recommendations': recommendations,
            'detailed_results': {
                'filtering_results': self._summarize_filtering_results(filtering_results),
                'final_selection': self._summarize_final_selection(final_selection_results),
                'optimization_results': optimization_results
            }
        }
        
        return report
    
    def _analyze_zones(self, original_results: List[Dict[str, Any]],
                      final_results) -> List[ZoneAnalysis]:
        """Analyze results by opportunity zone"""
        zone_analyses = []
        
        # Group final selections by zone
        final_by_zone = {}
        for idea in final_results.final_selection:
            zone_name = idea.get('zone_name', 'Unknown')
            if zone_name not in final_by_zone:
                final_by_zone[zone_name] = []
            final_by_zone[zone_name].append(idea)
        
        for zone_result in original_results:
            zone = zone_result.get('zone', {})
            zone_name = zone.get('name', 'Unknown')
            all_ideas = zone_result.get('all_ideas', [])
            
            selected_ideas = final_by_zone.get(zone_name, [])
            
            # Calculate metrics
            total_ideas = len(all_ideas)
            selected_count = len(selected_ideas)
            selection_rate = selected_count / total_ideas if total_ideas > 0 else 0
            
            # Calculate average composite score for selected ideas
            composite_scores = []
            for idea in selected_ideas:
                scoring = idea.get('scoring', {})
                composite_scores.append(scoring.get('composite_score', 0))
            
            avg_composite = sum(composite_scores) / len(composite_scores) if composite_scores else 0
            
            # Count breakthroughs and moonshots
            breakthrough_count = sum(
                1 for idea in selected_ideas
                if idea.get('scoring', {}).get('breakthrough_analysis', {}).is_breakthrough
            )
            
            moonshot_count = sum(
                1 for idea in selected_ideas
                if idea.get('scoring', {}).get('breakthrough_analysis', {}).is_moonshot
            )
            
            # Risk distribution
            risk_distribution = {}
            for idea in selected_ideas:
                risk_level = idea.get('scoring', {}).get('idea_score', IdeaScore()).get_risk_level()
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Find top idea
            top_idea = None
            if selected_ideas:
                top_idea = max(
                    selected_ideas,
                    key=lambda x: x.get('scoring', {}).get('composite_score', 0)
                )
            
            zone_analysis = ZoneAnalysis(
                zone_name=zone_name,
                total_ideas=total_ideas,
                selected_ideas=selected_count,
                selection_rate=selection_rate,
                avg_composite_score=avg_composite,
                breakthrough_count=breakthrough_count,
                moonshot_count=moonshot_count,
                risk_distribution=risk_distribution,
                top_idea=top_idea
            )
            
            zone_analyses.append(zone_analysis)
        
        return zone_analyses
    
    def _calculate_breakthrough_metrics(self, original_results: List[Dict[str, Any]],
                                      final_results) -> BreakthroughMetrics:
        """Calculate breakthrough preservation metrics"""
        
        # Count total breakthroughs and moonshots
        total_breakthroughs = 0
        total_moonshots = 0
        all_original_ideas = []
        
        for zone_result in original_results:
            ideas = zone_result.get('all_ideas', [])
            all_original_ideas.extend(ideas)
            
            for idea in ideas:
                # Add scoring if not present (for backward compatibility)
                if 'scoring' not in idea:
                    idea_score = IdeaScore.from_idea_data(idea, self.config)
                    # Simplified breakthrough detection for missing data
                    is_breakthrough = idea_score.innovation_score >= 7.5
                    is_moonshot = idea_score.innovation_score >= 8.5
                    
                    idea['scoring'] = {
                        'idea_score': idea_score,
                        'breakthrough_analysis': type('obj', (object,), {
                            'is_breakthrough': is_breakthrough,
                            'is_moonshot': is_moonshot
                        })()
                    }
                
                breakthrough_analysis = idea.get('scoring', {}).get('breakthrough_analysis')
                if breakthrough_analysis:
                    if breakthrough_analysis.is_breakthrough:
                        total_breakthroughs += 1
                    if breakthrough_analysis.is_moonshot:
                        total_moonshots += 1
        
        # Count preserved breakthroughs and moonshots
        preserved_breakthroughs = 0
        preserved_moonshots = 0
        
        for idea in final_results.final_selection:
            breakthrough_analysis = idea.get('scoring', {}).get('breakthrough_analysis')
            if breakthrough_analysis:
                if breakthrough_analysis.is_breakthrough:
                    preserved_breakthroughs += 1
                if breakthrough_analysis.is_moonshot:
                    preserved_moonshots += 1
        
        # Identify dropped breakthroughs
        final_ids = {id(idea) for idea in final_results.final_selection}
        dropped_breakthroughs = []
        
        for idea in all_original_ideas:
            if id(idea) not in final_ids:
                breakthrough_analysis = idea.get('scoring', {}).get('breakthrough_analysis')
                if breakthrough_analysis and breakthrough_analysis.is_breakthrough:
                    dropped_breakthroughs.append({
                        'name': idea.get('name', 'Unknown'),
                        'zone_name': idea.get('zone_name', 'Unknown'),
                        'composite_score': idea.get('scoring', {}).get('composite_score', 0),
                        'is_moonshot': breakthrough_analysis.is_moonshot
                    })
        
        # Calculate preservation rates
        breakthrough_preservation_rate = (
            preserved_breakthroughs / total_breakthroughs 
            if total_breakthroughs > 0 else 1.0
        )
        
        moonshot_preservation_rate = (
            preserved_moonshots / total_moonshots 
            if total_moonshots > 0 else 1.0
        )
        
        return BreakthroughMetrics(
            total_breakthroughs=total_breakthroughs,
            preserved_breakthroughs=preserved_breakthroughs,
            preservation_rate=breakthrough_preservation_rate,
            total_moonshots=total_moonshots,
            preserved_moonshots=preserved_moonshots,
            moonshot_preservation_rate=moonshot_preservation_rate,
            dropped_breakthroughs=dropped_breakthroughs
        )
    
    def _generate_selection_summary(self, original_results: List[Dict[str, Any]],
                                  filtering_results,
                                  final_results) -> Dict[str, Any]:
        """Generate high-level selection summary"""
        
        # Count total ideas across all stages
        total_original = sum(len(zone.get('all_ideas', [])) for zone in original_results)
        total_filtered = len(filtering_results.selected_ideas)
        total_final = len(final_results.final_selection)
        
        # Calculate reduction rates
        filtering_reduction = (total_original - total_filtered) / total_original if total_original > 0 else 0
        final_reduction = (total_filtered - total_final) / total_filtered if total_filtered > 0 else 0
        overall_reduction = (total_original - total_final) / total_original if total_original > 0 else 0
        
        # Calculate average scores at each stage
        def get_avg_composite_score(ideas):
            scores = [idea.get('scoring', {}).get('composite_score', 0) for idea in ideas]
            return sum(scores) / len(scores) if scores else 0
        
        all_original_ideas = []
        for zone in original_results:
            all_original_ideas.extend(zone.get('all_ideas', []))
        
        # Ensure scoring is available for original ideas
        for idea in all_original_ideas:
            if 'scoring' not in idea:
                idea_score = IdeaScore.from_idea_data(idea, self.config)
                idea['scoring'] = {'composite_score': idea_score.composite_score}
        
        avg_original_score = get_avg_composite_score(all_original_ideas)
        avg_filtered_score = get_avg_composite_score(filtering_results.selected_ideas)
        avg_final_score = get_avg_composite_score(final_results.final_selection)
        
        return {
            'idea_counts': {
                'original': total_original,
                'after_filtering': total_filtered,
                'final_selection': total_final
            },
            'reduction_rates': {
                'filtering_stage': filtering_reduction,
                'selection_stage': final_reduction,
                'overall': overall_reduction
            },
            'quality_progression': {
                'original_avg_score': avg_original_score,
                'filtered_avg_score': avg_filtered_score,
                'final_avg_score': avg_final_score,
                'quality_improvement': avg_final_score - avg_original_score
            },
            'zones_processed': len(original_results),
            'selection_confidence': final_results.selection_confidence
        }
    
    def _analyze_selection_quality(self, final_results) -> Dict[str, Any]:
        """Analyze the quality of the final selection"""
        
        ideas = final_results.final_selection
        
        if not ideas:
            return {'error': 'No ideas in final selection'}
        
        # Score distributions
        composite_scores = []
        innovation_scores = []
        viability_scores = []
        breakthrough_scores = []
        
        for idea in ideas:
            scoring = idea.get('scoring', {})
            idea_score = scoring.get('idea_score', IdeaScore())
            
            composite_scores.append(scoring.get('composite_score', 0))
            innovation_scores.append(idea_score.innovation_score)
            viability_scores.append(idea_score.viability_score)
            breakthrough_scores.append(idea_score.breakthrough_score)
        
        # Calculate statistics
        def calc_stats(scores):
            if not scores:
                return {'avg': 0, 'min': 0, 'max': 0, 'std': 0}
            
            avg = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)
            std = variance ** 0.5
            
            return {
                'avg': round(avg, 2),
                'min': round(min_score, 2),
                'max': round(max_score, 2),
                'std': round(std, 2)
            }
        
        # Risk distribution
        risk_distribution = {}
        for idea in ideas:
            risk_level = idea.get('scoring', {}).get('idea_score', IdeaScore()).get_risk_level()
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Market coverage
        market_segments = set()
        for idea in ideas:
            segment = idea.get('target_segment', '').lower()
            if 'b2b' in segment or 'business' in segment:
                market_segments.add('B2B')
            if 'b2c' in segment or 'consumer' in segment:
                market_segments.add('B2C')
            if 'b2g' in segment or 'government' in segment:
                market_segments.add('B2G')
        
        # Innovation diversity
        innovation_categories = {
            'incremental': sum(1 for s in innovation_scores if s < 6.0),
            'moderate': sum(1 for s in innovation_scores if 6.0 <= s < 8.0),
            'high': sum(1 for s in innovation_scores if s >= 8.0)
        }
        
        return {
            'score_statistics': {
                'composite': calc_stats(composite_scores),
                'innovation': calc_stats(innovation_scores),
                'viability': calc_stats(viability_scores),
                'breakthrough': calc_stats(breakthrough_scores)
            },
            'risk_distribution': risk_distribution,
            'market_coverage': {
                'segments_covered': list(market_segments),
                'coverage_count': len(market_segments)
            },
            'innovation_diversity': innovation_categories,
            'portfolio_balance': {
                'high_innovation_ratio': innovation_categories['high'] / len(ideas),
                'high_viability_ratio': sum(1 for s in viability_scores if s >= 7.0) / len(ideas),
                'balanced_ideas': sum(1 for i, v in zip(innovation_scores, viability_scores) 
                                    if i >= 6.0 and v >= 6.0)
            }
        }
    
    def _generate_recommendations(self, zone_analysis: List[ZoneAnalysis],
                                breakthrough_metrics: BreakthroughMetrics,
                                quality_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Zone-based recommendations
        low_selection_zones = [z for z in zone_analysis if z.selection_rate < 0.3]
        if low_selection_zones:
            recommendations.append({
                'category': 'Zone Balance',
                'priority': 'Medium',
                'recommendation': f"Consider reviewing selection criteria for zones with low selection rates: "
                                f"{', '.join(z.zone_name for z in low_selection_zones)}",
                'impact': 'Portfolio diversification'
            })
        
        # Breakthrough preservation recommendations
        if breakthrough_metrics.preservation_rate < 0.7:
            recommendations.append({
                'category': 'Innovation Risk',
                'priority': 'High',
                'recommendation': f"Breakthrough preservation rate is low ({breakthrough_metrics.preservation_rate:.1%}). "
                                f"Consider adjusting filtering criteria to better preserve innovative ideas.",
                'impact': 'Innovation potential'
            })
        
        if breakthrough_metrics.moonshot_preservation_rate < 0.5:
            recommendations.append({
                'category': 'Moonshot Risk',
                'priority': 'High',
                'recommendation': f"Moonshot preservation rate is concerning ({breakthrough_metrics.moonshot_preservation_rate:.1%}). "
                                f"Review selection criteria to ensure moonshot ideas are not systematically excluded.",
                'impact': 'Paradigm-shifting potential'
            })
        
        # Quality-based recommendations
        if 'score_statistics' in quality_analysis:
            avg_innovation = quality_analysis['score_statistics']['innovation']['avg']
            if avg_innovation < 6.0:
                recommendations.append({
                    'category': 'Innovation Level',
                    'priority': 'Medium',
                    'recommendation': f"Average innovation score is low ({avg_innovation:.1f}). "
                                    f"Consider including more innovative ideas to boost portfolio potential.",
                    'impact': 'Future competitiveness'
                })
            
            avg_viability = quality_analysis['score_statistics']['viability']['avg']
            if avg_viability < 6.0:
                recommendations.append({
                    'category': 'Execution Risk',
                    'priority': 'Medium',
                    'recommendation': f"Average viability score is low ({avg_viability:.1f}). "
                                    f"Focus on improving technical feasibility and market readiness.",
                    'impact': 'Implementation success'
                })
        
        # Portfolio balance recommendations
        if 'portfolio_balance' in quality_analysis:
            balance = quality_analysis['portfolio_balance']
            if balance['high_innovation_ratio'] < 0.3:
                recommendations.append({
                    'category': 'Innovation Balance',
                    'priority': 'Medium',
                    'recommendation': "Low proportion of high-innovation ideas. "
                                    "Consider including more breakthrough concepts for future growth.",
                    'impact': 'Long-term competitive advantage'
                })
        
        # Market coverage recommendations
        if 'market_coverage' in quality_analysis:
            coverage_count = quality_analysis['market_coverage']['coverage_count']
            if coverage_count == 1:
                recommendations.append({
                    'category': 'Market Risk',
                    'priority': 'Low',
                    'recommendation': "Portfolio is concentrated in a single market segment. "
                                    "Consider diversifying across B2B, B2C, and B2G markets.",
                    'impact': 'Market risk mitigation'
                })
        
        return recommendations
    
    def _create_executive_summary(self, zone_analysis: List[ZoneAnalysis],
                                breakthrough_metrics: BreakthroughMetrics,
                                selection_summary: Dict[str, Any],
                                quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary of the selection process"""
        
        # Key metrics
        total_zones = len(zone_analysis)
        total_ideas_processed = selection_summary['idea_counts']['original']
        final_selection_count = selection_summary['idea_counts']['final_selection']
        overall_reduction = selection_summary['reduction_rates']['overall']
        quality_improvement = selection_summary['quality_progression']['quality_improvement']
        
        # Top performing zones
        top_zones = sorted(zone_analysis, key=lambda x: x.avg_composite_score, reverse=True)[:3]
        
        # Risk assessment
        risk_level = 'Low'
        risk_factors = []
        
        if breakthrough_metrics.preservation_rate < 0.5:
            risk_level = 'High'
            risk_factors.append('Low breakthrough preservation')
        elif breakthrough_metrics.preservation_rate < 0.7:
            risk_level = 'Medium'
            risk_factors.append('Moderate breakthrough preservation')
        
        if quality_analysis.get('score_statistics', {}).get('viability', {}).get('avg', 0) < 6.0:
            if risk_level == 'Low':
                risk_level = 'Medium'
            risk_factors.append('Low average viability')
        
        # Success indicators
        success_indicators = []
        
        if quality_improvement > 1.0:
            success_indicators.append('Significant quality improvement through filtering')
        
        if breakthrough_metrics.moonshot_preservation_rate >= 0.8:
            success_indicators.append('Excellent moonshot preservation')
        
        if len(top_zones) > 0 and top_zones[0].avg_composite_score >= 8.0:
            success_indicators.append('High-quality zone leadership')
        
        return {
            'process_overview': {
                'zones_analyzed': total_zones,
                'ideas_processed': total_ideas_processed,
                'final_selection': final_selection_count,
                'reduction_rate': f"{overall_reduction:.1%}",
                'quality_improvement': f"+{quality_improvement:.1f} points"
            },
            'key_achievements': success_indicators,
            'risk_assessment': {
                'overall_risk': risk_level,
                'risk_factors': risk_factors
            },
            'breakthrough_performance': {
                'total_identified': breakthrough_metrics.total_breakthroughs,
                'preservation_rate': f"{breakthrough_metrics.preservation_rate:.1%}",
                'moonshots_preserved': f"{breakthrough_metrics.preserved_moonshots}/{breakthrough_metrics.total_moonshots}"
            },
            'top_performing_zones': [
                {
                    'name': zone.zone_name,
                    'avg_score': zone.avg_composite_score,
                    'selection_count': zone.selected_ideas
                }
                for zone in top_zones
            ],
            'selection_confidence': selection_summary['selection_confidence']
        }
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Get summary of configuration used"""
        return {
            'excellence_threshold': self.config.get('excellence_threshold', 8.5),
            'moonshot_preservation_threshold': self.config.get('moonshot_preservation_threshold', 8.0),
            'weights': self.config.get('weights', {}),
            'breakthrough_thresholds': self.config.get('breakthrough_thresholds', {})
        }
    
    def _summarize_filtering_results(self, filtering_results) -> Dict[str, Any]:
        """Summarize filtering results"""
        return {
            'total_selected': len(filtering_results.selected_ideas),
            'total_dropped': len(filtering_results.dropped_ideas),
            'excellence_preserved': len(filtering_results.excellence_preserved),
            'warnings_count': len(filtering_results.warnings),
            'filtering_stats': filtering_results.filtering_stats
        }
    
    def _summarize_final_selection(self, final_results) -> Dict[str, Any]:
        """Summarize final selection results"""
        return {
            'final_count': len(final_results.final_selection),
            'strategies_used': len(final_results.ensemble_strategies),
            'consensus_strength': final_results.consensus_analysis.get('consensus_strength', 0),
            'selection_confidence': final_results.selection_confidence,
            'warnings_count': len(final_results.warnings),
            'high_value_drops': len(final_results.dropped_high_value_ideas)
        }
    
    def export_report_markdown(self, report: Dict[str, Any]) -> str:
        """Export report as markdown format"""
        md_content = []
        
        # Title and metadata
        md_content.append("# Product Idea Selection Report")
        md_content.append(f"\n**Generated:** {report['metadata']['report_generated']}")
        md_content.append(f"**Version:** {report['metadata']['report_version']}\n")
        
        # Executive Summary
        md_content.append("## Executive Summary\n")
        exec_summary = report['executive_summary']
        
        overview = exec_summary['process_overview']
        md_content.append(f"- **Zones Analyzed:** {overview['zones_analyzed']}")
        md_content.append(f"- **Ideas Processed:** {overview['ideas_processed']}")
        md_content.append(f"- **Final Selection:** {overview['final_selection']}")
        md_content.append(f"- **Reduction Rate:** {overview['reduction_rate']}")
        md_content.append(f"- **Quality Improvement:** {overview['quality_improvement']}")
        md_content.append(f"- **Selection Confidence:** {exec_summary['selection_confidence']}/10\n")
        
        # Key Achievements
        if exec_summary['key_achievements']:
            md_content.append("### Key Achievements")
            for achievement in exec_summary['key_achievements']:
                md_content.append(f"- {achievement}")
            md_content.append("")
        
        # Risk Assessment
        risk = exec_summary['risk_assessment']
        md_content.append(f"### Risk Assessment: {risk['overall_risk']}")
        if risk['risk_factors']:
            for factor in risk['risk_factors']:
                md_content.append(f"- ⚠️ {factor}")
        md_content.append("")
        
        # Breakthrough Performance
        bt = exec_summary['breakthrough_performance']
        md_content.append("### Breakthrough Performance")
        md_content.append(f"- **Total Breakthroughs Identified:** {bt['total_identified']}")
        md_content.append(f"- **Preservation Rate:** {bt['preservation_rate']}")
        md_content.append(f"- **Moonshots Preserved:** {bt['moonshots_preserved']}\n")
        
        # Zone Analysis
        md_content.append("## Zone-by-Zone Analysis\n")
        for zone in report['zone_analysis']:
            md_content.append(f"### {zone.zone_name}")
            md_content.append(f"- **Ideas:** {zone.selected_ideas}/{zone.total_ideas} ({zone.selection_rate:.1%})")
            md_content.append(f"- **Average Score:** {zone.avg_composite_score:.2f}")
            md_content.append(f"- **Breakthroughs:** {zone.breakthrough_count}")
            md_content.append(f"- **Moonshots:** {zone.moonshot_count}")
            
            if zone.top_idea:
                top_name = zone.top_idea.get('name', 'Unknown')
                top_score = zone.top_idea.get('scoring', {}).get('composite_score', 0)
                md_content.append(f"- **Top Idea:** {top_name} ({top_score:.2f})")
            
            md_content.append("")
        
        # Recommendations
        if report['recommendations']:
            md_content.append("## Recommendations\n")
            for rec in report['recommendations']:
                priority_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(rec['priority'], '⚪')
                md_content.append(f"### {priority_emoji} {rec['category']} ({rec['priority']} Priority)")
                md_content.append(f"{rec['recommendation']}")
                md_content.append(f"**Impact:** {rec['impact']}\n")
        
        return "\n".join(md_content)
    
    def export_report_json(self, report: Dict[str, Any], filepath: str) -> None:
        """Export report as JSON file"""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)