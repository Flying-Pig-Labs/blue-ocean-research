#!/usr/bin/env python3
"""
Private Equity Acquisitions ACQUIRE Framework Demo

Demonstrates the PE acquisitions flavor with the ACQUIRE framework
for generating preliminary Letters of Intent (LOIs) from acquisition targets.
"""

from flavors.config_schema import FlavorRegistry
from flavors.framework_adapter import AcquireAdapter
from flavors.loi_synthesizer import LOISynthesizer

def demo_pe_acquisitions():
    """Demo the PE acquisitions flavor with ACQUIRE framework."""
    print("💰 Private Equity Acquisitions ACQUIRE Framework Demo")
    print("=" * 70)
    
    # Load the PE acquisitions flavor
    registry = FlavorRegistry(flavors_dir="flavors")
    pe_flavor = registry.get_flavor("private_equity_acquisitions")
    
    print(f"✅ Loaded flavor: {pe_flavor.name}")
    print(f"   Description: {pe_flavor.description}")
    print(f"   Framework: {pe_flavor.framework.framework_type.value.upper()}")
    
    # Initialize ACQUIRE framework adapter
    adapter = AcquireAdapter(pe_flavor.framework.params)
    print(f"\n📊 ACQUIRE Framework Dimensions:")
    dimension_labels = {
        'addressable_fragmentation': 'Addressable Fragmentation',
        'cashflow_quality': 'Cashflow Quality',
        'quality_of_operations': 'Quality of Operations',
        'upside_levers': 'Upside Levers',
        'integration_readiness': 'Integration Readiness',
        'risk_compliance': 'Risk & Compliance',
        'exit_pathways': 'Exit Pathways'
    }
    
    for dim in adapter.get_dimensions():
        label = dimension_labels.get(dim, dim.replace('_', ' ').title())
        print(f"   • {label}")
    
    # Show thesis preferences
    print(f"\n🎯 Investment Thesis:")
    thesis = pe_flavor.thesis_preferences
    print(f"   Industries: {', '.join(thesis.get('target_industries', []))}")
    print(f"   Geography: {', '.join(thesis.get('geography', {}).get('include_states', []))}")
    print(f"   Size Range: ${thesis.get('size_bounds', {}).get('revenue_min', 0)/1000000:.1f}M - ${thesis.get('size_bounds', {}).get('revenue_max', 0)/1000000:.0f}M revenue")
    
    # Create mock acquisition opportunity zones
    demo_zones = [
        {
            'id': 'hvac_consolidation_se',
            'name': 'HVAC Services Consolidation - Southeast',
            'pain_dimensions': {
                'market_fragmentation': 0.85,
                'consolidation_opportunity': 0.80,
                'scalability_potential': 0.65,
                'competitive_moats': 0.45,
                'technology_adoption': 0.35
            },
            'solution_requirements': [
                'Market consolidation through strategic acquisitions',
                'Technology platform for service optimization',
                'Geographic expansion across target states',
                'Operational excellence through standardization'
            ],
            'jtbds': [
                'Consolidate fragmented HVAC service market through roll-up strategy',
                'Implement technology-driven service delivery and customer management',
                'Build scalable platform for maintenance contract management'
            ],
            'discussions': [
                'HVAC market highly fragmented with many aging family-owned businesses seeking succession',
                'Strong recurring revenue from maintenance contracts providing stable cash flows',
                'Technology adoption lagging - huge opportunity for digitization and operational improvement',
                'Geographic clustering allows for route optimization and shared resources'
            ],
            'framework_analysis': {
                'overall_score': 0.0,  # Will be calculated
                'scores': {},
                'confidence_level': 0.0
            }
        },
        {
            'id': 'veterinary_clinic_expansion',
            'name': 'Veterinary Clinic Platform Expansion',
            'pain_dimensions': {
                'market_fragmentation': 0.70,
                'consolidation_opportunity': 0.75,
                'scalability_potential': 0.80,
                'competitive_moats': 0.60,
                'technology_adoption': 0.40
            },
            'solution_requirements': [
                'Veterinary practice management platform',
                'Standardized clinical protocols and training',
                'Technology integration for patient management',
                'Multi-site operational support systems'
            ],
            'jtbds': [
                'Create veterinary practice management platform for independent clinics',
                'Standardize clinical operations while maintaining local autonomy',
                'Implement technology solutions for patient care and business management'
            ],
            'discussions': [
                'Many veterinarians are excellent clinicians but struggle with business management',
                'Practice management software adoption uneven across independent clinics',
                'Strong customer loyalty and recurring revenue from pet wellness programs',
                'Shortage of veterinarians creating consolidation opportunities'
            ],
            'framework_analysis': {
                'overall_score': 0.0,  # Will be calculated
                'scores': {},
                'confidence_level': 0.0
            }
        }
    ]
    
    # Analyze zones with ACQUIRE framework
    print(f"\n🔍 Analyzing {len(demo_zones)} acquisition opportunity zones...")
    for zone in demo_zones:
        analysis = adapter.analyze_zone(zone)
        zone['framework_analysis'] = {
            'overall_score': analysis.overall_score,
            'scores': analysis.scores,
            'confidence_level': analysis.confidence_level
        }
        
        print(f"\n   Zone: {zone['name']}")
        print(f"   ACQUIRE Score: {analysis.overall_score:.2f}")
        for dim, score in analysis.scores.items():
            dim_label = dimension_labels.get(dim, dim.replace('_', ' ').title())
            print(f"     • {dim_label}: {score:.2f}")
    
    # Synthesize preliminary LOIs
    print(f"\n📋 Generating preliminary Letters of Intent...")
    synthesizer = LOISynthesizer(pe_flavor.__dict__)
    lois = synthesizer.synthesize_lois(demo_zones, target_count=2)
    
    # Display results
    for i, loi in enumerate(lois, 1):
        print(f"\n{'=' * 70}")
        print(f"📄 LOI #{i}: {loi.title}")
        print(f"{'=' * 70}")
        
        print(f"🏢 Target: {loi.target_company}")
        print(f"🏭 Industry: {loi.industry}")
        print(f"📍 Location: {loi.location}")
        print(f"📊 ACQUIRE Score: {loi.acquire_scores.get('rank_score', 0):.2f}")
        
        # Quick facts
        print(f"\n📈 Quick Facts:")
        for fact in loi.quick_facts[:3]:
            print(f"   • {fact}")
        
        # Deal structure
        if loi.offer_summary.get('price_range'):
            print(f"\n💰 Preliminary Offer: {loi.offer_summary['price_range']}")
        
        structure = loi.offer_summary.get('structure', {})
        if structure:
            print(f"📊 Deal Structure:")
            print(f"   • Cash at Close: {structure.get('cash_at_close_pct', 0):.0f}%")
            print(f"   • Seller Note: {structure.get('seller_note_pct', 0):.0f}%")
            print(f"   • Earnout: {structure.get('earnout_pct', 0):.0f}%")
        
        # Key risks
        print(f"\n⚠️  Key Risks:")
        for risk in loi.key_risks[:3]:
            print(f"   • {risk}")
        
        # ACQUIRE breakdown
        print(f"\n🎯 ACQUIRE Analysis Highlights:")
        axes = loi.acquire_scores.get('axes', {})
        top_scores = sorted(axes.items(), key=lambda x: x[1], reverse=True)[:3]
        for dim, score in top_scores:
            dim_label = dimension_labels.get(dim, dim.replace('_', ' ').title())
            print(f"   • {dim_label}: {score:.2f} (Strong)")
        
        # Timeline
        print(f"\n📅 Transaction Timeline:")
        print(f"   • Exclusivity: {loi.exclusivity_days} days")
        print(f"   • Due Diligence: {loi.diligence_period_days} days")
        
        # GitHub preview
        print(f"\n🔗 GitHub Issue Preview:")
        github_issue = loi.to_github_issue()
        print(f"   Title: {github_issue['title']}")
        print(f"   Labels: {', '.join(github_issue['labels'])}")
        print(f"   Type: {github_issue['frontmatter']['type']}")
        
        # Investment thesis fit snippet
        thesis_fit = loi.thesis_fit[:200].replace('\n', ' ').replace('**', '')
        print(f"   Thesis Fit: {thesis_fit}...")
    
    print(f"\n{'=' * 70}")
    print("✅ Private Equity Acquisitions ACQUIRE Framework Demo Complete!")
    print(f"Generated {len(lois)} preliminary LOIs with comprehensive deal structure")
    print("Ready for GitHub repository creation with deal book and individual LOI issues")
    
    # Show framework weights
    print(f"\n⚖️  ACQUIRE Framework Weights:")
    weights = pe_flavor.framework.params.get('weights', {})
    weight_labels = {
        'A': 'Addressable Fragmentation',
        'C': 'Cashflow Quality', 
        'Q': 'Quality of Operations',
        'U': 'Upside Levers',
        'I': 'Integration Readiness',
        'R': 'Risk & Compliance',
        'E': 'Exit Pathways'
    }
    
    for code, weight in weights.items():
        label = weight_labels.get(code, code)
        print(f"   • {label}: {weight:.0%}")

if __name__ == "__main__":
    demo_pe_acquisitions()