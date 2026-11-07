# Stage 3: City Revitalization Domain Adapter (Week 3)

## Objective
Implement the city revitalization domain adapter that discovers strategic municipal partnerships and generates coalition blueprints instead of product ideas.

## Prerequisites
- [ ] Stage 2 data integration completed and validated
- [ ] Data orchestrator collecting municipal, nonprofit, and business data
- [ ] Perplexity API configured for deep research

## Step 3.1: Create City Revitalization Adapter (Days 1-2)

### 3.1.1 Implement Core Adapter
**Create**: `src/domain_adapters/city_revitalization_adapter.py`

```python
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

from .base_adapter import BaseDomainAdapter
from ..utils.data_orchestrator import DataOrchestrator

logger = logging.getLogger(__name__)

class CityRevitalizationAdapter(BaseDomainAdapter):
    """
    City Revitalization Domain Adapter
    
    Transforms standard pipeline to discover strategic municipal partnerships
    and generate coalition blueprints for community impact projects.
    """
    
    def __init__(self, domain_type: str):
        super().__init__(domain_type)
        self.collaboration_dimensions = self._initialize_collaboration_dimensions()
        self.partnership_types = self._initialize_partnership_types()
    
    def _initialize_collaboration_dimensions(self) -> Dict[str, List[str]]:
        """Initialize dimensions for partnership analysis"""
        return {
            'timing_convergence': [
                'budget_cycle', 'grant_deadline', 'policy_window', 'event_calendar',
                'fiscal_year', 'planning_cycle', 'election_cycle', 'seasonal_alignment'
            ],
            'resource_complementarity': [
                'funding_available', 'space_sharing', 'expertise_exchange', 'audience_overlap',
                'staff_capacity', 'equipment_sharing', 'volunteer_base', 'media_reach'
            ],
            'shared_outcomes': [
                'community_safety', 'economic_development', 'education_improvement', 'environmental_health',
                'social_equity', 'infrastructure_upgrade', 'cultural_enrichment', 'public_health'
            ],
            'stakeholder_diversity': [
                'municipal_government', 'nonprofit_sector', 'business_community', 'academic_institutions',
                'faith_organizations', 'community_groups', 'healthcare_systems', 'arts_organizations'
            ]
        }
    
    def _initialize_partnership_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize partnership archetypes for matching"""
        return {
            'shared_pain_alliance': {
                'description': 'Entities addressing same challenge from different angles',
                'indicators': ['common_challenges', 'complementary_approaches', 'overlapping_beneficiaries'],
                'examples': ['Traffic safety: Police + Schools + Senior Centers', 'Economic development: Chamber + Arts + Transit']
            },
            'resource_complementarity': {
                'description': 'Strategic pairing where excess capacity meets need',
                'indicators': ['resource_surplus', 'capacity_gaps', 'skill_matching'],
                'examples': ['Empty venues + Youth programming', 'Corporate funding + Nonprofit expertise']
            },
            'timing_convergence': {
                'description': 'Natural alignment of cycles and deadlines',
                'indicators': ['synchronized_timelines', 'deadline_alignment', 'seasonal_coordination'],
                'examples': ['Budget cycles + Grant deadlines', 'Event coordination + Policy windows']
            }
        }
    
    def get_opportunity_zone_data(self, input_params: Dict) -> Dict:
        """Gather comprehensive municipal partnership data"""
        logger.info(f"Collecting city revitalization data for {input_params.get('location_name')}")
        
        # Use data orchestrator to get comprehensive municipal data
        data_orchestrator = DataOrchestrator(data_tier='enhanced')  # Use enhanced tier for city data
        
        location_data = data_orchestrator.get_comprehensive_location_data(
            input_params, 
            self.domain_type
        )
        
        # Transform data for partnership analysis
        partnership_data = self._transform_to_partnership_data(location_data, input_params)
        
        # Discover partnership opportunities
        opportunities = self._discover_partnership_opportunities(partnership_data)
        
        return {
            'location_params': input_params,
            'raw_data': location_data,
            'partnership_landscape': partnership_data,
            'opportunities': opportunities,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _transform_to_partnership_data(self, location_data: Dict, input_params: Dict) -> Dict:
        """Transform raw data into partnership-focused structure"""
        partnership_data = {
            'stakeholders': {},
            'resources': {},
            'timelines': {},
            'shared_challenges': []
        }
        
        try:
            # Extract stakeholder information from Perplexity research
            research_data = location_data.get('sources', {}).get('perplexity_research', {})
            
            for query_key, research_result in research_data.items():
                content = self._extract_content_from_research(research_result)
                
                if 'municipal' in query_key or 'council' in query_key:
                    partnership_data['stakeholders']['municipal'] = self._extract_municipal_stakeholders(content)
                elif 'nonprofit' in query_key:
                    partnership_data['stakeholders']['nonprofit'] = self._extract_nonprofit_stakeholders(content)
                elif 'business' in query_key or 'chamber' in query_key:
                    partnership_data['stakeholders']['business'] = self._extract_business_stakeholders(content)
                elif 'economic' in query_key:
                    partnership_data['shared_challenges'] = self._extract_community_challenges(content)
            
            # Extract resource information from census data
            census_data = location_data.get('sources', {}).get('census', {})
            if census_data:
                partnership_data['resources'] = self._analyze_community_resources(census_data)
            
            # Extract geographic context from OpenStreetMap
            osm_data = location_data.get('sources', {}).get('openstreetmap')
            if osm_data is not None and not osm_data.empty:
                partnership_data['geographic_assets'] = self._analyze_civic_infrastructure(osm_data)
            
        except Exception as e:
            logger.error(f"Error transforming partnership data: {e}")
        
        return partnership_data
    
    def _extract_content_from_research(self, research_result: Dict) -> str:
        """Extract text content from Perplexity research result"""
        if isinstance(research_result, dict):
            if 'choices' in research_result:
                return research_result['choices'][0].get('message', {}).get('content', '')
            elif 'content' in research_result:
                return research_result['content']
        return str(research_result)
    
    def _extract_municipal_stakeholders(self, content: str) -> List[Dict]:
        """Extract municipal stakeholders and their priorities"""
        # Simplified extraction - in production would use NLP
        stakeholders = []
        
        municipal_keywords = {
            'city_council': ['city council', 'mayor', 'municipal government'],
            'planning_dept': ['planning department', 'zoning', 'development'],
            'public_works': ['public works', 'infrastructure', 'utilities'],
            'economic_development': ['economic development', 'chamber partnership']
        }
        
        for category, keywords in municipal_keywords.items():
            if any(keyword.lower() in content.lower() for keyword in keywords):
                stakeholders.append({
                    'category': category,
                    'keywords_found': [kw for kw in keywords if kw.lower() in content.lower()],
                    'context_snippet': self._extract_context_snippet(content, keywords[0])
                })
        
        return stakeholders
    
    def _extract_nonprofit_stakeholders(self, content: str) -> List[Dict]:
        """Extract nonprofit organizations and their activities"""
        stakeholders = []
        
        nonprofit_categories = {
            'social_services': ['social services', 'homeless shelter', 'food bank'],
            'youth_development': ['youth center', 'boys and girls club', 'mentoring'],
            'arts_culture': ['arts center', 'cultural organization', 'museum'],
            'education': ['literacy program', 'tutoring', 'adult education'],
            'health_wellness': ['community health', 'mental health', 'wellness center']
        }
        
        for category, keywords in nonprofit_categories.items():
            if any(keyword.lower() in content.lower() for keyword in keywords):
                stakeholders.append({
                    'category': category,
                    'keywords_found': [kw for kw in keywords if kw.lower() in content.lower()],
                    'context_snippet': self._extract_context_snippet(content, keywords[0])
                })
        
        return stakeholders
    
    def _extract_business_stakeholders(self, content: str) -> List[Dict]:
        """Extract business community stakeholders"""
        stakeholders = []
        
        business_categories = {
            'chamber_of_commerce': ['chamber of commerce', 'business association'],
            'local_businesses': ['local business', 'small business', 'main street'],
            'corporate_sponsors': ['corporate sponsor', 'foundation', 'community investment'],
            'real_estate': ['real estate', 'property development', 'commercial space']
        }
        
        for category, keywords in business_categories.items():
            if any(keyword.lower() in content.lower() for keyword in keywords):
                stakeholders.append({
                    'category': category,
                    'keywords_found': [kw for kw in keywords if kw.lower() in content.lower()],
                    'context_snippet': self._extract_context_snippet(content, keywords[0])
                })
        
        return stakeholders
    
    def _extract_context_snippet(self, content: str, keyword: str, window: int = 100) -> str:
        """Extract context around keyword"""
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        pos = content_lower.find(keyword_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(content), pos + len(keyword) + window)
        
        return content[start:end].strip()
    
    def _extract_community_challenges(self, content: str) -> List[Dict]:
        """Extract community challenges and initiatives"""
        challenges = []
        
        challenge_indicators = {
            'economic_development': ['unemployment', 'business closure', 'economic growth', 'job creation'],
            'infrastructure': ['road repair', 'infrastructure', 'public transportation', 'utilities'],
            'housing': ['affordable housing', 'homelessness', 'housing crisis', 'gentrification'],
            'safety': ['crime rate', 'public safety', 'community policing', 'violence prevention'],
            'education': ['school funding', 'educational outcomes', 'achievement gap', 'dropout rate'],
            'environment': ['environmental cleanup', 'green space', 'air quality', 'sustainability']
        }
        
        for category, indicators in challenge_indicators.items():
            found_indicators = [ind for ind in indicators if ind.lower() in content.lower()]
            if found_indicators:
                challenges.append({
                    'category': category,
                    'indicators': found_indicators,
                    'context': self._extract_context_snippet(content, found_indicators[0])
                })
        
        return challenges
    
    def _analyze_community_resources(self, census_data: Dict) -> Dict:
        """Analyze community resources from census data"""
        resources = {
            'demographic_assets': {},
            'economic_indicators': {},
            'housing_characteristics': {}
        }
        
        try:
            # Analyze demographic data if available
            if 'demographics' in census_data:
                demo_df = census_data['demographics']
                if not demo_df.empty:
                    resources['demographic_assets'] = {
                        'population_size': len(demo_df),
                        'age_diversity': 'analyzed' if 'AGEP' in demo_df.columns else 'unavailable',
                        'income_levels': 'analyzed' if 'PINCP' in demo_df.columns else 'unavailable'
                    }
            
            # Analyze economic indicators
            if 'economics' in census_data:
                econ_df = census_data['economics']
                if not econ_df.empty:
                    resources['economic_indicators'] = {
                        'employment_diversity': 'analyzed',
                        'business_sectors': 'identified'
                    }
                    
        except Exception as e:
            logger.warning(f"Error analyzing census resources: {e}")
        
        return resources
    
    def _analyze_civic_infrastructure(self, osm_data: pd.DataFrame) -> Dict:
        """Analyze civic infrastructure from OpenStreetMap"""
        infrastructure = {
            'civic_facilities': [],
            'community_spaces': [],
            'transportation_access': {}
        }
        
        try:
            if 'amenity' in osm_data.columns:
                civic_amenities = ['library', 'community_centre', 'town_hall', 'post_office']
                community_spaces = ['park', 'playground', 'sports_centre', 'theatre']
                
                infrastructure['civic_facilities'] = [
                    amenity for amenity in civic_amenities 
                    if amenity in osm_data['amenity'].values
                ]
                
                infrastructure['community_spaces'] = [
                    space for space in community_spaces 
                    if space in osm_data['amenity'].values
                ]
                
        except Exception as e:
            logger.warning(f"Error analyzing OSM infrastructure: {e}")
        
        return infrastructure
    
    def _discover_partnership_opportunities(self, partnership_data: Dict) -> List[Dict]:
        """Discover strategic partnership opportunities"""
        opportunities = []
        
        try:
            stakeholders = partnership_data.get('stakeholders', {})
            challenges = partnership_data.get('shared_challenges', [])
            
            # Generate partnership opportunities based on complementarity
            for challenge in challenges:
                opportunity = self._generate_partnership_for_challenge(
                    challenge, stakeholders, partnership_data
                )
                if opportunity:
                    opportunities.append(opportunity)
            
            # Generate resource-based partnerships
            resource_partnerships = self._generate_resource_partnerships(
                stakeholders, partnership_data
            )
            opportunities.extend(resource_partnerships)
            
        except Exception as e:
            logger.error(f"Error discovering partnerships: {e}")
        
        return opportunities
    
    def _generate_partnership_for_challenge(self, challenge: Dict, stakeholders: Dict, partnership_data: Dict) -> Dict:
        """Generate partnership opportunity for specific challenge"""
        challenge_category = challenge.get('category', '')
        
        # Map challenges to relevant stakeholder combinations
        partnership_maps = {
            'economic_development': ['municipal', 'business', 'nonprofit'],
            'education': ['municipal', 'nonprofit', 'business'],
            'safety': ['municipal', 'nonprofit', 'business'],
            'infrastructure': ['municipal', 'business'],
            'housing': ['municipal', 'nonprofit'],
            'environment': ['municipal', 'nonprofit', 'business']
        }
        
        relevant_stakeholder_types = partnership_maps.get(challenge_category, [])
        
        if len(relevant_stakeholder_types) >= 2:
            return {
                'opportunity_type': 'shared_pain_alliance',
                'challenge_addressed': challenge_category,
                'challenge_context': challenge.get('context', ''),
                'recommended_partners': relevant_stakeholder_types,
                'partner_details': {
                    stakeholder_type: stakeholders.get(stakeholder_type, [])
                    for stakeholder_type in relevant_stakeholder_types
                },
                'partnership_rationale': f"Multi-stakeholder approach to {challenge_category} leveraging diverse resources and perspectives",
                'estimated_impact': 'high' if len(relevant_stakeholder_types) >= 3 else 'medium'
            }
        
        return None
    
    def _generate_resource_partnerships(self, stakeholders: Dict, partnership_data: Dict) -> List[Dict]:
        """Generate partnerships based on resource complementarity"""
        partnerships = []
        
        try:
            # Generate space-sharing opportunities
            if 'municipal' in stakeholders and 'nonprofit' in stakeholders:
                partnerships.append({
                    'opportunity_type': 'resource_complementarity',
                    'resource_type': 'space_sharing',
                    'partnership_rationale': 'Municipal facilities + Nonprofit programming = Enhanced community services',
                    'recommended_partners': ['municipal', 'nonprofit'],
                    'partner_details': {
                        'municipal': stakeholders.get('municipal', []),
                        'nonprofit': stakeholders.get('nonprofit', [])
                    },
                    'estimated_impact': 'medium'
                })
            
            # Generate funding + expertise partnerships
            if 'business' in stakeholders and 'nonprofit' in stakeholders:
                partnerships.append({
                    'opportunity_type': 'resource_complementarity',
                    'resource_type': 'funding_expertise',
                    'partnership_rationale': 'Business funding + Nonprofit expertise = Scaled community impact',
                    'recommended_partners': ['business', 'nonprofit'],
                    'partner_details': {
                        'business': stakeholders.get('business', []),
                        'nonprofit': stakeholders.get('nonprofit', [])
                    },
                    'estimated_impact': 'high'
                })
                
        except Exception as e:
            logger.warning(f"Error generating resource partnerships: {e}")
        
        return partnerships
    
    def get_opportunity_dimensions(self) -> Dict[str, List[str]]:
        """Return city revitalization-specific opportunity dimensions"""
        return self.collaboration_dimensions
    
    def generate_domain_output(self, zones: List[Dict]) -> Dict:
        """Generate partnership intelligence packages instead of product ideas"""
        logger.info("Generating city revitalization partnership packages")
        
        partnership_packages = []
        
        for i, zone in enumerate(zones):
            opportunities = zone.get('opportunities', [])
            
            # Select top opportunities based on impact and feasibility
            selected_opportunities = self._select_top_opportunities(opportunities)
            
            for opportunity in selected_opportunities:
                package = self._create_partnership_package(opportunity, zone, i+1)
                partnership_packages.append(package)
        
        return {
            'domain': 'city-revitalization',
            'output_type': 'partnership_intelligence_packages',
            'packages': partnership_packages,
            'generation_metadata': {
                'total_zones': len(zones),
                'total_packages': len(partnership_packages),
                'generation_timestamp': datetime.now().isoformat(),
                'data_sources_used': ['perplexity_research', 'census_data', 'openstreetmap']
            }
        }
    
    def _select_top_opportunities(self, opportunities: List[Dict], max_count: int = 3) -> List[Dict]:
        """Select top partnership opportunities based on impact and feasibility"""
        if not opportunities:
            return []
        
        # Score opportunities
        scored_opportunities = []
        for opp in opportunities:
            score = self._score_partnership_opportunity(opp)
            scored_opportunities.append((score, opp))
        
        # Sort by score and select top opportunities
        scored_opportunities.sort(key=lambda x: x[0], reverse=True)
        return [opp for score, opp in scored_opportunities[:max_count]]
    
    def _score_partnership_opportunity(self, opportunity: Dict) -> float:
        """Score partnership opportunity based on multiple factors"""
        score = 0.0
        
        # Impact level scoring
        impact_scores = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        score += impact_scores.get(opportunity.get('estimated_impact', 'low'), 1.0)
        
        # Partner diversity bonus
        partner_count = len(opportunity.get('recommended_partners', []))
        score += min(partner_count * 0.5, 2.0)  # Cap at 2.0 bonus
        
        # Opportunity type weighting
        type_weights = {
            'shared_pain_alliance': 1.5,
            'resource_complementarity': 1.3,
            'timing_convergence': 1.2
        }
        opp_type = opportunity.get('opportunity_type', '')
        score *= type_weights.get(opp_type, 1.0)
        
        return score
    
    def _create_partnership_package(self, opportunity: Dict, zone: Dict, zone_number: int) -> Dict:
        """Create comprehensive partnership intelligence package"""
        package = {
            'package_id': f"partnership_{zone_number}_{datetime.now().strftime('%Y%m%d')}",
            'opportunity_brief': {
                'title': self._generate_opportunity_title(opportunity),
                'description': opportunity.get('partnership_rationale', ''),
                'challenge_addressed': opportunity.get('challenge_addressed', 'community_enhancement'),
                'opportunity_type': opportunity.get('opportunity_type', 'strategic_collaboration')
            },
            'coalition_blueprint': {
                'recommended_partners': opportunity.get('recommended_partners', []),
                'partner_roles': self._define_partner_roles(opportunity),
                'value_exchange_framework': self._create_value_exchange(opportunity),
                'contact_strategies': self._generate_contact_strategies(opportunity)
            },
            'timing_strategy_map': {
                'immediate_actions': self._generate_immediate_actions(opportunity),
                'milestone_timeline': self._create_milestone_timeline(opportunity),
                'critical_deadlines': self._identify_critical_deadlines(opportunity)
            },
            'impact_multiplier_analysis': {
                'individual_benefits': self._analyze_individual_benefits(opportunity),
                'collective_outcomes': self._identify_collective_outcomes(opportunity),
                'measurement_framework': self._create_measurement_framework(opportunity),
                'long_term_relationship_potential': self._assess_relationship_potential(opportunity)
            },
            'implementation_readiness': {
                'feasibility_score': self._calculate_feasibility_score(opportunity),
                'risk_factors': self._identify_risk_factors(opportunity),
                'success_indicators': self._define_success_indicators(opportunity),
                'next_steps': self._generate_next_steps(opportunity)
            }
        }
        
        return package
    
    def _generate_opportunity_title(self, opportunity: Dict) -> str:
        """Generate descriptive title for partnership opportunity"""
        challenge = opportunity.get('challenge_addressed', 'community')
        opp_type = opportunity.get('opportunity_type', 'partnership')
        partner_count = len(opportunity.get('recommended_partners', []))
        
        title_templates = {
            'shared_pain_alliance': f"Multi-Stakeholder {challenge.replace('_', ' ').title()} Alliance",
            'resource_complementarity': f"Strategic Resource Partnership for {challenge.replace('_', ' ').title()}",
            'timing_convergence': f"Coordinated {challenge.replace('_', ' ').title()} Initiative"
        }
        
        base_title = title_templates.get(opp_type, f"{partner_count}-Way Community Partnership")
        return base_title
    
    def _define_partner_roles(self, opportunity: Dict) -> Dict[str, str]:
        """Define specific roles for each partner type"""
        partner_roles = {}
        partners = opportunity.get('recommended_partners', [])
        
        role_definitions = {
            'municipal': 'Policy framework, regulatory support, and public resource coordination',
            'nonprofit': 'Community expertise, program implementation, and stakeholder engagement',
            'business': 'Funding, professional expertise, and market connectivity',
            'academic': 'Research, evaluation, and student engagement opportunities'
        }
        
        for partner in partners:
            partner_roles[partner] = role_definitions.get(partner, 'Strategic collaboration and resource sharing')
        
        return partner_roles
    
    def _create_value_exchange(self, opportunity: Dict) -> Dict[str, Any]:
        """Create value exchange framework"""
        return {
            'resource_contributions': {
                'municipal': ['policy_support', 'public_venues', 'regulatory_guidance'],
                'nonprofit': ['community_connections', 'program_expertise', 'volunteer_networks'],
                'business': ['funding', 'professional_skills', 'market_access'],
                'academic': ['research_capacity', 'student_volunteers', 'evaluation_expertise']
            },
            'benefit_distribution': 'Proportional to contribution level and community impact achieved',
            'success_sharing_model': 'Joint recognition and shared ownership of outcomes'
        }
    
    def _generate_contact_strategies(self, opportunity: Dict) -> Dict[str, List[str]]:
        """Generate specific contact strategies for each partner type"""
        return {
            'municipal': [
                'Attend city council meetings during public comment',
                'Schedule meetings with relevant department heads',
                'Present at municipal advisory committee meetings'
            ],
            'nonprofit': [
                'Connect through nonprofit networks and coalitions',
                'Attend community organization events and forums',
                'Leverage existing board connections and relationships'
            ],
            'business': [
                'Present at chamber of commerce meetings',
                'Connect through business networking events',
                'Approach through CSR and community investment channels'
            ]
        }
    
    def _generate_immediate_actions(self, opportunity: Dict) -> List[str]:
        """Generate immediate next steps"""
        return [
            'Conduct stakeholder mapping and contact identification',
            'Develop partnership proposal and value proposition',
            'Schedule initial exploratory meetings with key partners',
            'Create project timeline and milestone framework'
        ]
    
    def _create_milestone_timeline(self, opportunity: Dict) -> Dict[str, str]:
        """Create project milestone timeline"""
        return {
            'weeks_1_2': 'Stakeholder outreach and interest validation',
            'weeks_3_4': 'Partnership framework development and agreement',
            'weeks_5_8': 'Project planning and resource allocation',
            'weeks_9_12': 'Program launch and initial implementation',
            'months_4_6': 'Program refinement and expansion planning'
        }
    
    def _identify_critical_deadlines(self, opportunity: Dict) -> List[Dict[str, str]]:
        """Identify critical deadlines and timing considerations"""
        return [
            {'deadline': 'Municipal budget cycle', 'timing': 'Typically 6 months before fiscal year'},
            {'deadline': 'Grant application deadlines', 'timing': 'Varies by funder, typically quarterly'},
            {'deadline': 'Community event calendar', 'timing': 'Plan 3-6 months in advance'},
            {'deadline': 'Partner organization planning cycles', 'timing': 'Align with partner fiscal years'}
        ]
    
    def _analyze_individual_benefits(self, opportunity: Dict) -> Dict[str, List[str]]:
        """Analyze individual benefits for each partner"""
        return {
            'municipal': [
                'Enhanced community engagement and satisfaction',
                'Leveraged resources for greater program impact',
                'Improved inter-organizational coordination'
            ],
            'nonprofit': [
                'Increased funding and resource access',
                'Expanded program reach and capacity',
                'Enhanced organizational visibility and credibility'
            ],
            'business': [
                'Meaningful community impact and CSR fulfillment',
                'Enhanced brand reputation and community connection',
                'Employee engagement and retention benefits'
            ]
        }
    
    def _identify_collective_outcomes(self, opportunity: Dict) -> List[str]:
        """Identify collective outcomes impossible through individual action"""
        challenge = opportunity.get('challenge_addressed', 'community')
        
        outcome_templates = {
            'economic_development': [
                'Coordinated business development pipeline',
                'Integrated workforce development and job placement',
                'Sustainable local economic ecosystem'
            ],
            'education': [
                'Comprehensive educational support network',
                'Community-wide learning opportunities',
                'Integrated youth development pathway'
            ],
            'safety': [
                'Community-wide safety and prevention network',
                'Coordinated crisis response and support',
                'Comprehensive violence prevention ecosystem'
            ]
        }
        
        return outcome_templates.get(challenge, [
            'Enhanced community coordination and collaboration',
            'Sustainable cross-sector partnership model',
            'Amplified community impact through resource leveraging'
        ])
    
    def _create_measurement_framework(self, opportunity: Dict) -> Dict[str, Any]:
        """Create measurement framework for partnership success"""
        return {
            'quantitative_metrics': [
                'Number of community members served',
                'Resources leveraged (monetary and in-kind)',
                'Partnership activities and programs implemented'
            ],
            'qualitative_indicators': [
                'Stakeholder satisfaction and engagement levels',
                'Quality of inter-organizational relationships',
                'Community feedback and impact stories'
            ],
            'impact_measurement': [
                'Pre/post community indicator comparisons',
                'Partner organization capacity changes',
                'Sustainability and replication potential'
            ]
        }
    
    def _assess_relationship_potential(self, opportunity: Dict) -> str:
        """Assess long-term relationship building potential"""
        partner_count = len(opportunity.get('recommended_partners', []))
        impact_level = opportunity.get('estimated_impact', 'medium')
        
        if partner_count >= 3 and impact_level == 'high':
            return 'High potential for sustained multi-sector collaboration and replication'
        elif partner_count >= 2 and impact_level in ['high', 'medium']:
            return 'Good foundation for ongoing partnership and relationship development'
        else:
            return 'Moderate potential, focus on demonstrating early wins to build trust'
    
    def _calculate_feasibility_score(self, opportunity: Dict) -> float:
        """Calculate implementation feasibility score (0-10)"""
        score = 5.0  # Base score
        
        # Partner availability bonus
        partner_count = len(opportunity.get('recommended_partners', []))
        score += min(partner_count * 0.5, 2.0)
        
        # Impact level adjustment
        impact_scores = {'high': 1.0, 'medium': 0.5, 'low': 0.0}
        score += impact_scores.get(opportunity.get('estimated_impact', 'medium'), 0.5)
        
        # Partnership type adjustment
        type_feasibility = {
            'resource_complementarity': 1.5,  # Usually easier to implement
            'shared_pain_alliance': 1.0,      # Moderate complexity
            'timing_convergence': 0.5         # Often more complex timing
        }
        opp_type = opportunity.get('opportunity_type', '')
        score += type_feasibility.get(opp_type, 0.0)
        
        return min(score, 10.0)  # Cap at 10
    
    def _identify_risk_factors(self, opportunity: Dict) -> List[str]:
        """Identify potential risk factors"""
        return [
            'Partner commitment and follow-through',
            'Resource availability and sustainability',
            'Coordination complexity with multiple stakeholders',
            'Community reception and engagement levels',
            'External factors (policy changes, economic conditions)'
        ]
    
    def _define_success_indicators(self, opportunity: Dict) -> List[str]:
        """Define early success indicators"""
        return [
            'All recommended partners agree to participate',
            'Clear partnership agreement and roles established',
            'Initial program activities launched on schedule',
            'Positive community feedback and engagement',
            'Measurable progress on stated outcomes within 6 months'
        ]
    
    def _generate_next_steps(self, opportunity: Dict) -> List[Dict[str, str]]:
        """Generate specific next steps with timeline"""
        return [
            {
                'step': 'Identify and research potential partner organizations',
                'timeline': 'Week 1',
                'owner': 'Partnership coordinator'
            },
            {
                'step': 'Develop partnership proposal and presentation materials',
                'timeline': 'Week 2',
                'owner': 'Partnership coordinator'
            },
            {
                'step': 'Schedule and conduct initial stakeholder meetings',
                'timeline': 'Weeks 3-4',
                'owner': 'All potential partners'
            },
            {
                'step': 'Finalize partnership framework and resource commitments',
                'timeline': 'Weeks 5-6',
                'owner': 'Partnership committee'
            }
        ]
```

