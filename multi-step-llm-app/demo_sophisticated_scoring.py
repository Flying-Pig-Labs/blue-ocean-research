#!/usr/bin/env python3
"""
Demo of the Sophisticated Scoring System
=======================================

Demonstrates the capabilities of Issue #5 implementation without requiring API keys.
"""

import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from src.scoring import (
    IdeaScore, BreakthroughDetector, SmartFilterer, 
    CrossZoneOptimizer, ConfidenceScorer, FinalSelector, SelectionReporter
)

console = Console()

def create_sample_ideas():
    """Create sample ideas for demonstration"""
    ideas = [
        {
            'name': 'AI-Powered Smart Workspace',
            'value_proposition': 'Revolutionary AI system that adapts workspace layout and tools based on user behavior patterns, increasing productivity by 40%',
            'features': [
                'Machine learning workspace optimization',
                'Real-time environment adaptation', 
                'Predictive tool arrangement',
                'Cross-platform integration',
                'Biometric feedback loops'
            ],
            'target_segment': 'B2B knowledge workers and remote teams in technology companies',
            'differentiation': 'First-ever AI that learns individual work patterns and physically adapts the workspace in real-time',
            'viability_score': 7.5,
            'innovation_score': 8.5,
            'viability_details': {
                'technical_feasibility': 7.0,
                'market_readiness': 6.5,
                'resource_requirements': 6.0,
                'time_to_market': 7.5,
                'competitive_moat': 8.0
            }
        },
        {
            'name': 'Quantum Communication Network',
            'value_proposition': 'Breakthrough quantum entanglement communication system enabling instant, unhackable global communications with zero latency',
            'features': [
                'Quantum entanglement protocols',
                'Zero-latency transmission',
                'Unbreakable quantum encryption',
                'Global network infrastructure',
                'Enterprise security integration'
            ],
            'target_segment': 'Government agencies and enterprise security applications requiring ultimate data protection',
            'differentiation': 'Revolutionary quantum physics breakthrough enabling paradigm-shifting communication technology',
            'viability_score': 4.5,
            'innovation_score': 9.8,
            'viability_details': {
                'technical_feasibility': 3.5,
                'market_readiness': 4.0,
                'resource_requirements': 2.5,
                'time_to_market': 3.0,
                'competitive_moat': 10.0
            }
        },
        {
            'name': 'Sustainable Food Tracking Platform',
            'value_proposition': 'Comprehensive platform that tracks food from farm to table, reducing food waste by 30% and improving supply chain transparency',
            'features': [
                'Blockchain-based supply chain tracking',
                'IoT sensor integration',
                'Predictive analytics for inventory',
                'Consumer transparency dashboard',
                'Sustainability scoring'
            ],
            'target_segment': 'B2B food retailers and B2C environmentally conscious consumers',
            'differentiation': 'End-to-end visibility with real-time sustainability impact scoring',
            'viability_score': 8.0,
            'innovation_score': 6.5,
            'viability_details': {
                'technical_feasibility': 8.5,
                'market_readiness': 7.5,
                'resource_requirements': 7.0,
                'time_to_market': 8.0,
                'competitive_moat': 6.5
            }
        },
        {
            'name': 'Personalized Health Prediction Engine',
            'value_proposition': 'AI-powered health analytics that predicts potential health issues 6 months in advance using wearable data and genetic information',
            'features': [
                'Predictive health analytics',
                'Genetic data integration',
                'Wearable device connectivity',
                'Personalized intervention recommendations',
                'Healthcare provider integration'
            ],
            'target_segment': 'B2C health-conscious individuals and B2B healthcare providers',
            'differentiation': 'Advanced AI combining genetic and real-time biometric data for unprecedented predictive accuracy',
            'viability_score': 6.5,
            'innovation_score': 8.8,
            'viability_details': {
                'technical_feasibility': 6.0,
                'market_readiness': 5.5,
                'resource_requirements': 5.0,
                'time_to_market': 6.0,
                'competitive_moat': 8.5
            }
        },
        {
            'name': 'Smart City Traffic Optimizer',
            'value_proposition': 'Municipal traffic management system using AI and IoT to reduce congestion by 50% and cut emissions by 25%',
            'features': [
                'Real-time traffic flow optimization',
                'Predictive congestion modeling',
                'Smart traffic light coordination',
                'Public transit integration',
                'Environmental impact tracking'
            ],
            'target_segment': 'B2G municipal governments and smart city initiatives',
            'differentiation': 'Comprehensive city-wide optimization with proven environmental and efficiency benefits',
            'viability_score': 7.8,
            'innovation_score': 7.2,
            'viability_details': {
                'technical_feasibility': 8.0,
                'market_readiness': 7.0,
                'resource_requirements': 6.5,
                'time_to_market': 7.5,
                'competitive_moat': 7.0
            }
        }
    ]
    
    return ideas

