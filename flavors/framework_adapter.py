#!/usr/bin/env python3
"""
Framework Adapter System - Pluggable Strategic Analysis Frameworks

Provides a pluggable system for applying different strategic frameworks to opportunity zones.
Frameworks are completely swappable via YAML configuration, enabling domain-specific analysis
while maintaining consistent input/output interfaces.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class FrameworkResult:
    """Result of framework analysis on an opportunity zone."""
    zone_id: str
    zone_name: str
    framework_name: str
    scores: Dict[str, float]  # Framework dimension scores (0.0-1.0)
    rationales: Dict[str, str]  # Explanations for each dimension
    overall_score: float  # Weighted overall framework score
    recommendations: List[str]  # Specific recommendations
    citations: List[str]  # References to supporting evidence
    confidence_level: float  # Analysis confidence (0.0-1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'zone_id': self.zone_id,
            'zone_name': self.zone_name,
            'framework_name': self.framework_name,
            'scores': self.scores,
            'rationales': self.rationales,
            'overall_score': self.overall_score,
            'recommendations': self.recommendations,
            'citations': self.citations,
            'confidence_level': self.confidence_level
        }

class FrameworkAdapter(ABC):
    """Base class for all strategic analysis frameworks."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize framework with configuration."""
        self.config = config
        self.name = self.__class__.__name__.replace('Adapter', '').lower()
        
    @abstractmethod
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """
        Analyze an opportunity zone using this framework.
        
        Args:
            zone: Opportunity zone data with JTBDs, pain dimensions, solution requirements
            context: Additional context (research content, Reddit discussions, etc.)
            
        Returns:
            FrameworkResult with scores, rationales, and recommendations
        """
        pass
    
    @abstractmethod 
    def get_dimensions(self) -> List[str]:
        """Get the analysis dimensions for this framework."""
        pass
    
    @abstractmethod
    def get_scoring_criteria(self) -> Dict[str, str]:
        """Get description of scoring criteria for each dimension."""
        pass

class ERRCAdapter(FrameworkAdapter):
    """Blue Ocean Strategy ERRC Framework Adapter."""
    
    def get_dimensions(self) -> List[str]:
        return ['eliminate', 'reduce', 'raise', 'create']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'eliminate': 'Industry factors that should be eliminated completely',
            'reduce': 'Factors that should be reduced well below industry standards',
            'raise': 'Factors that should be raised well above industry standards', 
            'create': 'New factors that the industry has never offered'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze zone using Blue Ocean ERRC framework."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        # Extract pain dimensions and solution requirements
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbd_descriptions = zone.get('jtbd_descriptions', [])
        
        # ERRC Analysis Logic
        scores = {}
        rationales = {}
        citations = []
        
        # ELIMINATE: What traditional approaches create unnecessary friction?
        eliminate_factors = []
        eliminate_score = 0.0
        if 'process_complexity' in pain_dims and pain_dims['process_complexity'] > 0.5:
            eliminate_factors.append('Complex multi-step processes')
            eliminate_score += 0.3
        if 'communication_gaps' in pain_dims and pain_dims['communication_gaps'] > 0.5:
            eliminate_factors.append('Information silos and poor communication')
            eliminate_score += 0.3
        if 'trust_issues' in pain_dims and pain_dims['trust_issues'] > 0.4:
            eliminate_factors.append('Lack of transparency and verification')
            eliminate_score += 0.4
            
        scores['eliminate'] = min(eliminate_score, 1.0)
        rationales['eliminate'] = f"Eliminate: {', '.join(eliminate_factors) if eliminate_factors else 'No major elimination opportunities identified'}"
        
        # REDUCE: What factors can be simplified or minimized?
        reduce_factors = []
        reduce_score = 0.0
        if 'timing_coordination' in pain_dims and pain_dims['timing_coordination'] > 0.4:
            reduce_factors.append('Time-consuming coordination overhead')
            reduce_score += 0.4
        if 'financial_stress' in pain_dims and pain_dims['financial_stress'] > 0.6:
            reduce_factors.append('High upfront costs and fees')
            reduce_score += 0.4
        if 'decision_anxiety' in pain_dims and pain_dims['decision_anxiety'] > 0.5:
            reduce_factors.append('Decision complexity and choice paralysis')
            reduce_score += 0.2
            
        scores['reduce'] = min(reduce_score, 1.0)
        rationales['reduce'] = f"Reduce: {', '.join(reduce_factors) if reduce_factors else 'Limited reduction opportunities'}"
        
        # RAISE: What factors should be elevated above industry standards?
        raise_factors = []
        raise_score = 0.0
        if any('automation' in req.lower() for req in solutions):
            raise_factors.append('Automation and intelligent assistance')
            raise_score += 0.3
        if any('real-time' in req.lower() or 'instant' in req.lower() for req in solutions):
            raise_factors.append('Real-time information and updates')
            raise_score += 0.3
        if 'trust_issues' in pain_dims and pain_dims['trust_issues'] > 0.3:
            raise_factors.append('Transparency and trust mechanisms')
            raise_score += 0.4
            
        scores['raise'] = min(raise_score, 1.0)
        rationales['raise'] = f"Raise: {', '.join(raise_factors) if raise_factors else 'Standard elevation opportunities'}"
        
        # CREATE: What new factors can provide unprecedented value?
        create_factors = []
        create_score = 0.0
        if 'technology_gaps' in pain_dims and pain_dims['technology_gaps'] > 0.5:
            create_factors.append('AI-powered predictive insights')
            create_score += 0.4
        if len(solutions) > 3:  # Rich solution space indicates innovation potential
            create_factors.append('Integrated ecosystem approach')
            create_score += 0.3
        if any('platform' in req.lower() or 'hub' in req.lower() for req in solutions):
            create_factors.append('Unified platform experience')
            create_score += 0.3
            
        scores['create'] = min(create_score, 1.0)
        rationales['create'] = f"Create: {', '.join(create_factors) if create_factors else 'Limited creation opportunities identified'}"
        
        # Overall score (weighted by Blue Ocean impact)
        weights = {'eliminate': 0.3, 'reduce': 0.25, 'raise': 0.25, 'create': 0.2}
        overall_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        # Generate recommendations
        recommendations = []
        if scores['eliminate'] > 0.6:
            recommendations.append("Focus on eliminating industry friction points to create uncontested market space")
        if scores['create'] > 0.5:
            recommendations.append("Emphasize unique value creation that competitors cannot easily replicate")
        if overall_score > 0.6:
            recommendations.append("Strong Blue Ocean opportunity - pursue differentiated strategy")
        else:
            recommendations.append("Consider hybrid approach combining differentiation with cost optimization")
            
        # Add citations from JTBDs
        citations = [f"JTBD evidence: {desc}" for desc in jtbd_descriptions[:3]]
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='ERRC',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=citations,
            confidence_level=min(0.8, overall_score + 0.2)  # Higher confidence with stronger signals
        )

class JTBDAdapter(FrameworkAdapter):
    """Jobs-to-be-Done Framework Adapter."""
    
    def get_dimensions(self) -> List[str]:
        return ['functional', 'emotional', 'social']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'functional': 'What functional job is the customer trying to accomplish?',
            'emotional': 'What emotional outcome does the customer desire?',
            'social': 'How does the customer want to be perceived by others?'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze zone using Jobs-to-be-Done framework."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds_addressed', [])
        
        scores = {}
        rationales = {}
        
        # FUNCTIONAL: Core task/problem being solved
        functional_indicators = ['process_complexity', 'technology_gaps', 'timing_coordination']
        functional_score = sum(pain_dims.get(dim, 0) for dim in functional_indicators) / len(functional_indicators)
        scores['functional'] = min(functional_score, 1.0)
        rationales['functional'] = f"Functional job strength based on task-oriented pain points (score: {functional_score:.2f})"
        
        # EMOTIONAL: Feelings and desired outcomes
        emotional_indicators = ['decision_anxiety', 'trust_issues', 'financial_stress']
        emotional_score = sum(pain_dims.get(dim, 0) for dim in emotional_indicators) / len(emotional_indicators)
        scores['emotional'] = min(emotional_score, 1.0)
        rationales['emotional'] = f"Emotional job strength based on anxiety and trust factors (score: {emotional_score:.2f})"
        
        # SOCIAL: Perception and status concerns
        social_indicators = ['communication_gaps', 'market_dynamics']
        social_score = sum(pain_dims.get(dim, 0) for dim in social_indicators) / len(social_indicators)
        # Boost social score if there are multiple stakeholders involved
        if len(solutions) > 2 and any('multi-party' in req.lower() or 'stakeholder' in req.lower() for req in solutions):
            social_score = min(social_score + 0.3, 1.0)
        scores['social'] = social_score
        rationales['social'] = f"Social job strength based on communication and perception factors (score: {social_score:.2f})"
        
        # Overall score (weighted by JTBD importance)
        weights = {'functional': 0.5, 'emotional': 0.3, 'social': 0.2}
        overall_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        recommendations = []
        if scores['functional'] > 0.7:
            recommendations.append("Strong functional job - focus on core task efficiency and effectiveness")
        if scores['emotional'] > 0.6:
            recommendations.append("Significant emotional component - address anxiety and trust concerns")
        if scores['social'] > 0.5:
            recommendations.append("Social dimension present - consider multi-stakeholder experience design")
            
        citations = [f"JTBD cluster: {jtbd}" for jtbd in jtbds[:3]]
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='JTBD',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=citations,
            confidence_level=min(0.9, len(jtbds) * 0.1 + 0.5)  # Higher confidence with more JTBDs
        )

