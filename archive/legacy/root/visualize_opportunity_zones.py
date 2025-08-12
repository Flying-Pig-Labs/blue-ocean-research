#!/usr/bin/env python3
"""
Visualize opportunity zones analysis results.
"""

import json
import sys

def load_results(filepath='opportunity_zones.json'):
    """Load opportunity zones results."""
    with open(filepath, 'r') as f:
        return json.load(f)

def print_zone_summary(zone):
    """Print formatted summary of a single zone."""
    print(f"\n{'='*80}")
    print(f"🎯 {zone['zone_id']}: {zone['name']}")
    print(f"{'='*80}")
    
    print(f"\n📊 Market Metrics:")
    print(f"  • Opportunity Score: {zone['market_opportunity_score']:.0%}")
    print(f"  • JTBDs Addressed: {len(zone['jtbds_addressed'])}")
    print(f"  • Reddit Evidence: {zone['evidence_strength']['total_threads']} threads")
    print(f"  • Total Engagement: {zone['evidence_strength']['total_engagement']:,}")
    print(f"  • Avg Score/Thread: {zone['evidence_strength']['avg_score_per_thread']:.1f}")
    
    print(f"\n🔥 Top Pain Dimensions:")
    sorted_pains = sorted(zone['pain_dimensions'].items(), key=lambda x: x[1], reverse=True)
    for pain, score in sorted_pains[:3]:
        pain_label = pain.replace('_', ' ').title()
        bar = '█' * int(score * 20)
        print(f"  • {pain_label}: {bar} {score:.0%}")
    
    print(f"\n💼 Jobs-to-be-Done Addressed:")
    for i, (jtbd_id, desc) in enumerate(zip(zone['jtbds_addressed'][:3], zone['jtbd_descriptions'][:3]), 1):
        print(f"  {i}. {desc[:70]}...")
    if len(zone['jtbds_addressed']) > 3:
        print(f"  ... and {len(zone['jtbds_addressed'])-3} more")
    
    print(f"\n🛠️ Solution Requirements:")
    for i, req in enumerate(zone['solution_requirements'][:3], 1):
        print(f"  {i}. {req[:70]}...")

def main():
    """Main visualization function."""
    # Load results
    results = load_results()
    
    # Print header
    print("\n" + "="*80)
    print("🚀 OPPORTUNITY ZONES ANALYSIS RESULTS")
    print("="*80)
    
    # Print metadata
    meta = results['analysis_metadata']
    print(f"\n📈 Analysis Overview:")
    print(f"  • Total JTBDs Analyzed: {meta['total_jtbds']}")
    print(f"  • Reddit Threads Processed: {meta['total_reddit_threads']}")
    print(f"  • Opportunity Zones Discovered: {meta['total_zones_discovered']}")
    print(f"  • Analysis Timestamp: {meta['timestamp']}")
    
    # Print summary
    summary = results['zone_summary']
    print(f"\n🏆 Key Insights:")
    print(f"  • Highest Opportunity Zone: {summary['highest_opportunity']}")
    print(f"  • Market Coverage: {summary['total_market_coverage']:.0%} of all JTBDs")
    print(f"  • Strongest Pain Dimension: {summary['strongest_pain_dimension'].replace('_', ' ').title()}")
    
    # Print top 3 zones in detail
    print(f"\n\n{'='*80}")
    print("TOP 3 OPPORTUNITY ZONES")
    print("="*80)
    
    for zone in results['opportunity_zones'][:3]:
        print_zone_summary(zone)
    
    # Print summary table of all zones
    print(f"\n\n{'='*80}")
    print("ALL OPPORTUNITY ZONES SUMMARY")
    print("="*80)
    print(f"\n{'Zone ID':<10} {'Name':<45} {'JTBDs':<8} {'Score':<8}")
    print("-"*80)
    
    for zone in results['opportunity_zones']:
        name = zone['name'][:42] + "..." if len(zone['name']) > 45 else zone['name']
        print(f"{zone['zone_id']:<10} {name:<45} {len(zone['jtbds_addressed']):<8} {zone['market_opportunity_score']:.2f}")
    
    # Print pain dimension matrix
    print(f"\n\n{'='*80}")
    print("PAIN DIMENSION MATRIX (Top 3 Zones)")
    print("="*80)
    
    dimensions = list(results['opportunity_zones'][0]['pain_dimensions'].keys())
    
    # Header
    print(f"\n{'Dimension':<25}", end="")
    for zone in results['opportunity_zones'][:3]:
        print(f"{zone['zone_id']:<12}", end="")
    print()
    print("-"*61)
    
    # Data rows
    for dim in dimensions:
        dim_label = dim.replace('_', ' ').title()[:23]
        print(f"{dim_label:<25}", end="")
        for zone in results['opportunity_zones'][:3]:
            score = zone['pain_dimensions'].get(dim, 0)
            if score > 0.6:
                print(f"{'HIGH':<12}", end="")
            elif score > 0.3:
                print(f"{'MED':<12}", end="")
            else:
                print(f"{'LOW':<12}", end="")
        print()
    
    print("\n" + "="*80)
    print("✅ Analysis Complete! See opportunity_zones.json for full details.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()