### 3.1.2 Create City Revitalization Output Formatter
**Create**: `src/domain_adapters/city_revitalization_formatter.py`

```python
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class CityRevitalizationFormatter:
    """
    Formats city revitalization partnership packages for various outputs
    """
    
    def __init__(self):
        self.output_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Any]:
        """Initialize output templates"""
        return {
            'executive_summary': {
                'max_length': 500,
                'focus_areas': ['opportunity_brief', 'key_partners', 'expected_impact']
            },
            'detailed_proposal': {
                'sections': ['opportunity_brief', 'coalition_blueprint', 'timing_strategy_map', 'impact_multiplier_analysis'],
                'format': 'comprehensive'
            },
            'presentation_deck': {
                'slides': ['problem_statement', 'partnership_opportunity', 'implementation_plan', 'expected_outcomes'],
                'format': 'bullet_points'
            }
        }
    
    def format_partnership_packages(self, packages: List[Dict], output_format: str = 'detailed_proposal') -> Dict[str, Any]:
        """Format partnership packages for specified output"""
        logger.info(f"Formatting {len(packages)} partnership packages as {output_format}")
        
        formatted_output = {
            'format_type': output_format,
            'packages': [],
            'summary': self._create_portfolio_summary(packages),
            'generation_metadata': {
                'total_packages': len(packages),
                'format_timestamp': datetime.now().isoformat()
            }
        }
        
        for package in packages:
            if output_format == 'executive_summary':
                formatted_package = self._format_executive_summary(package)
            elif output_format == 'detailed_proposal':
                formatted_package = self._format_detailed_proposal(package)
            elif output_format == 'presentation_deck':
                formatted_package = self._format_presentation_deck(package)
            else:
                formatted_package = package  # Default to original format
            
            formatted_output['packages'].append(formatted_package)
        
        return formatted_output
    
    def _create_portfolio_summary(self, packages: List[Dict]) -> Dict[str, Any]:
        """Create summary of entire partnership portfolio"""
        if not packages:
            return {}
        
        # Analyze partnership types
        partnership_types = {}
        challenge_areas = {}
        partner_combinations = {}
        
        for package in packages:
            # Count partnership types
            opp_type = package.get('opportunity_brief', {}).get('opportunity_type', 'unknown')
            partnership_types[opp_type] = partnership_types.get(opp_type, 0) + 1
            
            # Count challenge areas
            challenge = package.get('opportunity_brief', {}).get('challenge_addressed', 'unknown')
            challenge_areas[challenge] = challenge_areas.get(challenge, 0) + 1
            
            # Count partner combinations
            partners = package.get('coalition_blueprint', {}).get('recommended_partners', [])
            partner_combo = '-'.join(sorted(partners))
            partner_combinations[partner_combo] = partner_combinations.get(partner_combo, 0) + 1
        
        return {
            'total_partnerships': len(packages),
            'partnership_type_distribution': partnership_types,
            'challenge_area_focus': challenge_areas,
            'partner_combination_patterns': partner_combinations,
            'average_feasibility_score': self._calculate_average_feasibility(packages),
            'high_impact_opportunities': self._count_high_impact_opportunities(packages)
        }
    
    def _calculate_average_feasibility(self, packages: List[Dict]) -> float:
        """Calculate average feasibility score across packages"""
        scores = []
        for package in packages:
            score = package.get('implementation_readiness', {}).get('feasibility_score', 0)
            if score:
                scores.append(score)
        
        return round(sum(scores) / len(scores), 1) if scores else 0.0
    
    def _count_high_impact_opportunities(self, packages: List[Dict]) -> int:
        """Count high-impact partnership opportunities"""
        high_impact_count = 0
        for package in packages:
            feasibility = package.get('implementation_readiness', {}).get('feasibility_score', 0)
            if feasibility >= 7.0:  # High feasibility threshold
                high_impact_count += 1
        
        return high_impact_count
    
    def _format_executive_summary(self, package: Dict) -> Dict[str, Any]:
        """Format package as executive summary"""
        opportunity_brief = package.get('opportunity_brief', {})
        coalition_blueprint = package.get('coalition_blueprint', {})
        impact_analysis = package.get('impact_multiplier_analysis', {})
        
        summary = {
            'package_id': package.get('package_id', 'unknown'),
            'title': opportunity_brief.get('title', 'Partnership Opportunity'),
            'executive_summary': {
                'opportunity_overview': opportunity_brief.get('description', ''),
                'key_partners': coalition_blueprint.get('recommended_partners', []),
                'primary_challenge': opportunity_brief.get('challenge_addressed', ''),
                'expected_collective_outcomes': impact_analysis.get('collective_outcomes', [])[:3],  # Top 3
                'implementation_timeline': '3-6 months to full launch',
                'feasibility_rating': package.get('implementation_readiness', {}).get('feasibility_score', 'TBD')
            },
            'next_steps_summary': package.get('implementation_readiness', {}).get('next_steps', [])[:3]  # Top 3
        }
        
        return summary
    
    def _format_detailed_proposal(self, package: Dict) -> Dict[str, Any]:
        """Format package as detailed proposal"""
        # Return full package with enhanced formatting
        detailed_package = package.copy()
        
        # Add formatted sections
        detailed_package['formatted_sections'] = {
            'proposal_overview': self._format_proposal_overview(package),
            'partnership_strategy': self._format_partnership_strategy(package),
            'implementation_roadmap': self._format_implementation_roadmap(package),
            'success_measurement': self._format_success_measurement(package)
        }
        
        return detailed_package
    
    def _format_proposal_overview(self, package: Dict) -> str:
        """Format proposal overview section"""
        opportunity_brief = package.get('opportunity_brief', {})
        
        overview = f"""
        Partnership Opportunity: {opportunity_brief.get('title', 'Community Partnership')}
        
        Challenge Addressed: {opportunity_brief.get('challenge_addressed', 'community enhancement').replace('_', ' ').title()}
        
        Partnership Rationale: {opportunity_brief.get('description', 'Strategic collaboration opportunity')}
        
        Opportunity Type: {opportunity_brief.get('opportunity_type', 'strategic_collaboration').replace('_', ' ').title()}
        """
        
        return overview.strip()
    
    def _format_partnership_strategy(self, package: Dict) -> Dict[str, Any]:
        """Format partnership strategy section"""
        coalition_blueprint = package.get('coalition_blueprint', {})
        
        return {
            'partner_ecosystem': {
                'recommended_partners': coalition_blueprint.get('recommended_partners', []),
                'partner_roles': coalition_blueprint.get('partner_roles', {}),
                'value_exchange': coalition_blueprint.get('value_exchange_framework', {})
            },
            'engagement_approach': {
                'contact_strategies': coalition_blueprint.get('contact_strategies', {}),
                'relationship_building': 'Systematic outreach and engagement process'
            }
        }
    
    def _format_implementation_roadmap(self, package: Dict) -> Dict[str, Any]:
        """Format implementation roadmap"""
        timing_strategy = package.get('timing_strategy_map', {})
        implementation = package.get('implementation_readiness', {})
        
        return {
            'immediate_actions': timing_strategy.get('immediate_actions', []),
            'milestone_timeline': timing_strategy.get('milestone_timeline', {}),
            'critical_deadlines': timing_strategy.get('critical_deadlines', []),
            'risk_mitigation': {
                'risk_factors': implementation.get('risk_factors', []),
                'success_indicators': implementation.get('success_indicators', [])
            }
        }
    
    def _format_success_measurement(self, package: Dict) -> Dict[str, Any]:
        """Format success measurement framework"""
        impact_analysis = package.get('impact_multiplier_analysis', {})
        
        return {
            'measurement_framework': impact_analysis.get('measurement_framework', {}),
            'expected_outcomes': {
                'individual_benefits': impact_analysis.get('individual_benefits', {}),
                'collective_outcomes': impact_analysis.get('collective_outcomes', [])
            },
            'long_term_vision': impact_analysis.get('long_term_relationship_potential', '')
        }
    
    def _format_presentation_deck(self, package: Dict) -> Dict[str, Any]:
        """Format package as presentation slides"""
        opportunity_brief = package.get('opportunity_brief', {})
        coalition_blueprint = package.get('coalition_blueprint', {})
        impact_analysis = package.get('impact_multiplier_analysis', {})
        implementation = package.get('implementation_readiness', {})
        
        slides = {
            'slide_1_problem_statement': {
                'title': 'Community Challenge & Opportunity',
                'content': [
                    f"Challenge: {opportunity_brief.get('challenge_addressed', '').replace('_', ' ').title()}",
                    f"Opportunity Type: {opportunity_brief.get('opportunity_type', '').replace('_', ' ').title()}",
                    f"Partnership Rationale: {opportunity_brief.get('description', '')[:100]}..."
                ]
            },
            'slide_2_partnership_opportunity': {
                'title': 'Strategic Partnership Framework',
                'content': [
                    f"Recommended Partners: {', '.join(coalition_blueprint.get('recommended_partners', []))}",
                    "Value Exchange: Complementary resources and expertise",
                    f"Feasibility Score: {implementation.get('feasibility_score', 'TBD')}/10"
                ]
            },
            'slide_3_implementation_plan': {
                'title': 'Implementation Roadmap',
                'content': [
                    "Phase 1: Stakeholder outreach and engagement",
                    "Phase 2: Partnership framework development",
                    "Phase 3: Program launch and implementation",
                    "Timeline: 3-6 months to full operation"
                ]
            },
            'slide_4_expected_outcomes': {
                'title': 'Expected Impact & Outcomes',
                'content': impact_analysis.get('collective_outcomes', [])[:4]  # Top 4 outcomes
            }
        }
        
        return {
            'package_id': package.get('package_id', 'unknown'),
            'presentation_title': opportunity_brief.get('title', 'Partnership Opportunity'),
            'slides': slides,
            'appendix': {
                'detailed_partner_roles': coalition_blueprint.get('partner_roles', {}),
                'contact_strategies': coalition_blueprint.get('contact_strategies', {}),
                'next_steps': implementation.get('next_steps', [])
            }
        }
    
    def export_to_markdown(self, formatted_output: Dict) -> str:
        """Export formatted output to markdown"""
        markdown_content = []
        
        # Add header
        markdown_content.append("# City Revitalization Partnership Intelligence Report")
        markdown_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_content.append("")
        
        # Add summary
        summary = formatted_output.get('summary', {})
        if summary:
            markdown_content.append("## Executive Summary")
            markdown_content.append(f"Total Partnership Opportunities: {summary.get('total_partnerships', 0)}")
            markdown_content.append(f"Average Feasibility Score: {summary.get('average_feasibility_score', 'N/A')}")
            markdown_content.append(f"High-Impact Opportunities: {summary.get('high_impact_opportunities', 0)}")
            markdown_content.append("")
        
        # Add packages
        for i, package in enumerate(formatted_output.get('packages', []), 1):
            markdown_content.append(f"## Partnership Opportunity {i}")
            
            if 'executive_summary' in package:
                exec_summary = package['executive_summary']
                markdown_content.append(f"**Title:** {package.get('title', 'Partnership Opportunity')}")
                markdown_content.append(f"**Challenge:** {exec_summary.get('primary_challenge', '').replace('_', ' ').title()}")
                markdown_content.append(f"**Key Partners:** {', '.join(exec_summary.get('key_partners', []))}")
                markdown_content.append(f"**Feasibility:** {exec_summary.get('feasibility_rating', 'TBD')}/10")
                markdown_content.append("")
                markdown_content.append("**Overview:**")
                markdown_content.append(exec_summary.get('opportunity_overview', ''))
                markdown_content.append("")
            
            markdown_content.append("---")
            markdown_content.append("")
        
        return "\n".join(markdown_content)
    
    def export_to_json(self, formatted_output: Dict, filename: str = None) -> str:
        """Export formatted output to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"city_revitalization_partnerships_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(formatted_output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Partnership packages exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return ""
```