class UnifyAdapter(FrameworkAdapter):
    """UNIFY Framework Adapter for City Revitalization with Uncommon Alliances."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.weights = config.get('weights', {
            'NA': 0.20,   # Need Alignment
            'UPS': 0.25,  # Uncommon Pairing Strength  
            'FZ': 0.15,   # Feasibility
            'IP': 0.20,   # Impact Potential
            'NR': 0.10,   # Narrative Resonance
            'RS': 0.10    # Resilience
        })
        self.require_alliance_map = config.get('require_alliance_map', True)
        
    def get_dimensions(self) -> List[str]:
        return ['need_alignment', 'uncommon_pairing_strength', 'feasibility', 'impact_potential', 'narrative_resonance', 'resilience']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'need_alignment': 'How directly the initiative addresses urban pain points and community goals',
            'uncommon_pairing_strength': 'Degree of novelty and cross-boundary alliance formation', 
            'feasibility': 'Practicality in terms of cost, governance, logistics, and policy constraints',
            'impact_potential': 'Expected economic, social, cultural, and environmental uplift',
            'narrative_resonance': 'Story power and compelling nature for community buy-in and funding',
            'resilience': 'Likelihood the alliance survives under stress (political shifts, funding shortfalls)'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze opportunity zone for city revitalization potential using UNIFY framework."""
        zone_id = zone.get('id', 'unknown')
        zone_name = zone.get('name', f'Zone {zone_id}')
        
        # Extract key zone information
        pain_dimensions = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds', [])
        discussions = zone.get('discussions', [])
        
        # UNIFY dimension scoring
        scores = {}
        rationales = {}
        
        # Need Alignment (NA) - how directly addresses urban challenges
        urban_indicators = ['community_disconnect', 'economic_decline', 'infrastructure_gaps', 'resource_scarcity']
        need_score = sum(pain_dimensions.get(dim, 0) for dim in urban_indicators) / len(urban_indicators)
        # Boost for directly addressing multiple urban challenges
        if len([dim for dim in urban_indicators if pain_dimensions.get(dim, 0) > 0.5]) >= 2:
            need_score = min(need_score + 0.2, 1.0)
        scores['need_alignment'] = need_score
        rationales['need_alignment'] = f"Need alignment based on urban challenge indicators (score: {need_score:.2f})"
        
        # Uncommon Pairing Strength (UPS) - cross-sector alliance potential
        cross_sector_keywords = ['partnership', 'alliance', 'collaboration', 'coalition', 'unusual', 'unexpected']
        cross_sector_mentions = sum(1 for disc in discussions for keyword in cross_sector_keywords if keyword in disc.lower())
        diversity_indicators = ['multi-party', 'stakeholder', 'community', 'business', 'nonprofit', 'government']
        diversity_score = len([ind for ind in diversity_indicators if any(ind in sol.lower() for sol in solutions)]) / len(diversity_indicators)
        uncommon_score = min((cross_sector_mentions * 0.1) + diversity_score, 1.0)
        scores['uncommon_pairing_strength'] = uncommon_score
        rationales['uncommon_pairing_strength'] = f"Cross-sector alliance potential from discussions and stakeholder diversity (score: {uncommon_score:.2f})"
        
        # Feasibility (FZ) - practical implementation assessment
        feasibility_barriers = ['governance_barriers', 'resource_scarcity', 'regulatory_risk']
        barrier_score = sum(pain_dimensions.get(dim, 0) for dim in feasibility_barriers) / len(feasibility_barriers)
        feasibility_score = max(0.1, 1.0 - barrier_score)  # Invert barriers to get feasibility
        # Boost if solutions mention concrete steps
        concrete_keywords = ['pilot', 'timeline', 'budget', 'partnership agreement', 'MOU']
        if any(keyword in ' '.join(solutions).lower() for keyword in concrete_keywords):
            feasibility_score = min(feasibility_score + 0.15, 1.0)
        scores['feasibility'] = feasibility_score
        rationales['feasibility'] = f"Implementation feasibility based on barriers and concrete planning indicators (score: {feasibility_score:.2f})"
        
        # Impact Potential (IP) - expected community uplift
        impact_keywords = ['jobs', 'economic', 'safety', 'health', 'education', 'housing', 'environment']
        impact_mentions = sum(1 for disc in discussions for keyword in impact_keywords if keyword in disc.lower())
        scale_indicators = ['neighborhood', 'district', 'citywide', 'regional']
        scale_score = len([ind for ind in scale_indicators if any(ind in disc.lower() for disc in discussions)]) / len(scale_indicators)
        impact_score = min((impact_mentions * 0.05) + scale_score, 1.0)
        scores['impact_potential'] = impact_score
        rationales['impact_potential'] = f"Impact potential from community benefit mentions and scale indicators (score: {impact_score:.2f})"
        
        # Narrative Resonance (NR) - story power and community appeal
        story_keywords = ['story', 'compelling', 'inspiring', 'innovative', 'first', 'unique', 'model']
        story_mentions = sum(1 for disc in discussions for keyword in story_keywords if keyword in disc.lower())
        community_keywords = ['community', 'local', 'resident', 'neighbor', 'grassroots']
        community_mentions = sum(1 for disc in discussions for keyword in community_keywords if keyword in disc.lower())
        narrative_score = min((story_mentions * 0.1) + (community_mentions * 0.05), 1.0)
        scores['narrative_resonance'] = narrative_score  
        rationales['narrative_resonance'] = f"Narrative appeal from story power and community connection mentions (score: {narrative_score:.2f})"
        
        # Resilience (RS) - alliance stability under stress
        stability_keywords = ['sustainable', 'long-term', 'permanent', 'institutionalize', 'formalize']
        risk_keywords = ['political', 'funding', 'leadership', 'turnover', 'change']
        stability_mentions = sum(1 for disc in discussions for keyword in stability_keywords if keyword in disc.lower())
        risk_mentions = sum(1 for disc in discussions for keyword in risk_keywords if keyword in disc.lower())
        resilience_score = max(0.1, min((stability_mentions * 0.2) + 0.5 - (risk_mentions * 0.1), 1.0))
        scores['resilience'] = resilience_score
        rationales['resilience'] = f"Alliance resilience from stability indicators minus risk factors (score: {resilience_score:.2f})"
        
        # Overall UNIFY score (weighted)
        dimension_weights = {
            'need_alignment': self.weights.get('NA', 0.20),
            'uncommon_pairing_strength': self.weights.get('UPS', 0.25),
            'feasibility': self.weights.get('FZ', 0.15),
            'impact_potential': self.weights.get('IP', 0.20),
            'narrative_resonance': self.weights.get('NR', 0.10),
            'resilience': self.weights.get('RS', 0.10)
        }
        overall_score = sum(scores[dim] * dimension_weights[dim] for dim in scores)
        
        # Generate recommendations based on UNIFY scores
        recommendations = []
        if scores['need_alignment'] > 0.7:
            recommendations.append("Strong need alignment - initiative directly addresses core urban challenges")
        if scores['uncommon_pairing_strength'] > 0.6:
            recommendations.append("High alliance potential - leverage cross-sector partnerships for innovative solutions")
        if scores['feasibility'] < 0.5:
            recommendations.append("Feasibility concerns - address governance and resource barriers before launch")
        if scores['impact_potential'] > 0.7:
            recommendations.append("High impact opportunity - scale initiative for maximum community benefit")
        if scores['narrative_resonance'] > 0.6:
            recommendations.append("Strong story potential - emphasize narrative for community buy-in and media attention")
        if scores['resilience'] < 0.5:
            recommendations.append("Resilience risk - develop contingency plans and diversify alliance support")
            
        citations = [f"Urban challenge cluster: {list(pain_dimensions.keys())[:3]}"]
        if discussions:
            citations.extend([f"Community discussion: {disc[:100]}..." for disc in discussions[:2]])
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='UNIFY',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=citations,
            confidence_level=min(0.9, len(discussions) * 0.05 + 0.6)  # Higher confidence with more community input
        )

