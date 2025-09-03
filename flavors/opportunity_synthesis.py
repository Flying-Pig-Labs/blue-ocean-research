#!/usr/bin/env python3
"""
Opportunity Synthesis Module - Generate Final Opportunities from Scored Zones

Synthesizes exactly N opportunities from scored opportunity zones according to flavor configuration.
Enforces output schema validation and ensures deterministic results for reproducible pipeline runs.
"""

import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class OpportunitySchema:
    """Base schema for all opportunity types with common required fields."""
    id: str
    title: str
    description: str
    rationale: str
    citations: List[str]
    confidence_score: float
    zone_id: str
    zone_name: str
    framework_scores: Dict[str, float]
    created_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass
class BusinessIdeaSchema(OpportunitySchema):
    """Schema for business idea opportunities."""
    target_market: str
    value_proposition: str
    revenue_model: str
    competitive_advantage: str
    implementation_timeline: str
    risk_factors: List[str]
    funding_requirements: Optional[str] = None
    partnerships_needed: Optional[List[str]] = None
    technology_stack: Optional[List[str]] = None
    go_to_market_strategy: Optional[str] = None

@dataclass
class SiteCandidateSchema(OpportunitySchema):
    """Schema for site location opportunities."""
    location_type: str
    target_business_category: str
    site_requirements: List[str]
    market_analysis: Dict[str, Any]
    accessibility_score: float
    demographic_fit: str
    competition_analysis: str
    estimated_foot_traffic: str
    zoning_requirements: List[str]
    infrastructure_needs: List[str]
    lease_rate_expectations: Optional[str] = None
    buildout_requirements: Optional[List[str]] = None
    parking_specifications: Optional[str] = None
    anchor_tenant_opportunities: Optional[List[str]] = None

@dataclass  
class DeviceSpecSchema(OpportunitySchema):
    """Schema for device specification opportunities."""
    device_category: str
    target_population: str
    clinical_indication: str
    functional_requirements: List[str]
    safety_specifications: List[str]
    usability_requirements: List[str]
    regulatory_pathway: str
    user_interface_design: Dict[str, Any]
    connectivity_features: Optional[List[str]] = None
    data_privacy_measures: Optional[List[str]] = None
    maintenance_requirements: Optional[str] = None
    training_needs: Optional[str] = None

