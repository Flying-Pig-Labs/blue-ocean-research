#!/usr/bin/env python3
"""
PE Acquisitions Real Data Enrichment Demo

Demonstrates how to enrich PE acquisition targets with real data using:
1. Claude 4 Opus for intelligent financial estimates and market analysis
2. Firecrawl for respectful web scraping of brokerage listings

This shows how to get real acquisition targets instead of synthetic data.
"""

import asyncio
import json
from flavors.config_schema import FlavorRegistry
from flavors.framework_adapter import AcquireAdapter
from flavors.loi_synthesizer import LOISynthesizer
from flavors.data_enrichment import enrich_pe_opportunities

async def demo_pe_real_data_enrichment():
    """Demo PE acquisitions with real market data enrichment."""
    print("🔍 PE Acquisitions - Real Data Enrichment Demo")
    print("=" * 70)
    
    # Load PE acquisitions flavor
    registry = FlavorRegistry(flavors_dir="flavors")
    pe_flavor = registry.get_flavor("private_equity_acquisitions")
    
    print(f"✅ Loaded PE flavor: {pe_flavor.name}")
    
    # Show data sources that would be accessed
    print(f"\n📊 Data Sources Configuration:")
    sources = pe_flavor.sources.get('broker_sites', [])
    for source in sources:
        print(f"   • {source.get('name', 'Unknown')}")
    
    print(f"\n🎯 Investment Thesis:")
    thesis = pe_flavor.thesis_preferences
    print(f"   Industries: {', '.join(thesis.get('target_industries', []))}")
    print(f"   States: {', '.join(thesis.get('geography', {}).get('include_states', []))}")
    size_bounds = thesis.get('size_bounds', {})
    print(f"   Revenue Range: ${size_bounds.get('revenue_min', 0)/1000000:.1f}M - ${size_bounds.get('revenue_max', 0)/1000000:.0f}M")
    
    print(f"\n🔄 Enrichment Process Overview:")
    print("   1. 🌐 Firecrawl scrapes brokerage listings (BizBuySell, BizQuest, etc.)")
    print("   2. 🧠 Claude 4 Opus analyzes and estimates missing financial data")
    print("   3. 📈 Market intelligence generated from industry patterns")
    print("   4. 🎯 ACQUIRE framework scores each opportunity")
    print("   5. 📋 Preliminary LOIs generated for top targets")
    
    # Note: For demo purposes, we'll use mock data since we don't have API keys
    print(f"\n⚠️  Demo Mode: Using mock data (real implementation requires API keys)")
    print("   Real usage: Provide FIRECRAWL_API_KEY environment variable")
    print("   Claude API: Using built-in access for financial analysis")
    
    # Enrich opportunities with real data (mock for demo)
    print(f"\n🔍 Enriching acquisition opportunities...")
    
    try:
        # This would use real Firecrawl + Claude 4 Opus in production
        enriched_zones = await enrich_pe_opportunities(pe_flavor.__dict__)
        
        print(f"   ✅ Successfully enriched {len(enriched_zones)} acquisition targets")
        
        # Show enriched data sample
        if enriched_zones:
            sample_zone = enriched_zones[0]
            enriched_data = sample_zone.get('enriched_data', {})
            
            print(f"\n📋 Sample Enriched Target:")
            print(f"   Company: {sample_zone.get('name', 'Unknown')}")
            print(f"   Industry: {enriched_data.get('industry', 'Unknown')}")
            print(f"   Location: {enriched_data.get('location', 'Unknown')}")
            
            # Financial estimates from Claude 4 Opus
            financial_est = enriched_data.get('financial_estimates', {})
            if financial_est:
                revenue_est = financial_est.get('revenue_estimate', {})
                sde_est = financial_est.get('sde_estimate', {})
                print(f"   Revenue Estimate: ${revenue_est.get('low', 0)/1000000:.1f}M - ${revenue_est.get('high', 0)/1000000:.1f}M")
                print(f"   SDE Estimate: ${sde_est.get('low', 0)/1000:.0f}k - ${sde_est.get('high', 0)/1000:.0f}k")
                print(f"   Recurring Revenue: {financial_est.get('recurring_revenue_pct', {}).get('estimate', 0)}%")
            
            # Market intelligence from Claude 4 Opus
            market_intel = enriched_data.get('market_intelligence', {})
            if market_intel:
                print(f"   Market Fragmentation: {market_intel.get('market_fragmentation_score', 0)}/10")
                print(f"   Typical Multiples: {market_intel.get('typical_multiples', {}).get('sde_low', 0):.1f}x - {market_intel.get('typical_multiples', {}).get('sde_high', 0):.1f}x SDE")
        
        # Run ACQUIRE framework analysis
        print(f"\n🎯 Running ACQUIRE Framework Analysis...")
        adapter = AcquireAdapter(pe_flavor.framework.params)
        
        analyzed_zones = []
        for zone in enriched_zones:
            analysis = adapter.analyze_zone(zone)
            zone['framework_analysis'] = {
                'overall_score': analysis.overall_score,
                'scores': analysis.scores,
                'confidence_level': analysis.confidence_level,
                'recommendations': analysis.recommendations
            }
            analyzed_zones.append(zone)
        
        # Generate preliminary LOIs
        print(f"\n📋 Generating Preliminary LOIs...")
        synthesizer = LOISynthesizer(pe_flavor.__dict__)
        lois = synthesizer.synthesize_lois(analyzed_zones, target_count=3)
        
        print(f"   ✅ Generated {len(lois)} preliminary LOIs")
        
        # Display results
        for i, loi in enumerate(lois, 1):
            print(f"\n{'=' * 60}")
            print(f"📄 LOI #{i}: {loi.title}")
            print(f"{'=' * 60}")
            
            print(f"🏢 Target: {loi.target_company}")
            print(f"🎯 ACQUIRE Score: {loi.acquire_scores.get('rank_score', 0):.2f}")
            
            # Show real data integration
            enriched_data = analyzed_zones[i-1].get('enriched_data', {})
            if enriched_data.get('source_url'):
                print(f"🔗 Broker Listing: {enriched_data['source_url']}")
            if enriched_data.get('broker_contact'):
                print(f"👨‍💼 Broker: {enriched_data['broker_contact']}")
            
            # Financial data from enrichment
            financial_est = enriched_data.get('financial_estimates', {})
            if financial_est and loi.offer_summary.get('price_range'):
                print(f"💰 Preliminary Offer: {loi.offer_summary['price_range']}")
                revenue_est = financial_est.get('revenue_estimate', {})
                if revenue_est.get('confidence', 0) > 0.6:
                    print(f"📊 Revenue Base: ${revenue_est.get('low', 0)/1000000:.1f}M - ${revenue_est.get('high', 0)/1000000:.1f}M (confidence: {revenue_est.get('confidence', 0):.2f})")
            
            # Market intelligence insights
            market_intel = enriched_data.get('market_intelligence', {})
            if market_intel:
                consolidation = market_intel.get('consolidation_activity', '')
                if consolidation:
                    print(f"🏭 Market Context: {consolidation[:100]}...")
            
            # Show ACQUIRE analysis
            axes = loi.acquire_scores.get('axes', {})
            if axes:
                top_score = max(axes.items(), key=lambda x: x[1])
                print(f"🎯 Top Strength: {top_score[0].replace('_', ' ').title()} ({top_score[1]:.2f})")
        
        # Implementation guide
        print(f"\n{'=' * 70}")
        print("🚀 Implementation Guide for Real Data")
        print("=" * 70)
        
        print(f"\n1. 🔑 API Keys Required:")
        print("   • FIRECRAWL_API_KEY - Sign up at https://firecrawl.dev/")
        print("   • ANTHROPIC_API_KEY - For Claude 4 Opus analysis (optional - uses default)")
        
        print(f"\n2. 🌐 Supported Broker Sites:")
        for site in sources:
            site_name = site.get('name', 'Unknown')
            print(f"   • {site_name} - Respectful scraping with rate limits")
        
        print(f"\n3. 🧠 Claude 4 Opus Enrichment:")
        print("   • Financial metric estimation from incomplete data")
        print("   • Market fragmentation and consolidation analysis")
        print("   • Industry-specific benchmarks and multiples")
        print("   • Risk assessment and opportunity identification")
        
        print(f"\n4. 📊 Real Data Integration Flow:")
        print("   • Geographic filtering by target states")
        print("   • Industry filtering by thesis preferences")
        print("   • Revenue/size filtering by investment criteria")
        print("   • Automatic deduplication across broker sites")
        print("   • Financial gap-filling with Claude analysis")
        
        print(f"\n5. ⚡ Usage Example:")
        print("   export FIRECRAWL_API_KEY='your_key_here'")
        print("   python run_pe_enriched_pipeline.py --flavor private_equity_acquisitions")
        print("   # Generates GitHub repo with real acquisition targets and LOIs")
        
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        print("💡 This is expected in demo mode without API keys")