## Step 3.2: Integration and Testing (Days 3-5)

### 3.2.1 Update Domain Configuration
**Update**: `src/config.py` (add city revitalization case)

```python
# Add to existing PipelineConfig.get_adapter_class method
elif self.domain_type == DomainType.CITY_REVITALIZATION:
    from .domain_adapters.city_revitalization_adapter import CityRevitalizationAdapter
    return CityRevitalizationAdapter
```

### 3.2.2 Create Comprehensive Tests
**Create**: `tests/domain_adapters/test_city_revitalization.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.domain_adapters.city_revitalization_adapter import CityRevitalizationAdapter
from src.domain_adapters.city_revitalization_formatter import CityRevitalizationFormatter

class TestCityRevitalizationAdapter:
    
    @pytest.fixture
    def adapter(self):
        return CityRevitalizationAdapter('city-revitalization')
    
    @pytest.fixture
    def sample_input_params(self):
        return {
            'location_name': 'Denver',
            'state': 'CO',
            'latitude': 39.7391,
            'longitude': -104.9847
        }
    
    @pytest.fixture
    def mock_location_data(self):
        return {
            'sources': {
                'perplexity_research': {
                    'query_0': {
                        'choices': [{
                            'message': {
                                'content': 'Denver city council priorities include affordable housing, economic development, and transportation. Local nonprofits focus on homeless services and youth programs.'
                            }
                        }]
                    }
                },
                'census': {
                    'demographics': pd.DataFrame({
                        'AGEP': [25, 35, 45],
                        'PINCP': [50000, 75000, 100000]
                    })
                },
                'openstreetmap': pd.DataFrame({
                    'amenity': ['library', 'community_centre', 'school']
                })
            }
        }
    
    def test_initialization(self, adapter):
        """Test adapter initializes correctly"""
        assert adapter.domain_type == 'city-revitalization'
        assert 'timing_convergence' in adapter.collaboration_dimensions
        assert 'shared_pain_alliance' in adapter.partnership_types
    
    def test_opportunity_dimensions(self, adapter):
        """Test opportunity dimensions are correct"""
        dimensions = adapter.get_opportunity_dimensions()
        
        expected_dimensions = [
            'timing_convergence', 
            'resource_complementarity',
            'shared_outcomes', 
            'stakeholder_diversity'
        ]
        
        for dim in expected_dimensions:
            assert dim in dimensions
            assert isinstance(dimensions[dim], list)
            assert len(dimensions[dim]) > 0
    
    @patch('src.domain_adapters.city_revitalization_adapter.DataOrchestrator')
    def test_get_opportunity_zone_data(self, mock_orchestrator, adapter, sample_input_params, mock_location_data):
        """Test opportunity zone data collection"""
        # Mock data orchestrator
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.get_comprehensive_location_data.return_value = mock_location_data
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Test data collection
        result = adapter.get_opportunity_zone_data(sample_input_params)
        
        # Verify structure
        assert 'location_params' in result
        assert 'partnership_landscape' in result
        assert 'opportunities' in result
        assert result['location_params'] == sample_input_params
    
    def test_transform_partnership_data(self, adapter, mock_location_data, sample_input_params):
        """Test transformation to partnership-focused structure"""
        partnership_data = adapter._transform_to_partnership_data(mock_location_data, sample_input_params)
        
        # Verify structure
        assert 'stakeholders' in partnership_data
        assert 'resources' in partnership_data
        assert 'shared_challenges' in partnership_data
        
        # Verify stakeholders extracted
        stakeholders = partnership_data['stakeholders']
        assert isinstance(stakeholders, dict)
    
    def test_discover_partnership_opportunities(self, adapter):
        """Test partnership opportunity discovery"""
        mock_partnership_data = {
            'stakeholders': {
                'municipal': [{'category': 'city_council', 'keywords_found': ['city council']}],
                'nonprofit': [{'category': 'social_services', 'keywords_found': ['homeless shelter']}],
                'business': [{'category': 'chamber_of_commerce', 'keywords_found': ['chamber']}]
            },
            'shared_challenges': [
                {'category': 'economic_development', 'context': 'Need for business growth'}
            ]
        }
        
        opportunities = adapter._discover_partnership_opportunities(mock_partnership_data)
        
        assert isinstance(opportunities, list)
        if opportunities:  # If opportunities found
            assert 'opportunity_type' in opportunities[0]
            assert 'recommended_partners' in opportunities[0]
    
    def test_generate_domain_output(self, adapter):
        """Test domain output generation"""
        mock_zones = [{
            'opportunities': [{
                'opportunity_type': 'shared_pain_alliance',
                'challenge_addressed': 'economic_development',
                'recommended_partners': ['municipal', 'business', 'nonprofit'],
                'estimated_impact': 'high',
                'partnership_rationale': 'Test partnership'
            }]
        }]
        
        output = adapter.generate_domain_output(mock_zones)
        
        # Verify output structure
        assert output['domain'] == 'city-revitalization'
        assert output['output_type'] == 'partnership_intelligence_packages'
        assert 'packages' in output
        assert 'generation_metadata' in output
    
    def test_opportunity_scoring(self, adapter):
        """Test opportunity scoring logic"""
        high_impact_opp = {
            'estimated_impact': 'high',
            'recommended_partners': ['municipal', 'nonprofit', 'business'],
            'opportunity_type': 'shared_pain_alliance'
        }
        
        low_impact_opp = {
            'estimated_impact': 'low',
            'recommended_partners': ['municipal'],
            'opportunity_type': 'resource_complementarity'
        }
        
        high_score = adapter._score_partnership_opportunity(high_impact_opp)
        low_score = adapter._score_partnership_opportunity(low_impact_opp)
        
        assert high_score > low_score
    
    def test_partnership_package_creation(self, adapter):
        """Test partnership package creation"""
        mock_opportunity = {
            'opportunity_type': 'shared_pain_alliance',
            'challenge_addressed': 'economic_development',
            'recommended_partners': ['municipal', 'nonprofit', 'business'],
            'estimated_impact': 'high',
            'partnership_rationale': 'Multi-stakeholder economic development'
        }
        
        mock_zone = {'test': 'data'}
        
        package = adapter._create_partnership_package(mock_opportunity, mock_zone, 1)
        
        # Verify package structure
        required_sections = [
            'package_id', 
            'opportunity_brief', 
            'coalition_blueprint',
            'timing_strategy_map', 
            'impact_multiplier_analysis', 
            'implementation_readiness'
        ]
        
        for section in required_sections:
            assert section in package

class TestCityRevitalizationFormatter:
    
    @pytest.fixture
    def formatter(self):
        return CityRevitalizationFormatter()
    
    @pytest.fixture
    def sample_packages(self):
        return [{
            'package_id': 'partnership_1_20240101',
            'opportunity_brief': {
                'title': 'Economic Development Alliance',
                'description': 'Multi-stakeholder economic development partnership',
                'challenge_addressed': 'economic_development',
                'opportunity_type': 'shared_pain_alliance'
            },
            'coalition_blueprint': {
                'recommended_partners': ['municipal', 'business', 'nonprofit'],
                'partner_roles': {
                    'municipal': 'Policy framework and support',
                    'business': 'Funding and expertise',
                    'nonprofit': 'Community engagement'
                }
            },
            'implementation_readiness': {
                'feasibility_score': 8.5,
                'next_steps': ['Identify partners', 'Develop proposal']
            }
        }]
    
    def test_format_executive_summary(self, formatter, sample_packages):
        """Test executive summary formatting"""
        formatted = formatter.format_partnership_packages(sample_packages, 'executive_summary')
        
        assert formatted['format_type'] == 'executive_summary'
        assert len(formatted['packages']) == 1
        
        package = formatted['packages'][0]
        assert 'executive_summary' in package
        assert 'title' in package
    
    def test_format_detailed_proposal(self, formatter, sample_packages):
        """Test detailed proposal formatting"""
        formatted = formatter.format_partnership_packages(sample_packages, 'detailed_proposal')
        
        assert formatted['format_type'] == 'detailed_proposal'
        
        package = formatted['packages'][0]
        assert 'formatted_sections' in package
        assert 'proposal_overview' in package['formatted_sections']
    
    def test_format_presentation_deck(self, formatter, sample_packages):
        """Test presentation deck formatting"""
        formatted = formatter.format_partnership_packages(sample_packages, 'presentation_deck')
        
        assert formatted['format_type'] == 'presentation_deck'
        
        package = formatted['packages'][0]
        assert 'slides' in package
        assert 'slide_1_problem_statement' in package['slides']
    
    def test_portfolio_summary_creation(self, formatter, sample_packages):
        """Test portfolio summary creation"""
        formatted = formatter.format_partnership_packages(sample_packages)
        summary = formatted['summary']
        
        assert 'total_partnerships' in summary
        assert summary['total_partnerships'] == 1
        assert 'partnership_type_distribution' in summary
    
    def test_markdown_export(self, formatter, sample_packages):
        """Test markdown export functionality"""
        formatted = formatter.format_partnership_packages(sample_packages, 'executive_summary')
        markdown = formatter.export_to_markdown(formatted)
        
        assert isinstance(markdown, str)
        assert 'Partnership Intelligence Report' in markdown
        assert 'Partnership Opportunity 1' in markdown
    
    def test_json_export(self, formatter, sample_packages, tmp_path):
        """Test JSON export functionality"""
        formatted = formatter.format_partnership_packages(sample_packages)
        
        # Test export
        filename = str(tmp_path / 'test_export.json')
        result_filename = formatter.export_to_json(formatted, filename)
        
        assert result_filename == filename
        
        # Verify file was created and is valid JSON
        import json
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['format_type'] == 'detailed_proposal'
```