def create_sample_zones(ideas):
    """Create sample opportunity zones"""
    zones = [
        {
            'zone': {
                'name': 'Productivity & Workspace Innovation',
                'importance_percentage': 35
            },
            'all_ideas': [ideas[0], ideas[3]],  # AI Workspace, Health Prediction
            'filtered_ideas': [ideas[0]],
            'ideas_kept': 1,
            'ideas_total': 2
        },
        {
            'zone': {
                'name': 'Next-Generation Communication',
                'importance_percentage': 25
            },
            'all_ideas': [ideas[1]],  # Quantum Communication
            'filtered_ideas': [ideas[1]],
            'ideas_kept': 1,
            'ideas_total': 1
        },
        {
            'zone': {
                'name': 'Sustainable Technology Solutions',
                'importance_percentage': 40
            },
            'all_ideas': [ideas[2], ideas[4]],  # Food Tracking, Traffic Optimizer
            'filtered_ideas': [ideas[2], ideas[4]],
            'ideas_kept': 2,
            'ideas_total': 2
        }
    ]
    
    return zones

def demonstrate_sophisticated_scoring():
    """Demonstrate the sophisticated scoring system"""
    console.print(Panel.fit(
        "[bold green]Sophisticated Scoring System Demo[/bold green]\n"
        "Issue #5: Sophisticated Scoring with Smart Filtering",
        border_style="green"
    ))
    
    # Create sample data
    console.print("\n[cyan]🎯 Creating sample product ideas...[/cyan]")
    ideas = create_sample_ideas()
    zones = create_sample_zones(ideas)
    
    console.print(f"[green]✅ Created {len(ideas)} sample ideas across {len(zones)} opportunity zones[/green]")
    
    # Step 1: Apply sophisticated scoring
    console.print("\n[cyan]🔬 Step 1: Applying sophisticated scoring system...[/cyan]")
    
    for zone in zones:
        zone_name = zone['zone']['name']
        console.print(f"  Processing zone: [bold]{zone_name}[/bold]")
        
        enhanced_ideas = []
        for idea in zone['all_ideas']:
            # Add zone context
            idea['zone_name'] = zone_name
            
            # Apply comprehensive scoring
            idea_score = IdeaScore.from_idea_data(idea)
            breakthrough_detector = BreakthroughDetector()
            breakthrough_analysis = breakthrough_detector.analyze_idea(idea, idea_score)
            confidence_scorer = ConfidenceScorer()
            confidence_analysis = confidence_scorer.calculate_confidence(idea, idea_score)
            
            # Add scoring data
            idea['scoring'] = {
                'idea_score': idea_score,
                'breakthrough_analysis': breakthrough_analysis,
                'confidence_analysis': confidence_analysis,
                'composite_score': confidence_analysis.adjusted_scores.get('composite_score', idea_score.composite_score),
                'is_excellence': idea_score.is_high_potential(),
                'is_moonshot': breakthrough_analysis.is_moonshot,
                'is_breakthrough': breakthrough_analysis.is_breakthrough,
                'risk_level': idea_score.get_risk_level(),
                'confidence_category': confidence_scorer.get_confidence_category(confidence_analysis.overall_confidence)
            }
            
            enhanced_ideas.append(idea)
        
        zone['all_ideas'] = enhanced_ideas
    
    console.print("[green]✅ Sophisticated scoring complete[/green]")
    
    # Display scoring results
    console.print("\n[cyan]📊 Scoring Results Summary:[/cyan]")
    
    table = Table(title="Idea Scoring Results")
    table.add_column("Idea", style="cyan", no_wrap=True)
    table.add_column("Zone", style="yellow")
    table.add_column("Composite", style="green", justify="right")
    table.add_column("Innovation", style="blue", justify="right")
    table.add_column("Viability", style="magenta", justify="right")
    table.add_column("Breakthrough", style="red", justify="right")
    table.add_column("Confidence", style="purple", justify="right")
    table.add_column("Category", style="white")
    
    all_ideas = []
    for zone in zones:
        all_ideas.extend(zone['all_ideas'])
    
    for idea in all_ideas:
        scoring = idea['scoring']
        idea_score = scoring['idea_score']
        
        # Format scores
        composite = f"{scoring['composite_score']:.1f}"
        innovation = f"{idea_score.innovation_score:.1f}"
        viability = f"{idea_score.viability_score:.1f}"
        breakthrough = f"{idea_score.breakthrough_score:.1f}"
        confidence = f"{scoring['confidence_analysis'].overall_confidence:.1f}"
        
        # Determine category
        category = ""
        if scoring['is_moonshot']:
            category = "🌙 Moonshot"
        elif scoring['is_breakthrough']:
            category = "🚀 Breakthrough"
        elif scoring['is_excellence']:
            category = "⭐ Excellence"
        else:
            category = "📈 Standard"
        
        table.add_row(
            idea['name'][:25] + "..." if len(idea['name']) > 25 else idea['name'],
            idea['zone_name'][:20] + "..." if len(idea['zone_name']) > 20 else idea['zone_name'],
            composite, innovation, viability, breakthrough, confidence, category
        )
    
    console.print(table)
    
    # Step 2: Apply smart filtering
    console.print("\n[cyan]🧠 Step 2: Applying smart filtering with excellence preservation...[/cyan]")
    
    smart_filterer = SmartFilterer()
    filtering_results = smart_filterer.filter_ideas(zones)
    
    console.print(f"[green]✅ Smart filtering complete[/green]")
    console.print(f"  • Selected ideas: {len(filtering_results.selected_ideas)}")
    console.print(f"  • Excellence preserved: {len(filtering_results.excellence_preserved)}")
    console.print(f"  • Warnings generated: {len(filtering_results.warnings)}")
    
    # Step 3: Apply final selection
    console.print("\n[cyan]🎯 Step 3: Applying final selection with ensemble strategies...[/cyan]")
    
    final_selector = FinalSelector()
    final_selection_results = final_selector.select_final_ideas(filtering_results)
    
    console.print(f"[green]✅ Final selection complete[/green]")
    console.print(f"  • Final selection: {len(final_selection_results.final_selection)} ideas")
    console.print(f"  • Selection confidence: {final_selection_results.selection_confidence:.1f}/10")
    console.print(f"  • Strategies used: {len(final_selection_results.ensemble_strategies)}")
    
    # Step 4: Portfolio optimization
    console.print("\n[cyan]⚡ Step 4: Optimizing portfolio across zones...[/cyan]")
    
    cross_zone_optimizer = CrossZoneOptimizer()
    optimization_results = cross_zone_optimizer.optimize_portfolio(
        final_selection_results.final_selection
    )
    
    console.print(f"[green]✅ Portfolio optimization complete[/green]")
    
    # Display optimization results
    baseline = optimization_results['baseline_metrics']
    optimized = optimization_results['optimized_metrics']
    improvement = optimization_results['improvement']
    
    opt_table = Table(title="Portfolio Optimization Results")
    opt_table.add_column("Metric", style="cyan")
    opt_table.add_column("Baseline", style="yellow", justify="right")
    opt_table.add_column("Optimized", style="green", justify="right")
    opt_table.add_column("Improvement", style="blue", justify="right")
    
    metrics = [
        ("Innovation Diversity", baseline.innovation_diversity, optimized.innovation_diversity),
        ("Risk Balance", baseline.risk_balance, optimized.risk_balance),
        ("Market Coverage", baseline.market_coverage, optimized.market_coverage),
        ("Technical Synergy", baseline.technical_synergy, optimized.technical_synergy),
        ("Resource Efficiency", baseline.resource_efficiency, optimized.resource_efficiency),
        ("Overall Balance", baseline.overall_balance, optimized.overall_balance)
    ]
    
    for metric_name, baseline_val, optimized_val in metrics:
        improvement_val = optimized_val - baseline_val
        improvement_str = f"+{improvement_val:.1f}" if improvement_val >= 0 else f"{improvement_val:.1f}"
        
        opt_table.add_row(
            metric_name,
            f"{baseline_val:.1f}",
            f"{optimized_val:.1f}",
            improvement_str
        )
    
    console.print(opt_table)
    
    # Step 5: Generate comprehensive report
    console.print("\n[cyan]📊 Step 5: Generating comprehensive selection report...[/cyan]")
    
    selection_reporter = SelectionReporter()
    comprehensive_report = selection_reporter.generate_report(
        zones, filtering_results, final_selection_results, optimization_results
    )
    
    console.print(f"[green]✅ Comprehensive report generated[/green]")
    
    # Display final summary
    console.print("\n[cyan]🏆 Final Results Summary:[/cyan]")
    
    exec_summary = comprehensive_report['executive_summary']
    
    summary_panel = Panel(
        f"🎯 [bold]Process Overview:[/bold]\n"
        f"  • Zones analyzed: {exec_summary['process_overview']['zones_analyzed']}\n"
        f"  • Ideas processed: {exec_summary['process_overview']['ideas_processed']}\n"
        f"  • Final selection: {exec_summary['process_overview']['final_selection']}\n"
        f"  • Quality improvement: {exec_summary['process_overview']['quality_improvement']}\n\n"
        f"⭐ [bold]Key Achievements:[/bold]\n" +
        (f"  • {chr(10).join(exec_summary['key_achievements'])}\n\n" if exec_summary['key_achievements'] else "  • Successfully completed sophisticated scoring\n\n") +
        f"🚀 [bold]Breakthrough Performance:[/bold]\n"
        f"  • Total breakthroughs: {exec_summary['breakthrough_performance']['total_identified']}\n"
        f"  • Preservation rate: {exec_summary['breakthrough_performance']['preservation_rate']}\n"
        f"  • Moonshots preserved: {exec_summary['breakthrough_performance']['moonshots_preserved']}\n\n"
        f"🎯 [bold]Selection Confidence:[/bold] {exec_summary['selection_confidence']:.1f}/10",
        title="🚀 Sophisticated Scoring Results",
        border_style="green"
    )
    
    console.print(summary_panel)
    
    # Display final selected ideas
    console.print("\n[cyan]🏅 Final Selected Ideas:[/cyan]")
    
    final_table = Table(title="Final Portfolio Selection")
    final_table.add_column("Rank", style="cyan", justify="center")
    final_table.add_column("Idea", style="bold cyan")
    final_table.add_column("Zone", style="yellow")
    final_table.add_column("Score", style="green", justify="right")
    final_table.add_column("Category", style="white")
    final_table.add_column("Risk Level", style="magenta")
    
    # Sort final selection by composite score
    sorted_final = sorted(
        final_selection_results.final_selection,
        key=lambda x: x.get('scoring', {}).get('composite_score', 0),
        reverse=True
    )
    
    for i, idea in enumerate(sorted_final, 1):
        scoring = idea.get('scoring', {})
        
        category = ""
        if scoring.get('is_moonshot'):
            category = "🌙 Moonshot"
        elif scoring.get('is_breakthrough'):
            category = "🚀 Breakthrough"
        elif scoring.get('is_excellence'):
            category = "⭐ Excellence"
        else:
            category = "📈 Standard"
        
        final_table.add_row(
            str(i),
            idea['name'][:35] + "..." if len(idea['name']) > 35 else idea['name'],
            idea.get('zone_name', 'Unknown')[:25] + "..." if len(idea.get('zone_name', '')) > 25 else idea.get('zone_name', 'Unknown'),
            f"{scoring.get('composite_score', 0):.1f}",
            category,
            scoring.get('risk_level', 'Unknown')
        )
    
    console.print(final_table)
    
    # Show warnings if any
    total_warnings = len(filtering_results.warnings) + len(final_selection_results.warnings)
    if total_warnings > 0:
        console.print(f"\n[yellow]⚠️  {total_warnings} warnings generated during processing:[/yellow]")
        for warning in (filtering_results.warnings + final_selection_results.warnings)[:5]:
            console.print(f"   • {warning}")
        if total_warnings > 5:
            console.print(f"   • ... and {total_warnings - 5} more warnings")
    
    console.print("\n[green]✅ Sophisticated scoring system demonstration complete![/green]")
    console.print("\n[cyan]This demo showcased all features from Issue #5:[/cyan]")
    console.print("  🔬 Multi-dimensional scoring with weighted composites")
    console.print("  🚀 Breakthrough detection and moonshot identification")
    console.print("  🧠 Smart filtering with excellence preservation")
    console.print("  ⚡ Cross-zone portfolio optimization")
    console.print("  🎯 Ensemble selection with multiple strategies")
    console.print("  📊 Comprehensive reporting and analysis")

if __name__ == "__main__":
    demonstrate_sophisticated_scoring()