def show_enrichment_capabilities():
    """Show what the enrichment system can provide."""
    print(f"\n🔧 Enrichment Capabilities:")
    print("=" * 40)
    
    print(f"\n📊 Financial Data Estimation:")
    print("   • Revenue ranges from market signals")
    print("   • SDE/EBITDA margins by industry")
    print("   • Customer concentration estimates")
    print("   • Recurring revenue percentages")
    print("   • Seasonal variation patterns")
    print("   • Working capital requirements")
    
    print(f"\n🏭 Market Intelligence:")
    print("   • Market fragmentation scoring")
    print("   • Consolidation activity analysis")
    print("   • Success factor identification")
    print("   • Technology adoption opportunities")
    print("   • Regulatory complexity assessment")
    print("   • Typical acquisition multiples")
    
    print(f"\n🎯 Geographic Targeting:")
    print("   • State-by-state listing aggregation")
    print("   • Local market density analysis")
    print("   • Cluster fit scoring within radius")
    print("   • Regional competitive dynamics")
    
    print(f"\n🤖 Automated Processing:")
    print("   • Duplicate listing detection")
    print("   • Missing data interpolation")
    print("   • Confidence scoring for estimates")
    print("   • Source attribution and citations")

if __name__ == "__main__":
    print("Starting PE Acquisitions Real Data Enrichment Demo...")
    show_enrichment_capabilities()
    
    # Run async demo
    try:
        asyncio.run(demo_pe_real_data_enrichment())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    
    print(f"\n✅ Demo completed! Ready to implement real data enrichment.")