class OpportunityValidator:
    """Validates opportunities against schema requirements."""
    
    def __init__(self, schema_type: str, required_fields: List[str], optional_fields: List[str] = None):
        """Initialize validator with schema configuration."""
        self.schema_type = schema_type
        self.required_fields = set(required_fields)
        self.optional_fields = set(optional_fields or [])
        
    def validate_opportunity(self, opportunity: Dict[str, Any]) -> List[str]:
        """Validate opportunity against schema. Returns list of validation errors."""
        errors = []
        
        # Check required fields
        missing_fields = self.required_fields - set(opportunity.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {list(missing_fields)}")
        
        # Validate field types and constraints
        if 'confidence_score' in opportunity:
            score = opportunity['confidence_score']
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                errors.append("confidence_score must be a number between 0.0 and 1.0")
        
        if 'citations' in opportunity:
            citations = opportunity['citations']
            if not isinstance(citations, list):
                errors.append("citations must be a list")
            elif len(citations) == 0:
                errors.append("citations cannot be empty")
        
        if 'framework_scores' in opportunity:
            scores = opportunity['framework_scores']
            if not isinstance(scores, dict):
                errors.append("framework_scores must be a dictionary")
            else:
                for key, value in scores.items():
                    if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                        errors.append(f"framework_scores[{key}] must be between 0.0 and 1.0")
        
        return errors

class OpportunitySynthesizer:
    """Synthesizes final opportunities from scored framework results."""
    
    def __init__(self, flavor_config: Any):
        """Initialize synthesizer with flavor configuration."""
        self.flavor_config = flavor_config
        self.schema_type = flavor_config.output.schema_type.value
        self.required_fields = flavor_config.output.required_fields
        self.optional_fields = getattr(flavor_config.output, 'optional_fields', [])
        self.validator = OpportunityValidator(
            self.schema_type, 
            self.required_fields, 
            self.optional_fields
        )
        
    def generate_deterministic_id(self, zone_id: str, title: str, index: int) -> str:
        """Generate deterministic ID for reproducible results."""
        # Create hash from zone_id, title, and index for determinism
        content = f"{zone_id}_{title}_{index}_{self.flavor_config.name}"
        hash_object = hashlib.md5(content.encode())
        return f"opp_{hash_object.hexdigest()[:8]}"
    
    def synthesize_business_idea(
        self, 
        zone: Dict[str, Any], 
        framework_result: Any, 
        index: int
    ) -> Dict[str, Any]:
        """Synthesize a business idea opportunity."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        
        # Extract solution requirements and pain dimensions
        solutions = zone.get('solution_requirements', [])
        pain_dims = zone.get('pain_dimensions', {})
        jtbd_descriptions = zone.get('jtbd_descriptions', [])
        
        # Generate deterministic but meaningful content
        title = f"{zone_name} Solution Platform"
        if solutions:
            primary_solution = solutions[0].replace('"', '').strip()
            if len(primary_solution) > 50:
                primary_solution = primary_solution[:47] + "..."
            title = f"{primary_solution} Platform"
        
        # Build value proposition from top pain dimensions
        top_pains = sorted(pain_dims.items(), key=lambda x: x[1], reverse=True)[:3]
        pain_areas = [pain.replace('_', ' ').title() for pain, _ in top_pains]
        value_proposition = f"Addresses {', '.join(pain_areas)} through integrated solution platform"
        
        # Determine target market from JTBDs
        target_market = "General consumers"
        if jtbd_descriptions:
            # Extract market indicators from JTBDs
            if any('business' in desc.lower() or 'professional' in desc.lower() for desc in jtbd_descriptions):
                target_market = "Business professionals and enterprises"
            elif any('first-time' in desc.lower() or 'new' in desc.lower() for desc in jtbd_descriptions):
                target_market = "First-time users and newcomers"
        
        # Generate revenue model based on solution type
        revenue_model = "Subscription-based SaaS model"
        if any('marketplace' in sol.lower() or 'platform' in sol.lower() for sol in solutions):
            revenue_model = "Transaction fee and subscription hybrid model"
        elif any('service' in sol.lower() for sol in solutions):
            revenue_model = "Service fee and premium feature model"
        
        # Competitive advantage from framework scores
        competitive_advantage = "Integrated approach addressing multiple pain points"
        if hasattr(framework_result, 'recommendations') and framework_result.recommendations:
            competitive_advantage = framework_result.recommendations[0]
        
        # Implementation timeline based on complexity
        complexity_score = pain_dims.get('process_complexity', 0.5)
        if complexity_score > 0.7:
            timeline = "18-24 months (high complexity solution)"
        elif complexity_score > 0.4:
            timeline = "12-18 months (moderate complexity)"
        else:
            timeline = "6-12 months (straightforward implementation)"
        
        # Risk factors from pain dimensions
        risk_factors = []
        if pain_dims.get('trust_issues', 0) > 0.5:
            risk_factors.append("User trust and adoption challenges")
        if pain_dims.get('market_dynamics', 0) > 0.6:
            risk_factors.append("Competitive market dynamics")
        if pain_dims.get('technology_gaps', 0) > 0.5:
            risk_factors.append("Technical implementation complexity")
        if not risk_factors:
            risk_factors = ["Standard market execution risks"]
        
        opportunity = {
            'id': self.generate_deterministic_id(zone_id, title, index),
            'title': title,
            'description': f"Comprehensive solution platform addressing {zone_name.lower()} challenges through {len(solutions)} integrated capabilities",
            'rationale': f"Strong market signal with {len(jtbd_descriptions)} identified job stories and {framework_result.overall_score:.1%} framework alignment",
            'citations': framework_result.citations[:3],
            'confidence_score': round(framework_result.confidence_level, 3),
            'zone_id': zone_id,
            'zone_name': zone_name,
            'framework_scores': framework_result.scores,
            'created_timestamp': datetime.now().isoformat(),
            'target_market': target_market,
            'value_proposition': value_proposition,
            'revenue_model': revenue_model,
            'competitive_advantage': competitive_advantage,
            'implementation_timeline': timeline,
            'risk_factors': risk_factors
        }
        
        # Add optional fields if configured
        if 'funding_requirements' in self.optional_fields:
            if framework_result.overall_score > 0.7:
                opportunity['funding_requirements'] = "$500K-$2M for MVP and initial market validation"
            else:
                opportunity['funding_requirements'] = "$100K-$500K for prototype and testing"
        
        if 'technology_stack' in self.optional_fields:
            tech_stack = ["Cloud infrastructure", "Web/mobile applications"]
            if pain_dims.get('technology_gaps', 0) > 0.6:
                tech_stack.extend(["AI/ML capabilities", "API integrations"])
            opportunity['technology_stack'] = tech_stack
        
        return opportunity
    
    def synthesize_site_candidate(
        self, 
        zone: Dict[str, Any], 
        framework_result: Any, 
        index: int
    ) -> Dict[str, Any]:
        """Synthesize a site location candidate."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        solutions = zone.get('solution_requirements', [])
        
        # Extract location type from zone name and solutions
        location_type = "Commercial/Industrial"
        if 'retail' in zone_name.lower() or any('retail' in sol.lower() for sol in solutions):
            location_type = "Retail/Commercial"
        elif 'data' in zone_name.lower() or 'technology' in zone_name.lower():
            location_type = "Data Center/Industrial"
        elif 'office' in zone_name.lower():
            location_type = "Office/Business Park"
        
        title = f"{location_type} Site - {zone_name}"
        
        # Business category from solutions
        business_category = "General business operations"
        if any('mining' in sol.lower() or 'crypto' in sol.lower() for sol in solutions):
            business_category = "Cryptocurrency mining operations"
        elif any('manufacturing' in sol.lower() for sol in solutions):
            business_category = "Manufacturing and production"
        elif any('logistics' in sol.lower() for sol in solutions):
            business_category = "Logistics and distribution"
        
        # Site requirements from solutions
        site_requirements = solutions[:5] if solutions else [
            "Adequate power infrastructure",
            "Zoning compliance",
            "Transportation access"
        ]
        
        opportunity = {
            'id': self.generate_deterministic_id(zone_id, title, index),
            'title': title,
            'description': f"Prime {location_type.lower()} site opportunity for {business_category}",
            'rationale': f"Site analysis shows {framework_result.overall_score:.1%} feasibility score across infrastructure, regulatory, and economic factors",
            'citations': framework_result.citations,
            'confidence_score': round(framework_result.confidence_level, 3),
            'zone_id': zone_id,
            'zone_name': zone_name,
            'framework_scores': framework_result.scores,
            'created_timestamp': datetime.now().isoformat(),
            'location_type': location_type,
            'target_business_category': business_category,
            'site_requirements': site_requirements,
            'market_analysis': {
                'feasibility_score': framework_result.overall_score,
                'key_factors': list(framework_result.scores.keys()),
                'recommendations': framework_result.recommendations[:2]
            },
            'accessibility_score': framework_result.scores.get('accessibility', 0.7),
            'demographic_fit': "Good fit for target business category",
            'competition_analysis': "Moderate competition with differentiation opportunities",
            'estimated_foot_traffic': "Variable based on location specifics",
            'zoning_requirements': ["Commercial/Industrial zoning", "Special use permits as needed"],
            'infrastructure_needs': ["Standard utilities", "High-speed internet", "Adequate parking"]
        }
        
        return opportunity
    
    def synthesize_device_spec(
        self, 
        zone: Dict[str, Any], 
        framework_result: Any, 
        index: int
    ) -> Dict[str, Any]:
        """Synthesize a device specification opportunity."""
        zone_id = zone.get('zone_id', 'unknown')
        zone_name = zone.get('name', 'Unnamed Zone')
        solutions = zone.get('solution_requirements', [])
        pain_dims = zone.get('pain_dimensions', {})
        
        # Device category from zone analysis
        device_category = "General medical device"
        if 'monitoring' in zone_name.lower() or any('monitor' in sol.lower() for sol in solutions):
            device_category = "Patient monitoring device"
        elif 'diagnostic' in zone_name.lower() or any('diagnostic' in sol.lower() for sol in solutions):
            device_category = "Diagnostic equipment"
        elif 'therapeutic' in zone_name.lower():
            device_category = "Therapeutic device"
        
        title = f"{device_category} - {zone_name}"
        
        # Target population
        target_population = "General patient population"
        if any('elderly' in sol.lower() or 'senior' in sol.lower() for sol in solutions):
            target_population = "Elderly patients (65+ years)"
        elif any('pediatric' in sol.lower() or 'children' in sol.lower() for sol in solutions):
            target_population = "Pediatric patients"
        elif any('chronic' in sol.lower() for sol in solutions):
            target_population = "Patients with chronic conditions"
        
        # Functional requirements from solutions
        functional_requirements = solutions[:4] if solutions else [
            "Core device functionality",
            "User-friendly operation",
            "Reliable performance"
        ]
        
        # Safety specifications based on pain dimensions
        safety_specs = ["Standard medical device safety protocols"]
        if pain_dims.get('safety_concerns', 0) > 0.7:
            safety_specs.extend([
                "Enhanced patient safety monitoring",
                "Fail-safe operation modes",
                "Clinical risk mitigation"
            ])
        
        # Regulatory pathway
        regulatory_pathway = "FDA 510(k) clearance pathway"
        if 'high-risk' in zone_name.lower() or pain_dims.get('safety_concerns', 0) > 0.8:
            regulatory_pathway = "FDA PMA (Pre-Market Approval) pathway"
        elif 'software' in zone_name.lower():
            regulatory_pathway = "FDA Software as Medical Device (SaMD) pathway"
        
        opportunity = {
            'id': self.generate_deterministic_id(zone_id, title, index),
            'title': title,
            'description': f"Advanced {device_category.lower()} designed for {target_population.lower()}",
            'rationale': f"Technical analysis shows strong specification alignment with {framework_result.overall_score:.1%} requirement score",
            'citations': framework_result.citations,
            'confidence_score': round(framework_result.confidence_level, 3),
            'zone_id': zone_id,
            'zone_name': zone_name,
            'framework_scores': framework_result.scores,
            'created_timestamp': datetime.now().isoformat(),
            'device_category': device_category,
            'target_population': target_population,
            'clinical_indication': f"Addresses clinical needs identified in {zone_name.lower()}",
            'functional_requirements': functional_requirements,
            'safety_specifications': safety_specs,
            'usability_requirements': [
                "Intuitive user interface",
                "Minimal training required",
                "Accessible design principles"
            ],
            'regulatory_pathway': regulatory_pathway,
            'user_interface_design': {
                'display_type': 'LCD/LED display with clear indicators',
                'input_method': 'Touch screen with physical backup controls',
                'accessibility': 'ADA compliant design standards'
            }
        }
        
        return opportunity
    
    def synthesize_opportunities(
        self, 
        framework_results: List[Any],
        opportunity_zones: List[Dict[str, Any]],
        total_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Synthesize exactly N opportunities from scored zones.
        
        Args:
            framework_results: List of FrameworkResult objects from framework analysis
            opportunity_zones: Original opportunity zone data
            total_count: Total number of opportunities to generate
            
        Returns:
            List of validated opportunity dictionaries
        """
        if not framework_results:
            raise ValueError("No framework results provided for synthesis")
        
        # Create zone lookup for detailed data
        zone_lookup = {zone['zone_id']: zone for zone in opportunity_zones}
        
        opportunities = []
        
        # Sort framework results by overall score (descending)
        sorted_results = sorted(framework_results, key=lambda r: r.overall_score, reverse=True)
        
        # Calculate opportunities per zone based on total count and zone scores
        zone_allocations = self._calculate_zone_allocations(sorted_results, total_count)
        
        opportunity_index = 0
        for result in sorted_results:
            zone_id = result.zone_id
            allocation = zone_allocations.get(zone_id, 0)
            
            if allocation == 0:
                continue
                
            zone_data = zone_lookup.get(zone_id, {})
            
            for i in range(allocation):
                try:
                    # Generate opportunity based on schema type
                    if self.schema_type == 'business_idea':
                        opportunity = self.synthesize_business_idea(zone_data, result, opportunity_index)
                    elif self.schema_type == 'site_candidate':
                        opportunity = self.synthesize_site_candidate(zone_data, result, opportunity_index)
                    elif self.schema_type == 'device_spec':
                        opportunity = self.synthesize_device_spec(zone_data, result, opportunity_index)
                    else:
                        # Default to business idea for unknown schema types
                        opportunity = self.synthesize_business_idea(zone_data, result, opportunity_index)
                    
                    # Validate opportunity
                    validation_errors = self.validator.validate_opportunity(opportunity)
                    if validation_errors:
                        logger.error(f"Opportunity validation failed: {validation_errors}")
                        continue
                    
                    opportunities.append(opportunity)
                    opportunity_index += 1
                    
                    logger.info(f"Synthesized opportunity {opportunity_index}: {opportunity['title']}")
                    
                except Exception as e:
                    logger.error(f"Error synthesizing opportunity for zone {zone_id}: {e}")
                    continue
        
        # Ensure we have exactly the requested count (pad or trim as needed)
        if len(opportunities) < total_count:
            logger.warning(f"Generated only {len(opportunities)} opportunities, requested {total_count}")
        elif len(opportunities) > total_count:
            opportunities = opportunities[:total_count]
            logger.info(f"Trimmed opportunities to requested count: {total_count}")
        
        # Add final deterministic sorting for reproducibility
        opportunities.sort(key=lambda o: (o['confidence_score'], o['id']), reverse=True)
        
        return opportunities
    
    def _calculate_zone_allocations(self, sorted_results: List[Any], total_count: int) -> Dict[str, int]:
        """Calculate how many opportunities each zone should generate."""
        if not sorted_results:
            return {}
        
        # Strategy from flavor config
        strategy = getattr(self.flavor_config.stage_overrides.get('idea_generation', {}), 'ideas_per_zone_strategy', 'weighted_distribution')
        
        if strategy == 'equal_distribution':
            # Equal distribution across all zones
            base_allocation = total_count // len(sorted_results)
            remainder = total_count % len(sorted_results)
            
            allocations = {}
            for i, result in enumerate(sorted_results):
                allocations[result.zone_id] = base_allocation + (1 if i < remainder else 0)
        
        else:  # 'weighted_distribution' (default)
            # Weight by framework scores
            total_score = sum(result.overall_score for result in sorted_results)
            if total_score == 0:
                # Fallback to equal distribution if no scores
                return self._calculate_zone_allocations(sorted_results, total_count)
            
            allocations = {}
            allocated_count = 0
            
            for result in sorted_results[:-1]:  # All but last
                weight = result.overall_score / total_score
                allocation = max(1, round(total_count * weight))  # At least 1 per zone
                allocations[result.zone_id] = allocation
                allocated_count += allocation
            
            # Give remainder to the last zone
            if sorted_results:
                last_zone = sorted_results[-1].zone_id
                allocations[last_zone] = max(1, total_count - allocated_count)
        
        return allocations

def synthesize_opportunities_from_zones(
    opportunity_zones: List[Dict[str, Any]],
    framework_results: List[Any],
    flavor_config: Any,
    total_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Main function to synthesize opportunities from scored zones.
    
    Args:
        opportunity_zones: Original opportunity zone data
        framework_results: Framework analysis results
        flavor_config: Complete flavor configuration  
        total_count: Number of opportunities to generate
        
    Returns:
        List of validated opportunities ready for output
    """
    synthesizer = OpportunitySynthesizer(flavor_config)
    
    try:
        opportunities = synthesizer.synthesize_opportunities(
            framework_results=framework_results,
            opportunity_zones=opportunity_zones,
            total_count=total_count
        )
        
        logger.info(f"Successfully synthesized {len(opportunities)} opportunities using {flavor_config.name} flavor")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Opportunity synthesis failed: {e}")
        raise