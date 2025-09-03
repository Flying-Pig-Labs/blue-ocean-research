#!/usr/bin/env python3
"""
City Revitalization UNIFY Framework Demo

Demonstrates the city revitalization flavor with the UNIFY framework
for generating uncommon alliance-based urban improvement initiatives.
"""

from flavors.config_schema import FlavorRegistry
from flavors.framework_adapter import UnifyAdapter
from flavors.revitalization_synthesizer import RevitalizationSynthesizer

def demo_city_revitalization():
    """Demo the city revitalization flavor with UNIFY framework."""
    print("🏙️  City Revitalization UNIFY Framework Demo")
    print("=" * 60)
    
    # Load the city revitalization flavor
    registry = FlavorRegistry(flavors_dir="flavors")
    city_flavor = registry.get_flavor("city_revitalization")
    
    print(f"✅ Loaded flavor: {city_flavor.name}")
    print(f"   Description: {city_flavor.description}")
    print(f"   Framework: {city_flavor.framework.framework_type.value.upper()}")
    
    # Initialize UNIFY framework adapter
    adapter = UnifyAdapter(city_flavor.framework.params)
    print(f"\n📊 UNIFY Framework Dimensions:")
    for dim in adapter.get_dimensions():
        print(f"   • {dim.replace('_', ' ').title()}")
    
    # Create mock opportunity zones for demonstration
    demo_zones = [
        {
            'id': 'downtown_food_desert',
            'name': 'Downtown Food Access Crisis',
            'pain_dimensions': {
                'community_disconnect': 0.8,
                'economic_decline': 0.7,
                'infrastructure_gaps': 0.5,
                'governance_barriers': 0.3,
                'resource_scarcity': 0.6
            },
            'solution_requirements': [
                'Cross-sector partnerships for food access',
                'Shared commercial kitchen facilities',
                'Community-driven food distribution networks',
                'Multi-stakeholder collaboration platforms'
            ],
            'jtbds': [
                'Access fresh affordable food in downtown area',
                'Support local food entrepreneurs and vendors',
                'Create community gathering spaces around food'
            ],
            'discussions': [
                'Sports arena kitchens sit unused 300+ days per year while downtown is a food desert',
                'Community groups want more partnership between businesses and nonprofits',
                'Local co-op struggling with storage and distribution logistics',
                'Arena management facing pressure to demonstrate community benefit'
            ],
            'framework_analysis': {
                'overall_score': 0.0,  # Will be calculated
                'scores': {},
                'confidence_level': 0.0
            }
        },
        {
            'id': 'vacant_arts_district',
            'name': 'Arts District Revitalization',
            'pain_dimensions': {
                'community_disconnect': 0.6,
                'economic_decline': 0.9,
                'infrastructure_gaps': 0.7,
                'governance_barriers': 0.4,
                'resource_scarcity': 0.8
            },
            'solution_requirements': [
                'Innovative financing for creative spaces',
                'Tech-enabled community engagement platforms',
                'Cross-industry mentorship programs',
                'Shared workspace and equipment access'
            ],
            'jtbds': [
                'Affordable creative workspace for artists',
                'Community engagement through technology',
                'Economic opportunities in creative industries'
            ],
            'discussions': [
                'Tech companies want authentic community partnership opportunities',
                'Artists need affordable workspace but lack startup capital',
                'Faith communities have underutilized buildings and strong volunteer networks',
                'City looking for innovative economic development approaches'
            ],
            'framework_analysis': {
                'overall_score': 0.0,  # Will be calculated
                'scores': {},
                'confidence_level': 0.0
            }
        }
    ]
    
    # Analyze zones with UNIFY framework
    print(f"\n🔍 Analyzing {len(demo_zones)} opportunity zones...")
    for zone in demo_zones:
        analysis = adapter.analyze_zone(zone)
        zone['framework_analysis'] = {
            'overall_score': analysis.overall_score,
            'scores': analysis.scores,
            'confidence_level': analysis.confidence_level
        }
        
        print(f"\n   Zone: {zone['name']}")
        print(f"   UNIFY Score: {analysis.overall_score:.2f}")
        for dim, score in analysis.scores.items():
            print(f"     • {dim.replace('_', ' ').title()}: {score:.2f}")
    
    # Synthesize revitalization initiatives
    print(f"\n🤝 Generating revitalization initiatives...")
    synthesizer = RevitalizationSynthesizer()
    initiatives = synthesizer.synthesize_initiatives(demo_zones, target_count=2)
    
    # Display results
    for i, initiative in enumerate(initiatives, 1):
        print(f"\n{'=' * 60}")
        print(f"🏆 Initiative #{i}: {initiative.title}")
        print(f"{'=' * 60}")
        
        print(f"🎯 Zone Focus: {initiative.zone_focus}")
        print(f"🤝 Uncommon Alliance: {' + '.join(initiative.uncommon_alliance)}")
        print(f"📊 UNIFY Score: {initiative.unify_scores.get('composite', 0):.2f}")
        
        print(f"\n💡 Alliance Rationale:")
        print(f"{initiative.rationale[:200]}...")
        
        print(f"\n📋 Key Stakeholders:")
        for stakeholder in initiative.stakeholder_map[:3]:
            print(f"   • {stakeholder}")
        
        print(f"\n📈 Impact Metrics:")
        for metric in initiative.impact_metrics[:3]:
            print(f"   • {metric}")
        
        print(f"\n⚠️  Resilience Notes:")
        print(f"{initiative.resilience_notes[:200]}...")
        
        print(f"\n🔗 GitHub Issue Preview:")
        github_issue = initiative.to_github_issue()
        print(f"   Title: {github_issue['title']}")
        print(f"   Labels: {', '.join(github_issue['labels'])}")
        print(f"   Type: {github_issue['frontmatter']['type']}")
    
    print(f"\n{'=' * 60}")
    print("✅ City Revitalization UNIFY Framework Demo Complete!")
    print(f"Generated {len(initiatives)} uncommon alliance initiatives")
    print("Ready for GitHub repository creation and issue tracking")

if __name__ == "__main__":
    demo_city_revitalization()