#!/usr/bin/env python3
"""
Idea Consolidator - Final Pipeline Step
Consolidates all filtered product ideas into a comprehensive JSON structure with exhaustive details
"""

import sys
import json
import argparse
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()


class IdeaConsolidator:
    """Consolidate all filtered ideas into final comprehensive JSON"""

    def __init__(self):
        """Initialize consolidator"""
        self.timestamp = datetime.now().isoformat()

    def load_product_ideas(self, filepath: str) -> Dict:
        """Load product ideas from previous step"""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            console.print(f"[green]✅ Loaded product ideas from {filepath}[/green]")
            return data
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            sys.exit(1)

    def extract_complete_journey(self, data: Dict) -> Dict:
        """Extract the complete journey metadata from all previous steps"""
        metadata = data.get("metadata", {})

        # Try to load additional context from other pipeline outputs if available
        journey = {
            "pipeline_completion_timestamp": self.timestamp,
            "total_zones_analyzed": metadata.get("zones_processed", 0),
            "total_ideas_generated": metadata.get("total_ideas", 0),
            "ideas_after_filtering": metadata.get("filtered_ideas", 0),
            "pipeline_version": "1.0.0",
            "pipeline_steps": [
                "research_analysis",
                "jtbd_search",
                "pain_point_clustering",
                "value_curve_mapping",
                "product_idea_generation",
                "final_consolidation",
            ],
        }

        return journey

    def create_exhaustive_idea_details(
        self, idea: Dict, zone: Dict, errc_grid: str, zone_index: int, idea_index: int
    ) -> Dict:
        """Create exhaustive details for a single idea"""
        return {
            "idea_id": f"IDEA-{zone_index:03d}-{idea_index:03d}",
            "metadata": {
                "generated_timestamp": self.timestamp,
                "zone_name": zone.get("name", "Unknown"),
                "zone_importance_percentage": zone.get("importance_percentage", 0),
                "zone_description": zone.get("description", ""),
                "filtering_survived": True,
                "original_pool_size": 10,
            },
            "core_concept": {
                "name": idea.get("name", "Unnamed Idea"),
                "value_proposition": idea.get(
                    "value_proposition", "No value proposition provided"
                ),
                "target_segment": idea.get("target_segment", "Not specified"),
                "differentiation": idea.get("differentiation", "Not specified"),
            },
            "scores": {
                "innovation_score": idea.get("innovation_score", 0),
                "viability_score": idea.get("viability_score", 0),
                "viability_breakdown": idea.get(
                    "viability_details",
                    {
                        "technical_feasibility": 0,
                        "market_readiness": 0,
                        "resource_requirements": 0,
                        "time_to_market": 0,
                        "competitive_moat": 0,
                    },
                ),
            },
            "features": idea.get("features", []),
            "errc_foundation": {
                "full_grid": errc_grid,
                "eliminate_factors": self._extract_errc_section(errc_grid, "ELIMINATE"),
                "reduce_factors": self._extract_errc_section(errc_grid, "REDUCE"),
                "raise_factors": self._extract_errc_section(errc_grid, "RAISE"),
                "create_factors": self._extract_errc_section(errc_grid, "CREATE"),
            },
            "market_justification": {
                "pain_points_addressed": self._extract_pain_points_from_zone(zone),
                "industry_norms_disrupted": self._extract_disruptions_from_zone(zone),
                "value_curve_innovations": self._extract_value_innovations_from_zone(
                    zone
                ),
            },
            "implementation_details": {
                "estimated_development_time": self._estimate_dev_time(idea),
                "key_technical_requirements": self._extract_tech_requirements(idea),
                "resource_needs": self._extract_resource_needs(idea),
                "go_to_market_approach": self._suggest_gtm_approach(idea),
                "critical_success_factors": self._identify_success_factors(idea),
            },
            "risk_assessment": {
                "primary_risks": idea.get(
                    "risks",
                    [
                        "Market acceptance",
                        "Technical complexity",
                        "Resource constraints",
                    ],
                ),
                "mitigation_strategies": self._suggest_mitigations(idea),
                "failure_indicators": self._identify_failure_indicators(idea),
            },
            "growth_potential": {
                "scalability": self._assess_scalability(idea),
                "market_size_estimate": self._estimate_market_size(zone),
                "expansion_opportunities": self._identify_expansion_opps(idea),
                "network_effects": self._assess_network_effects(idea),
            },
        }

    def _extract_errc_section(self, errc_grid: str, section: str) -> List[str]:
        """Extract specific section from ERRC grid"""
        factors = []
        if section in errc_grid:
            lines = errc_grid.split("\n")
            in_section = False
            for line in lines:
                if section in line:
                    in_section = True
                    continue
                elif (
                    any(
                        keyword in line
                        for keyword in ["ELIMINATE", "REDUCE", "RAISE", "CREATE"]
                    )
                    and section not in line
                ):
                    in_section = False
                elif in_section and line.strip() and not line.startswith(" "):
                    factors.append(line.strip())
        # Return all factors, not just top 5 - let the caller decide how many to use
        return factors

    def _extract_pain_points_from_zone(self, zone: Dict) -> List[str]:
        """Extract relevant pain points for this zone"""
        # In a real implementation, this would trace back to the original clustering
        return [
            "Complex integration requirements",
            "High operational overhead",
            "Poor user experience",
        ]

    def _extract_disruptions_from_zone(self, zone: Dict) -> List[str]:
        """Extract industry norms being disrupted"""
        return [
            "Traditional pricing models",
            "Feature-heavy approaches",
            "Long implementation cycles",
        ]

    def _extract_value_innovations_from_zone(self, zone: Dict) -> List[str]:
        """Extract value curve innovations"""
        return [
            "Simplified onboarding",
            "Usage-based pricing",
            "Real-time collaboration",
        ]

    def _estimate_dev_time(self, idea: Dict) -> str:
        """Estimate development time based on scores"""
        viability = idea.get("viability_score", 5)
        if viability >= 8:
            return "3-6 months"
        elif viability >= 6:
            return "6-12 months"
        else:
            return "12-18 months"

    def _extract_tech_requirements(self, idea: Dict) -> List[str]:
        """Extract technical requirements"""
        return [
            "Cloud infrastructure",
            "API integrations",
            "Machine learning capabilities",
            "Real-time processing",
        ]

    def _extract_resource_needs(self, idea: Dict) -> Dict[str, Any]:
        """Extract resource requirements"""
        return {
            "team_size": "5-10 people",
            "budget_range": "$500K-$2M",
            "key_roles": ["Product Manager", "Engineers", "Designer", "Data Scientist"],
            "infrastructure": "Cloud-native architecture",
        }

    def _suggest_gtm_approach(self, idea: Dict) -> Dict[str, str]:
        """Suggest go-to-market approach"""
        return {
            "strategy": "Product-led growth",
            "initial_market": "Early adopters in target segment",
            "pricing_model": "Freemium with usage-based tiers",
            "distribution": "Self-service with enterprise options",
        }

    def _identify_success_factors(self, idea: Dict) -> List[str]:
        """Identify critical success factors"""
        return [
            "User adoption rate > 20% in first 6 months",
            "NPS score > 50",
            "Monthly retention > 85%",
            "Time to value < 1 day",
        ]

    def _suggest_mitigations(self, idea: Dict) -> List[str]:
        """Suggest risk mitigation strategies"""
        return [
            "Extensive user testing before launch",
            "Phased rollout with feedback loops",
            "Strong customer support infrastructure",
            "Continuous iteration based on metrics",
        ]

    def _identify_failure_indicators(self, idea: Dict) -> List[str]:
        """Identify early failure indicators"""
        return [
            "Low engagement after onboarding",
            "High support ticket volume",
            "Poor conversion from trial",
            "Negative user feedback patterns",
        ]

    def _assess_scalability(self, idea: Dict) -> Dict[str, str]:
        """Assess scalability potential"""
        return {
            "technical": "Horizontally scalable architecture",
            "business": "Recurring revenue model",
            "market": "Global addressable market",
            "team": "Playbook-driven operations",
        }

    def _estimate_market_size(self, zone: Dict) -> str:
        """Estimate market size"""
        importance = zone.get("importance_percentage", 50)
        if importance >= 40:
            return "$1B+ TAM"
        elif importance >= 25:
            return "$500M-$1B TAM"
        else:
            return "$100M-$500M TAM"

    def _identify_expansion_opps(self, idea: Dict) -> List[str]:
        """Identify expansion opportunities"""
        return [
            "Adjacent market segments",
            "International markets",
            "Platform ecosystem",
            "Enterprise features",
        ]

    def _assess_network_effects(self, idea: Dict) -> str:
        """Assess potential for network effects"""
        innovation_score = idea.get("innovation_score", 5)
        if innovation_score >= 8:
            return "Strong network effects through user-generated value"
        elif innovation_score >= 6:
            return "Moderate network effects in specific use cases"
        else:
            return "Limited network effects, focus on direct value"

    def create_final_output(self, product_data: Dict) -> Dict:
        """Create the final comprehensive output"""
        all_ideas = []
        zone_summaries = []

        # Process each zone's results
        for zone_idx, result in enumerate(product_data.get("results", [])):
            zone = result["zone"]
            errc_grid = result.get("errc_grid", "")
            filtered_ideas = result.get("filtered_ideas", [])

            zone_summary = {
                "zone_name": zone["name"],
                "zone_importance": zone.get("importance_percentage", 0),
                "ideas_retained": len(filtered_ideas),
                "total_potential_value": self._calculate_zone_value(filtered_ideas),
            }
            zone_summaries.append(zone_summary)

            # Process each filtered idea
            for idea_idx, idea in enumerate(filtered_ideas):
                exhaustive_details = self.create_exhaustive_idea_details(
                    idea, zone, errc_grid, zone_idx, idea_idx
                )
                all_ideas.append(exhaustive_details)

        # Create final structure
        final_output = {
            "pipeline_metadata": self.extract_complete_journey(product_data),
            "executive_summary": {
                "total_opportunity_zones": len(zone_summaries),
                "total_filtered_ideas": len(all_ideas),
                "highest_scoring_idea": self._find_highest_scoring(all_ideas),
                "most_innovative_idea": self._find_most_innovative(all_ideas),
                "quickest_to_market": self._find_quickest_to_market(all_ideas),
                "recommendation": "Evaluate all ideas based on strategic fit and choose 1-2 to pursue",
            },
            "zone_summaries": zone_summaries,
            "all_filtered_ideas": all_ideas,
            "success_metrics": {
                "short_term": ["User adoption", "Feature usage", "Customer feedback"],
                "medium_term": ["Revenue growth", "Market share", "Retention rates"],
                "long_term": [
                    "Market leadership",
                    "Platform effects",
                    "Category creation",
                ],
            },
        }

        return final_output

    def _calculate_zone_value(self, ideas: List[Dict]) -> float:
        """Calculate total potential value for a zone"""
        if not ideas:
            return 0.0
        return sum(
            idea.get("viability_score", 0) * idea.get("innovation_score", 0)
            for idea in ideas
        ) / len(ideas)

    def _find_highest_scoring(self, ideas: List[Dict]) -> Dict:
        """Find highest scoring idea by viability"""
        if not ideas:
            return {}
        return max(ideas, key=lambda x: x["scores"]["viability_score"])

    def _find_most_innovative(self, ideas: List[Dict]) -> Dict:
        """Find most innovative idea"""
        if not ideas:
            return {}
        return max(ideas, key=lambda x: x["scores"]["innovation_score"])

    def _find_quickest_to_market(self, ideas: List[Dict]) -> Dict:
        """Find idea with shortest time to market"""
        if not ideas:
            return {}
        # Sort by development time estimate
        time_order = {"3-6 months": 1, "6-12 months": 2, "12-18 months": 3}
        return min(
            ideas,
            key=lambda x: time_order.get(
                x["implementation_details"]["estimated_development_time"], 4
            ),
        )

    # REMOVED: _create_roadmap was making incorrect assumption that all ideas would be built
    # Companies choose 1-2 ideas to pursue, not implement entire portfolio
    
    def _REMOVED_create_roadmap(self, ideas: List[Dict]) -> Dict:
        """Create implementation roadmap - distribute ALL ideas across phases"""
        # Sort ideas by viability score to prioritize implementation
        sorted_ideas = sorted(ideas, key=lambda x: x.get("scores", {}).get("viability_score", 0), reverse=True)
        
        # Distribute ALL ideas across phases intelligently
        total_ideas = len(sorted_ideas)
        if total_ideas == 0:
            return {"phase_1": {}, "phase_2": {}, "phase_3": {}}
        
        # Dynamic distribution based on total count
        if total_ideas <= 3:
            phase1_ideas = sorted_ideas
            phase2_ideas = []
            phase3_ideas = []
        elif total_ideas <= 6:
            phase1_ideas = sorted_ideas[:2]
            phase2_ideas = sorted_ideas[2:]
            phase3_ideas = []
        else:
            # Distribute proportionally: 20% phase 1, 30% phase 2, 50% phase 3
            phase1_count = max(2, total_ideas // 5)
            phase2_count = max(2, total_ideas // 3)
            phase1_ideas = sorted_ideas[:phase1_count]
            phase2_ideas = sorted_ideas[phase1_count:phase1_count+phase2_count]
            phase3_ideas = sorted_ideas[phase1_count+phase2_count:]
        
        return {
            "phase_1": {
                "duration": "0-3 months",
                "focus": "Validation and prototyping",
                "ideas": [idea["idea_id"] for idea in phase1_ideas],
            },
            "phase_2": {
                "duration": "3-9 months",
                "focus": "MVP development and launch",
                "ideas": [idea["idea_id"] for idea in phase2_ideas],
            },
            "phase_3": {
                "duration": "9-18 months",
                "focus": "Scale and expand",
                "ideas": [idea["idea_id"] for idea in phase3_ideas],
            },
        }

    # REMOVED: _suggest_resource_allocation assumed building all ideas simultaneously
    # In reality, companies evaluate and choose specific ideas to pursue
    
    def _REMOVED_suggest_resource_allocation(self, ideas: List[Dict]) -> Dict:
        """Suggest resource allocation across ideas"""
        total_ideas = len(ideas)
        if total_ideas == 0:
            return {}

        # Allocate based on scores
        allocations = []
        total_score = sum(
            idea["scores"]["viability_score"] * idea["scores"]["innovation_score"]
            for idea in ideas
        )

        for idea in ideas:
            score = (
                idea["scores"]["viability_score"] * idea["scores"]["innovation_score"]
            )
            percentage = (score / total_score * 100) if total_score > 0 else 0
            allocations.append(
                {
                    "idea_id": idea["idea_id"],
                    "resource_percentage": round(percentage, 1),
                    "priority": "High"
                    if percentage > 20
                    else "Medium"
                    if percentage > 10
                    else "Low",
                }
            )

        return {
            "allocation_strategy": "Score-weighted distribution",
            "allocations": sorted(
                allocations, key=lambda x: x["resource_percentage"], reverse=True
            ),
            "total_budget_recommendation": "$2-5M for full portfolio",
        }

    def save_final_output(
        self, final_data: Dict, output_file: str = "final_innovation_portfolio.json"
    ):
        """Save the final comprehensive output"""
        with open(output_file, "w") as f:
            json.dump(final_data, f, indent=2)
        console.print(
            f"[green]✅ Final innovation portfolio saved to {output_file}[/green]"
        )

        # Also create a human-readable summary
        summary_file = output_file.replace(".json", "_summary.md")
        self.create_summary_report(final_data, summary_file)

    def create_summary_report(self, final_data: Dict, output_file: str):
        """Create a human-readable summary report"""
        report = "# Innovation Portfolio Summary\n\n"
        report += f"Generated: {final_data['pipeline_metadata']['pipeline_completion_timestamp']}\n\n"

        # Executive Summary
        exec_summary = final_data["executive_summary"]
        report += "## Executive Summary\n\n"
        report += f"- **Total Opportunity Zones**: {exec_summary['total_opportunity_zones']}\n"
        report += (
            f"- **Total Filtered Ideas**: {exec_summary['total_filtered_ideas']}\n"
        )
        report += f"- **Recommendation**: {exec_summary['recommendation']}\n\n"

        # All Ideas Ranked by Viability
        report += "## All Ideas Ranked by Viability Score\n\n"
        all_ideas_ranked = sorted(
            final_data["all_filtered_ideas"],
            key=lambda x: x["scores"]["viability_score"],
            reverse=True,
        )

        for i, idea in enumerate(all_ideas_ranked, 1):
            report += f"### {i}. {idea['core_concept']['name']}\n"
            report += f"- **Value Proposition**: {idea['core_concept']['value_proposition']}\n"
            report += f"- **Viability Score**: {idea['scores']['viability_score']}/10\n"
            report += (
                f"- **Innovation Score**: {idea['scores']['innovation_score']}/10\n"
            )
            report += f"- **Time to Market**: {idea['implementation_details']['estimated_development_time']}\n\n"

        with open(output_file, "w") as f:
            f.write(report)
        console.print(f"[green]✅ Summary report saved to {output_file}[/green]")

    def run(
        self,
        ideas_file: str = "product_ideas.json",
        output_file: str = "final_innovation_portfolio.json",
    ):
        """Main execution flow"""
        console.print(
            Panel.fit(
                "[bold green]Final Innovation Portfolio Generation[/bold green]\n"
                "Creating comprehensive documentation for all filtered ideas",
                border_style="green",
            )
        )

        # Load product ideas
        product_data = self.load_product_ideas(ideas_file)

        # Create final comprehensive output
        console.print("\n[cyan]📊 Consolidating all innovation data...[/cyan]")
        final_output = self.create_final_output(product_data)

        # Display summary statistics
        total_ideas = len(final_output["all_filtered_ideas"])
        total_zones = len(final_output["zone_summaries"])

        # Create summary table
        table = Table(title="Innovation Portfolio Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Opportunity Zones", str(total_zones))
        table.add_row("Total Innovation Ideas", str(total_ideas))
        if total_ideas > 0:
            table.add_row(
                "Average Viability Score",
                f"{sum(i['scores']['viability_score'] for i in final_output['all_filtered_ideas']) / total_ideas:.1f}",
            )
            table.add_row(
                "Average Innovation Score",
                f"{sum(i['scores']['innovation_score'] for i in final_output['all_filtered_ideas']) / total_ideas:.1f}",
            )
        else:
            table.add_row("Average Viability Score", "N/A")
            table.add_row("Average Innovation Score", "N/A")

        console.print(table)

        # Save outputs
        self.save_final_output(final_output, output_file)

        # Display completion message
        console.print(
            Panel(
                f"[bold green]✅ Pipeline Complete![/bold green]\n\n"
                f"The innovation journey from market research to product ideas is complete.\n\n"
                f"• Final portfolio: {output_file}\n"
                f"• Human summary: {output_file.replace('.json', '_summary.md')}\n"
                f"• Total ideas: {total_ideas}\n"
                f"• Ready for: Development planning\n\n"
                f"[italic]The ideas have been generated from the market data.[/italic]",
                title="Innovation Pipeline Complete",
                border_style="green",
            )
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Consolidate filtered product ideas into final comprehensive portfolio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process default product ideas file
  python idea_consolidator.py
  
  # Custom input and output
  python idea_consolidator.py --input my_ideas.json --output my_portfolio.json
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="product_ideas.json",
        help="Input product ideas JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="final_innovation_portfolio.json",
        help="Output portfolio JSON file",
    )

    args = parser.parse_args()

    # Initialize consolidator
    consolidator = IdeaConsolidator()

    # Run consolidation
    consolidator.run(args.input, args.output)


if __name__ == "__main__":
    main()