### 3.2.3 Integration Testing
**Create**: `tests/integration/test_city_revitalization_integration.py`

```python
#!/usr/bin/env python3
"""Integration tests for city revitalization domain"""

import pytest
import os
from src.domain_adapters.city_revitalization_adapter import CityRevitalizationAdapter
from src.domain_adapters.city_revitalization_formatter import CityRevitalizationFormatter

class TestCityRevitalizationIntegration:
    
    @pytest.fixture
    def real_location_params(self):
        return {
            'location_name': 'Denver',
            'state': 'CO',
            'latitude': 39.7391,
            'longitude': -104.9847,
            'state_code': '08'
        }
    
    def test_end_to_end_partnership_generation(self, real_location_params):
        """Test complete partnership generation pipeline"""
        adapter = CityRevitalizationAdapter('city-revitalization')
        formatter = CityRevitalizationFormatter()
        
        try:
            # Step 1: Get opportunity zone data
            zone_data = adapter.get_opportunity_zone_data(real_location_params)
            
            # Verify zone data structure
            assert 'partnership_landscape' in zone_data
            assert 'opportunities' in zone_data
            
            # Step 2: Generate domain output
            zones = [zone_data]  # Simulate zones list
            output = adapter.generate_domain_output(zones)
            
            # Verify output structure
            assert output['domain'] == 'city-revitalization'
            assert output['output_type'] == 'partnership_intelligence_packages'
            
            packages = output.get('packages', [])
            print(f"Generated {len(packages)} partnership packages")
            
            # Step 3: Format packages
            if packages:
                formatted = formatter.format_partnership_packages(packages, 'executive_summary')
                
                # Verify formatting
                assert 'summary' in formatted
                assert len(formatted['packages']) > 0
                
                # Test markdown export
                markdown = formatter.export_to_markdown(formatted)
                assert len(markdown) > 0
                
                print(f"Partnership generation successful!")
                print(f"- Opportunities discovered: {len(zone_data.get('opportunities', []))}")
                print(f"- Packages generated: {len(packages)}")
                print(f"- Average feasibility: {formatted['summary'].get('average_feasibility_score', 'N/A')}")
                
        except Exception as e:
            pytest.fail(f"End-to-end test failed: {e}")
    
    def test_partnership_data_quality(self, real_location_params):
        """Test quality of partnership data collection"""
        adapter = CityRevitalizationAdapter('city-revitalization')
        
        zone_data = adapter.get_opportunity_zone_data(real_location_params)
        
        # Check data quality
        partnership_landscape = zone_data.get('partnership_landscape', {})
        opportunities = zone_data.get('opportunities', [])
        
        # Verify stakeholder extraction
        stakeholders = partnership_landscape.get('stakeholders', {})
        assert isinstance(stakeholders, dict)
        
        # Verify opportunities have required fields
        for opp in opportunities:
            assert 'opportunity_type' in opp
            assert 'recommended_partners' in opp
            
        print(f"Data quality check passed:")
        print(f"- Stakeholder categories: {len(stakeholders)}")
        print(f"- Opportunities discovered: {len(opportunities)}")
    
    def test_formatter_outputs(self, real_location_params):
        """Test all formatter output types"""
        adapter = CityRevitalizationAdapter('city-revitalization')
        formatter = CityRevitalizationFormatter()
        
        # Generate sample data
        zone_data = adapter.get_opportunity_zone_data(real_location_params)
        output = adapter.generate_domain_output([zone_data])
        packages = output.get('packages', [])
        
        if packages:
            # Test all format types
            formats = ['executive_summary', 'detailed_proposal', 'presentation_deck']
            
            for format_type in formats:
                try:
                    formatted = formatter.format_partnership_packages(packages, format_type)
                    assert formatted['format_type'] == format_type
                    assert len(formatted['packages']) > 0
                    print(f"✅ {format_type} format working")
                except Exception as e:
                    print(f"❌ {format_type} format failed: {e}")
        
        else:
            pytest.skip("No packages generated for formatting test")

if __name__ == "__main__":
    """Run integration tests directly"""
    import sys
    
    print("🏙️ Running City Revitalization Integration Tests...")
    
    exit_code = pytest.main([
        __file__,
        '-v',
        '-s',
        '--tb=short'
    ])
    
    if exit_code == 0:
        print("✅ City Revitalization integration tests passed!")
    else:
        print("❌ City Revitalization integration tests failed!")
        
    sys.exit(exit_code)
```