class AcquireAdapter(FrameworkAdapter):
    """ACQUIRE Framework Adapter for Private Equity Acquisition Analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.weights = config.get('weights', {
            'A': 0.15,  # Addressable Fragmentation
            'C': 0.20,  # Cashflow Quality
            'Q': 0.15,  # Quality of Operations
            'U': 0.20,  # Upside Levers
            'I': 0.10,  # Integration Readiness
            'R': 0.10,  # Risk & Compliance (inverted)
            'E': 0.10   # Exit Pathways
        })
        self.boosts = config.get('boost', {
            'ownership_match': 0.05,
            'cluster_fit': 0.05
        })
        self.signals = config.get('signals', {
            'recurring_revenue_keywords': [],
            'digitization_keywords': []
        })
        
    def get_dimensions(self) -> List[str]:
        return ['addressable_fragmentation', 'cashflow_quality', 'quality_of_operations', 'upside_levers', 'integration_readiness', 'risk_compliance', 'exit_pathways']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'addressable_fragmentation': 'Market fragmentation, local density, and tuck-in potential assessment',
            'cashflow_quality': 'SDE/EBITDA clarity, seasonality, retention, and customer concentration analysis',
            'quality_of_operations': 'Process maturity, systems digitization, and KPI discipline evaluation',
            'upside_levers': 'Consolidation, digitization, geographic expansion, and operational excellence opportunities',
            'integration_readiness': 'Culture fit, SOPs, platform compatibility, and add-on suitability',
            'risk_compliance': 'Licenses, regulatory exposure, litigation, and contract risk assessment',
            'exit_pathways': 'Buyer universe, roll-up logic, and multiple expansion potential'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze opportunity zone for private equity acquisition potential using ACQUIRE framework."""
        zone_id = zone.get('id', 'unknown')
        zone_name = zone.get('name', f'Acquisition Zone {zone_id}')
        
        # Extract key zone information
        pain_dimensions = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds', [])
        discussions = zone.get('discussions', [])
        
        # ACQUIRE dimension scoring
        scores = {}
        rationales = {}
        
        # Addressable Fragmentation (A) - market fragmentation and consolidation opportunity
        fragmentation_indicators = ['market_fragmentation', 'consolidation_opportunity', 'competitive_gaps']
        fragmentation_score = sum(pain_dimensions.get(dim, 0) for dim in fragmentation_indicators) / len(fragmentation_indicators)
        # Boost for multiple fragmentation signals in discussions
        fragmentation_keywords = ['fragmented', 'consolidation', 'roll-up', 'acquisition', 'market share']
        fragmentation_mentions = sum(1 for disc in discussions for keyword in fragmentation_keywords if keyword in disc.lower())
        if fragmentation_mentions >= 2:
            fragmentation_score = min(fragmentation_score + 0.2, 1.0)
        scores['addressable_fragmentation'] = fragmentation_score
        rationales['addressable_fragmentation'] = f"Market fragmentation assessment based on consolidation indicators (score: {fragmentation_score:.2f})"
        
        # Cashflow Quality (C) - revenue predictability and financial health
        cashflow_keywords = ['recurring', 'subscription', 'contract', 'maintenance', 'retainer', 'predictable']
        recurring_mentions = sum(1 for disc in discussions for keyword in self.signals['recurring_revenue_keywords'] if keyword in disc.lower())
        seasonal_keywords = ['seasonal', 'volatility', 'cyclical']
        seasonal_mentions = sum(1 for disc in discussions for keyword in seasonal_keywords if keyword in disc.lower())
        
        base_cashflow = 0.6  # Base score for established businesses
        if recurring_mentions >= 2:
            base_cashflow = min(base_cashflow + 0.3, 1.0)  # Boost for recurring revenue
        if seasonal_mentions >= 1:
            base_cashflow = max(base_cashflow - 0.2, 0.1)  # Penalty for seasonality
        
        scores['cashflow_quality'] = base_cashflow
        rationales['cashflow_quality'] = f"Cashflow quality from recurring revenue signals and seasonality factors (score: {base_cashflow:.2f})"
        
        # Quality of Operations (Q) - process maturity and systems
        digitization_mentions = sum(1 for disc in discussions for keyword in self.signals['digitization_keywords'] if keyword in disc.lower())
        process_keywords = ['system', 'process', 'workflow', 'automated', 'digital', 'software']
        process_mentions = sum(1 for disc in discussions for keyword in process_keywords if keyword in disc.lower())
        
        ops_score = 0.4  # Base score
        ops_score += min(digitization_mentions * 0.1, 0.3)  # Boost for digitization
        ops_score += min(process_mentions * 0.05, 0.3)  # Boost for process mentions
        ops_score = min(ops_score, 1.0)
        
        scores['quality_of_operations'] = ops_score
        rationales['quality_of_operations'] = f"Operational quality from digitization and process maturity indicators (score: {ops_score:.2f})"
        
        # Upside Levers (U) - value creation opportunities
        upside_keywords = ['expansion', 'scale', 'growth', 'efficiency', 'automation', 'consolidate']
        upside_mentions = sum(1 for disc in discussions for keyword in upside_keywords if keyword in disc.lower())
        
        # Look for specific value driver mentions in solutions
        value_drivers = ['consolidation', 'digitization', 'geographic expansion', 'operational excellence']
        driver_matches = len([driver for driver in value_drivers if any(driver.lower() in sol.lower() for sol in solutions)])
        
        upside_score = 0.5 + min(upside_mentions * 0.05, 0.3) + min(driver_matches * 0.1, 0.2)
        scores['upside_levers'] = min(upside_score, 1.0)
        rationales['upside_levers'] = f"Value creation potential from growth and efficiency opportunities (score: {upside_score:.2f})"
        
        # Integration Readiness (I) - cultural and operational fit
        integration_keywords = ['culture', 'team', 'management', 'compatible', 'integrate']
        integration_mentions = sum(1 for disc in discussions for keyword in integration_keywords if keyword in disc.lower())
        
        # Look for red flags in discussions
        red_flags = ['difficult owner', 'resistant to change', 'family drama', 'key person risk']
        red_flag_mentions = sum(1 for disc in discussions for flag in red_flags if flag in disc.lower())
        
        integration_score = 0.7 - min(red_flag_mentions * 0.2, 0.5) + min(integration_mentions * 0.05, 0.2)
        scores['integration_readiness'] = max(min(integration_score, 1.0), 0.1)
        rationales['integration_readiness'] = f"Integration readiness from cultural fit and management quality signals (score: {integration_score:.2f})"
        
        # Risk & Compliance (R) - regulatory and operational risks (inverted)
        risk_keywords = ['litigation', 'regulatory', 'compliance', 'violation', 'lawsuit', 'fine']
        risk_mentions = sum(1 for disc in discussions for keyword in risk_keywords if keyword in disc.lower())
        
        # Industry-specific risk factors
        high_risk_industries = ['healthcare', 'financial', 'environmental', 'food service']
        industry_risk = 0.0
        all_text = ' '.join(discussions + solutions).lower()
        for industry in high_risk_industries:
            if industry in all_text:
                industry_risk += 0.1
                
        risk_score = min(risk_mentions * 0.2 + industry_risk, 0.8)  # Higher risk score = worse
        scores['risk_compliance'] = risk_score
        rationales['risk_compliance'] = f"Risk and compliance assessment from regulatory and legal indicators (score: {risk_score:.2f})"
        
        # Exit Pathways (E) - strategic buyer universe and exit potential
        exit_keywords = ['strategic buyer', 'acquisition target', 'IPO', 'exit', 'multiple expansion']
        exit_mentions = sum(1 for disc in discussions for keyword in exit_keywords if keyword in disc.lower())
        
        # Industry consolidation trend indicators
        consolidation_keywords = ['consolidating', 'private equity', 'strategic', 'platform']
        consolidation_mentions = sum(1 for disc in discussions for keyword in consolidation_keywords if keyword in disc.lower())
        
        exit_score = 0.5 + min(exit_mentions * 0.1, 0.2) + min(consolidation_mentions * 0.05, 0.3)
        scores['exit_pathways'] = min(exit_score, 1.0)
        rationales['exit_pathways'] = f"Exit pathway potential from strategic buyer and consolidation indicators (score: {exit_score:.2f})"
        
        # Calculate overall ACQUIRE score (with Risk inverted)
        dimension_weights = {
            'addressable_fragmentation': self.weights.get('A', 0.15),
            'cashflow_quality': self.weights.get('C', 0.20),
            'quality_of_operations': self.weights.get('Q', 0.15),
            'upside_levers': self.weights.get('U', 0.20),
            'integration_readiness': self.weights.get('I', 0.10),
            'risk_compliance': self.weights.get('R', 0.10),
            'exit_pathways': self.weights.get('E', 0.10)
        }
        
        # Calculate base score (with risk inverted)
        base_score = (
            scores['addressable_fragmentation'] * dimension_weights['addressable_fragmentation'] +
            scores['cashflow_quality'] * dimension_weights['cashflow_quality'] +
            scores['quality_of_operations'] * dimension_weights['quality_of_operations'] +
            scores['upside_levers'] * dimension_weights['upside_levers'] +
            scores['integration_readiness'] * dimension_weights['integration_readiness'] +
            (1.0 - scores['risk_compliance']) * dimension_weights['risk_compliance'] +  # Risk inverted
            scores['exit_pathways'] * dimension_weights['exit_pathways']
        )
        
        overall_score = base_score
        
        # Generate recommendations based on ACQUIRE scores
        recommendations = []
        if scores['addressable_fragmentation'] > 0.7:
            recommendations.append("High fragmentation opportunity - strong roll-up potential in target market")
        if scores['cashflow_quality'] > 0.7:
            recommendations.append("Strong recurring revenue base - attractive cash flow profile for PE investment")
        if scores['quality_of_operations'] < 0.5:
            recommendations.append("Operational improvement opportunity - focus on systems and process optimization")
        if scores['upside_levers'] > 0.7:
            recommendations.append("Multiple value creation levers available - strong growth and efficiency potential")
        if scores['integration_readiness'] < 0.5:
            recommendations.append("Integration risk - assess cultural fit and management retention carefully")
        if scores['risk_compliance'] > 0.5:
            recommendations.append("Elevated risk profile - thorough regulatory and legal due diligence required")
        if scores['exit_pathways'] > 0.6:
            recommendations.append("Strong exit potential - attractive strategic buyer universe and consolidation trends")
            
        citations = [f"Market analysis cluster: {list(pain_dimensions.keys())[:3]}"]
        if discussions:
            citations.extend([f"Acquisition discussion: {disc[:80]}..." for disc in discussions[:2]])
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='ACQUIRE',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=citations,
            confidence_level=min(0.9, len(discussions) * 0.05 + 0.7)  # Higher confidence with more market data
        )

