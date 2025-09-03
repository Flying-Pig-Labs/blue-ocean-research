#!/usr/bin/env python3
"""
City Revitalization Initiative Synthesizer - UNIFY Framework

Transforms opportunity zones into city revitalization initiatives that emphasize
unexpected alliances and cross-sector partnerships for urban improvement.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RevitalizationInitiative:
    """City revitalization initiative with uncommon alliance focus."""
    
    # Core identification
    initiative_id: str
    title: str
    zone_focus: str
    
    # Uncommon alliance details
    uncommon_alliance: List[str]
    alliance_origin: str
    rationale: str
    
    # Implementation details
    initiative_plan: str
    stakeholder_map: List[str]
    impact_metrics: List[str]
    resilience_notes: str
    
    # Scoring and analysis
    unify_scores: Dict[str, float]
    
    # Supporting information
    citations: List[str]
    funding_channels: List[str] = field(default_factory=list)
    timeline_milestones: List[str] = field(default_factory=list)
    risk_mitigation: List[str] = field(default_factory=list)
    success_stories: List[str] = field(default_factory=list)
    
    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence_score: float = 0.0
    
    def to_github_issue(self) -> Dict[str, Any]:
        """Convert to GitHub issue format with YAML frontmatter."""
        
        # Create YAML frontmatter
        frontmatter = {
            'type': 'revitalization_initiative',
            'title': self.title,
            'zone_focus': self.zone_focus,
            'uncommon_alliance': self.uncommon_alliance,
            'rationale': self.rationale,
            'initiative_plan': self.initiative_plan,
            'stakeholder_map': self.stakeholder_map,
            'alliance_origin': self.alliance_origin,
            'impact_metrics': self.impact_metrics,
            'resilience_notes': self.resilience_notes,
            'unify_scores': self.unify_scores,
            'citations': self.citations
        }
        
        # Add optional fields if present
        if self.funding_channels:
            frontmatter['funding_channels'] = self.funding_channels
        if self.timeline_milestones:
            frontmatter['timeline_milestones'] = self.timeline_milestones
        if self.risk_mitigation:
            frontmatter['risk_mitigation'] = self.risk_mitigation
        if self.success_stories:
            frontmatter['success_stories'] = self.success_stories
            
        # Create issue body
        body_parts = []
        
        # Executive summary
        body_parts.append("## Executive Summary")
        body_parts.append(f"**Zone Focus**: {self.zone_focus}")
        body_parts.append(f"**Alliance Partners**: {', '.join(self.uncommon_alliance)}")
        body_parts.append(f"**UNIFY Score**: {self.unify_scores.get('composite', 0.0):.2f}")
        body_parts.append("")
        
        # Alliance rationale
        body_parts.append("## Uncommon Alliance Rationale")
        body_parts.append(self.rationale)
        body_parts.append("")
        
        # Implementation plan
        body_parts.append("## Initiative Implementation Plan")
        body_parts.append(self.initiative_plan)
        body_parts.append("")
        
        # Alliance origin story
        body_parts.append("## Alliance Origin & Context")
        body_parts.append(self.alliance_origin)
        body_parts.append("")
        
        # Stakeholder ecosystem
        body_parts.append("## Stakeholder Ecosystem")
        for stakeholder in self.stakeholder_map:
            body_parts.append(f"- {stakeholder}")
        body_parts.append("")
        
        # Impact measurement
        body_parts.append("## Expected Impact Metrics")
        for metric in self.impact_metrics:
            body_parts.append(f"- {metric}")
        body_parts.append("")
        
        # Resilience analysis
        body_parts.append("## Alliance Resilience & Risk Management")
        body_parts.append(self.resilience_notes)
        body_parts.append("")
        
        # UNIFY framework scores
        body_parts.append("## UNIFY Framework Analysis")
        body_parts.append("| Dimension | Score | Description |")
        body_parts.append("|-----------|-------|-------------|")
        
        dimension_descriptions = {
            'need_alignment': 'How directly addresses urban pain points',
            'uncommon_pairing_strength': 'Novelty of cross-boundary alliance',
            'feasibility': 'Practical implementation viability',
            'impact_potential': 'Expected community uplift',
            'narrative_resonance': 'Story power for buy-in',
            'resilience': 'Alliance survival under stress'
        }
        
        for dim, score in self.unify_scores.items():
            if dim != 'composite':
                desc = dimension_descriptions.get(dim, dim.replace('_', ' ').title())
                body_parts.append(f"| {dim.replace('_', ' ').title()} | {score:.2f} | {desc} |")
        body_parts.append("")
        
        # Funding opportunities
        if self.funding_channels:
            body_parts.append("## Potential Funding Channels")
            for funding in self.funding_channels:
                body_parts.append(f"- {funding}")
            body_parts.append("")
        
        # Timeline
        if self.timeline_milestones:
            body_parts.append("## Implementation Timeline")
            for milestone in self.timeline_milestones:
                body_parts.append(f"- {milestone}")
            body_parts.append("")
                
        # Supporting evidence
        body_parts.append("## Supporting Evidence & Citations")
        for citation in self.citations:
            body_parts.append(f"- {citation}")
            
        return {
            'title': f"🤝 {self.title}",
            'body': '\n'.join(body_parts),
            'frontmatter': frontmatter,
            'labels': ['opportunity', 'revitalization', 'uncommon-alliance', 'city-planning', 'community-partnership']
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'initiative_id': self.initiative_id,
            'title': self.title,
            'zone_focus': self.zone_focus,
            'uncommon_alliance': self.uncommon_alliance,
            'alliance_origin': self.alliance_origin,
            'rationale': self.rationale,
            'initiative_plan': self.initiative_plan,
            'stakeholder_map': self.stakeholder_map,
            'impact_metrics': self.impact_metrics,
            'resilience_notes': self.resilience_notes,
            'unify_scores': self.unify_scores,
            'citations': self.citations,
            'funding_channels': self.funding_channels,
            'timeline_milestones': self.timeline_milestones,
            'risk_mitigation': self.risk_mitigation,
            'success_stories': self.success_stories,
            'created_date': self.created_date,
            'confidence_score': self.confidence_score
        }

class RevitalizationSynthesizer:
    """Synthesizes city revitalization initiatives from opportunity zones using UNIFY framework."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize synthesizer with configuration."""
        self.config = config or {}
        self.unify_weights = self.config.get('unify_weights', {
            'NA': 0.20, 'UPS': 0.25, 'FZ': 0.15, 'IP': 0.20, 'NR': 0.10, 'RS': 0.10
        })
        
    def synthesize_initiatives(self, zones: List[Dict[str, Any]], 
                             target_count: int = 10) -> List[RevitalizationInitiative]:
        """
        Synthesize city revitalization initiatives from opportunity zones.
        
        Args:
            zones: List of opportunity zone dictionaries with UNIFY analysis
            target_count: Target number of initiatives to generate
            
        Returns:
            List of RevitalizationInitiative objects
        """
        initiatives = []
        
        # Sort zones by UNIFY composite score (highest first)
        sorted_zones = sorted(zones, 
                            key=lambda z: z.get('framework_analysis', {}).get('overall_score', 0), 
                            reverse=True)
        
        for i, zone in enumerate(sorted_zones[:target_count]):
            try:
                initiative = self._create_initiative_from_zone(zone, i + 1)
                initiatives.append(initiative)
                logger.info(f"Created revitalization initiative: {initiative.title}")
                
            except Exception as e:
                logger.error(f"Failed to create initiative from zone {zone.get('id', 'unknown')}: {e}")
                continue
                
        return initiatives
    
    def _create_initiative_from_zone(self, zone: Dict[str, Any], index: int) -> RevitalizationInitiative:
        """Create a single revitalization initiative from an opportunity zone."""
        
        zone_id = zone.get('id', f'zone_{index}')
        zone_name = zone.get('name', f'Opportunity Zone {index}')
        
        # Extract framework analysis
        framework_analysis = zone.get('framework_analysis', {})
        unify_scores = framework_analysis.get('scores', {})
        recommendations = framework_analysis.get('recommendations', [])
        
        # Extract zone data
        pain_dimensions = zone.get('pain_dimensions', {})
        solution_requirements = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds', [])
        discussions = zone.get('discussions', [])
        
        # Generate initiative components
        title = self._generate_initiative_title(zone_name, pain_dimensions, index)
        zone_focus = self._extract_zone_focus(pain_dimensions, jtbds)
        uncommon_alliance = self._generate_uncommon_alliance(solution_requirements, discussions)
        alliance_origin = self._generate_alliance_origin(discussions, zone_focus)
        rationale = self._generate_alliance_rationale(uncommon_alliance, zone_focus, pain_dimensions)
        initiative_plan = self._generate_initiative_plan(recommendations, solution_requirements, uncommon_alliance)
        stakeholder_map = self._generate_stakeholder_map(discussions, solution_requirements)
        impact_metrics = self._generate_impact_metrics(pain_dimensions, recommendations)
        resilience_notes = self._generate_resilience_notes(unify_scores, recommendations)
        citations = self._generate_citations(zone, discussions)
        funding_channels = self._generate_funding_channels(zone_focus, impact_metrics)
        
        # Add composite UNIFY score
        composite_score = self._calculate_composite_unify_score(unify_scores)
        unify_scores['composite'] = composite_score
        
        return RevitalizationInitiative(
            initiative_id=f"revit_{zone_id}_{index:02d}",
            title=title,
            zone_focus=zone_focus,
            uncommon_alliance=uncommon_alliance,
            alliance_origin=alliance_origin,
            rationale=rationale,
            initiative_plan=initiative_plan,
            stakeholder_map=stakeholder_map,
            impact_metrics=impact_metrics,
            resilience_notes=resilience_notes,
            unify_scores=unify_scores,
            citations=citations,
            funding_channels=funding_channels,
            confidence_score=framework_analysis.get('confidence_level', 0.5)
        )
    
    def _generate_initiative_title(self, zone_name: str, pain_dimensions: Dict[str, float], index: int) -> str:
        """Generate a catchy initiative title."""
        # Extract top pain dimension for theme
        top_pain = max(pain_dimensions.items(), key=lambda x: x[1])[0] if pain_dimensions else "community"
        
        title_templates = {
            'community_disconnect': ["Bridge Builder Alliance", "Neighbor Connect Hub", "Community Crossroads"],
            'economic_decline': ["Commerce Revival Coalition", "Business Bridge Initiative", "Economic Unity Project"],
            'infrastructure_gaps': ["Infrastructure Innovation Alliance", "Systems Sync Partnership", "Urban Grid Coalition"],
            'governance_barriers': ["Civic Bridge Initiative", "Policy Partnership Hub", "Governance Gateway"],
            'resource_scarcity': ["Resource Sharing Alliance", "Abundance Partnership", "Community Resource Hub"]
        }
        
        templates = title_templates.get(top_pain, ["Alliance Initiative", "Partnership Project", "Coalition Hub"])
        
        if index <= len(templates):
            return templates[index - 1]
        else:
            return f"{templates[0]} #{index}"
    
    def _extract_zone_focus(self, pain_dimensions: Dict[str, float], jtbds: List[str]) -> str:
        """Extract the primary focus area for the zone."""
        if not pain_dimensions:
            return "Community revitalization and cross-sector collaboration"
            
        top_pain = max(pain_dimensions.items(), key=lambda x: x[1])[0]
        
        focus_mapping = {
            'community_disconnect': 'Building community connections and social cohesion',
            'economic_decline': 'Revitalizing local economy and small business ecosystem', 
            'infrastructure_gaps': 'Improving urban infrastructure and systems integration',
            'governance_barriers': 'Enhancing civic engagement and policy coordination',
            'resource_scarcity': 'Optimizing resource sharing and community assets'
        }
        
        return focus_mapping.get(top_pain, f"Addressing {top_pain.replace('_', ' ')} challenges")
    
    def _generate_uncommon_alliance(self, solution_requirements: List[str], discussions: List[str]) -> List[str]:
        """Generate an unexpected but logical alliance of 2-3 partners."""
        
        # Extract potential stakeholder types from solutions and discussions
        stakeholder_keywords = {
            'sports': ['arena', 'stadium', 'sports', 'team', 'athletics'],
            'food_service': ['restaurant', 'food', 'kitchen', 'catering', 'concession'],
            'healthcare': ['hospital', 'clinic', 'health', 'medical', 'care'],
            'education': ['school', 'university', 'college', 'education', 'student'],
            'faith': ['church', 'religious', 'faith', 'congregation', 'spiritual'],
            'tech': ['technology', 'tech', 'digital', 'internet', 'startup'],
            'utilities': ['utility', 'power', 'electric', 'water', 'infrastructure'],
            'arts': ['art', 'artist', 'creative', 'culture', 'gallery'],
            'transit': ['transit', 'bus', 'transportation', 'mobility', 'parking'],
            'retail': ['business', 'retail', 'shop', 'store', 'commercial']
        }
        
        # Find mentioned stakeholder types
        mentioned_types = []
        all_text = ' '.join(solution_requirements + discussions).lower()
        
        for stakeholder_type, keywords in stakeholder_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                mentioned_types.append(stakeholder_type)
        
        # Generate uncommon alliance combinations
        uncommon_pairs = [
            ['Sports arena operators', 'Community health clinics'],
            ['Religious congregations', 'Tech startups'],
            ['University research labs', 'Local food vendors'],
            ['Utility companies', 'Arts organizations'],
            ['Transit authorities', 'Small retailers'],
            ['Hospital systems', 'Community colleges'],
            ['Food service suppliers', 'Neighborhood co-ops'],
            ['Energy cooperatives', 'Cultural centers']
        ]
        
        # Select most relevant alliance or default
        if len(mentioned_types) >= 2:
            # Try to match mentioned types to alliance pairs
            for pair in uncommon_pairs:
                if any(stype in pair[0].lower() for stype in mentioned_types) and \
                   any(stype in pair[1].lower() for stype in mentioned_types):
                    return pair
                    
        # Default to first alliance as fallback
        return uncommon_pairs[0]
    
    def _generate_alliance_origin(self, discussions: List[str], zone_focus: str) -> str:
        """Generate the origin story for why this alliance formed now."""
        
        origin_templates = [
            f"Recent community discussions about {zone_focus.lower()} revealed complementary assets that were previously overlooked, creating an opportune moment for this unexpected partnership.",
            f"A convergence of local events and policy changes has created unique conditions where these traditionally separate sectors can collaborate effectively on {zone_focus.lower()}.",
            f"Community pressure and funding opportunities have aligned to enable this cross-sector alliance, addressing {zone_focus.lower()} through innovative partnership structures.",
            f"Local leaders identified untapped synergies between these sectors during recent {zone_focus.lower()} planning sessions, leading to this pioneering collaboration model."
        ]
        
        # Look for specific events or contexts in discussions
        event_keywords = ['funding', 'policy', 'crisis', 'opportunity', 'change', 'new', 'initiative']
        if discussions and any(keyword in ' '.join(discussions).lower() for keyword in event_keywords):
            return origin_templates[1]  # Use policy/events template
            
        return origin_templates[0]  # Default template
    
    def _generate_alliance_rationale(self, alliance: List[str], zone_focus: str, pain_dimensions: Dict[str, float]) -> str:
        """Generate rationale for why this alliance makes unexpected sense."""
        
        partner1 = alliance[0] if len(alliance) > 0 else "First partner"
        partner2 = alliance[1] if len(alliance) > 1 else "Second partner"
        
        # Identify primary challenge
        top_challenge = "community challenges"
        if pain_dimensions:
            top_pain = max(pain_dimensions.items(), key=lambda x: x[1])[0]
            top_challenge = top_pain.replace('_', ' ')
        
        rationale = f"""
This alliance between {partner1.lower()} and {partner2.lower()} initially appears unlikely, but reveals powerful complementary strengths when addressing {top_challenge}.

**Complementary Assets:**
- {partner1} bring underutilized physical infrastructure, established community presence, and operational systems
- {partner2} contribute specialized expertise, community trust, and flexible service delivery capabilities

**Unexpected Synergies:**
- Shared timing and resource optimization - both sectors have complementary peak/off-peak periods
- Mutual community credibility - each partner reaches different but overlapping community segments
- Resource efficiency - combining facilities, supply chains, and operational expertise reduces costs for both

**Strategic Logic:**
Rather than competing for limited community resources, this alliance creates new value through resource sharing and expanded service capacity, directly addressing {zone_focus.lower()} in ways neither partner could achieve independently.
        """.strip()
        
        return rationale
    
    def _generate_initiative_plan(self, recommendations: List[str], solutions: List[str], alliance: List[str]) -> str:
        """Generate concrete implementation plan."""
        
        partner1 = alliance[0] if len(alliance) > 0 else "Primary partner"
        partner2 = alliance[1] if len(alliance) > 1 else "Secondary partner"
        
        plan = f"""
**Phase 1: Partnership Foundation (Months 1-3)**
- Establish formal partnership agreement between {partner1.lower()} and {partner2.lower()}
- Conduct joint asset mapping and resource assessment
- Develop shared governance structure and decision-making protocols
- Secure initial pilot funding and regulatory approvals

**Phase 2: Pilot Implementation (Months 4-9)**
- Launch limited-scope pilot program with 2-3 specific services/programs
- Establish shared operational procedures and communication systems
- Begin community outreach and stakeholder engagement
- Implement basic performance measurement and feedback systems

**Phase 3: Scale and Optimize (Months 10-18)**
- Expand successful pilot elements based on community response
- Integrate additional community partners and stakeholder organizations
- Develop sustainable funding model combining multiple revenue streams
- Establish long-term governance and succession planning

**Key Success Factors:**
- Regular community feedback sessions and adaptive program design
- Transparent resource sharing agreements with clear benefit distribution
- Strong communication protocols between alliance partners
- Measurable impact metrics aligned with community priorities
        """.strip()
        
        return plan
    
    def _generate_stakeholder_map(self, discussions: List[str], solutions: List[str]) -> List[str]:
        """Generate list of relevant local stakeholders."""
        
        stakeholder_categories = [
            "City planning department and zoning authorities",
            "Local business association and chamber of commerce", 
            "Neighborhood councils and resident associations",
            "Community development corporations",
            "Local nonprofit organizations and service providers",
            "Faith-based community organizations",
            "Educational institutions and workforce development agencies",
            "Public safety and emergency services coordination"
        ]
        
        # Look for specific stakeholder mentions in discussions/solutions
        mentioned_stakeholders = []
        all_text = ' '.join(discussions + solutions).lower()
        
        stakeholder_keywords = {
            'government': ['city', 'municipal', 'government', 'council', 'mayor'],
            'business': ['business', 'chamber', 'commerce', 'economic', 'entrepreneur'],
            'community': ['community', 'neighborhood', 'resident', 'citizen', 'local'],
            'nonprofit': ['nonprofit', 'foundation', 'charity', 'service', 'organization'],
            'education': ['school', 'university', 'college', 'education', 'workforce'],
            'healthcare': ['health', 'medical', 'clinic', 'hospital', 'wellness'],
            'faith': ['church', 'faith', 'religious', 'congregation', 'spiritual'],
            'safety': ['police', 'fire', 'safety', 'emergency', 'security']
        }
        
        for category, keywords in stakeholder_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                if category == 'government':
                    mentioned_stakeholders.append("City planning department and zoning authorities")
                elif category == 'business':
                    mentioned_stakeholders.append("Local business association and chamber of commerce")
                elif category == 'community':
                    mentioned_stakeholders.append("Neighborhood councils and resident associations")
                elif category == 'nonprofit':
                    mentioned_stakeholders.append("Local nonprofit organizations and service providers")
                elif category == 'education':
                    mentioned_stakeholders.append("Educational institutions and workforce development agencies")
                elif category == 'healthcare':
                    mentioned_stakeholders.append("Community health centers and medical facilities")
                elif category == 'faith':
                    mentioned_stakeholders.append("Faith-based community organizations")
                elif category == 'safety':
                    mentioned_stakeholders.append("Public safety and emergency services coordination")
        
        # Return mentioned stakeholders or default set
        return mentioned_stakeholders[:6] if mentioned_stakeholders else stakeholder_categories[:6]
    
    def _generate_impact_metrics(self, pain_dimensions: Dict[str, float], recommendations: List[str]) -> List[str]:
        """Generate measurable impact metrics."""
        
        base_metrics = [
            "Number of residents directly served per month",
            "Square footage of underutilized space activated",
            "Number of new cross-sector partnerships established", 
            "Reduction in service delivery costs per capita",
            "Community satisfaction scores (quarterly survey)",
            "Number of jobs created or sustained",
            "Increase in local business participation",
            "Improvement in neighborhood walkability scores"
        ]
        
        # Customize based on pain dimensions
        if pain_dimensions:
            top_pain = max(pain_dimensions.items(), key=lambda x: x[1])[0]
            
            pain_specific_metrics = {
                'community_disconnect': [
                    "Increase in inter-community event attendance",
                    "Growth in neighborhood social network connections",
                    "Reduction in community conflict incidents"
                ],
                'economic_decline': [
                    "Local business revenue growth percentage",
                    "Reduction in commercial vacancy rates",
                    "Number of new local jobs created"
                ],
                'infrastructure_gaps': [
                    "Infrastructure reliability improvement scores",
                    "Reduction in service interruption incidents",
                    "Community access improvement metrics"
                ]
            }
            
            specific_metrics = pain_specific_metrics.get(top_pain, [])
            return base_metrics[:5] + specific_metrics
            
        return base_metrics[:6]
    
    def _generate_resilience_notes(self, unify_scores: Dict[str, float], recommendations: List[str]) -> str:
        """Generate resilience analysis and risk management notes."""
        
        resilience_score = unify_scores.get('resilience', 0.5)
        
        if resilience_score > 0.7:
            risk_level = "Low"
            resilience_assessment = "Strong alliance resilience with multiple stability factors"
        elif resilience_score > 0.4:
            risk_level = "Moderate" 
            resilience_assessment = "Moderate resilience requiring proactive risk management"
        else:
            risk_level = "High"
            resilience_assessment = "Resilience concerns requiring significant risk mitigation"
            
        resilience_notes = f"""
**Risk Assessment Level: {risk_level}**

**Resilience Analysis:**
{resilience_assessment}. Key factors include alliance partner stability, funding sustainability, and community support levels.

**Primary Risks:**
- Leadership turnover in partner organizations could disrupt operational continuity
- Policy or regulatory changes may affect operational permissions or funding
- Economic downturns could impact partner organization resource availability
- Community priorities may shift, affecting program relevance and support

**Mitigation Strategies:**
- Develop succession planning and institutional knowledge transfer protocols
- Diversify funding sources across public, private, and philanthropic channels
- Build broad stakeholder coalition to provide multiple sources of support
- Create flexible program design that can adapt to changing community needs
- Establish formal agreements with clear dispute resolution mechanisms

**Contingency Plans:**
- Identify backup partners for each core alliance function
- Maintain emergency funding reserves equivalent to 3-6 months operations
- Develop scaled-down service delivery models for resource-constrained periods
- Create community advisory structure to provide ongoing guidance and legitimacy
        """.strip()
        
        return resilience_notes
    
    def _generate_citations(self, zone: Dict[str, Any], discussions: List[str]) -> List[str]:
        """Generate supporting citations and references."""
        
        citations = []
        
        # Zone-based citations
        zone_id = zone.get('id', 'unknown')
        citations.append(f"Opportunity Zone Analysis: {zone_id}")
        
        # Discussion citations
        if discussions:
            for i, discussion in enumerate(discussions[:3]):
                # Create abbreviated citation from discussion
                citation_text = discussion[:100] + "..." if len(discussion) > 100 else discussion
                citations.append(f"Community Discussion {i+1}: {citation_text}")
        
        # Framework citations
        framework_analysis = zone.get('framework_analysis', {})
        if framework_analysis:
            citations.append(f"UNIFY Framework Analysis (confidence: {framework_analysis.get('confidence_level', 0):.2f})")
            
        # Add generic supportive citations
        citations.extend([
            "Local stakeholder interviews and community feedback sessions",
            "Municipal planning documents and zoning analysis",
            "Cross-sector partnership best practices research"
        ])
        
        return citations[:6]  # Limit to 6 citations
    
    def _generate_funding_channels(self, zone_focus: str, impact_metrics: List[str]) -> List[str]:
        """Generate potential funding opportunities."""
        
        funding_channels = [
            "Community Development Block Grant (CDBG) funds",
            "Private foundation grants focused on community partnerships",
            "Corporate social responsibility programs from alliance partners",
            "Municipal innovation or pilot program funding",
            "Federal opportunity zone investment incentives",
            "Social impact bond financing for measurable outcomes",
            "Crowdfunding campaigns for community-supported initiatives",
            "Revenue sharing from improved community services"
        ]
        
        # Customize based on focus area
        if 'economic' in zone_focus.lower():
            funding_channels.extend([
                "Small Business Administration (SBA) community development programs",
                "Economic development authority grants and loan programs"
            ])
        elif 'infrastructure' in zone_focus.lower():
            funding_channels.extend([
                "Infrastructure improvement bonds and special assessments",
                "Utility company community investment programs"
            ])
        elif 'health' in zone_focus.lower():
            funding_channels.extend([
                "Public health department community wellness grants",
                "Healthcare system community benefit program funding"
            ])
            
        return funding_channels[:8]  # Limit to 8 funding options
    
    def _calculate_composite_unify_score(self, unify_scores: Dict[str, float]) -> float:
        """Calculate weighted composite UNIFY score."""
        
        if not unify_scores:
            return 0.0
            
        weighted_score = 0.0
        total_weight = 0.0
        
        dimension_weights = {
            'need_alignment': self.unify_weights.get('NA', 0.20),
            'uncommon_pairing_strength': self.unify_weights.get('UPS', 0.25),
            'feasibility': self.unify_weights.get('FZ', 0.15),
            'impact_potential': self.unify_weights.get('IP', 0.20),
            'narrative_resonance': self.unify_weights.get('NR', 0.10),
            'resilience': self.unify_weights.get('RS', 0.10)
        }
        
        for dimension, score in unify_scores.items():
            if dimension in dimension_weights:
                weight = dimension_weights[dimension]
                weighted_score += score * weight
                total_weight += weight
                
        return round(weighted_score / total_weight if total_weight > 0 else 0.0, 3)