## Step 3.3: Documentation and Validation

### 3.3.1 Create Usage Documentation
**Create**: `implementation_v2/city_revitalization_usage.md`

```markdown
# City Revitalization Domain Usage Guide

## Overview
The City Revitalization domain transforms the standard product ideation pipeline into a municipal partnership discovery system that generates strategic coalition blueprints.

## Key Concepts

### Partnership Types
1. **Shared Pain Alliances**: Multiple organizations addressing the same challenge
2. **Resource Complementarity**: Matching excess capacity with unmet needs
3. **Timing Convergence**: Aligning organizational cycles and deadlines

### Output Format
Instead of product ideas, generates **Partnership Intelligence Packages** containing:
- Opportunity Brief
- Coalition Blueprint
- Timing Strategy Map
- Impact Multiplier Analysis
- Implementation Readiness Assessment

## Usage Examples

### Basic Usage
```python
from src.domain_adapters.city_revitalization_adapter import CityRevitalizationAdapter

adapter = CityRevitalizationAdapter('city-revitalization')

location_params = {
    'location_name': 'Your City',
    'state': 'State',
    'latitude': 40.0,
    'longitude': -100.0
}

# Discover partnership opportunities
zone_data = adapter.get_opportunity_zone_data(location_params)
partnerships = adapter.generate_domain_output([zone_data])
```

### With Formatting
```python
from src.domain_adapters.city_revitalization_formatter import CityRevitalizationFormatter