class SiteFeasibilityAdapter(FrameworkAdapter):
    """Site Location Feasibility Framework Adapter."""
    
    def get_dimensions(self) -> List[str]:
        return ['accessibility', 'infrastructure', 'regulatory', 'economic', 'environmental']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'accessibility': 'Transportation, connectivity, and physical access quality',
            'infrastructure': 'Power, telecommunications, and utility infrastructure adequacy',
            'regulatory': 'Regulatory compliance feasibility and policy support',
            'economic': 'Cost efficiency and financial viability factors',
            'environmental': 'Environmental sustainability and climate suitability'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze zone for site location feasibility."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        
        scores = {}
        rationales = {}
        
        # ACCESSIBILITY: Transportation and connectivity
        accessibility_factors = []
        accessibility_score = 0.8  # Default good accessibility
        if 'timing_coordination' in pain_dims and pain_dims['timing_coordination'] > 0.5:
            accessibility_factors.append('Transportation coordination challenges')
            accessibility_score -= 0.3
        if any('remote' in req.lower() or 'location' in req.lower() for req in solutions):
            accessibility_factors.append('Location-specific requirements')
            accessibility_score += 0.2
        scores['accessibility'] = max(0.0, min(accessibility_score, 1.0))
        rationales['accessibility'] = f"Accessibility: {', '.join(accessibility_factors) if accessibility_factors else 'Standard accessibility requirements'}"
        
        # INFRASTRUCTURE: Utility and technical infrastructure
        infrastructure_score = 0.7  # Default adequate infrastructure
        if 'technology_gaps' in pain_dims and pain_dims['technology_gaps'] > 0.6:
            infrastructure_score += 0.2  # Infrastructure needs create opportunity
        if any('power' in req.lower() or 'cooling' in req.lower() for req in solutions):
            infrastructure_score += 0.1
        scores['infrastructure'] = min(infrastructure_score, 1.0)
        rationales['infrastructure'] = "Infrastructure adequacy based on technical requirements and gaps"
        
        # REGULATORY: Compliance and policy environment
        regulatory_score = 0.6  # Default moderate regulatory complexity
        if 'trust_issues' in pain_dims and pain_dims['trust_issues'] > 0.5:
            regulatory_score += 0.2  # Regulatory clarity can address trust
        if any('compliance' in req.lower() or 'regulatory' in req.lower() for req in solutions):
            regulatory_score += 0.2
        scores['regulatory'] = min(regulatory_score, 1.0)
        rationales['regulatory'] = "Regulatory feasibility based on compliance requirements and policy clarity"
        
        # ECONOMIC: Cost and financial viability
        economic_score = 0.5  # Neutral starting point
        if 'financial_stress' in pain_dims and pain_dims['financial_stress'] > 0.6:
            economic_score += 0.3  # High financial stress indicates cost optimization opportunity
        if 'market_dynamics' in pain_dims and pain_dims['market_dynamics'] > 0.4:
            economic_score += 0.2
        scores['economic'] = min(economic_score, 1.0)
        rationales['economic'] = "Economic viability based on cost pressures and market dynamics"
        
        # ENVIRONMENTAL: Sustainability and climate factors
        environmental_score = 0.7  # Default environmentally suitable
        if any('sustainable' in req.lower() or 'green' in req.lower() for req in solutions):
            environmental_score += 0.2
        scores['environmental'] = min(environmental_score, 1.0)
        rationales['environmental'] = "Environmental suitability for site operations"
        
        # Overall weighted score
        weights = {'accessibility': 0.25, 'infrastructure': 0.25, 'regulatory': 0.2, 'economic': 0.2, 'environmental': 0.1}
        overall_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        recommendations = []
        if scores['infrastructure'] > 0.7:
            recommendations.append("Strong infrastructure foundation - suitable for technology-intensive operations")
        if scores['economic'] > 0.7:
            recommendations.append("Favorable economic conditions - proceed with detailed financial analysis")
        if scores['regulatory'] > 0.6:
            recommendations.append("Manageable regulatory environment - develop compliance strategy")
        if overall_score > 0.7:
            recommendations.append("High site feasibility - recommended for detailed site analysis")
        else:
            recommendations.append("Moderate feasibility - identify specific improvement areas")
            
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='SiteFeasibility',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=[f"Site requirement: {req}" for req in solutions[:3]],
            confidence_level=0.8  # Site analysis typically has good data
        )

class SpecTradeoffsAdapter(FrameworkAdapter):
    """Technical Specification Tradeoffs Framework Adapter."""
    
    def get_dimensions(self) -> List[str]:
        return ['performance', 'cost', 'usability', 'reliability', 'scalability']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'performance': 'Speed, efficiency, and capability requirements vs. constraints',
            'cost': 'Development, manufacturing, and operational cost considerations', 
            'usability': 'User experience, ease of use, and accessibility requirements',
            'reliability': 'Safety, durability, and dependability requirements',
            'scalability': 'Growth potential and future expansion considerations'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze zone for technical specification tradeoffs."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        
        scores = {}
        rationales = {}
        
        # PERFORMANCE: Speed and capability requirements
        performance_score = 0.6  # Baseline performance expectation
        if 'timing_coordination' in pain_dims and pain_dims['timing_coordination'] > 0.5:
            performance_score += 0.3  # Time sensitivity increases performance needs
        if any('real-time' in req.lower() or 'fast' in req.lower() for req in solutions):
            performance_score += 0.2
        scores['performance'] = min(performance_score, 1.0)
        rationales['performance'] = "Performance requirements based on timing sensitivity and speed needs"
        
        # COST: Development and operational cost constraints
        cost_score = 0.7  # Default cost awareness
        if 'financial_stress' in pain_dims and pain_dims['financial_stress'] > 0.6:
            cost_score += 0.2  # High cost sensitivity
        scores['cost'] = min(cost_score, 1.0)
        rationales['cost'] = "Cost constraints based on financial sensitivity and budget pressures"
        
        # USABILITY: User experience requirements
        usability_score = 0.5  # Baseline usability
        if 'process_complexity' in pain_dims and pain_dims['process_complexity'] > 0.5:
            usability_score += 0.3  # Complexity issues drive usability needs
        if any('intuitive' in req.lower() or 'easy' in req.lower() for req in solutions):
            usability_score += 0.2
        scores['usability'] = min(usability_score, 1.0)
        rationales['usability'] = "Usability priority based on complexity issues and ease-of-use requirements"
        
        # RELIABILITY: Safety and dependability
        reliability_score = 0.8  # High default reliability expectation
        if 'trust_issues' in pain_dims and pain_dims['trust_issues'] > 0.4:
            reliability_score += 0.1  # Trust issues drive reliability needs
        if any('safety' in req.lower() or 'secure' in req.lower() for req in solutions):
            reliability_score = min(reliability_score + 0.1, 1.0)
        scores['reliability'] = reliability_score
        rationales['reliability'] = "Reliability requirements based on trust factors and safety needs"
        
        # SCALABILITY: Growth and expansion potential
        scalability_score = 0.6  # Moderate scalability baseline
        if 'market_dynamics' in pain_dims and pain_dims['market_dynamics'] > 0.5:
            scalability_score += 0.2  # Market pressure drives scalability needs
        if len(solutions) > 4:  # Complex solution space suggests scalability needs
            scalability_score += 0.1
        scores['scalability'] = min(scalability_score, 1.0)
        rationales['scalability'] = "Scalability needs based on market dynamics and solution complexity"
        
        # Overall score with engineering tradeoff weighting
        weights = {'performance': 0.25, 'cost': 0.2, 'usability': 0.2, 'reliability': 0.2, 'scalability': 0.15}
        overall_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        recommendations = []
        if scores['performance'] > 0.8 and scores['cost'] > 0.8:
            recommendations.append("High performance and cost sensitivity - optimize for efficiency")
        if scores['usability'] > 0.7:
            recommendations.append("Strong usability focus - prioritize user-centered design")
        if scores['reliability'] > 0.8:
            recommendations.append("Critical reliability requirements - implement robust testing and validation")
        if scores['scalability'] > 0.7:
            recommendations.append("Scalability important - design modular and extensible architecture")
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='SpecTradeoffs',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=[f"Technical requirement: {req}" for req in solutions[:3]],
            confidence_level=0.85  # Technical analysis typically has clear requirements
        )

class FrameworkAdapterRegistry:
    """Registry for managing framework adapters."""
    
    def __init__(self):
        """Initialize with built-in framework adapters."""
        self._adapters = {
            'errc': ERRCAdapter,
            'jtbd': JTBDAdapter,
            'jobs_to_be_done': JTBDAdapter,  # Alias
            'site_feasibility': SiteFeasibilityAdapter,
            'spec_tradeoffs': SpecTradeoffsAdapter,
        }
    
    def register_adapter(self, name: str, adapter_class: type):
        """Register a custom framework adapter."""
        if not issubclass(adapter_class, FrameworkAdapter):
            raise ValueError(f"Adapter must inherit from FrameworkAdapter")
        self._adapters[name.lower()] = adapter_class
        logger.info(f"Registered framework adapter: {name}")
    
    def get_adapter(self, framework_type: str, config: Dict[str, Any] = None) -> FrameworkAdapter:
        """Get a framework adapter instance."""
        framework_key = framework_type.lower()
        if framework_key not in self._adapters:
            available = list(self._adapters.keys())
            raise ValueError(f"Unknown framework type: {framework_type}. Available: {available}")
        
        adapter_class = self._adapters[framework_key]
        return adapter_class(config or {})
    
    def list_frameworks(self) -> List[str]:
        """List all available framework types."""
        return list(self._adapters.keys())

def analyze_zones_with_framework(
    opportunity_zones: List[Dict[str, Any]], 
    framework_type: str,
    config: Dict[str, Any] = None,
    context: Dict[str, Any] = None
) -> List[FrameworkResult]:
    """
    Analyze all opportunity zones using specified framework.
    
    Args:
        opportunity_zones: List of opportunity zone dictionaries
        framework_type: Framework to use (errc, jtbd, site_feasibility, spec_tradeoffs)
        config: Framework configuration
        context: Additional analysis context
        
    Returns:
        List of FrameworkResult objects with scores and recommendations
    """
    registry = FrameworkAdapterRegistry()
    adapter = registry.get_adapter(framework_type, config)
    
    results = []
    for zone in opportunity_zones:
        try:
            result = adapter.analyze_zone(zone, context)
            results.append(result)
            logger.info(f"Analyzed zone {result.zone_id} with {framework_type}: score={result.overall_score:.3f}")
        except Exception as e:
            logger.error(f"Error analyzing zone {zone.get('zone_id', 'unknown')} with {framework_type}: {e}")
            # Continue with other zones
    
    # Sort by overall score (descending)
    results.sort(key=lambda r: r.overall_score, reverse=True)
    
    return results


