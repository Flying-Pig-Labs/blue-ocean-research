"""
Cross-Zone Portfolio Optimization
================================

Optimizes idea selection across opportunity zones considering synergies,
portfolio balance, and multi-objective optimization.
"""

from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
import itertools
from collections import defaultdict
from .idea_score import IdeaScore


@dataclass
class SynergyAnalysis:
    """Analysis of synergies between ideas"""
    idea_pairs: List[Tuple[str, str]]
    synergy_score: float
    synergy_type: str
    explanation: str
    risk_mitigation: bool
    market_expansion: bool


@dataclass
class PortfolioMetrics:
    """Portfolio optimization metrics"""
    innovation_diversity: float
    risk_balance: float
    market_coverage: float
    technical_synergy: float
    resource_efficiency: float
    overall_balance: float


class CrossZoneOptimizer:
    """
    Multi-objective portfolio optimizer that considers synergies between ideas
    across different opportunity zones
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize cross-zone optimizer"""
        if config is None:
            config = IdeaScore.load_config()
        
        self.config = config
        
        # Synergy detection parameters
        self.synergy_keywords = {
            'platform': ['platform', 'ecosystem', 'infrastructure', 'foundation'],
            'data': ['data', 'analytics', 'intelligence', 'insights', 'learning'],
            'integration': ['api', 'integration', 'connect', 'interoperable', 'compatible'],
            'technology': ['ai', 'ml', 'blockchain', 'cloud', 'iot', 'automation'],
            'user_experience': ['user', 'interface', 'experience', 'design', 'usability'],
            'market': ['customer', 'market', 'segment', 'channel', 'distribution']
        }
        
        # Portfolio balance weights
        self.portfolio_weights = config.get('portfolio_weights', {
            'innovation_diversity': 0.25,
            'risk_balance': 0.20,
            'market_coverage': 0.20,
            'technical_synergy': 0.20,
            'resource_efficiency': 0.15
        })
    
    def optimize_portfolio(self, selected_ideas: List[Dict[str, Any]], 
                          max_adjustments: int = 5) -> Dict[str, Any]:
        """
        Optimize the portfolio of selected ideas across zones
        
        Args:
            selected_ideas: Currently selected ideas from filtering
            max_adjustments: Maximum number of optimization adjustments
            
        Returns:
            Dictionary with optimized portfolio and analysis
        """
        # Calculate baseline portfolio metrics
        baseline_metrics = self._calculate_portfolio_metrics(selected_ideas)
        
        # Identify synergies between ideas
        synergies = self._identify_synergies(selected_ideas)
        
        # Analyze portfolio gaps and imbalances
        gaps_analysis = self._analyze_portfolio_gaps(selected_ideas)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(
            selected_ideas, synergies, gaps_analysis, baseline_metrics
        )
        
        # Apply optimizations within constraints
        optimized_ideas, optimization_log = self._apply_optimizations(
            selected_ideas, recommendations, max_adjustments
        )
        
        # Calculate optimized metrics
        optimized_metrics = self._calculate_portfolio_metrics(optimized_ideas)
        
        return {
            'original_ideas': selected_ideas,
            'optimized_ideas': optimized_ideas,
            'baseline_metrics': baseline_metrics,
            'optimized_metrics': optimized_metrics,
            'improvement': self._calculate_improvement(baseline_metrics, optimized_metrics),
            'synergies': synergies,
            'gaps_analysis': gaps_analysis,
            'recommendations': recommendations,
            'optimization_log': optimization_log
        }
    
    def _calculate_portfolio_metrics(self, ideas: List[Dict[str, Any]]) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        if not ideas:
            return PortfolioMetrics(0, 0, 0, 0, 0, 0)
        
        # Innovation diversity
        innovation_scores = [idea.get('scoring', {}).get('idea_score', IdeaScore()).innovation_score 
                           for idea in ideas]
        innovation_diversity = self._calculate_diversity(innovation_scores)
        
        # Risk balance
        risk_balance = self._calculate_risk_balance(ideas)
        
        # Market coverage
        market_coverage = self._calculate_market_coverage(ideas)
        
        # Technical synergy
        technical_synergy = self._calculate_technical_synergy(ideas)
        
        # Resource efficiency
        resource_efficiency = self._calculate_resource_efficiency(ideas)
        
        # Overall balance
        weights = self.portfolio_weights
        overall_balance = (
            innovation_diversity * weights.get('innovation_diversity', 0.25) +
            risk_balance * weights.get('risk_balance', 0.20) +
            market_coverage * weights.get('market_coverage', 0.20) +
            technical_synergy * weights.get('technical_synergy', 0.20) +
            resource_efficiency * weights.get('resource_efficiency', 0.15)
        )
        
        return PortfolioMetrics(
            innovation_diversity=round(innovation_diversity, 2),
            risk_balance=round(risk_balance, 2),
            market_coverage=round(market_coverage, 2),
            technical_synergy=round(technical_synergy, 2),
            resource_efficiency=round(resource_efficiency, 2),
            overall_balance=round(overall_balance, 2)
        )
    
    def _calculate_diversity(self, scores: List[float]) -> float:
        """Calculate diversity score from a list of values"""
        if len(scores) <= 1:
            return 0.0
        
        # Calculate coefficient of variation (normalized standard deviation)
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        if mean_score == 0:
            return 0.0
        
        # Normalize to 0-10 scale where higher values indicate better diversity
        cv = std_dev / mean_score
        diversity_score = min(10.0, cv * 10)  # Scale coefficient of variation
        
        return diversity_score
    
    def _calculate_risk_balance(self, ideas: List[Dict[str, Any]]) -> float:
        """Calculate risk balance across the portfolio"""
        risk_levels = []
        
        for idea in ideas:
            scoring = idea.get('scoring', {})
            idea_score = scoring.get('idea_score')
            
            if idea_score:
                # Calculate risk score (inverse of viability and confidence)
                risk_score = 10 - (idea_score.viability_score + idea_score.confidence_score) / 2
                risk_levels.append(risk_score)
        
        if not risk_levels:
            return 5.0
        
        # Ideal risk balance: mix of low, medium, and high risk ideas
        low_risk = sum(1 for r in risk_levels if r <= 3.0)
        medium_risk = sum(1 for r in risk_levels if 3.0 < r <= 6.0)
        high_risk = sum(1 for r in risk_levels if r > 6.0)
        
        total_ideas = len(risk_levels)
        
        # Calculate balance score (penalize extreme imbalances)
        low_ratio = low_risk / total_ideas
        medium_ratio = medium_risk / total_ideas
        high_ratio = high_risk / total_ideas
        
        # Ideal distribution: 40% low, 40% medium, 20% high risk
        ideal_low, ideal_medium, ideal_high = 0.4, 0.4, 0.2
        
        balance_score = 10 - (
            abs(low_ratio - ideal_low) +
            abs(medium_ratio - ideal_medium) +
            abs(high_ratio - ideal_high)
        ) * 5  # Scale factor
        
        return max(0.0, balance_score)
    
    def _calculate_market_coverage(self, ideas: List[Dict[str, Any]]) -> float:
        """Calculate market coverage diversity"""
        markets = set()
        segments = set()
        
        for idea in ideas:
            # Extract market/segment information
            target_segment = idea.get('target_segment', '').lower()
            value_prop = idea.get('value_proposition', '').lower()
            
            # Identify market types
            if any(term in target_segment + value_prop for term in ['b2b', 'business', 'enterprise']):
                markets.add('b2b')
            if any(term in target_segment + value_prop for term in ['b2c', 'consumer', 'individual']):
                markets.add('b2c')
            if any(term in target_segment + value_prop for term in ['b2g', 'government', 'public']):
                markets.add('b2g')
            
            # Identify industry segments
            industries = ['healthcare', 'finance', 'education', 'retail', 'manufacturing', 
                         'transportation', 'energy', 'entertainment', 'agriculture']
            for industry in industries:
                if industry in target_segment + value_prop:
                    segments.add(industry)
        
        # Score based on coverage breadth
        market_diversity = len(markets) * 2  # Up to 6 points for market types
        segment_diversity = min(4, len(segments))  # Up to 4 points for industry segments
        
        return market_diversity + segment_diversity
    
    def _calculate_technical_synergy(self, ideas: List[Dict[str, Any]]) -> float:
        """Calculate technical synergy potential"""
        synergy_score = 0.0
        total_pairs = 0
        
        # Compare all pairs of ideas for technical synergies
        for i, idea1 in enumerate(ideas):
            for j, idea2 in enumerate(ideas[i+1:], i+1):
                total_pairs += 1
                pair_synergy = self._calculate_pair_technical_synergy(idea1, idea2)
                synergy_score += pair_synergy
        
        if total_pairs == 0:
            return 0.0
        
        return synergy_score / total_pairs
    
    def _calculate_pair_technical_synergy(self, idea1: Dict[str, Any], idea2: Dict[str, Any]) -> float:
        """Calculate technical synergy between two ideas"""
        text1 = self._extract_idea_text(idea1)
        text2 = self._extract_idea_text(idea2)
        
        synergy_score = 0.0
        
        # Check for shared technology categories
        for category, keywords in self.synergy_keywords.items():
            if category == 'technology':
                matches1 = sum(1 for keyword in keywords if keyword in text1)
                matches2 = sum(1 for keyword in keywords if keyword in text2)
                if matches1 > 0 and matches2 > 0:
                    synergy_score += 2.0
        
        # Check for platform/ecosystem synergies
        platform_keywords = self.synergy_keywords['platform']
        if any(keyword in text1 for keyword in platform_keywords) and \
           any(keyword in text2 for keyword in platform_keywords):
            synergy_score += 3.0
        
        # Check for data/integration synergies
        if any(keyword in text1 for keyword in self.synergy_keywords['data']) and \
           any(keyword in text2 for keyword in self.synergy_keywords['integration']):
            synergy_score += 1.5
        
        return min(10.0, synergy_score)
    
    def _calculate_resource_efficiency(self, ideas: List[Dict[str, Any]]) -> float:
        """Calculate resource efficiency of the portfolio"""
        total_efficiency = 0.0
        
        for idea in ideas:
            scoring = idea.get('scoring', {})
            idea_score = scoring.get('idea_score')
            
            if idea_score:
                # Resource efficiency = high viability with reasonable resource requirements
                viability = idea_score.viability_score
                resource_req = idea_score.viability_breakdown.get('resource_requirements', 5.0)
                
                # Higher resource_requirements score means LESS resources needed
                efficiency = (viability + resource_req) / 2
                total_efficiency += efficiency
        
        return total_efficiency / len(ideas) if ideas else 0.0
    
    def _identify_synergies(self, ideas: List[Dict[str, Any]]) -> List[SynergyAnalysis]:
        """Identify synergies between ideas"""
        synergies = []
        
        # Check all pairs of ideas
        for i, idea1 in enumerate(ideas):
            for j, idea2 in enumerate(ideas[i+1:], i+1):
                synergy = self._analyze_idea_pair_synergy(idea1, idea2)
                if synergy.synergy_score >= 3.0:  # Significant synergy threshold
                    synergies.append(synergy)
        
        # Sort by synergy score
        synergies.sort(key=lambda x: x.synergy_score, reverse=True)
        
        return synergies
    
    def _analyze_idea_pair_synergy(self, idea1: Dict[str, Any], idea2: Dict[str, Any]) -> SynergyAnalysis:
        """Analyze synergy between two specific ideas"""
        text1 = self._extract_idea_text(idea1)
        text2 = self._extract_idea_text(idea2)
        
        synergy_score = 0.0
        synergy_types = []
        explanations = []
        risk_mitigation = False
        market_expansion = False
        
        # Technology synergy
        tech_synergy = self._calculate_pair_technical_synergy(idea1, idea2)
        if tech_synergy >= 2.0:
            synergy_score += tech_synergy
            synergy_types.append('Technical')
            explanations.append('Shared technology stack or complementary technologies')
        
        # Platform synergy
        if any(kw in text1 for kw in self.synergy_keywords['platform']) and \
           any(kw in text2 for kw in self.synergy_keywords['platform']):
            synergy_score += 3.0
            synergy_types.append('Platform')
            explanations.append('Platform ecosystem opportunities')
        
        # Data synergy
        if any(kw in text1 for kw in self.synergy_keywords['data']) and \
           any(kw in text2 for kw in self.synergy_keywords['data']):
            synergy_score += 2.0
            synergy_types.append('Data')
            explanations.append('Shared data or analytics capabilities')
        
        # Market synergy
        segment1 = idea1.get('target_segment', '').lower()
        segment2 = idea2.get('target_segment', '').lower()
        
        # Check for complementary markets
        if ('b2b' in segment1 and 'b2c' in segment2) or ('b2c' in segment1 and 'b2b' in segment2):
            synergy_score += 1.5
            synergy_types.append('Market')
            explanations.append('Complementary market segments')
            market_expansion = True
        
        # Risk mitigation synergy
        scoring1 = idea1.get('scoring', {})
        scoring2 = idea2.get('scoring', {})
        
        risk1 = scoring1.get('idea_score', IdeaScore()).get_risk_level()
        risk2 = scoring2.get('idea_score', IdeaScore()).get_risk_level()
        
        if ('High Risk' in risk1 and 'Low Risk' in risk2) or ('Low Risk' in risk1 and 'High Risk' in risk2):
            synergy_score += 1.0
            synergy_types.append('Risk Balance')
            explanations.append('Risk balancing between high and low risk ideas')
            risk_mitigation = True
        
        # User experience synergy
        if any(kw in text1 for kw in self.synergy_keywords['user_experience']) and \
           any(kw in text2 for kw in self.synergy_keywords['user_experience']):
            synergy_score += 1.0
            synergy_types.append('UX')
            explanations.append('Shared user experience patterns')
        
        synergy_type = ' + '.join(synergy_types) if synergy_types else 'None'
        explanation = '; '.join(explanations) if explanations else 'No significant synergy detected'
        
        return SynergyAnalysis(
            idea_pairs=[idea1.get('name', 'Unknown'), idea2.get('name', 'Unknown')],
            synergy_score=round(synergy_score, 2),
            synergy_type=synergy_type,
            explanation=explanation,
            risk_mitigation=risk_mitigation,
            market_expansion=market_expansion
        )
    
    def _analyze_portfolio_gaps(self, ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze gaps and imbalances in the portfolio"""
        gaps = {
            'innovation_gaps': [],
            'market_gaps': [],
            'technology_gaps': [],
            'risk_imbalances': [],
            'zone_imbalances': []
        }
        
        # Innovation spectrum analysis
        innovation_scores = [idea.get('scoring', {}).get('idea_score', IdeaScore()).innovation_score 
                           for idea in ideas]
        
        if innovation_scores:
            avg_innovation = sum(innovation_scores) / len(innovation_scores)
            if avg_innovation < 6.0:
                gaps['innovation_gaps'].append('Low overall innovation level')
            if max(innovation_scores) - min(innovation_scores) < 3.0:
                gaps['innovation_gaps'].append('Limited innovation diversity')
        
        # Market coverage analysis
        market_types = set()
        for idea in ideas:
            target = idea.get('target_segment', '').lower()
            if 'b2b' in target or 'business' in target:
                market_types.add('B2B')
            if 'b2c' in target or 'consumer' in target:
                market_types.add('B2C')
            if 'b2g' in target or 'government' in target:
                market_types.add('B2G')
        
        if len(market_types) == 1:
            gaps['market_gaps'].append(f'Limited to {list(market_types)[0]} market only')
        
        # Technology diversity analysis
        tech_categories = defaultdict(int)
        for idea in ideas:
            text = self._extract_idea_text(idea)
            for category, keywords in self.synergy_keywords.items():
                if any(kw in text for kw in keywords):
                    tech_categories[category] += 1
        
        if len(tech_categories) < 3:
            gaps['technology_gaps'].append('Limited technology diversity')
        
        # Risk balance analysis
        risk_distribution = defaultdict(int)
        for idea in ideas:
            risk_level = idea.get('scoring', {}).get('idea_score', IdeaScore()).get_risk_level()
            risk_distribution[risk_level] += 1
        
        total_ideas = len(ideas)
        if risk_distribution.get('High Risk', 0) / total_ideas > 0.6:
            gaps['risk_imbalances'].append('Portfolio too heavily weighted toward high-risk ideas')
        elif risk_distribution.get('Low Risk', 0) / total_ideas > 0.8:
            gaps['risk_imbalances'].append('Portfolio too conservative, lacking breakthrough potential')
        
        # Zone balance analysis
        zone_distribution = defaultdict(int)
        for idea in ideas:
            zone_name = idea.get('zone_name', 'Unknown')
            zone_distribution[zone_name] += 1
        
        if len(zone_distribution) > 1:
            max_zone_count = max(zone_distribution.values())
            min_zone_count = min(zone_distribution.values())
            if max_zone_count / min_zone_count > 3:
                gaps['zone_imbalances'].append('Uneven distribution across opportunity zones')
        
        return gaps
    
    def _generate_optimization_recommendations(self, ideas: List[Dict[str, Any]], 
                                             synergies: List[SynergyAnalysis],
                                             gaps: Dict[str, Any],
                                             metrics: PortfolioMetrics) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Synergy-based recommendations
        for synergy in synergies[:3]:  # Top 3 synergies
            if synergy.synergy_score >= 5.0:
                recommendations.append({
                    'type': 'enhance_synergy',
                    'priority': 'high',
                    'description': f'Leverage synergy between {synergy.idea_pairs[0]} and {synergy.idea_pairs[1]}',
                    'rationale': synergy.explanation,
                    'impact': synergy.synergy_score
                })
        
        # Gap-filling recommendations
        for gap_category, gap_list in gaps.items():
            for gap in gap_list:
                recommendations.append({
                    'type': 'fill_gap',
                    'priority': 'medium',
                    'description': f'Address {gap_category.replace("_", " ")}: {gap}',
                    'rationale': 'Portfolio balance improvement',
                    'impact': 3.0
                })
        
        # Balance recommendations
        if metrics.risk_balance < 6.0:
            recommendations.append({
                'type': 'rebalance_risk',
                'priority': 'medium',
                'description': 'Improve risk balance across portfolio',
                'rationale': f'Current risk balance score: {metrics.risk_balance}',
                'impact': 4.0
            })
        
        if metrics.innovation_diversity < 5.0:
            recommendations.append({
                'type': 'increase_diversity',
                'priority': 'high',
                'description': 'Increase innovation diversity',
                'rationale': f'Current innovation diversity: {metrics.innovation_diversity}',
                'impact': 5.0
            })
        
        # Sort by priority and impact
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['impact']), reverse=True)
        
        return recommendations
    
    def _apply_optimizations(self, ideas: List[Dict[str, Any]], 
                           recommendations: List[Dict[str, Any]], 
                           max_adjustments: int) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Apply optimization recommendations within constraints"""
        optimized_ideas = ideas.copy()
        optimization_log = []
        
        adjustments_made = 0
        
        for rec in recommendations:
            if adjustments_made >= max_adjustments:
                break
            
            rec_type = rec['type']
            
            if rec_type == 'enhance_synergy':
                # For now, just log the synergy (actual enhancement would require additional ideas)
                optimization_log.append(f"Identified synergy opportunity: {rec['description']}")
            
            elif rec_type == 'fill_gap':
                optimization_log.append(f"Gap identified: {rec['description']}")
            
            elif rec_type == 'rebalance_risk':
                # Try to reorder ideas to better balance risk
                rebalanced = self._rebalance_risk(optimized_ideas)
                if rebalanced:
                    optimized_ideas = rebalanced
                    optimization_log.append("Applied risk rebalancing")
                    adjustments_made += 1
            
            elif rec_type == 'increase_diversity':
                optimization_log.append(f"Diversity improvement needed: {rec['description']}")
        
        return optimized_ideas, optimization_log
    
    def _rebalance_risk(self, ideas: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Attempt to rebalance risk distribution"""
        # Sort ideas by risk level
        risk_sorted = sorted(ideas, key=lambda x: x.get('scoring', {}).get('idea_score', IdeaScore()).get_risk_level())
        
        # For now, return the risk-sorted list (more sophisticated rebalancing could be added)
        return risk_sorted
    
    def _extract_idea_text(self, idea: Dict[str, Any]) -> str:
        """Extract text content from idea for analysis"""
        text_fields = ['name', 'value_proposition', 'features', 'differentiation', 'target_segment']
        text_parts = []
        
        for field in text_fields:
            value = idea.get(field, '')
            if isinstance(value, list):
                text_parts.extend(str(item) for item in value)
            elif value:
                text_parts.append(str(value))
        
        return ' '.join(text_parts).lower()
    
    def _calculate_improvement(self, baseline: PortfolioMetrics, optimized: PortfolioMetrics) -> Dict[str, float]:
        """Calculate improvement metrics"""
        return {
            'innovation_diversity_improvement': optimized.innovation_diversity - baseline.innovation_diversity,
            'risk_balance_improvement': optimized.risk_balance - baseline.risk_balance,
            'market_coverage_improvement': optimized.market_coverage - baseline.market_coverage,
            'technical_synergy_improvement': optimized.technical_synergy - baseline.technical_synergy,
            'resource_efficiency_improvement': optimized.resource_efficiency - baseline.resource_efficiency,
            'overall_balance_improvement': optimized.overall_balance - baseline.overall_balance
        }