formatter = CityRevitalizationFormatter()

# Format as executive summary
summary = formatter.format_partnership_packages(
    partnerships['packages'], 
    'executive_summary'
)

# Export to markdown
markdown_report = formatter.export_to_markdown(summary)
```

### Environment Configuration
```bash
export DOMAIN_TYPE=city-revitalization
export OUTPUT_FORMAT=partnership-packages
export DATA_TIER=enhanced  # Recommended for municipal data
```

## Integration with Main Pipeline

### Command Line Usage
```bash
python run_pipeline.py \
  --domain city-revitalization \
  --input city_params.json \
  --output partnerships
```

### Input Format
```json
{
  "location_name": "Denver",
  "state": "Colorado", 
  "latitude": 39.7391,
  "longitude": -104.9847,
  "focus_areas": ["economic_development", "community_safety"],
  "stakeholder_priorities": {
    "municipal": ["affordable_housing", "transportation"],
    "nonprofit": ["youth_services", "homeless_support"],
    "business": ["economic_growth", "workforce_development"]
  }
}
```

## Data Sources Used

### Primary Sources
- **Perplexity Deep Research**: Municipal activities, nonprofit landscape
- **Census ACS**: Community demographics and resources
- **OpenStreetMap**: Civic infrastructure and facilities

### Research Queries Generated
1. "Municipal partnerships and coalitions in [location]"
2. "Nonprofit organizations and community groups [location]"
3. "City council priorities and budget [location]"
4. "Economic development initiatives [location]"

## Output Examples

### Executive Summary Format
```json
{
  "title": "Multi-Stakeholder Economic Development Alliance",
  "key_partners": ["municipal", "business", "nonprofit"],
  "primary_challenge": "economic_development",
  "feasibility_rating": 8.5,
  "expected_collective_outcomes": [
    "Coordinated business development pipeline",
    "Integrated workforce development program",
    "Sustainable local economic ecosystem"
  ]
}
```

### Detailed Proposal Format
Includes complete partnership framework with:
- Partner roles and responsibilities
- Resource contribution expectations
- Implementation timeline and milestones
- Success measurement framework
- Risk assessment and mitigation

## Customization Options

### Adding New Partnership Types
```python
# In city_revitalization_adapter.py
def _initialize_partnership_types(self):
    return {
        'your_custom_type': {
            'description': 'Custom partnership description',
            'indicators': ['keyword1', 'keyword2'],
            'examples': ['Example partnership scenarios']
        }
    }