class SpecTraceAdapter(FrameworkAdapter):
    """SPEC-TRACE Framework Adapter for Medical Device Specifications."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.weights = config.get('weights', {
            'CF': 0.22,  # Clinical Fit
            'RC': 0.10,  # Regulatory Complexity (inverted)
            'SR': 0.10,  # Safety & Risk (inverted)
            'BF': 0.18,  # Build Feasibility
            'HF': 0.12,  # Human Factors
            'DC': 0.08,  # Data & Cyber
            'EP': 0.12,  # Evidence Path
            'TTM': 0.08  # Time-to-Market
        })
        self.category_overrides = config.get('category_overrides', {})
        self.require_standards_map = config.get('require_standards_map', True)
    
    def get_dimensions(self) -> List[str]:
        return ['CF', 'RC', 'SR', 'BF', 'HF', 'DC', 'EP', 'TTM']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'CF': 'Clinical Fit - strength of clinical need, alignment to guidelines, outcome impact',
            'RC': 'Regulatory Complexity - expected class, predicates, special controls, data burden (inverted)',
            'SR': 'Safety & Risk - inherent hazards, misuse risk, mitigations per ISO 14971 (inverted)',
            'BF': 'Build Feasibility - materials, processes, COGS, supply risk, manufacturability',
            'HF': 'Human Factors - IEC 62366 usability, user types, use environment, alarm/fail-safe',
            'DC': 'Data & Cyber - software/SaMD, connectivity, cybersecurity posture',
            'EP': 'Evidence Path - verification/validation burden, clinical study feasibility',
            'TTM': 'Time-to-Market - pathway speed, dependencies, lead times'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze zone using SPEC-TRACE framework for medical device specifications."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        # Extract medical device context
        pain_dims = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbd_descriptions = zone.get('jtbd_descriptions', [])
        
        # Detect device category for category-specific weighting
        device_category = self._detect_device_category(solutions, jtbd_descriptions, context)
        
        # Get weights (with category overrides if applicable)
        weights = self._get_category_weights(device_category)
        
        # Compute axis scores
        scores = {}
        rationales = {}
        
        # Clinical Fit (CF) - strength of clinical need
        cf_score = self._assess_clinical_fit(pain_dims, solutions, jtbd_descriptions, context)
        scores['CF'] = cf_score
        rationales['CF'] = "Clinical need strength based on pain dimensions and outcome impact"
        
        # Regulatory Complexity (RC) - inverted score (higher complexity = lower score)
        rc_complexity = self._assess_regulatory_complexity(solutions, device_category, context)
        scores['RC'] = 1.0 - rc_complexity  # Invert complexity to score
        rationales['RC'] = f"Regulatory pathway complexity assessment for {device_category} category"
        
        # Safety & Risk (SR) - inverted score (higher risk = lower score) 
        sr_risk = self._assess_safety_risk(solutions, device_category, pain_dims, context)
        scores['SR'] = 1.0 - sr_risk  # Invert risk to score
        rationales['SR'] = "Safety risk assessment per ISO 14971 hazard analysis"
        
        # Build Feasibility (BF) - manufacturability and supply chain
        bf_score = self._assess_build_feasibility(solutions, device_category, context)
        scores['BF'] = bf_score
        rationales['BF'] = "Manufacturing feasibility and supply chain assessment"
        
        # Human Factors (HF) - IEC 62366 usability considerations
        hf_score = self._assess_human_factors(pain_dims, solutions, device_category, context)
        scores['HF'] = hf_score
        rationales['HF'] = "Human factors usability per IEC 62366 framework"
        
        # Data & Cyber (DC) - software and connectivity security
        dc_score = self._assess_data_cyber(solutions, device_category, context)
        scores['DC'] = dc_score
        rationales['DC'] = "Data handling and cybersecurity posture assessment"
        
        # Evidence Path (EP) - verification/validation burden
        ep_score = self._assess_evidence_path(device_category, solutions, context)
        scores['EP'] = ep_score
        rationales['EP'] = "Evidence generation pathway and clinical validation requirements"
        
        # Time-to-Market (TTM) - pathway speed and dependencies
        ttm_score = self._assess_time_to_market(device_category, rc_complexity, solutions, context)
        scores['TTM'] = ttm_score
        rationales['TTM'] = "Time-to-market assessment based on pathway and dependencies"
        
        # Compute composite SPEC-TRACE score
        composite_score = sum(scores[dim] * weights[dim] for dim in scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(scores, device_category, weights)
        
        # Extract citations from context
        citations = []
        if context:
            citations.extend(context.get('reddit_discussions', [])[:3])
            citations.extend(context.get('report_sections', [])[:2])
        
        result = FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='SPEC_TRACE',
            scores=scores,
            rationales=rationales,
            overall_score=composite_score,
            recommendations=recommendations,
            citations=citations,
            confidence_level=self._calculate_confidence(scores, len(solutions), len(jtbd_descriptions))
        )
        
        # Add standards map if required
        if self.require_standards_map:
            result.standards_map = self._generate_standards_map(device_category, scores)
        
        return result
    
    def _detect_device_category(self, solutions: List[str], jtbds: List[str], context: Dict[str, Any]) -> str:
        """Detect device category from solution requirements and JTBDs."""
        text_analysis = ' '.join(solutions + jtbds).lower()
        
        # Category detection based on keywords
        if any(word in text_analysis for word in ['monitor', 'sensor', 'measurement', 'vital signs']):
            return 'monitoring'
        elif any(word in text_analysis for word in ['surgical', 'instrument', 'procedure', 'operation']):
            return 'surgical_accessory'
        elif any(word in text_analysis for word in ['implant', 'permanent', 'subcutaneous', 'internal']):
            return 'implantable'
        elif any(word in text_analysis for word in ['diagnostic', 'test', 'assay', 'screening']):
            return 'diagnostic'
        elif any(word in text_analysis for word in ['wound', 'dressing', 'healing', 'skin']):
            return 'wound_care'
        else:
            return 'general'
    
    def _get_category_weights(self, category: str) -> Dict[str, float]:
        """Get category-specific weights with overrides."""
        weights = self.weights.copy()
        
        if category in self.category_overrides:
            overrides = self.category_overrides[category]
            for dim, override_weight in overrides.items():
                weights[dim] = override_weight
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight != 1.0:
            for dim in weights:
                weights[dim] = weights[dim] / total_weight
        
        return weights
    
    def _assess_clinical_fit(self, pain_dims: Dict, solutions: List, jtbds: List, context: Dict) -> float:
        """Assess clinical fit based on need strength and outcome impact."""
        base_score = 0.5
        
        # Strong clinical need indicators
        if any('patient' in sol.lower() or 'clinical' in sol.lower() for sol in solutions):
            base_score += 0.2
        
        # Pain dimension analysis for clinical impact
        clinical_pain_weight = (
            pain_dims.get('decision_anxiety', 0) * 0.3 +
            pain_dims.get('timing_coordination', 0) * 0.25 +
            pain_dims.get('trust_issues', 0) * 0.2 +
            pain_dims.get('process_complexity', 0) * 0.25
        )
        base_score += clinical_pain_weight * 0.3
        
        return min(base_score, 1.0)
    
    def _assess_regulatory_complexity(self, solutions: List, category: str, context: Dict) -> float:
        """Assess regulatory complexity (higher = more complex)."""
        base_complexity = 0.3  # Default moderate complexity
        
        # Category-based complexity
        category_complexity = {
            'monitoring': 0.4,
            'diagnostic': 0.6,
            'surgical_accessory': 0.5,
            'implantable': 0.8,
            'wound_care': 0.3
        }
        base_complexity = category_complexity.get(category, 0.4)
        
        # Solution complexity indicators
        if any('novel' in sol.lower() or 'first-of-kind' in sol.lower() for sol in solutions):
            base_complexity += 0.2
        if any('ai' in sol.lower() or 'algorithm' in sol.lower() for sol in solutions):
            base_complexity += 0.15  # SaMD complexity
        
        return min(base_complexity, 1.0)
    
    def _assess_safety_risk(self, solutions: List, category: str, pain_dims: Dict, context: Dict) -> float:
        """Assess safety risk (higher = more risky)."""
        base_risk = 0.2  # Default low risk
        
        # Category-based risk
        category_risk = {
            'monitoring': 0.2,
            'diagnostic': 0.3,
            'surgical_accessory': 0.5,
            'implantable': 0.7,
            'wound_care': 0.2
        }
        base_risk = category_risk.get(category, 0.3)
        
        # Solution risk indicators
        if any('invasive' in sol.lower() or 'penetrating' in sol.lower() for sol in solutions):
            base_risk += 0.2
        if any('critical' in sol.lower() or 'life-support' in sol.lower() for sol in solutions):
            base_risk += 0.3
        
        return min(base_risk, 1.0)
    
    def _assess_build_feasibility(self, solutions: List, category: str, context: Dict) -> float:
        """Assess manufacturing and build feasibility."""
        base_feasibility = 0.6
        
        # Solution feasibility indicators
        if any('custom' in sol.lower() or 'specialized' in sol.lower() for sol in solutions):
            base_feasibility -= 0.1  # Custom components reduce feasibility
        if any('standard' in sol.lower() or 'existing' in sol.lower() for sol in solutions):
            base_feasibility += 0.2  # Standard components increase feasibility
        
        # Category feasibility
        category_feasibility = {
            'monitoring': 0.7,
            'diagnostic': 0.6,
            'surgical_accessory': 0.8,
            'implantable': 0.4,
            'wound_care': 0.8
        }
        category_modifier = category_feasibility.get(category, 0.6)
        base_feasibility = (base_feasibility + category_modifier) / 2
        
        return min(base_feasibility, 1.0)
    
    def _assess_human_factors(self, pain_dims: Dict, solutions: List, category: str, context: Dict) -> float:
        """Assess human factors usability requirements."""
        base_hf = 0.5
        
        # Pain dimensions affecting usability
        usability_pain = (
            pain_dims.get('process_complexity', 0) * 0.4 +
            pain_dims.get('communication_gaps', 0) * 0.3 +
            pain_dims.get('technology_gaps', 0) * 0.3
        )
        base_hf += usability_pain * 0.4
        
        # Solution usability requirements
        if any('intuitive' in sol.lower() or 'easy' in sol.lower() for sol in solutions):
            base_hf += 0.2
        if any('training' in sol.lower() or 'complex' in sol.lower() for sol in solutions):
            base_hf += 0.1  # Training needs indicate HF importance
        
        return min(base_hf, 1.0)
    
    def _assess_data_cyber(self, solutions: List, category: str, context: Dict) -> float:
        """Assess data handling and cybersecurity requirements."""
        base_dc = 0.3  # Default low data/cyber requirements
        
        # Solution data/cyber indicators
        if any('connected' in sol.lower() or 'wireless' in sol.lower() for sol in solutions):
            base_dc += 0.3
        if any('data' in sol.lower() or 'cloud' in sol.lower() for sol in solutions):
            base_dc += 0.2
        if any('ai' in sol.lower() or 'algorithm' in sol.lower() for sol in solutions):
            base_dc += 0.3  # SaMD requirements
        
        return min(base_dc, 1.0)
    
    def _assess_evidence_path(self, category: str, solutions: List, context: Dict) -> float:
        """Assess evidence generation pathway requirements."""
        base_evidence = 0.6
        
        # Category-based evidence requirements
        category_evidence = {
            'monitoring': 0.7,
            'diagnostic': 0.8,
            'surgical_accessory': 0.6,
            'implantable': 0.4,  # High evidence burden (inverted for score)
            'wound_care': 0.7
        }
        base_evidence = category_evidence.get(category, 0.6)
        
        # Solution evidence indicators
        if any('clinical' in sol.lower() or 'outcome' in sol.lower() for sol in solutions):
            base_evidence -= 0.1  # Clinical outcomes require more evidence
        
        return max(base_evidence, 0.1)
    
    def _assess_time_to_market(self, category: str, regulatory_complexity: float, solutions: List, context: Dict) -> float:
        """Assess time-to-market based on pathway and dependencies."""
        base_ttm = 0.6
        
        # Regulatory complexity affects time-to-market
        base_ttm -= regulatory_complexity * 0.3
        
        # Solution time indicators
        if any('rapid' in sol.lower() or 'quick' in sol.lower() for sol in solutions):
            base_ttm += 0.2
        if any('custom' in sol.lower() or 'development' in sol.lower() for sol in solutions):
            base_ttm -= 0.1  # Custom development takes longer
        
        return max(base_ttm, 0.1)
    
    def _generate_recommendations(self, scores: Dict, category: str, weights: Dict) -> List[str]:
        """Generate recommendations based on SPEC-TRACE scores."""
        recommendations = []
        
        # High clinical fit recommendations
        if scores['CF'] > 0.8:
            recommendations.append(f"Strong clinical need identified - prioritize {category} development")
        
        # Regulatory complexity recommendations
        if scores['RC'] < 0.4:  # High complexity (inverted score)
            recommendations.append("Complex regulatory pathway - engage FDA early for pre-submission")
        
        # Safety risk recommendations
        if scores['SR'] < 0.4:  # High risk (inverted score)
            recommendations.append("Significant safety considerations - implement comprehensive risk management per ISO 14971")
        
        # Build feasibility recommendations
        if scores['BF'] > 0.8:
            recommendations.append("Excellent manufacturability - consider DFM optimization for cost reduction")
        elif scores['BF'] < 0.4:
            recommendations.append("Manufacturing challenges identified - conduct feasibility studies early")
        
        # Human factors recommendations
        if scores['HF'] > 0.7:
            recommendations.append("Critical usability requirements - implement IEC 62366 human factors program")
        
        return recommendations
    
    def _generate_standards_map(self, category: str, scores: Dict) -> Dict[str, List[str]]:
        """Generate applicable standards map based on category and scores."""
        standards_map = {
            'universal': ['ISO 13485', 'ISO 14971'],
            'electrical': [],
            'biocompatibility': [],
            'usability': [],
            'software': [],
            'cybersecurity': []
        }
        
        # Category-specific standards
        if category in ['monitoring', 'diagnostic']:
            standards_map['electrical'] = ['IEC 60601-1', 'IEC 60601-1-2']
        
        # Score-driven standards
        if scores['HF'] > 0.6:
            standards_map['usability'] = ['IEC 62366-1', 'IEC 62366-2']
        
        if scores['DC'] > 0.5:
            standards_map['software'] = ['IEC 62304']
            standards_map['cybersecurity'] = ['FDA Cybersecurity Guidelines']
        
        if category in ['implantable', 'wound_care']:
            standards_map['biocompatibility'] = ['ISO 10993 series']
        
        return standards_map
    
    def _calculate_confidence(self, scores: Dict, num_solutions: int, num_jtbds: int) -> float:
        """Calculate confidence level based on data completeness."""
        base_confidence = 0.6
        
        # Data completeness affects confidence
        if num_solutions >= 3:
            base_confidence += 0.2
        if num_jtbds >= 3:
            base_confidence += 0.1
        
        # Score consistency affects confidence
        score_variance = sum((score - 0.5) ** 2 for score in scores.values()) / len(scores)
        if score_variance < 0.1:  # Low variance = uncertain differentiation
            base_confidence -= 0.1
        
        return min(base_confidence, 1.0)


class MiningViabilityAdapter(FrameworkAdapter):
    """Mining Viability Framework Adapter with 9 core modules (M1-M9)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Extract scoring weights from viability_formula
        self.weights = config.get('scoring', {}).get('weights', {
            'w1_cost_index': 0.25,
            'w2_setup_friction': 0.20,
            'w3_policy_risk': 0.15,
            'w4_logistics_risk': 0.15,
            'w5_community_anecdote_risk': 0.10,
            'w6_roi_quality': 0.15
        })
        self.modules = config.get('modules', {})
        self.user_inputs = config.get('user_inputs', {})
        
    def get_dimensions(self) -> List[str]:
        return ['M1_decision_price_sensitivity', 'M2_power_hunt_normalizer', 'M3_infrastructure_feasibility',
                'M4_hardware_selector', 'M5_logistics_customs', 'M6_financial_synthesizer',
                'M7_compliance_policy', 'M8_community_signal_overlay', 'M9_ranker_explainer']
    
    def get_scoring_criteria(self) -> Dict[str, str]:
        return {
            'M1_decision_price_sensitivity': 'ROI envelope before searching the world',
            'M2_power_hunt_normalizer': 'Real, contractable power opportunities',
            'M3_infrastructure_feasibility': 'Physical MW landing capability',
            'M4_hardware_selector': 'Rig selection for power + timeline reality',
            'M5_logistics_customs': 'Getting rigs there on time/cost sanely',
            'M6_financial_synthesizer': 'Cashflow and risk synthesis',
            'M7_compliance_policy': 'Policy and regulatory risk assessment',
            'M8_community_signal_overlay': 'Operator experience overlay',
            'M9_ranker_explainer': 'Ranking and explanation of top opportunities'
        }
    
    def analyze_zone(self, zone: Dict[str, Any], context: Dict[str, Any] = None) -> FrameworkResult:
        """Analyze mining setup viability using the 9-module framework."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', f'Mining Setup {zone_id}')
        
        # Extract zone information 
        pain_dimensions = zone.get('pain_dimensions', {})
        solutions = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds', [])
        discussions = zone.get('discussions', [])
        
        # Get enriched data if available
        enriched_data = zone.get('enriched_data', {})
        
        # Module scores and rationales
        scores = {}
        rationales = {}
        
        # M1: Decision Price Sensitivity - ROI envelope analysis
        m1_score = self._analyze_roi_envelope(enriched_data, pain_dimensions, context)
        scores['M1_decision_price_sensitivity'] = m1_score
        rationales['M1_decision_price_sensitivity'] = f"ROI feasibility envelope based on price scenarios and efficiency requirements (score: {m1_score:.2f})"
        
        # M2: Power Hunt Normalizer - Real contractable power assessment
        m2_score = self._assess_power_viability(enriched_data, pain_dimensions, discussions, context)
        scores['M2_power_hunt_normalizer'] = m2_score
        rationales['M2_power_hunt_normalizer'] = f"Real power availability and contractability assessment (score: {m2_score:.2f})"
        
        # M3: Infrastructure Feasibility - MW landing capability
        m3_score = self._assess_infrastructure_readiness(pain_dimensions, solutions, discussions, context)
        scores['M3_infrastructure_feasibility'] = m3_score
        rationales['M3_infrastructure_feasibility'] = f"Infrastructure readiness for MW-scale deployment (score: {m3_score:.2f})"
        
        # M4: Hardware Selector - Rig selection for conditions
        m4_score = self._assess_hardware_availability(enriched_data, pain_dimensions, solutions, context)
        scores['M4_hardware_selector'] = m4_score
        rationales['M4_hardware_selector'] = f"Hardware availability and suitability for timeline/conditions (score: {m4_score:.2f})"
        
        # M5: Logistics Customs - Shipping and customs feasibility
        m5_score = self._assess_logistics_feasibility(enriched_data, pain_dimensions, context)
        scores['M5_logistics_customs'] = m5_score
        rationales['M5_logistics_customs'] = f"Logistics and customs risk assessment for equipment delivery (score: {m5_score:.2f})"
        
        # M6: Financial Synthesizer - Comprehensive financial analysis
        m6_score = self._synthesize_financial_model(enriched_data, m1_score, m2_score, m4_score, context)
        scores['M6_financial_synthesizer'] = m6_score
        rationales['M6_financial_synthesizer'] = f"Financial model synthesis with capex/opex and sensitivity analysis (score: {m6_score:.2f})"
        
        # M7: Compliance Policy - Regulatory risk assessment
        m7_score = self._assess_policy_compliance(enriched_data, pain_dimensions, discussions, context)
        scores['M7_compliance_policy'] = m7_score
        rationales['M7_compliance_policy'] = f"Policy stability and regulatory compliance assessment (score: {m7_score:.2f})"
        
        # M8: Community Signal Overlay - Operator experience integration
        m8_score = self._overlay_community_signals(discussions, enriched_data, context)
        scores['M8_community_signal_overlay'] = m8_score
        rationales['M8_community_signal_overlay'] = f"Community signals and operator experience integration (score: {m8_score:.2f})"
        
        # M9: Ranker Explainer - Overall viability ranking
        m9_score, viability_components = self._rank_and_explain_viability(scores, enriched_data, context)
        scores['M9_ranker_explainer'] = m9_score
        rationales['M9_ranker_explainer'] = f"Overall viability ranking with transparent rationale (score: {m9_score:.2f})"
        
        # Calculate composite viability score using the formula:
        # 100 - w1*CostIndex - w2*SetupFriction - w3*PolicyRisk - w4*LogisticsRisk - w5*CommunityAnecdoteRisk + w6*ROIQuality
        cost_index = max(0, 1.0 - m2_score)  # Invert power score for cost
        setup_friction = max(0, 1.0 - m3_score)  # Invert infrastructure score for friction
        policy_risk = max(0, 1.0 - m7_score)  # Invert compliance score for risk
        logistics_risk = max(0, 1.0 - m5_score)  # Invert logistics score for risk
        community_risk = max(0, 1.0 - m8_score)  # Invert community score for risk
        roi_quality = m6_score  # Financial score as ROI quality
        
        viability_raw = (100 - 
                        self.weights['w1_cost_index'] * cost_index * 100 -
                        self.weights['w2_setup_friction'] * setup_friction * 100 -
                        self.weights['w3_policy_risk'] * policy_risk * 100 -
                        self.weights['w4_logistics_risk'] * logistics_risk * 100 -
                        self.weights['w5_community_anecdote_risk'] * community_risk * 100 +
                        self.weights['w6_roi_quality'] * roi_quality * 100)
        
        overall_score = max(0.0, min(viability_raw / 100.0, 1.0))  # Normalize to 0-1
        
        # Generate mining-specific recommendations
        recommendations = self._generate_mining_recommendations(scores, viability_components, enriched_data)
        
        # Extract citations
        citations = []
        if enriched_data.get('source_url'):
            citations.append(f"Power data source: {enriched_data['source_url']}")
        if discussions:
            citations.extend([f"Mining discussion: {disc[:80]}..." for disc in discussions[:2]])
        citations.extend([f"Module analysis: {list(scores.keys())[:3]}"])
        
        return FrameworkResult(
            zone_id=zone_id,
            zone_name=zone_name,
            framework_name='MiningViability',
            scores=scores,
            rationales=rationales,
            overall_score=round(overall_score, 3),
            recommendations=recommendations,
            citations=citations,
            confidence_level=min(0.9, len(discussions) * 0.05 + len(solutions) * 0.1 + 0.6)
        )
    
    def _analyze_roi_envelope(self, enriched_data: Dict, pain_dims: Dict, context: Dict) -> float:
        """M1: Analyze ROI envelope and price sensitivity."""
        base_score = 0.5
        
        # Check if financial estimates are available
        financial_est = enriched_data.get('financial_estimates', {})
        if financial_est:
            # Strong financial fundamentals boost ROI envelope
            if financial_est.get('payback_months', {}).get('base', 999) < 24:
                base_score += 0.3  # Good payback period
            if financial_est.get('break_even_price', 0) < 30000:  # Reasonable BTC break-even
                base_score += 0.2
        
        # Pain dimensions indicating cost sensitivity
        if pain_dims.get('financial_stress', 0) > 0.6:
            base_score += 0.2  # High cost pressure = good ROI focus
        
        # User inputs consideration
        budget = self.user_inputs.get('budget_usd', 0)
        timeline = self.user_inputs.get('timeline_days', 0)
        if budget >= 1000000 and timeline <= 180:  # Adequate budget and timeline
            base_score += 0.1
            
        return min(base_score, 1.0)
    
    def _assess_power_viability(self, enriched_data: Dict, pain_dims: Dict, discussions: List, context: Dict) -> float:
        """M2: Assess real, contractable power opportunities."""
        base_score = 0.4
        
        # Power data from enrichment
        power_data = enriched_data.get('power_data', {})
        if power_data:
            power_rate = power_data.get('industrial_rate_kwh', 1.0)
            if power_rate <= 0.05:  # Under 5 cents/kWh
                base_score += 0.4
            elif power_rate <= 0.08:  # Under 8 cents/kWh
                base_score += 0.2
            
            # Availability and reliability
            if power_data.get('availability_mw', 0) >= 1.0:  # At least 1 MW available
                base_score += 0.2
                
        # Community discussions about power
        power_keywords = ['power', 'electricity', 'utility', 'grid', 'ppa', 'renewable']
        power_mentions = sum(1 for disc in discussions for keyword in power_keywords if keyword in disc.lower())
        if power_mentions >= 3:
            base_score += 0.1
        
        # Pain dimensions related to power/infrastructure
        if pain_dims.get('infrastructure_gaps', 0) > 0.5:
            base_score -= 0.1  # Infrastructure challenges reduce power viability
            
        return min(max(base_score, 0.1), 1.0)
    
    def _assess_infrastructure_readiness(self, pain_dims: Dict, solutions: List, discussions: List, context: Dict) -> float:
        """M3: Assess infrastructure feasibility for MW landing."""
        base_score = 0.5
        
        # Infrastructure-related solutions
        infra_keywords = ['infrastructure', 'substation', 'transformer', 'permits', 'zoning']
        infra_solutions = len([sol for sol in solutions if any(kw in sol.lower() for kw in infra_keywords)])
        base_score += min(infra_solutions * 0.1, 0.3)
        
        # Pain dimensions affecting infrastructure
        if pain_dims.get('regulatory_barriers', 0) > 0.6:
            base_score -= 0.2  # Regulatory barriers hurt infrastructure
        if pain_dims.get('process_complexity', 0) > 0.5:
            base_score -= 0.1  # Complex processes slow infrastructure
            
        # Community discussions about infrastructure challenges
        barrier_keywords = ['permits', 'zoning', 'transformer', 'lead time', 'delays']
        barrier_mentions = sum(1 for disc in discussions for keyword in barrier_keywords if keyword in disc.lower())
        if barrier_mentions >= 2:
            base_score -= 0.1  # Infrastructure friction
        
        return min(max(base_score, 0.1), 1.0)
    
    def _assess_hardware_availability(self, enriched_data: Dict, pain_dims: Dict, solutions: List, context: Dict) -> float:
        """M4: Assess hardware selection and availability for conditions."""
        base_score = 0.6
        
        # Hardware data from enrichment
        hardware_data = enriched_data.get('hardware_data', {})
        if hardware_data:
            # ASIC efficiency and availability
            efficiency = hardware_data.get('efficiency_wth', 0)
            if efficiency >= 25:  # Good efficiency (higher is worse for ASIC)
                base_score += 0.2
            elif efficiency <= 20:  # Excellent efficiency
                base_score += 0.3
                
            # Availability and lead time
            if hardware_data.get('availability', 'low') == 'high':
                base_score += 0.2
            elif hardware_data.get('lead_time_weeks', 99) <= 12:  # Within 3 months
                base_score += 0.1
        
        # Solutions mentioning hardware considerations
        hw_keywords = ['asic', 'miner', 'hardware', 'equipment', 'cooling']
        hw_solutions = len([sol for sol in solutions if any(kw in sol.lower() for kw in hw_keywords)])
        base_score += min(hw_solutions * 0.05, 0.1)
        
        # Timeline pressure from user inputs
        timeline = self.user_inputs.get('timeline_days', 365)
        if timeline <= 120:  # Tight timeline
            base_score -= 0.1  # Harder to get hardware quickly
            
        return min(max(base_score, 0.1), 1.0)
    
    def _assess_logistics_feasibility(self, enriched_data: Dict, pain_dims: Dict, context: Dict) -> float:
        """M5: Assess logistics and customs feasibility."""
        base_score = 0.6
        
        # Geographic factors from user inputs
        regions = self.user_inputs.get('preferred_regions', [])
        
        # Logistics-friendly regions
        friendly_regions = ['US-TX', 'US-FL', 'CA-QC', 'NO']  # Texas, Florida, Quebec, Norway
        risky_regions = ['PY', 'KZ', 'RU']  # Paraguay, Kazakhstan, Russia
        
        friendly_count = len([r for r in regions if r in friendly_regions])
        risky_count = len([r for r in regions if r in risky_regions])
        
        base_score += min(friendly_count * 0.15, 0.3)
        base_score -= min(risky_count * 0.2, 0.4)
        
        # Logistics data from enrichment
        logistics_data = enriched_data.get('logistics_data', {})
        if logistics_data:
            # Duty rates and shipping time
            duty_rate = logistics_data.get('duty_rate_pct', 0)
            if duty_rate <= 5:  # Low duty
                base_score += 0.2
            elif duty_rate >= 15:  # High duty
                base_score -= 0.2
                
            shipping_weeks = logistics_data.get('shipping_weeks', 12)
            if shipping_weeks <= 8:  # Fast shipping
                base_score += 0.1
        
        return min(max(base_score, 0.1), 1.0)
    
    def _synthesize_financial_model(self, enriched_data: Dict, roi_score: float, power_score: float, hw_score: float, context: Dict) -> float:
        """M6: Synthesize comprehensive financial model."""
        base_score = 0.5
        
        # Integrate M1, M2, M4 scores (ROI, power, hardware)
        component_average = (roi_score + power_score + hw_score) / 3
        base_score = component_average * 0.7 + base_score * 0.3  # Weighted blend
        
        # Financial data enhancement
        financial_est = enriched_data.get('financial_estimates', {})
        if financial_est:
            # Payback analysis
            payback_base = financial_est.get('payback_months', {}).get('base', 999)
            payback_bear = financial_est.get('payback_months', {}).get('bear', 999)
            
            if payback_base <= 18:  # Excellent payback
                base_score += 0.2
            elif payback_base <= 30:  # Good payback
                base_score += 0.1
                
            if payback_bear <= 36:  # Bear case still viable
                base_score += 0.1
                
            # IRR analysis
            irr_base = financial_est.get('irr_pct', {}).get('base', 0)
            if irr_base >= 25:  # Strong IRR
                base_score += 0.2
            elif irr_base >= 15:  # Good IRR
                base_score += 0.1
        
        return min(max(base_score, 0.1), 1.0)
    
    def _assess_policy_compliance(self, enriched_data: Dict, pain_dims: Dict, discussions: List, context: Dict) -> float:
        """M7: Assess policy stability and regulatory compliance."""
        base_score = 0.6
        
        # Regulatory data from enrichment
        regulatory_data = enriched_data.get('regulatory_data', {})
        if regulatory_data:
            crypto_stance = regulatory_data.get('crypto_stance', 'neutral')
            if crypto_stance == 'supportive':
                base_score += 0.3
            elif crypto_stance == 'hostile':
                base_score -= 0.4
                
            # Energy policy
            energy_policy = regulatory_data.get('energy_policy', 'neutral')
            if energy_policy == 'renewable_friendly':
                base_score += 0.1
        
        # Community discussions about regulatory issues
        regulatory_keywords = ['regulation', 'banned', 'legal', 'government', 'policy', 'tax']
        regulatory_mentions = sum(1 for disc in discussions for keyword in regulatory_keywords if keyword in disc.lower())
        
        positive_keywords = ['approved', 'legal', 'supportive', 'friendly']
        negative_keywords = ['banned', 'illegal', 'crackdown', 'hostile']
        
        positive_mentions = sum(1 for disc in discussions for keyword in positive_keywords if keyword in disc.lower())
        negative_mentions = sum(1 for disc in discussions for keyword in negative_keywords if keyword in disc.lower())
        
        base_score += min(positive_mentions * 0.1, 0.2)
        base_score -= min(negative_mentions * 0.2, 0.4)
        
        # Pain dimensions related to regulatory barriers
        if pain_dims.get('regulatory_barriers', 0) > 0.7:
            base_score -= 0.2
        
        return min(max(base_score, 0.1), 1.0)
    
    def _overlay_community_signals(self, discussions: List, enriched_data: Dict, context: Dict) -> float:
        """M8: Overlay community signals and operator experience."""
        base_score = 0.5
        
        # Positive community signals
        positive_keywords = ['profitable', 'successful', 'working', 'good experience', 'recommend']
        negative_keywords = ['scam', 'failed', 'problems', 'avoid', 'disaster']
        
        positive_mentions = sum(1 for disc in discussions for keyword in positive_keywords if keyword in disc.lower())
        negative_mentions = sum(1 for disc in discussions for keyword in negative_keywords if keyword in disc.lower())
        
        # Weight positive and negative signals
        base_score += min(positive_mentions * 0.1, 0.3)
        base_score -= min(negative_mentions * 0.15, 0.4)
        
        # Operator experience signals
        experience_keywords = ['experience', 'lessons learned', 'tips', 'advice', 'mistakes']
        experience_mentions = sum(1 for disc in discussions for keyword in experience_keywords if keyword in disc.lower())
        
        if experience_mentions >= 3:
            base_score += 0.2  # Rich experience sharing
        elif experience_mentions >= 1:
            base_score += 0.1
        
        # Community intelligence from enrichment
        community_intel = enriched_data.get('community_intelligence', {})
        if community_intel:
            sentiment = community_intel.get('overall_sentiment', 'neutral')
            if sentiment == 'positive':
                base_score += 0.2
            elif sentiment == 'negative':
                base_score -= 0.2
                
            confidence = community_intel.get('confidence', 0)
            base_score += min(confidence * 0.1, 0.1)  # Higher confidence helps
        
        return min(max(base_score, 0.1), 1.0)
    
    def _rank_and_explain_viability(self, scores: Dict, enriched_data: Dict, context: Dict) -> tuple:
        """M9: Rank viability and generate explanation."""
        # Calculate weighted viability components
        components = {
            'technical_feasibility': (scores.get('M1_decision_price_sensitivity', 0) + 
                                    scores.get('M4_hardware_selector', 0)) / 2,
            'operational_readiness': (scores.get('M2_power_hunt_normalizer', 0) + 
                                    scores.get('M3_infrastructure_feasibility', 0)) / 2,
            'financial_viability': scores.get('M6_financial_synthesizer', 0),
            'risk_factors': (scores.get('M7_compliance_policy', 0) + 
                           scores.get('M5_logistics_customs', 0)) / 2,
            'market_validation': scores.get('M8_community_signal_overlay', 0)
        }
        
        # Overall viability score (average of components)
        overall_viability = sum(components.values()) / len(components)
        
        # Boost score based on component balance
        component_variance = sum((score - overall_viability) ** 2 for score in components.values()) / len(components)
        if component_variance < 0.05:  # Well-balanced components
            overall_viability = min(overall_viability + 0.1, 1.0)
        
        return overall_viability, components
    
    def _generate_mining_recommendations(self, scores: Dict, components: Dict, enriched_data: Dict) -> List[str]:
        """Generate mining-specific recommendations based on analysis."""
        recommendations = []
        
        # ROI and financial recommendations
        if scores.get('M1_decision_price_sensitivity', 0) > 0.8:
            recommendations.append("Strong ROI fundamentals - proceed with detailed financial modeling")
        elif scores.get('M1_decision_price_sensitivity', 0) < 0.4:
            recommendations.append("ROI concerns - reassess price assumptions and efficiency requirements")
        
        # Power and infrastructure recommendations
        if scores.get('M2_power_hunt_normalizer', 0) > 0.7:
            recommendations.append("Excellent power opportunity - secure long-term contracts quickly")
        if scores.get('M3_infrastructure_feasibility', 0) < 0.5:
            recommendations.append("Infrastructure challenges - budget extra time and cost for permitting")
        
        # Hardware recommendations
        if scores.get('M4_hardware_selector', 0) > 0.8:
            recommendations.append("Strong hardware availability - lock in orders with preferred suppliers")
        elif scores.get('M4_hardware_selector', 0) < 0.4:
            recommendations.append("Hardware constraints - consider alternative models or extended timeline")
        
        # Risk mitigation recommendations
        if scores.get('M7_compliance_policy', 0) < 0.5:
            recommendations.append("Regulatory risk elevated - engage legal counsel for compliance strategy")
        if scores.get('M5_logistics_customs', 0) < 0.5:
            recommendations.append("Logistics risk - consider alternative shipping routes and customs preparation")
        
        # Community validation recommendations
        if scores.get('M8_community_signal_overlay', 0) > 0.7:
            recommendations.append("Strong community validation - leverage operator networks for implementation")
        elif scores.get('M8_community_signal_overlay', 0) < 0.4:
            recommendations.append("Limited community validation - conduct additional due diligence")
        
        # Overall viability recommendations
        overall_score = scores.get('M9_ranker_explainer', 0)
        if overall_score > 0.8:
            recommendations.append("Top-tier mining opportunity - recommend immediate action")
        elif overall_score > 0.6:
            recommendations.append("Viable mining setup - proceed with detailed planning")
        elif overall_score > 0.4:
            recommendations.append("Marginal viability - address key risk factors before proceeding")
        else:
            recommendations.append("Below viability threshold - reassess fundamental assumptions")
        
        return recommendations


# Register all framework adapters
_registry = FrameworkAdapterRegistry()
_registry.register_adapter('spec_trace', SpecTraceAdapter)
_registry.register_adapter('spec_trace_v1', SpecTraceAdapter)
_registry.register_adapter('unify', UnifyAdapter)
_registry.register_adapter('unify_v1', UnifyAdapter)
_registry.register_adapter('acquire', AcquireAdapter)
_registry.register_adapter('acquire_v1', AcquireAdapter)
_registry.register_adapter('mining_viability', MiningViabilityAdapter)
_registry.register_adapter('mining_viability_v1', MiningViabilityAdapter)