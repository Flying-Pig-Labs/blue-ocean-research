#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Product Idea Generator - Final Pipeline Step
Generates and filters product ideas based on ERRC analysis for each opportunity zone
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import openai
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.markdown import Markdown

# Import sophisticated scoring system
from src.scoring import (
    IdeaScore,
    BreakthroughDetector,
    SmartFilterer,
    CrossZoneOptimizer,
    ConfidenceScorer,
    FinalSelector,
    SelectionReporter,
)
from src.utils.debug_logger import DebugLogger
from src.utils.pipeline_logger import PipelineLogger

# Import GitHub integration
from github_integration import create_github_output
from create_enhanced_github_repo import EnhancedGitHubIntegration

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()


class ProductIdeaGenerator:
    """Generate and filter product ideas based on value curve analysis with sophisticated scoring"""

    def __init__(self, debug_mode: bool = False):
        """Initialize API clients and scoring system"""
        self.debug_mode = debug_mode

        # Initialize logging
        self.debug_logger = DebugLogger() if debug_mode else None
        self.pipeline_logger = PipelineLogger()

        # Initialize scoring system components
        self.breakthrough_detector = BreakthroughDetector()
        self.smart_filterer = SmartFilterer()
        self.cross_zone_optimizer = CrossZoneOptimizer()
        self.confidence_scorer = ConfidenceScorer()
        self.final_selector = FinalSelector()
        self.selection_reporter = SelectionReporter()

        if debug_mode:
            self.debug_logger.log_operation(
                "system_init",
                {
                    "component": "ProductIdeaGenerator",
                    "scoring_system": "sophisticated_scoring_v5",
                    "features": [
                        "breakthrough_detection",
                        "smart_filtering",
                        "cross_zone_optimization",
                    ],
                },
            )
        # OpenAI setup for o1 model
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            console.print("[red]Error: OPENAI_API_KEY not found![/red]")
            sys.exit(1)

        try:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            self.model_o1 = "gpt-4o"  # Using GPT-4o for advanced reasoning
        except Exception as e:
            console.print(f"[red]Error initializing OpenAI client: {e}[/red]")
            sys.exit(1)

        # Anthropic setup for Opus
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
            sys.exit(1)

        try:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            self.model_opus = "claude-3-opus-20240229"
        except Exception as e:
            console.print(f"[red]Error initializing Anthropic client: {e}[/red]")
            sys.exit(1)

    def load_value_curves(self, filepath: str) -> Dict:
        """Load value curve analysis results"""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            console.print(f"[green]✅ Loaded value curves from {filepath}[/green]")
            return data
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            sys.exit(1)

    def generate_errc_grid(self, zone_analysis: Dict) -> str:
        """Use OpenAI o1 to generate ERRC grid from value curve analysis"""
        zone_name = zone_analysis["zone"]["name"]
        console.print(f"\n[cyan]🧠 Generating ERRC grid for: {zone_name}[/cyan]")

        # Prepare context from value curve analysis
        context = f"""Opportunity Zone: {zone_name}
Description: {zone_analysis["zone"].get("description", "")}
Importance: {zone_analysis["zone"].get("importance_percentage", 0)}%

Industry Norms & Sacred Cows:
{zone_analysis.get("industry_norms", "Not available")}

Engineering Spectrum Analysis:
{zone_analysis.get("engineering_spectrum", "Not available")}

Competitive Intelligence Summary:
"""

        # Add competitive data if available
        comp_data = zone_analysis.get("competitive_data", {})
        for i, result in enumerate(comp_data.get("search_results", [])[:3], 1):
            context += f"\n{i}. {result.get('title', 'N/A')}"
            if result.get("highlights"):
                context += f"\n   Key insights: {', '.join(result['highlights'][:2])}"

        prompt = """Based on this value curve analysis, create a comprehensive ERRC Grid (Eliminate-Reduce-Raise-Create) for disrupting this market:

ELIMINATE: What industry factors should be eliminated that the industry has long competed on?
REDUCE: What factors should be reduced well below the industry's standard?
RAISE: What factors should be raised well above the industry's standard?
CREATE: What factors should be created that the industry has never offered?

For each quadrant, provide:
1. Specific factors/features/attributes
2. Rationale based on the analysis
3. Expected impact on value curve

Format as a structured table with clear actionable items."""

        try:
            # o1 models work best with simpler message structure
            response = self.openai_client.chat.completions.create(
                model=self.model_o1,
                messages=[{"role": "user", "content": context + "\n\n" + prompt}],
                temperature=1.0,  # o1 models use fixed temperature
            )

            errc_grid = response.choices[0].message.content
            console.print("[green]✅ ERRC grid generated[/green]")
            return errc_grid

        except Exception as e:
            console.print(f"[red]Error generating ERRC grid: {e}[/red]")
            return f"Error generating ERRC grid: {str(e)}"

    def generate_product_ideas(self, zone_name: str, errc_grid: str) -> List[Dict]:
        """Use Claude Opus to generate 10 product ideas based on ERRC grid"""
        console.print(f"[cyan]💡 Generating 10 product ideas for: {zone_name}[/cyan]")

        prompt = f"""Based on this ERRC Grid analysis for the '{zone_name}' opportunity zone:

{errc_grid}

Generate exactly 10 innovative product ideas that embody this ERRC strategy. For each idea:

1. Product Name (catchy and memorable)
2. Core Value Proposition (one sentence)
3. Key Features (3-5 bullets aligned with ERRC)
4. Target Customer Segment
5. Differentiation from Status Quo
6. Innovation Score (1-10, based on how radically it applies ERRC)

Format each idea clearly with numbered sections."""

        try:
            message = self.anthropic_client.messages.create(
                model=self.model_opus,
                max_tokens=4000,
                temperature=0.8,
                system="You are a visionary product strategist who excels at blue ocean thinking and disruptive innovation.",
                messages=[{"role": "user", "content": prompt}],
            )

            ideas_text = message.content[0].text

            # Parse ideas into structured format
            ideas = self._parse_product_ideas(ideas_text)
            console.print(f"[green]✅ Generated {len(ideas)} product ideas[/green]")
            return ideas

        except Exception as e:
            console.print(f"[red]Error generating product ideas: {e}[/red]")
            return []

    def scope_viability(self, ideas: List[Dict], zone_name: str) -> List[Dict]:
        """Use Claude Opus to evaluate viability of product ideas"""
        console.print(f"[cyan]🔍 Evaluating viability of {len(ideas)} ideas[/cyan]")

        # Prepare ideas summary for evaluation
        ideas_summary = ""
        for i, idea in enumerate(ideas, 1):
            ideas_summary += f"\n{i}. {idea.get('name', f'Idea {i}')}: {idea.get('value_proposition', 'N/A')}"

        prompt = f"""Evaluate the viability of these {len(ideas)} product ideas for the '{zone_name}' opportunity zone:

{ideas_summary}

For each idea, assess:
1. Technical Feasibility (1-10): How achievable with current/near-term technology?
2. Market Readiness (1-10): How ready is the market for this solution?
3. Resource Requirements (1-10): 10=minimal resources, 1=massive resources needed
4. Time to Market (1-10): 10=quick launch, 1=years of development
5. Competitive Moat (1-10): How defensible once launched?
6. Overall Viability Score (1-10): Weighted assessment

Provide brief rationale for each score. Also identify the top 3 critical risks for each idea.

Output in a structured format that can be parsed."""

        try:
            message = self.anthropic_client.messages.create(
                model=self.model_opus,
                max_tokens=4000,
                temperature=0.5,
                system="You are a seasoned product strategist and venture analyst with deep expertise in assessing product-market fit and go-to-market viability.",
                messages=[{"role": "user", "content": prompt}],
            )

            viability_text = message.content[0].text

            # Parse and merge viability scores with ideas
            scored_ideas = self._merge_viability_scores(ideas, viability_text)
            console.print("[green]✅ Viability assessment complete[/green]")
            return scored_ideas

        except Exception as e:
            console.print(f"[red]Error evaluating viability: {e}[/red]")
            # Return ideas with default scores if evaluation fails
            for idea in ideas:
                idea["viability_score"] = 5.0
                idea["viability_details"] = {"error": str(e)}
            return ideas

    def filter_ideas_by_percentage(
        self, ideas: List[Dict], percentage: float
    ) -> List[Dict]:
        """Filter ideas based on opportunity zone percentage"""
        # Sort by viability score
        sorted_ideas = sorted(
            ideas, key=lambda x: x.get("viability_score", 0), reverse=True
        )

        # Calculate how many ideas to keep
        ideas_to_keep = max(1, round(len(ideas) * (percentage / 100)))

        console.print(
            f"[yellow]Filtering: {len(ideas)} ideas × {percentage}% = {ideas_to_keep} ideas to keep[/yellow]"
        )

        return sorted_ideas[:ideas_to_keep]

    def _parse_product_ideas(self, ideas_text: str) -> List[Dict]:
        """Parse product ideas from text into structured format"""
        ideas = []

        # Simple parsing - split by numbers and extract key info
        idea_blocks = ideas_text.split("\n\n")
        current_idea = {}

        for block in idea_blocks:
            if any(f"{i}." in block or f"{i})" in block for i in range(1, 11)):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {
                    "name": "",
                    "value_proposition": "",
                    "features": [],
                    "target_segment": "",
                    "differentiation": "",
                    "innovation_score": 5,
                }

            # Extract information
            lines = block.strip().split("\n")
            for line in lines:
                line_lower = line.lower()
                if "product name" in line_lower or "name:" in line_lower:
                    current_idea["name"] = line.split(":", 1)[-1].strip()
                elif "value proposition" in line_lower:
                    current_idea["value_proposition"] = line.split(":", 1)[-1].strip()
                elif "innovation score" in line_lower:
                    try:
                        score = float("".join(filter(str.isdigit, line.split(":")[-1])))
                        current_idea["innovation_score"] = min(10, max(1, score))
                    except (ValueError, IndexError):
                        current_idea["innovation_score"] = 5

        if current_idea:
            ideas.append(current_idea)

        # Ensure we have exactly 10 ideas (pad if necessary)
        while len(ideas) < 10:
            ideas.append(
                {
                    "name": f"Idea {len(ideas) + 1}",
                    "value_proposition": "Placeholder idea",
                    "innovation_score": 5,
                }
            )

        return ideas[:10]

    def _merge_viability_scores(
        self, ideas: List[Dict], viability_text: str
    ) -> List[Dict]:
        """Merge viability assessment with product ideas"""
        # Simple score extraction
        for i, idea in enumerate(ideas):
            # Look for overall viability score for this idea
            search_patterns = [
                f"{i + 1}.",
                f"idea {i + 1}",
                idea.get("name", "").lower(),
            ]

            # Default scores
            idea["viability_score"] = 5.0
            idea["viability_details"] = {
                "technical_feasibility": 5,
                "market_readiness": 5,
                "resource_requirements": 5,
                "time_to_market": 5,
                "competitive_moat": 5,
            }

            # Try to find scores in text
            lines = viability_text.lower().split("\n")
            for j, line in enumerate(lines):
                if any(pattern in line for pattern in search_patterns):
                    # Look for scores in nearby lines
                    for k in range(max(0, j - 5), min(len(lines), j + 10)):
                        if "overall" in lines[k] and "viability" in lines[k]:
                            try:
                                score = float(
                                    "".join(
                                        filter(
                                            lambda x: x.isdigit() or x == ".",
                                            lines[k].split(":")[-1],
                                        )
                                    )
                                )
                                idea["viability_score"] = min(10, max(1, score))
                                break
                            except (ValueError, IndexError):
                                pass

        return ideas

    def _apply_sophisticated_scoring(
        self, ideas: List[Dict], zone_name: str
    ) -> List[Dict]:
        """Apply sophisticated scoring system to ideas"""
        enhanced_ideas = []

        for idea in ideas:
            # Add zone context
            idea["zone_name"] = zone_name

            # Calculate comprehensive scores
            idea_score = IdeaScore.from_idea_data(idea)
            breakthrough_analysis = self.breakthrough_detector.analyze_idea(
                idea, idea_score
            )
            confidence_analysis = self.confidence_scorer.calculate_confidence(
                idea, idea_score
            )

            # Add all scoring data to idea
            idea["scoring"] = {
                "idea_score": idea_score,
                "breakthrough_analysis": breakthrough_analysis,
                "confidence_analysis": confidence_analysis,
                "composite_score": confidence_analysis.adjusted_scores.get(
                    "composite_score", idea_score.composite_score
                ),
                "adjusted_scores": confidence_analysis.adjusted_scores,
                "is_excellence": idea_score.is_high_potential(),
                "is_moonshot": breakthrough_analysis.is_moonshot,
                "is_breakthrough": breakthrough_analysis.is_breakthrough,
                "risk_level": idea_score.get_risk_level(),
                "confidence_category": self.confidence_scorer.get_confidence_category(
                    confidence_analysis.overall_confidence
                ),
            }

            if self.debug_mode:
                self.debug_logger.log_operation(
                    "idea_scoring",
                    {
                        "idea_name": idea.get("name", "Unknown"),
                        "zone_name": zone_name,
                        "composite_score": idea_score.composite_score,
                        "adjusted_composite": confidence_analysis.adjusted_scores.get(
                            "composite_score", idea_score.composite_score
                        ),
                        "is_breakthrough": breakthrough_analysis.is_breakthrough,
                        "is_moonshot": breakthrough_analysis.is_moonshot,
                        "confidence_level": confidence_analysis.overall_confidence,
                    },
                )

            enhanced_ideas.append(idea)

        return enhanced_ideas

    def process_opportunity_zone(self, zone_analysis: Dict) -> Dict:
        """Process a single opportunity zone through the entire pipeline with sophisticated scoring"""
        zone = zone_analysis["zone"]
        zone_name = zone["name"]
        importance_percentage = zone.get("importance_percentage", 50)

        console.print(
            Panel.fit(
                f"[bold cyan]Processing: {zone_name}[/bold cyan]\n"
                f"Importance: {importance_percentage}%",
                border_style="cyan",
            )
        )

        if self.debug_mode:
            self.debug_logger.log_operation(
                "zone_processing_start",
                {
                    "zone_name": zone_name,
                    "importance_percentage": importance_percentage,
                },
            )

        # Step 1: Generate ERRC Grid (OpenAI o1)
        errc_grid = self.generate_errc_grid(zone_analysis)

        # Step 2: Generate Product Ideas (Claude Opus)
        product_ideas = self.generate_product_ideas(zone_name, errc_grid)

        # Step 3: Evaluate Viability (Claude Opus)
        scored_ideas = self.scope_viability(product_ideas, zone_name)

        # Step 4: Apply sophisticated scoring to all ideas
        console.print(f"[cyan]🔬 Applying sophisticated scoring system...[/cyan]")
        enhanced_ideas = self._apply_sophisticated_scoring(scored_ideas, zone_name)

        # Step 5: Basic filtering by percentage (sophisticated filtering applied later)
        filtered_ideas = self.filter_ideas_by_percentage(
            enhanced_ideas, importance_percentage
        )

        if self.debug_mode:
            self.debug_logger.log_operation(
                "zone_processing_complete",
                {
                    "zone_name": zone_name,
                    "total_ideas": len(enhanced_ideas),
                    "filtered_ideas": len(filtered_ideas),
                },
            )

        return {
            "zone": zone,
            "errc_grid": errc_grid,
            "all_ideas": enhanced_ideas,
            "filtered_ideas": filtered_ideas,
            "ideas_kept": len(filtered_ideas),
            "ideas_total": len(enhanced_ideas),
        }

    def generate_final_report(self, results: List[Dict]) -> str:
        """Generate comprehensive final report"""
        report = "# Product Innovation Pipeline Results\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Executive Summary
        total_ideas = sum(r["ideas_total"] for r in results)
        filtered_ideas = sum(r["ideas_kept"] for r in results)

        report += "## Executive Summary\n\n"
        report += f"- **Opportunity Zones Analyzed**: {len(results)}\n"
        report += f"- **Total Ideas Generated**: {total_ideas}\n"
        report += f"- **Ideas After Filtering**: {filtered_ideas}\n"
        report += (
            f"- **Average Ideas per Zone**: {filtered_ideas / len(results):.1f}\n\n"
        )

        # Top Ideas Across All Zones
        report += "## Top Product Ideas (All Zones)\n\n"

        all_filtered_ideas = []
        for result in results:
            for idea in result["filtered_ideas"]:
                idea["zone_name"] = result["zone"]["name"]
                all_filtered_ideas.append(idea)

        # Sort by viability score
        top_ideas = sorted(
            all_filtered_ideas, key=lambda x: x.get("viability_score", 0), reverse=True
        )[:5]

        for i, idea in enumerate(top_ideas, 1):
            report += f"### {i}. {idea.get('name', 'Unnamed')}\n"
            report += f"- **Zone**: {idea['zone_name']}\n"
            report += (
                f"- **Value Proposition**: {idea.get('value_proposition', 'N/A')}\n"
            )
            report += f"- **Viability Score**: {idea.get('viability_score', 0)}/10\n"
            report += (
                f"- **Innovation Score**: {idea.get('innovation_score', 0)}/10\n\n"
            )

        report += "---\n\n"

        # Detailed Results by Zone
        report += "## Detailed Results by Opportunity Zone\n\n"

        for result in results:
            zone = result["zone"]
            report += f"### {zone['name']} (Priority: {zone.get('importance_percentage', 0)}%)\n\n"

            # ERRC Grid
            report += "#### ERRC Grid\n\n"
            report += result["errc_grid"] + "\n\n"

            # Filtered Ideas
            report += f"#### Selected Ideas ({result['ideas_kept']} of {result['ideas_total']})\n\n"

            for j, idea in enumerate(result["filtered_ideas"], 1):
                report += f"**{j}. {idea.get('name', 'Unnamed')}**\n"
                report += f"- Value: {idea.get('value_proposition', 'N/A')}\n"
                report += f"- Viability: {idea.get('viability_score', 0)}/10\n"
                report += f"- Innovation: {idea.get('innovation_score', 0)}/10\n\n"

            report += "---\n\n"

        # Implementation Roadmap
        report += "## Suggested Implementation Roadmap\n\n"
        report += (
            "1. **Immediate (0-3 months)**: Focus on highest viability score ideas\n"
        )
        report += "2. **Short-term (3-6 months)**: Prototype top 2-3 concepts\n"
        report += "3. **Medium-term (6-12 months)**: Market test and iterate\n"
        report += "4. **Long-term (12+ months)**: Scale successful concepts\n"

        return report

    def save_results(
        self,
        results: List[Dict],
        report: str,
        json_output: str = "product_ideas.json",
        report_output: str = "product_ideas_report.md",
    ):
        """Save results to files"""
        # Save JSON data
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "zones_processed": len(results),
                "total_ideas": sum(r["ideas_total"] for r in results),
                "filtered_ideas": sum(r["ideas_kept"] for r in results),
            },
            "results": results,
        }

        with open(json_output, "w") as f:
            json.dump(output_data, f, indent=2)
        console.print(f"[green]✅ Results saved to {json_output}[/green]")

        # Save markdown report
        with open(report_output, "w") as f:
            f.write(report)
        console.print(f"[green]✅ Report saved to {report_output}[/green]")

    def run(
        self,
        value_curves_file: str = "value_curves.json",
        json_output: str = "product_ideas.json",
        report_output: str = "product_ideas_report.md",
        create_github_repo: bool = False,
        github_repo_name: str = "market-research-insights",
        github_private: bool = False,
    ):
        """Main execution flow with sophisticated scoring and selection"""
        console.print(
            Panel.fit(
                "[bold green]Product Idea Generation Pipeline with Sophisticated Scoring[/bold green]\n"
                "ERRC → Ideas → Viability → Scoring → Smart Filtering → Selection → Optimization",
                border_style="green",
            )
        )

        if self.debug_mode:
            self.debug_logger.log_operation(
                "pipeline_start",
                {
                    "input_file": value_curves_file,
                    "output_files": {"json": json_output, "report": report_output},
                },
            )

        # Load value curves
        value_curves_data = self.load_value_curves(value_curves_file)
        analyses = value_curves_data.get("analyses", [])

        if not analyses:
            console.print("[red]Error: No analyses found in value curves file[/red]")
            sys.exit(1)

        console.print(
            f"\n[cyan]Found {len(analyses)} opportunity zones to process[/cyan]"
        )

        # Step 1: Process each zone with basic scoring
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=False,
        ) as progress:
            task = progress.add_task("Processing zones...", total=len(analyses))

            for analysis in analyses:
                zone_name = analysis["zone"]["name"]
                progress.update(task, description=f"Processing {zone_name}...")

                result = self.process_opportunity_zone(analysis)
                results.append(result)

                progress.update(task, advance=1)

        # Step 2: Apply smart filtering across all zones
        console.print(
            "\n[cyan]🧠 Applying smart filtering with excellence preservation...[/cyan]"
        )
        filtering_results = self.smart_filterer.filter_ideas(results)

        if self.debug_mode:
            self.debug_logger.log_operation(
                "smart_filtering_complete",
                {
                    "total_selected": len(filtering_results.selected_ideas),
                    "excellence_preserved": len(filtering_results.excellence_preserved),
                    "warnings": len(filtering_results.warnings),
                },
            )

        # Step 3: Apply final selection with ensemble approach
        console.print(
            "[cyan]🎯 Applying final selection with ensemble strategies...[/cyan]"
        )
        final_selection_results = self.final_selector.select_final_ideas(
            filtering_results
        )

        # Step 4: Cross-zone portfolio optimization
        console.print("[cyan]⚡ Optimizing portfolio across zones...[/cyan]")
        optimization_results = self.cross_zone_optimizer.optimize_portfolio(
            final_selection_results.final_selection
        )

        # Step 5: Generate comprehensive report
        console.print("\n[cyan]📊 Generating comprehensive selection report...[/cyan]")
        comprehensive_report = self.selection_reporter.generate_report(
            results, filtering_results, final_selection_results, optimization_results
        )

        # Step 6: Generate traditional report for compatibility
        traditional_report = self.generate_final_report(results)

        # Step 7: Save all results
        self._save_comprehensive_results(
            results,
            filtering_results,
            final_selection_results,
            optimization_results,
            comprehensive_report,
            traditional_report,
            json_output,
            report_output,
            create_github_repo,
            github_repo_name,
            github_private,
            value_curves_file,
        )

        # Display comprehensive summary
        self._display_comprehensive_summary(
            results,
            filtering_results,
            final_selection_results,
            optimization_results,
            comprehensive_report,
            report_output,
        )

        if self.debug_mode:
            self.debug_logger.log_operation(
                "pipeline_complete",
                {
                    "zones_processed": len(results),
                    "final_selection_count": len(
                        final_selection_results.final_selection
                    ),
                    "optimization_applied": optimization_results is not None,
                },
            )

    def _save_comprehensive_results(
        self,
        zone_results,
        filtering_results,
        final_selection_results,
        optimization_results,
        comprehensive_report,
        traditional_report,
        json_output: str,
        report_output: str,
        create_github_repo: bool = False,
        github_repo_name: str = "market-research-insights",
        github_private: bool = False,
        value_curves_file: str = "value_curves.json",
    ):
        """Save all comprehensive results"""

        # Save comprehensive JSON data
        comprehensive_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "pipeline_version": "sophisticated_scoring_v5",
                "zones_processed": len(zone_results),
                "scoring_features": [
                    "multi_dimensional_scoring",
                    "breakthrough_detection",
                    "smart_filtering",
                    "ensemble_selection",
                    "portfolio_optimization",
                ],
            },
            "zone_results": self._serialize_results(zone_results),
            "filtering_results": self._serialize_filtering_results(filtering_results),
            "final_selection": self._serialize_final_selection(final_selection_results),
            "optimization_results": optimization_results,
            "comprehensive_report": comprehensive_report,
            "traditional_results": self._serialize_results(
                zone_results
            ),  # For backward compatibility
        }

        # Save comprehensive JSON
        comprehensive_json_path = json_output.replace(".json", "_comprehensive.json")
        with open(comprehensive_json_path, "w") as f:
            json.dump(comprehensive_data, f, indent=2, default=str)
        console.print(
            f"[green]✅ Comprehensive results saved to {comprehensive_json_path}[/green]"
        )

        # Save traditional JSON for compatibility
        traditional_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "zones_processed": len(zone_results),
                "total_ideas": sum(r["ideas_total"] for r in zone_results),
                "filtered_ideas": sum(r["ideas_kept"] for r in zone_results),
            },
            "results": zone_results,
        }

        with open(json_output, "w") as f:
            json.dump(traditional_data, f, indent=2, default=str)
        console.print(f"[green]✅ Traditional results saved to {json_output}[/green]")

        # Save comprehensive markdown report
        comprehensive_md_path = report_output.replace(".md", "_comprehensive.md")
        comprehensive_md = self.selection_reporter.export_report_markdown(
            comprehensive_report
        )
        with open(comprehensive_md_path, "w") as f:
            f.write(comprehensive_md)
        console.print(
            f"[green]✅ Comprehensive report saved to {comprehensive_md_path}[/green]"
        )

        # Save traditional markdown report
        with open(report_output, "w") as f:
            f.write(traditional_report)
        console.print(f"[green]✅ Traditional report saved to {report_output}[/green]")

        # Create GitHub repository if requested
        if create_github_repo:
            console.print(
                "\n[cyan]📊 Creating GitHub repository with analysis results...[/cyan]"
            )

            # Load necessary data for GitHub integration
            # We need research analysis, JTBD data, zones data, and ideas data

            # Get comprehensive_data that was just saved
            with open(comprehensive_json_path, "r") as f:
                comprehensive_data = json.load(f)

            # Load JTBD data from the pipeline
            jtbd_file = "jobs_to_be_done.json"
            if os.path.exists(jtbd_file):
                with open(jtbd_file, "r") as f:
                    jtbd_data = json.load(f)
            else:
                jtbd_data = {"jtbd_data": {"jobs_list": []}}

            # Load research analysis
            research_file = "research_analysis.json"
            if os.path.exists(research_file):
                with open(research_file, "r") as f:
                    research_analysis = json.load(f)
            else:
                research_analysis = {"executive_summary": "Market research analysis"}

            # Load zones data (from value curves)
            zones_data = {"clustered_zones": {}}
            if os.path.exists(value_curves_file):
                with open(value_curves_file, "r") as f:
                    value_curves_data = json.load(f)
                    # Convert value curves analyses to zones format
                    for i, analysis in enumerate(value_curves_data.get("analyses", [])):
                        zones_data["clustered_zones"][f"zone_{i + 1}"] = {
                            "name": analysis.get("zone_name", f"Zone {i + 1}"),
                            "market_size": analysis.get("market_size", "N/A"),
                            "pain_level": analysis.get("pain_level", "medium"),
                            "key_themes": analysis.get("key_themes", []),
                            "competitive_intensity": analysis.get(
                                "competitive_intensity", "medium"
                            ),
                        }

            # Convert our product ideas format to the expected format
            ideas_data = {
                "product_ideas": [],
                "consolidation_analysis": {},  # No consolidation analysis in this pipeline
                "viability_analysis": {
                    "market_assessment": comprehensive_data.get(
                        "comprehensive_report", {}
                    ).get("market_summary", {}),
                    "financial_projections": comprehensive_data.get(
                        "comprehensive_report", {}
                    ).get("financial_summary", {}),
                },
            }

            # Extract all ideas from comprehensive data
            for zone_result in comprehensive_data.get("traditional_results", []):
                for idea in zone_result.get("filtered_ideas", []):
                    ideas_data["product_ideas"].append(idea)

            # Track start time for processing duration
            import datetime
            pipeline_start_time = datetime.datetime.now()
            
            # Create appendix files list
            appendix_files_to_upload = [
                (value_curves_file, "Stage 4: Value Curve Analysis"),
                (json_output, "Stage 5: Product Ideas"),
                (comprehensive_json_path, "Stage 5: Comprehensive Analysis"),
                (report_output, "Stage 5: Product Ideas Report"),
            ]
            
            # Add other pipeline files if they exist
            other_files = [
                ("analysis_results.md", "Stage 1: Market Research Analysis"),
                ("jtbd_research.md", "Stage 2: Jobs-to-be-Done Research"),
                ("jtbd_research_pain_points.txt", "Stage 2: Extracted Pain Points"),
                ("opportunity_zones.json", "Stage 3: Clustered Opportunity Zones"),
                ("value_curves_report.md", "Stage 4: Value Curve Report"),
                ("jobs_to_be_done.json", "Structured JTBD Data"),
                ("research_analysis.json", "Research Summary Data"),
            ]
            
            for filename, description in other_files:
                if os.path.exists(filename) and filename not in [f[0] for f in appendix_files_to_upload]:
                    appendix_files_to_upload.append((filename, description))
            
            # Use enhanced GitHub integration
            try:
                # Initialize enhanced GitHub integration
                github_token = os.getenv("GITHUB_TOKEN")
                organization = "ocean-shark-tank"  # Default organization
                
                enhanced_github = EnhancedGitHubIntegration(github_token, organization)
                
                # Create repository
                repo = enhanced_github.create_repository(
                    repo_name=github_repo_name,
                    description="AI-powered innovation pipeline results with market research, JTBD analysis, and product recommendations",
                    private=github_private
                )
                
                # Create labels
                enhanced_github.create_labels(repo)
                
                # Upload appendix files
                console.print("
[cyan]📁 Creating appendix with research documents...[/cyan]")
                uploaded_files = []
                for filename, description in appendix_files_to_upload:
                    if os.path.exists(filename):
                        try:
                            with open(filename, 'r') as f:
                                file_content = f.read()
                            
                            path = f"appendix/{filename}"
                            repo.create_file(
                                path=path,
                                message=f"Add {description} to appendix",
                                content=file_content,
                                branch="main"
                            )
                            uploaded_files.append((path, description))
                            console.print(f"  ✓ Uploaded {path}")
                            import time
                            time.sleep(0.5)  # Rate limiting
                        except Exception as e:
                            console.print(f"  ✗ Error uploading {filename}: {e}")
                
                # Load pipeline data
                pipeline_data = {
                    "research_analysis": research_analysis,
                    "jtbd_data": jtbd_data,
                    "zones_data": zones_data,
                    "value_curves": {},
                    "product_ideas": ideas_data
                }
                
                # Generate enhanced README
                readme_content = enhanced_github.generate_enhanced_readme(
                    pipeline_data, 
                    github_repo_name, 
                    uploaded_files, 
                    pipeline_start_time
                )
                
                # Create README
                repo.create_file(
                    path="README.md",
                    message="Add comprehensive innovation analysis with full documentation",
                    content=readme_content,
                    branch="main"
                )
                console.print("  ✓ Created enhanced README.md")
                
                # Create issues for product ideas
                console.print("
[cyan]💡 Creating product idea issues...[/cyan]")
                issues_created = 0
                
                for i, idea in enumerate(ideas_data.get("product_ideas", []), 1):
                    try:
                        issue_data = enhanced_github.create_issue_content(idea, i)
                        
                        # Determine labels
                        issue_labels = ["product-idea"]
                        
                        # Add priority based on innovation score
                        innovation = idea.get("innovation_score", idea.get("market_opportunity", 5))
                        if innovation >= 7:
                            issue_labels.append("high-priority")
                        elif innovation >= 5:
                            issue_labels.append("medium-priority")
                        else:
                            issue_labels.append("low-priority")
                        
                        # Create the issue
                        issue = repo.create_issue(
                            title=issue_data["title"],
                            body=issue_data["body"],
                            labels=issue_labels
                        )
                        
                        console.print(f"  ✓ Created issue #{issue.number}: {issue.title}")
                        issues_created += 1
                        import time
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        console.print(f"  ✗ Error creating issue for {idea.get('name', f'idea {i}')}: {e}")
                
                console.print(
                    f"[green]✅ Enhanced GitHub repository created: {repo.html_url}[/green]"
                )
                console.print(
                    f"[green]✅ Created {issues_created} issues with {len(uploaded_files)} appendix documents[/green]"
                )
                
            except Exception as e:
                console.print(f"[red]❌ GitHub integration error: {str(e)}[/red]")
                console.print(
                    "[yellow]Make sure GITHUB_TOKEN environment variable is set[/yellow]"
                )

    def _serialize_results(self, results):
        """Serialize results for JSON output"""
        serialized = []
        for result in results:
            serialized_result = result.copy()
            # Convert complex objects to dictionaries
            if "all_ideas" in serialized_result:
                serialized_result["all_ideas"] = [
                    self._serialize_idea(idea)
                    for idea in serialized_result["all_ideas"]
                ]
            if "filtered_ideas" in serialized_result:
                serialized_result["filtered_ideas"] = [
                    self._serialize_idea(idea)
                    for idea in serialized_result["filtered_ideas"]
                ]
            serialized.append(serialized_result)
        return serialized

    def _serialize_idea(self, idea):
        """Serialize idea for JSON output"""
        serialized_idea = idea.copy()
        if "scoring" in serialized_idea:
            scoring = serialized_idea["scoring"]
            # Convert scoring objects to dictionaries
            if hasattr(scoring.get("idea_score"), "to_dict"):
                scoring["idea_score"] = scoring["idea_score"].to_dict()
            # Convert other complex objects to dictionaries using their __dict__
            for key, value in scoring.items():
                if hasattr(value, "__dict__") and not isinstance(
                    value, (str, int, float, bool, list, dict)
                ):
                    scoring[key] = value.__dict__
        return serialized_idea

    def _serialize_filtering_results(self, filtering_results):
        """Serialize filtering results"""
        return {
            "selected_ideas": [
                self._serialize_idea(idea) for idea in filtering_results.selected_ideas
            ],
            "dropped_ideas": [
                self._serialize_idea(idea) for idea in filtering_results.dropped_ideas
            ],
            "excellence_preserved": [
                self._serialize_idea(idea)
                for idea in filtering_results.excellence_preserved
            ],
            "quota_adjustments": filtering_results.quota_adjustments,
            "filtering_stats": filtering_results.filtering_stats,
            "warnings": filtering_results.warnings,
        }

    def _serialize_final_selection(self, final_results):
        """Serialize final selection results"""
        return {
            "final_selection": [
                self._serialize_idea(idea) for idea in final_results.final_selection
            ],
            "ensemble_strategies": [
                strategy.__dict__ for strategy in final_results.ensemble_strategies
            ],
            "consensus_analysis": final_results.consensus_analysis,
            "safety_checks": final_results.safety_checks,
            "warnings": final_results.warnings,
            "selection_confidence": final_results.selection_confidence,
            "dropped_high_value_ideas": final_results.dropped_high_value_ideas,
        }

    def _display_comprehensive_summary(
        self,
        zone_results,
        filtering_results,
        final_selection_results,
        optimization_results,
        comprehensive_report,
        report_output: str,
    ):
        """Display comprehensive summary of the pipeline"""

        # Basic stats
        total_ideas = sum(r["ideas_total"] for r in zone_results)
        filtered_ideas = len(filtering_results.selected_ideas)
        final_ideas = len(final_selection_results.final_selection)

        # Excellence and breakthrough stats
        excellence_preserved = len(filtering_results.excellence_preserved)
        breakthrough_count = sum(
            1
            for idea in final_selection_results.final_selection
            if idea.get("scoring", {}).get("is_breakthrough", False)
        )
        moonshot_count = sum(
            1
            for idea in final_selection_results.final_selection
            if idea.get("scoring", {}).get("is_moonshot", False)
        )

        # Quality metrics
        exec_summary = comprehensive_report["executive_summary"]
        quality_improvement = exec_summary["process_overview"]["quality_improvement"]
        selection_confidence = final_selection_results.selection_confidence

        # Warnings
        total_warnings = len(filtering_results.warnings) + len(
            final_selection_results.warnings
        )

        console.print(
            Panel(
                f"🎯 [bold green]Sophisticated Scoring Pipeline Complete![/bold green]\n\n"
                f"📊 [bold]Processing Results:[/bold]\n"
                f"  • Zones processed: {len(zone_results)}\n"
                f"  • Ideas generated: {total_ideas}\n"
                f"  • After smart filtering: {filtered_ideas}\n"
                f"  • Final selection: {final_ideas}\n"
                f"  • Overall reduction: {(1 - final_ideas / total_ideas) * 100:.1f}%\n\n"
                f"⭐ [bold]Quality Metrics:[/bold]\n"
                f"  • Excellence ideas preserved: {excellence_preserved}\n"
                f"  • Breakthrough ideas: {breakthrough_count}\n"
                f"  • Moonshot ideas: {moonshot_count}\n"
                f"  • Quality improvement: {quality_improvement}\n"
                f"  • Selection confidence: {selection_confidence:.1f}/10\n\n"
                f"🎯 [bold]Portfolio Optimization:[/bold]\n"
                f"  • Strategies applied: {len(final_selection_results.ensemble_strategies)}\n"
                f"  • Portfolio balance: {optimization_results['optimized_metrics'].overall_balance:.1f}/10\n"
                f"  • Technical synergy: {optimization_results['optimized_metrics'].technical_synergy:.1f}/10\n\n"
                f"⚠️  [bold]Warnings & Alerts:[/bold] {total_warnings}\n\n"
                f"📋 [bold]Reports Generated:[/bold]\n"
                f"  • Comprehensive report: {report_output.replace('.md', '_comprehensive.md')}\n"
                f"  • Traditional report: {report_output}\n"
                f"  • JSON data: {report_output.replace('.md', '.json')}",
                title="🚀 Sophisticated Scoring Results",
                border_style="green",
            )
        )

        # Display warnings if any
        if total_warnings > 0:
            console.print(
                f"\n[yellow]⚠️  {total_warnings} warnings generated. Check reports for details.[/yellow]"
            )

        # Display top ideas
        if final_selection_results.final_selection:
            console.print(f"\n[cyan]🏆 Top 3 Selected Ideas:[/cyan]")

            sorted_final = sorted(
                final_selection_results.final_selection,
                key=lambda x: x.get("scoring", {}).get("composite_score", 0),
                reverse=True,
            )

            for i, idea in enumerate(sorted_final[:3], 1):
                name = idea.get("name", "Unknown")
                score = idea.get("scoring", {}).get("composite_score", 0)
                zone = idea.get("zone_name", "Unknown")
                is_breakthrough = (
                    "🚀"
                    if idea.get("scoring", {}).get("is_breakthrough", False)
                    else ""
                )
                is_moonshot = (
                    "🌙" if idea.get("scoring", {}).get("is_moonshot", False) else ""
                )

                console.print(
                    f"  {i}. [bold]{name}[/bold] {is_breakthrough}{is_moonshot}"
                )
                console.print(f"     Zone: {zone} | Score: {score:.2f}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate and filter product ideas based on value curve analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process value curves from default file
  python product_idea_generator.py
  
  # Custom input and output files
  python product_idea_generator.py --input my_curves.json --json-output ideas.json --report-output ideas.md
  
  # Create GitHub repository with results
  python product_idea_generator.py --github --repo-name "my-product-ideas"
  
  # Create private GitHub repository
  python product_idea_generator.py --github --repo-name "my-product-ideas" --github-private
  
  # Test API connections
  python product_idea_generator.py --test
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="value_curves.json",
        help="Input value curves JSON file",
    )
    parser.add_argument(
        "--json-output", type=str, default="product_ideas.json", help="Output JSON file"
    )
    parser.add_argument(
        "--report-output",
        type=str,
        default="product_ideas_report.md",
        help="Output report file",
    )
    parser.add_argument("--test", action="store_true", help="Test API connections")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with detailed logging"
    )

    # GitHub integration arguments
    parser.add_argument(
        "--github", action="store_true", help="Create GitHub repository with results"
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        default="market-research-insights",
        help="GitHub repository name (default: market-research-insights)",
    )
    parser.add_argument(
        "--github-private", action="store_true", help="Create private GitHub repository"
    )

    args = parser.parse_args()

    # Initialize generator with debug mode
    generator = ProductIdeaGenerator(debug_mode=args.debug)

    if args.debug:
        console.print(
            "[yellow]🐛 Debug mode enabled - detailed logging activated[/yellow]"
        )

    if args.test:
        # Test mode
        console.print("[cyan]Testing API connections...[/cyan]")

        # Test OpenAI
        try:
            response = generator.openai_client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for test since o1 might have restrictions
                messages=[{"role": "user", "content": "Say 'OpenAI connected!'"}],
                max_tokens=10,
            )
            console.print(
                f"[green]✅ OpenAI: {response.choices[0].message.content}[/green]"
            )
        except Exception as e:
            console.print(f"[red]❌ OpenAI test failed: {e}[/red]")

        # Test Anthropic Opus
        try:
            response = generator.anthropic_client.messages.create(
                model=generator.model_opus,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Opus connected!'"}],
            )
            console.print(f"[green]✅ Claude Opus: {response.content[0].text}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Opus test failed: {e}[/red]")

        return

    # Run product idea generation
    generator.run(
        args.input,
        args.json_output,
        args.report_output,
        create_github_repo=args.github,
        github_repo_name=args.repo_name,
        github_private=args.github_private,
    )


if __name__ == "__main__":
    main()