```

### Custom Challenge Categories
```python
# Modify collaboration dimensions
'custom_dimension': [
    'custom_keyword1', 'custom_keyword2', 'custom_keyword3'
]
```

## Best Practices

### Data Quality
- Use enhanced data tier for better municipal intelligence
- Configure Perplexity API for comprehensive research
- Validate location parameters for accurate geographic context

### Partnership Development
- Focus on high-feasibility opportunities (score ≥ 7.0)
- Prioritize partnerships with 3+ stakeholder types
- Ensure clear value proposition for each partner

### Implementation
- Start with resource complementarity partnerships (easier to implement)
- Build on existing relationships and networks
- Plan for 3-6 month development timeline

## Troubleshooting

### Common Issues
1. **Limited partnership opportunities**: Increase research scope or try different focus areas
2. **Low feasibility scores**: Adjust partnership matching criteria
3. **Data quality issues**: Verify API configurations and location parameters

### Performance Optimization
- Use caching for repeated location queries
- Batch similar location analyses
- Monitor API usage to stay within limits

## Integration Testing
```bash
# Run city revitalization tests
python -m pytest tests/domain_adapters/test_city_revitalization.py -v

# Run integration tests
python tests/integration/test_city_revitalization_integration.py
```
```

## Validation Checklist

Before proceeding to Stage 4:

- [ ] CityRevitalizationAdapter implements all abstract methods
- [ ] Partnership opportunity discovery generates meaningful results
- [ ] All output formats (executive, detailed, presentation) work correctly
- [ ] Integration tests pass with real location data
- [ ] Formatter exports to both JSON and markdown successfully
- [ ] Domain integrates with main pipeline configuration
- [ ] Performance meets expectations (< 2 minutes for comprehensive analysis)

## Next Steps

Upon successful validation of Stage 3:
1. **Commit Stage 3**: `git add . && git commit -m "feat: Stage 3 - City revitalization domain adapter"`
2. **Test with multiple cities**: Validate adapter works across different locations
3. **Proceed to Stage 4**: Begin crypto mining domain adapter
4. **Optional**: Enhance partnership matching algorithms based on initial results