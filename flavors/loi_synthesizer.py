#!/usr/bin/env python3
"""
Private Equity LOI Synthesizer - ACQUIRE Framework

Transforms opportunity zones into preliminary Letters of Intent (LOIs) 
for private equity acquisition targets with detailed deal structure and terms.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PreliminaryLOI:
    """Preliminary Letter of Intent for private equity acquisition."""
    
    # Core identification
    loi_id: str
    title: str
    target_company: str
    industry: str
    location: str
    source_url: str
    
    # Market intelligence
    quick_facts: List[str]
    thesis_fit: str
    seller_motivation: Optional[str] = None
    
    # ACQUIRE scoring
    acquire_scores: Dict[str, Any] = field(default_factory=dict)
    
    # Deal structure
    offer_summary: Dict[str, Any] = field(default_factory=dict)
    contingencies: List[str] = field(default_factory=list)
    exclusivity_days: int = 45
    diligence_period_days: int = 60
    
    # Risk and planning
    key_risks: List[str] = field(default_factory=list)
    post_close_plan: str = ""
    
    # Contact and references
    broker_contact: Optional[str] = None
    citations: List[str] = field(default_factory=list)
    
    # Optional terms
    rollover_equity_terms: Optional[str] = None
    management_retention: Optional[str] = None
    
    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence_score: float = 0.0
    
    def to_github_issue(self) -> Dict[str, Any]:
        """Convert to GitHub issue format with YAML frontmatter."""
        
        # Create YAML frontmatter
        frontmatter = {
            'type': 'preliminary_loi',
            'title': self.title,
            'target_company': self.target_company,
            'industry': self.industry,
            'location': self.location,
            'source_url': self.source_url,
            'quick_facts': self.quick_facts,
            'thesis_fit': self.thesis_fit,
            'acquire_scores': self.acquire_scores,
            'offer_summary': self.offer_summary,
            'contingencies': self.contingencies,
            'exclusivity_days': self.exclusivity_days,
            'diligence_period_days': self.diligence_period_days,
            'key_risks': self.key_risks,
            'post_close_plan': self.post_close_plan,
            'citations': self.citations
        }
        
        # Add optional fields if present
        if self.seller_motivation:
            frontmatter['seller_motivation'] = self.seller_motivation
        if self.broker_contact:
            frontmatter['broker_contact'] = self.broker_contact
        if self.rollover_equity_terms:
            frontmatter['rollover_equity_terms'] = self.rollover_equity_terms
        if self.management_retention:
            frontmatter['management_retention'] = self.management_retention
            
        # Create issue body
        body_parts = []
        
        # Executive summary
        body_parts.append("## Executive Summary")
        body_parts.append(f"**Target**: {self.target_company}")
        body_parts.append(f"**Industry**: {self.industry}")
        body_parts.append(f"**Location**: {self.location}")
        body_parts.append(f"**ACQUIRE Score**: {self.acquire_scores.get('rank_score', self.acquire_scores.get('composite', 0.0)):.2f}")
        if self.offer_summary.get('price_range'):
            body_parts.append(f"**Preliminary Offer**: {self.offer_summary['price_range']}")
        body_parts.append("")
        
        # Quick facts
        body_parts.append("## Target Profile")
        for fact in self.quick_facts:
            body_parts.append(f"- {fact}")
        body_parts.append("")
        
        # Thesis fit
        body_parts.append("## Investment Thesis Fit")
        body_parts.append(self.thesis_fit)
        body_parts.append("")
        
        # ACQUIRE framework analysis
        body_parts.append("## ACQUIRE Framework Analysis")
        body_parts.append("| Dimension | Score | Weight | Contribution |")
        body_parts.append("|-----------|-------|--------|--------------|")
        
        dimension_labels = {
            'addressable_fragmentation': 'Addressable Fragmentation',
            'cashflow_quality': 'Cashflow Quality',
            'quality_of_operations': 'Quality of Operations',
            'upside_levers': 'Upside Levers',
            'integration_readiness': 'Integration Readiness',
            'risk_compliance': 'Risk & Compliance',
            'exit_pathways': 'Exit Pathways'
        }
        
        axes = self.acquire_scores.get('axes', {})
        weights = self.acquire_scores.get('weights', {})
        
        for dim_key, score in axes.items():
            label = dimension_labels.get(dim_key, dim_key.replace('_', ' ').title())
            weight = weights.get(dim_key.upper()[:1], 0.0)
            contribution = score * weight
            body_parts.append(f"| {label} | {score:.2f} | {weight:.0%} | {contribution:.3f} |")
        
        composite = self.acquire_scores.get('composite', 0.0)
        rank_score = self.acquire_scores.get('rank_score', composite)
        body_parts.append(f"| **Composite** | **{composite:.2f}** | | |")
        body_parts.append(f"| **Rank Score** | **{rank_score:.2f}** | | |")
        body_parts.append("")
        
        # Deal structure
        body_parts.append("## Preliminary Deal Structure")
        body_parts.append("*Subject to due diligence and final negotiation*")
        body_parts.append("")
        
        if self.offer_summary:
            if self.offer_summary.get('price_range'):
                body_parts.append(f"**Purchase Price**: {self.offer_summary['price_range']}")
            
            structure = self.offer_summary.get('structure', {})
            if structure:
                body_parts.append("\n**Deal Structure**:")
                if structure.get('cash_at_close_pct'):
                    body_parts.append(f"- Cash at Close: {structure['cash_at_close_pct']:.0f}%")
                if structure.get('seller_note_pct'):
                    body_parts.append(f"- Seller Note: {structure['seller_note_pct']:.0f}%")
                if structure.get('earnout_pct'):
                    body_parts.append(f"- Earnout: {structure['earnout_pct']:.0f}%")
                
                if structure.get('earnout_metrics'):
                    body_parts.append("\n**Earnout Metrics**:")
                    for metric in structure['earnout_metrics']:
                        body_parts.append(f"- {metric}")
            
            if self.offer_summary.get('working_capital_target'):
                body_parts.append(f"\n**Working Capital**: {self.offer_summary['working_capital_target']}")
        
        body_parts.append("")
        
        # Due diligence contingencies
        body_parts.append("## Due Diligence Contingencies")
        for contingency in self.contingencies:
            body_parts.append(f"- {contingency}")
        body_parts.append("")
        
        # Timeline
        body_parts.append("## Transaction Timeline")
        body_parts.append(f"- **Exclusivity Period**: {self.exclusivity_days} days")
        body_parts.append(f"- **Due Diligence Period**: {self.diligence_period_days} days")
        
        drop_dead_date = datetime.now() + timedelta(days=120)
        body_parts.append(f"- **Estimated Drop-Dead Date**: {drop_dead_date.strftime('%B %d, %Y')}")
        body_parts.append("")
        
        # Risk assessment
        body_parts.append("## Key Risk Factors")
        for risk in self.key_risks:
            body_parts.append(f"- {risk}")
        body_parts.append("")
        
        # Post-close plan
        body_parts.append("## Post-Closing Integration Plan")
        body_parts.append(self.post_close_plan)
        body_parts.append("")
        
        # Contact information
        if self.broker_contact:
            body_parts.append("## Broker Contact")
            body_parts.append(f"**Contact**: {self.broker_contact}")
            body_parts.append("")
        
        # Disclaimers
        body_parts.append("## Important Disclaimers")
        body_parts.append("- **Non-Binding**: This LOI is preliminary and non-binding")
        body_parts.append("- **Subject to Diligence**: All terms subject to satisfactory due diligence")
        body_parts.append("- **Financing Contingent**: Offer contingent on financing availability")
        body_parts.append("- **Preliminary Valuation**: Price range is preliminary and subject to QoE")
        body_parts.append("")
        
        # Supporting evidence
        body_parts.append("## Supporting Evidence & Citations")
        for citation in self.citations:
            body_parts.append(f"- {citation}")
        
        # Add source link
        if self.source_url:
            body_parts.append(f"- Original Listing: [{self.source_url}]({self.source_url})")
            
        return {
            'title': f"[PE LOI] {self.target_company} – {self.location}",
            'body': '\n'.join(body_parts),
            'frontmatter': frontmatter,
            'labels': ['opportunity', 'PE', 'acquisition', 'preliminary-LOI', 'deal-book']
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'loi_id': self.loi_id,
            'title': self.title,
            'target_company': self.target_company,
            'industry': self.industry,
            'location': self.location,
            'source_url': self.source_url,
            'quick_facts': self.quick_facts,
            'thesis_fit': self.thesis_fit,
            'seller_motivation': self.seller_motivation,
            'acquire_scores': self.acquire_scores,
            'offer_summary': self.offer_summary,
            'contingencies': self.contingencies,
            'exclusivity_days': self.exclusivity_days,
            'diligence_period_days': self.diligence_period_days,
            'key_risks': self.key_risks,
            'post_close_plan': self.post_close_plan,
            'broker_contact': self.broker_contact,
            'citations': self.citations,
            'rollover_equity_terms': self.rollover_equity_terms,
            'management_retention': self.management_retention,
            'created_date': self.created_date,
            'confidence_score': self.confidence_score
        }

class LOISynthesizer:
    """Synthesizes preliminary Letters of Intent from opportunity zones using ACQUIRE framework."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize LOI synthesizer with configuration."""
        self.config = config or {}
        self.synthesis_config = self.config.get('synthesis', {})
        self.thesis_preferences = self.config.get('thesis_preferences', {})
        
    def synthesize_lois(self, zones: List[Dict[str, Any]], 
                       target_count: int = 10) -> List[PreliminaryLOI]:
        """
        Synthesize preliminary LOIs from opportunity zones.
        
        Args:
            zones: List of opportunity zone dictionaries with ACQUIRE analysis
            target_count: Target number of LOIs to generate
            
        Returns:
            List of PreliminaryLOI objects
        """
        lois = []
        
        # Sort zones by ACQUIRE rank score (highest first)
        sorted_zones = sorted(zones, 
                            key=lambda z: z.get('framework_analysis', {}).get('overall_score', 0), 
                            reverse=True)
        
        for i, zone in enumerate(sorted_zones[:target_count]):
            try:
                loi = self._create_loi_from_zone(zone, i + 1)
                lois.append(loi)
                logger.info(f"Created preliminary LOI: {loi.title}")
                
            except Exception as e:
                logger.error(f"Failed to create LOI from zone {zone.get('id', 'unknown')}: {e}")
                continue
                
        return lois
    
    def _create_loi_from_zone(self, zone: Dict[str, Any], index: int) -> PreliminaryLOI:
        """Create a single preliminary LOI from an opportunity zone."""
        
        zone_id = zone.get('id', f'zone_{index}')
        zone_name = zone.get('name', f'Acquisition Target {index}')
        
        # Extract framework analysis
        framework_analysis = zone.get('framework_analysis', {})
        acquire_scores = framework_analysis.get('scores', {})
        recommendations = framework_analysis.get('recommendations', [])
        
        # Extract zone data
        pain_dimensions = zone.get('pain_dimensions', {})
        solution_requirements = zone.get('solution_requirements', [])
        jtbds = zone.get('jtbds', [])
        discussions = zone.get('discussions', [])
        
        # Generate LOI components
        target_company = self._generate_target_company_name(zone_name, pain_dimensions)
        title = self._generate_loi_title(target_company, pain_dimensions, index)
        industry = self._extract_industry(pain_dimensions, discussions, jtbds)
        location = self._extract_location(zone_name, discussions)
        source_url = self._generate_source_url(zone_id, industry)
        
        quick_facts = self._generate_quick_facts(pain_dimensions, discussions, solution_requirements)
        thesis_fit = self._generate_thesis_fit(zone_name, pain_dimensions, recommendations)
        seller_motivation = self._extract_seller_motivation(discussions)
        
        # Enhanced ACQUIRE scores with modifiers
        enhanced_acquire_scores = self._enhance_acquire_scores(acquire_scores, framework_analysis)
        
        # Generate deal structure
        offer_summary = self._generate_offer_summary(quick_facts, enhanced_acquire_scores)
        contingencies = self._generate_contingencies(industry, enhanced_acquire_scores)
        key_risks = self._generate_key_risks(pain_dimensions, recommendations, industry)
        post_close_plan = self._generate_post_close_plan(recommendations, solution_requirements)
        
        # Generate contact and citations
        broker_contact = self._generate_broker_contact(source_url)
        citations = self._generate_citations(zone, discussions, source_url)
        
        return PreliminaryLOI(
            loi_id=f"loi_{zone_id}_{index:02d}",
            title=title,
            target_company=target_company,
            industry=industry,
            location=location,
            source_url=source_url,
            quick_facts=quick_facts,
            thesis_fit=thesis_fit,
            seller_motivation=seller_motivation,
            acquire_scores=enhanced_acquire_scores,
            offer_summary=offer_summary,
            contingencies=contingencies,
            exclusivity_days=self.synthesis_config.get('default_terms', {}).get('exclusivity_days', 45),
            diligence_period_days=self.synthesis_config.get('default_terms', {}).get('diligence_period_days', 60),
            key_risks=key_risks,
            post_close_plan=post_close_plan,
            broker_contact=broker_contact,
            citations=citations,
            confidence_score=framework_analysis.get('confidence_level', 0.5)
        )
    
    def _generate_target_company_name(self, zone_name: str, pain_dimensions: Dict[str, float]) -> str:
        """Generate a target company name based on zone characteristics."""
        
        # Extract industry indicators from zone name and pain dimensions
        industry_mapping = {
            'hvac': 'HVAC Services, LLC',
            'veterinary': 'Animal Care Clinic',
            'dental': 'Dental Associates',
            'managed services': 'IT Solutions Group',
            'msp': 'Managed Services Provider',
            'maintenance': 'Service Solutions, Inc.',
            'healthcare': 'Healthcare Partners'
        }
        
        zone_lower = zone_name.lower()
        for keyword, company_name in industry_mapping.items():
            if keyword in zone_lower:
                return f"Confidential {company_name}"
                
        # Default to generic service business
        return f"Confidential Services, LLC"
    
    def _generate_loi_title(self, target_company: str, pain_dimensions: Dict[str, float], index: int) -> str:
        """Generate LOI title based on acquisition strategy."""
        
        # Determine acquisition strategy based on pain dimensions
        if pain_dimensions.get('market_fragmentation', 0) > 0.6:
            strategy = "Roll-Up"
        elif pain_dimensions.get('consolidation_opportunity', 0) > 0.6:
            strategy = "Add-On"
        elif pain_dimensions.get('scalability_potential', 0) > 0.6:
            strategy = "Platform"
        else:
            strategy = "Acquisition"
            
        # Extract business type
        if 'HVAC' in target_company:
            business_type = "HVAC Service"
        elif 'Dental' in target_company:
            business_type = "Dental Practice"
        elif 'Veterinary' in target_company or 'Animal' in target_company:
            business_type = "Veterinary Clinic"
        elif 'IT' in target_company or 'Managed' in target_company:
            business_type = "MSP Business"
        else:
            business_type = "Service Business"
            
        return f"{strategy}: {business_type} Opportunity"
    
    def _extract_industry(self, pain_dimensions: Dict[str, float], discussions: List[str], jtbds: List[str]) -> str:
        """Extract primary industry from zone data."""
        
        # Check for industry keywords in discussions and JTBDs
        all_text = ' '.join(discussions + jtbds).lower()
        
        industry_keywords = {
            'HVAC services': ['hvac', 'heating', 'cooling', 'air conditioning', 'furnace'],
            'veterinary clinics': ['veterinary', 'vet', 'animal', 'pet', 'clinic'],
            'dental practices': ['dental', 'dentist', 'oral', 'teeth', 'hygienist'],
            'managed IT services': ['msp', 'managed services', 'it support', 'technology', 'computer']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                return industry
                
        # Default based on pain dimensions
        if pain_dimensions.get('technology_adoption', 0) > 0.5:
            return 'managed IT services'
        elif pain_dimensions.get('service_delivery', 0) > 0.5:
            return 'professional services'
        else:
            return 'business services'
    
    def _extract_location(self, zone_name: str, discussions: List[str]) -> str:
        """Extract location from zone name or discussions."""
        
        # Default geographic regions from thesis preferences
        thesis_states = self.thesis_preferences.get('geography', {}).get('include_states', [])
        
        # Look for state mentions in discussions
        state_mapping = {
            'VA': 'Virginia', 'NC': 'North Carolina', 'SC': 'South Carolina',
            'MD': 'Maryland', 'PA': 'Pennsylvania', 'TN': 'Tennessee', 'GA': 'Georgia'
        }
        
        all_text = ' '.join(discussions).lower()
        for state_code in thesis_states:
            state_name = state_mapping.get(state_code, state_code)
            if state_code.lower() in all_text or state_name.lower() in all_text:
                return f"Greater {state_name} Area"
                
        # Extract from zone name if possible
        if 'metro' in zone_name.lower() or 'area' in zone_name.lower():
            return zone_name
            
        # Default to first preferred state
        if thesis_states:
            default_state = state_mapping.get(thesis_states[0], thesis_states[0])
            return f"{default_state} Metro Area"
            
        return "Southeast United States"
    
    def _generate_source_url(self, zone_id: str, industry: str) -> str:
        """Generate a mock broker listing URL."""
        
        broker_sites = ['bizbuysell', 'bizquest', 'transworld', 'sunbelt']
        site = broker_sites[hash(zone_id) % len(broker_sites)]
        
        listing_id = f"{hash(zone_id + industry) % 100000:05d}"
        
        return f"https://www.{site}.com/listing/{listing_id}"
    
    def _generate_quick_facts(self, pain_dimensions: Dict[str, float], discussions: List[str], solutions: List[str]) -> List[str]:
        """Generate quick facts about the target business."""
        
        facts = []
        
        # Revenue estimate based on size bounds
        size_bounds = self.thesis_preferences.get('size_bounds', {})
        min_rev = size_bounds.get('revenue_min', 1000000)
        max_rev = size_bounds.get('revenue_max', 20000000)
        
        # Estimate revenue based on market signals
        market_score = pain_dimensions.get('market_fragmentation', 0.5)
        revenue_estimate = int(min_rev + (max_rev - min_rev) * market_score)
        facts.append(f"Revenue: ~${revenue_estimate/1000000:.1f}M (estimated from market signals)")
        
        # SDE estimate
        sde_margin = 0.15 if market_score > 0.6 else 0.12  # Higher margins for fragmented markets
        sde_estimate = int(revenue_estimate * sde_margin)
        facts.append(f"SDE: ~${sde_estimate/1000:.0f}k (estimated at {sde_margin:.0%} margin)")
        
        # Company age estimate
        age_estimate = 15 + int(market_score * 10)  # More mature markets = older companies
        founding_year = datetime.now().year - age_estimate
        facts.append(f"Founded: ~{founding_year} ({age_estimate} years in business)")
        
        # Employee count estimate
        employees = max(5, int(revenue_estimate / 200000))  # ~$200k revenue per employee
        facts.append(f"Staff: ~{employees} employees (estimated)")
        
        # Add specific facts from discussions
        recurring_keywords = ['maintenance', 'contract', 'subscription', 'recurring']
        if any(keyword in ' '.join(discussions).lower() for keyword in recurring_keywords):
            facts.append("Recurring revenue component identified")
            
        return facts[:5]  # Limit to 5 facts
    
    def _generate_thesis_fit(self, zone_name: str, pain_dimensions: Dict[str, float], recommendations: List[str]) -> str:
        """Generate investment thesis fit explanation."""
        
        # Extract top pain dimensions
        top_pains = sorted(pain_dimensions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        fit_explanation = f"""
**Market Opportunity**: {zone_name} represents a compelling acquisition target with strong alignment to our investment thesis.

**Key Value Drivers**:
"""
        
        # Add value drivers based on pain dimensions
        for pain, score in top_pains:
            if score > 0.5:
                pain_readable = pain.replace('_', ' ').title()
                if pain == 'market_fragmentation':
                    fit_explanation += f"- **Market Consolidation**: {pain_readable} score of {score:.2f} indicates strong roll-up potential\n"
                elif pain == 'scalability_potential':
                    fit_explanation += f"- **Growth Platform**: {pain_readable} score of {score:.2f} suggests expansion opportunities\n"
                elif pain == 'technology_adoption':
                    fit_explanation += f"- **Digitization Upside**: {pain_readable} score of {score:.2f} indicates operational improvement potential\n"
                else:
                    fit_explanation += f"- **{pain_readable}**: Score of {score:.2f} aligns with value creation strategy\n"
        
        # Add geographic fit
        target_states = self.thesis_preferences.get('geography', {}).get('include_states', [])
        if target_states:
            fit_explanation += f"\n**Geographic Focus**: Target location within preferred {'/'.join(target_states)} cluster geography.\n"
        
        # Add strategic recommendations
        if recommendations:
            fit_explanation += f"\n**Strategic Rationale**: {recommendations[0]}"
            
        return fit_explanation.strip()
    
    def _extract_seller_motivation(self, discussions: List[str]) -> Optional[str]:
        """Extract seller motivation from discussions."""
        
        all_text = ' '.join(discussions).lower()
        
        motivation_keywords = {
            'retirement': ['retire', 'retirement', 'stepping down', 'succession'],
            'succession': ['succession', 'next generation', 'family transition'],
            'burnout': ['burnout', 'exhausted', 'work-life balance', 'stress'],
            'relocation': ['relocating', 'moving', 'geographic', 'relocation']
        }
        
        for motivation, keywords in motivation_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                return f"{motivation.title()} (inferred from market analysis)"
                
        return None
    
    def _enhance_acquire_scores(self, base_scores: Dict[str, float], framework_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance ACQUIRE scores with modifiers and detailed breakdown."""
        
        enhanced = {
            'axes': base_scores.copy(),
            'composite': framework_analysis.get('overall_score', 0.0),
            'weights': {
                'A': 0.15, 'C': 0.20, 'Q': 0.15, 'U': 0.20, 
                'I': 0.10, 'R': 0.10, 'E': 0.10
            }
        }
        
        # Apply modifiers
        modifiers = {}
        
        # Ownership type match modifier
        ownership_match = 0.05  # Default boost for thesis alignment
        modifiers['preference_fit'] = ownership_match
        
        # Geographic cluster fit
        cluster_fit = 0.05  # Default boost for geographic fit  
        modifiers['cluster_fit'] = cluster_fit
        
        enhanced['modifiers'] = modifiers
        
        # Calculate final rank score
        base_composite = enhanced['composite']
        total_modifiers = sum(modifiers.values())
        rank_score = base_composite * (1.0 + total_modifiers)
        
        enhanced['rank_score'] = round(rank_score, 3)
        
        return enhanced
    
    def _generate_offer_summary(self, quick_facts: List[str], acquire_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preliminary offer structure."""
        
        # Extract revenue/SDE from quick facts
        revenue_fact = next((f for f in quick_facts if 'Revenue:' in f), None)
        sde_fact = next((f for f in quick_facts if 'SDE:' in f), None)
        
        revenue_estimate = None
        sde_estimate = None
        
        if revenue_fact:
            try:
                # Extract revenue number
                rev_str = revenue_fact.split('~$')[1].split('M')[0]
                revenue_estimate = float(rev_str) * 1000000
            except:
                pass
                
        if sde_fact:
            try:
                # Extract SDE number  
                sde_str = sde_fact.split('~$')[1].split('k')[0]
                sde_estimate = float(sde_str) * 1000
            except:
                pass
        
        offer_summary = {}
        
        # Generate price range if SDE available
        if sde_estimate:
            # Use market multiples based on ACQUIRE score
            acquire_score = acquire_scores.get('composite', 0.5)
            
            # Multiple ranges based on quality
            if acquire_score > 0.7:
                multiple_low, multiple_high = 3.5, 4.5
            elif acquire_score > 0.5:
                multiple_low, multiple_high = 2.8, 3.8
            else:
                multiple_low, multiple_high = 2.5, 3.2
                
            price_low = int(sde_estimate * multiple_low)
            price_high = int(sde_estimate * multiple_high)
            
            offer_summary['price_range'] = f"${price_low/1000000:.1f}M – ${price_high/1000000:.1f}M (preliminary)"
            offer_summary['implied_multiple'] = f"{multiple_low:.1f}x – {multiple_high:.1f}x SDE"
        else:
            offer_summary['price_range'] = "TBD – Subject to financial diligence"
            
        # Deal structure from config
        structure_policy = self.synthesis_config.get('structure_policy', {})
        preferred_mix = structure_policy.get('preferred_mix', {})
        
        structure = {
            'cash_at_close_pct': preferred_mix.get('cash_at_close_pct', 70),
            'seller_note_pct': preferred_mix.get('seller_note_pct', 15),
            'earnout_pct': preferred_mix.get('earnout_pct', 15)
        }
        
        # Generate earnout metrics based on industry
        earnout_metrics = [
            "12-month customer retention ≥ 90%",
            "EBITDA margin maintenance or improvement",
            "Key employee retention through transition"
        ]
        
        structure['earnout_metrics'] = earnout_metrics
        offer_summary['structure'] = structure
        offer_summary['working_capital_target'] = "Normalized working capital at closing"
        
        return offer_summary
    
    def _generate_contingencies(self, industry: str, acquire_scores: Dict[str, Any]) -> List[str]:
        """Generate due diligence contingencies."""
        
        base_contingencies = [
            "Quality of Earnings (QoE) including revenue recognition and working capital analysis",
            "Customer concentration analysis (no single customer >15% of revenue)",
            "Management interviews and key employee retention assessment",
            "Legal review including contracts, litigation, and compliance status"
        ]
        
        # Industry-specific contingencies
        industry_specific = {
            'HVAC services': [
                "Verification of licenses, certifications, and insurance coverage",
                "HVAC equipment condition assessment and replacement CapEx analysis",
                "Seasonal revenue pattern analysis and cash flow modeling"
            ],
            'veterinary clinics': [
                "Veterinary license transfers and regulatory compliance review",
                "Medical equipment valuation and condition assessment", 
                "Professional liability insurance and malpractice history review"
            ],
            'dental practices': [
                "Dental license verification and transfer requirements",
                "Patient records transition and HIPAA compliance assessment",
                "Equipment lease assignments and condition evaluation"
            ],
            'managed IT services': [
                "Technology stack audit and cybersecurity assessment",
                "MSP contract assignment and customer transition planning",
                "Recurring revenue validation and contract term analysis"
            ]
        }
        
        specific_contingencies = industry_specific.get(industry, [])
        
        # Risk-based contingencies
        risk_score = acquire_scores.get('axes', {}).get('risk_compliance', 0.0)
        if risk_score > 0.5:
            base_contingencies.extend([
                "Enhanced regulatory compliance review",
                "Litigation history and contingent liability assessment"
            ])
            
        return base_contingencies + specific_contingencies[:2]
    
    def _generate_key_risks(self, pain_dimensions: Dict[str, float], recommendations: List[str], industry: str) -> List[str]:
        """Generate key risk factors for the acquisition."""
        
        risks = []
        
        # Risk based on pain dimensions
        if pain_dimensions.get('competitive_moats', 0) < 0.4:
            risks.append("Limited competitive differentiation - market position vulnerability")
            
        if pain_dimensions.get('technology_adoption', 0) < 0.3:
            risks.append("Technology modernization requirements - potential integration complexity")
            
        if pain_dimensions.get('scalability_potential', 0) < 0.4:
            risks.append("Limited scalability - organic growth constraints")
        
        # Industry-specific risks
        industry_risks = {
            'HVAC services': [
                "Seasonal revenue volatility and working capital swings",
                "Skilled technician recruitment and retention challenges"
            ],
            'veterinary clinics': [
                "Key person dependency on lead veterinarian",
                "Regulatory changes affecting practice operations"
            ],
            'dental practices': [
                "Patient loyalty tied to individual practitioners", 
                "Insurance reimbursement rate pressures"
            ],
            'managed IT services': [
                "Technology obsolescence and continuous investment needs",
                "Cybersecurity liability and professional indemnity exposure"
            ]
        }
        
        risks.extend(industry_risks.get(industry, [])[:2])
        
        # General PE risks
        risks.extend([
            "Integration execution risk and cultural alignment challenges",
            "Market conditions affecting exit timing and valuation multiples"
        ])
        
        return risks[:5]  # Limit to top 5 risks
    
    def _generate_post_close_plan(self, recommendations: List[str], solutions: List[str]) -> str:
        """Generate 90-day post-closing integration plan."""
        
        # Extract value drivers from recommendations
        value_drivers = self.thesis_preferences.get('primary_value_drivers', [])
        primary_driver = value_drivers[0] if value_drivers else "Operational Excellence"
        
        plan = f"""
**90-Day Integration Plan - {primary_driver} Focus**

**Days 1-30: Foundation & Assessment**
- Complete management team introductions and cultural integration kickoff
- Conduct detailed operational assessment and baseline KPI establishment
- Implement basic reporting systems and performance dashboards
- Begin key employee retention conversations and incentive alignment

**Days 31-60: Process Optimization**
"""
        
        # Add driver-specific initiatives
        if primary_driver == "Consolidation":
            plan += """- Map consolidation opportunities and synergy identification
- Begin vendor rationalization and purchasing power leveraging
- Assess shared services implementation (finance, HR, IT)
- Develop integration timeline for additional acquisitions"""
            
        elif primary_driver == "Digitization":
            plan += """- Technology stack audit and modernization roadmap development
- CRM/ERP system evaluation and implementation planning
- Digital marketing and customer acquisition system setup
- Process automation identification and pilot program launch"""
            
        elif primary_driver == "Geographic Expansion":
            plan += """- Market expansion feasibility study and location analysis
- Sales territory mapping and coverage optimization
- Local market entry strategy development
- Franchise or branch location site selection process"""
            
        else:  # Operational Excellence
            plan += """- Process standardization and best practice implementation
- Quality management system establishment
- Cost structure optimization and margin improvement initiatives
- Customer satisfaction measurement and improvement programs"""
        
        plan += """

**Days 61-90: Value Creation Acceleration**
- Implement quick-win operational improvements identified in assessment
- Launch customer retention and cross-selling initiatives
- Begin management development and succession planning programs
- Establish regular performance reviews and continuous improvement processes

**Success Metrics**: Revenue growth, margin expansion, customer retention, employee satisfaction, and value creation milestone achievement."""
        
        return plan.strip()
    
    def _generate_broker_contact(self, source_url: str) -> Optional[str]:
        """Generate mock broker contact information."""
        
        # Extract broker site from URL
        if 'bizbuysell' in source_url:
            return "Sarah Johnson, Senior Advisor (sarah.j@bizbuysell.com)"
        elif 'bizquest' in source_url:
            return "Michael Chen, Business Broker (m.chen@bizquest.com)"
        elif 'transworld' in source_url:
            return "Jennifer Davis, Transaction Advisor (j.davis@tworld.com)"
        elif 'sunbelt' in source_url:
            return "Robert Martinez, Senior Associate (r.martinez@sunbelt.com)"
        else:
            return "Business Broker (contact via listing platform)"
    
    def _generate_citations(self, zone: Dict[str, Any], discussions: List[str], source_url: str) -> List[str]:
        """Generate supporting citations and references."""
        
        citations = []
        
        # Primary listing source
        citations.append(source_url)
        
        # Zone analysis
        zone_id = zone.get('id', 'unknown')
        citations.append(f"Market opportunity zone analysis: {zone_id}")
        
        # Market intelligence
        if discussions:
            citations.append(f"Industry discussion analysis ({len(discussions)} sources)")
            
        # Framework analysis
        framework_analysis = zone.get('framework_analysis', {})
        if framework_analysis:
            confidence = framework_analysis.get('confidence_level', 0)
            citations.append(f"ACQUIRE framework analysis (confidence: {confidence:.2f})")
        
        # Add mock enrichment sources
        citations.extend([
            "Company website and digital footprint analysis",
            "LinkedIn organizational insights and management assessment",
            "Local market density and competitive landscape mapping"
        ])
        
        return citations[:6]  # Limit to 6 citations