#!/usr/bin/env python3
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

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()

class ProductIdeaGenerator:
    """Generate and filter product ideas based on value curve analysis"""
    
    def __init__(self):
        """Initialize API clients"""
        # OpenAI setup for o1 model
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            console.print("[red]Error: OPENAI_API_KEY not found![/red]")
            sys.exit(1)
        
        try:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            self.model_o1 = "o1-preview"  # Using o1-preview for advanced reasoning
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
            with open(filepath, 'r') as f:
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
        zone_name = zone_analysis['zone']['name']
        console.print(f"\n[cyan]🧠 Generating ERRC grid for: {zone_name}[/cyan]")
        
        # Prepare context from value curve analysis
        context = f"""Opportunity Zone: {zone_name}
Description: {zone_analysis['zone'].get('description', '')}
Importance: {zone_analysis['zone'].get('importance_percentage', 0)}%

Industry Norms & Sacred Cows:
{zone_analysis.get('industry_norms', 'Not available')}

Engineering Spectrum Analysis:
{zone_analysis.get('engineering_spectrum', 'Not available')}

Competitive Intelligence Summary:
"""
        
        # Add competitive data if available
        comp_data = zone_analysis.get('competitive_data', {})
        for i, result in enumerate(comp_data.get('search_results', [])[:3], 1):
            context += f"\n{i}. {result.get('title', 'N/A')}"
            if result.get('highlights'):
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
                messages=[
                    {"role": "user", "content": context + "\n\n" + prompt}
                ],
                temperature=1.0  # o1 models use fixed temperature
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
                messages=[
                    {"role": "user", "content": prompt}
                ]
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
                messages=[
                    {"role": "user", "content": prompt}
                ]
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
                idea['viability_score'] = 5.0
                idea['viability_details'] = {"error": str(e)}
            return ideas
    
    def filter_ideas_by_percentage(self, ideas: List[Dict], percentage: float) -> List[Dict]:
        """Filter ideas based on opportunity zone percentage"""
        # Sort by viability score
        sorted_ideas = sorted(ideas, key=lambda x: x.get('viability_score', 0), reverse=True)
        
        # Calculate how many ideas to keep
        ideas_to_keep = max(1, round(len(ideas) * (percentage / 100)))
        
        console.print(f"[yellow]Filtering: {len(ideas)} ideas × {percentage}% = {ideas_to_keep} ideas to keep[/yellow]")
        
        return sorted_ideas[:ideas_to_keep]
    
    def _parse_product_ideas(self, ideas_text: str) -> List[Dict]:
        """Parse product ideas from text into structured format"""
        ideas = []
        
        # Simple parsing - split by numbers and extract key info
        idea_blocks = ideas_text.split('\n\n')
        current_idea = {}
        
        for block in idea_blocks:
            if any(f"{i}." in block or f"{i})" in block for i in range(1, 11)):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {
                    'name': '',
                    'value_proposition': '',
                    'features': [],
                    'target_segment': '',
                    'differentiation': '',
                    'innovation_score': 5
                }
            
            # Extract information
            lines = block.strip().split('\n')
            for line in lines:
                line_lower = line.lower()
                if 'product name' in line_lower or 'name:' in line_lower:
                    current_idea['name'] = line.split(':', 1)[-1].strip()
                elif 'value proposition' in line_lower:
                    current_idea['value_proposition'] = line.split(':', 1)[-1].strip()
                elif 'innovation score' in line_lower:
                    try:
                        score = float(''.join(filter(str.isdigit, line.split(':')[-1])))
                        current_idea['innovation_score'] = min(10, max(1, score))
                    except:
                        current_idea['innovation_score'] = 5
        
        if current_idea:
            ideas.append(current_idea)
        
        # Ensure we have exactly 10 ideas (pad if necessary)
        while len(ideas) < 10:
            ideas.append({
                'name': f'Idea {len(ideas) + 1}',
                'value_proposition': 'Placeholder idea',
                'innovation_score': 5
            })
        
        return ideas[:10]
    
    def _merge_viability_scores(self, ideas: List[Dict], viability_text: str) -> List[Dict]:
        """Merge viability assessment with product ideas"""
        # Simple score extraction
        for i, idea in enumerate(ideas):
            # Look for overall viability score for this idea
            search_patterns = [
                f"{i+1}.",
                f"idea {i+1}",
                idea.get('name', '').lower()
            ]
            
            # Default scores
            idea['viability_score'] = 5.0
            idea['viability_details'] = {
                'technical_feasibility': 5,
                'market_readiness': 5,
                'resource_requirements': 5,
                'time_to_market': 5,
                'competitive_moat': 5
            }
            
            # Try to find scores in text
            lines = viability_text.lower().split('\n')
            for j, line in enumerate(lines):
                if any(pattern in line for pattern in search_patterns):
                    # Look for scores in nearby lines
                    for k in range(max(0, j-5), min(len(lines), j+10)):
                        if 'overall' in lines[k] and 'viability' in lines[k]:
                            try:
                                score = float(''.join(filter(lambda x: x.isdigit() or x == '.', lines[k].split(':')[-1])))
                                idea['viability_score'] = min(10, max(1, score))
                                break
                            except:
                                pass
        
        return ideas
    
    def process_opportunity_zone(self, zone_analysis: Dict) -> Dict:
        """Process a single opportunity zone through the entire pipeline"""
        zone = zone_analysis['zone']
        zone_name = zone['name']
        importance_percentage = zone.get('importance_percentage', 50)
        
        console.print(Panel.fit(
            f"[bold cyan]Processing: {zone_name}[/bold cyan]\n"
            f"Importance: {importance_percentage}%",
            border_style="cyan"
        ))
        
        # Step 1: Generate ERRC Grid (OpenAI o1)
        errc_grid = self.generate_errc_grid(zone_analysis)
        
        # Step 2: Generate Product Ideas (Claude Opus)
        product_ideas = self.generate_product_ideas(zone_name, errc_grid)
        
        # Step 3: Evaluate Viability (Claude Opus)
        scored_ideas = self.scope_viability(product_ideas, zone_name)
        
        # Step 4: Filter by Percentage
        filtered_ideas = self.filter_ideas_by_percentage(scored_ideas, importance_percentage)
        
        return {
            'zone': zone,
            'errc_grid': errc_grid,
            'all_ideas': scored_ideas,
            'filtered_ideas': filtered_ideas,
            'ideas_kept': len(filtered_ideas),
            'ideas_total': len(scored_ideas)
        }
    
    def generate_final_report(self, results: List[Dict]) -> str:
        """Generate comprehensive final report"""
        report = "# Product Innovation Pipeline Results\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Executive Summary
        total_ideas = sum(r['ideas_total'] for r in results)
        filtered_ideas = sum(r['ideas_kept'] for r in results)
        
        report += "## Executive Summary\n\n"
        report += f"- **Opportunity Zones Analyzed**: {len(results)}\n"
        report += f"- **Total Ideas Generated**: {total_ideas}\n"
        report += f"- **Ideas After Filtering**: {filtered_ideas}\n"
        report += f"- **Average Ideas per Zone**: {filtered_ideas / len(results):.1f}\n\n"
        
        # Top Ideas Across All Zones
        report += "## Top Product Ideas (All Zones)\n\n"
        
        all_filtered_ideas = []
        for result in results:
            for idea in result['filtered_ideas']:
                idea['zone_name'] = result['zone']['name']
                all_filtered_ideas.append(idea)
        
        # Sort by viability score
        top_ideas = sorted(all_filtered_ideas, key=lambda x: x.get('viability_score', 0), reverse=True)[:5]
        
        for i, idea in enumerate(top_ideas, 1):
            report += f"### {i}. {idea.get('name', 'Unnamed')}\n"
            report += f"- **Zone**: {idea['zone_name']}\n"
            report += f"- **Value Proposition**: {idea.get('value_proposition', 'N/A')}\n"
            report += f"- **Viability Score**: {idea.get('viability_score', 0)}/10\n"
            report += f"- **Innovation Score**: {idea.get('innovation_score', 0)}/10\n\n"
        
        report += "---\n\n"
        
        # Detailed Results by Zone
        report += "## Detailed Results by Opportunity Zone\n\n"
        
        for result in results:
            zone = result['zone']
            report += f"### {zone['name']} (Priority: {zone.get('importance_percentage', 0)}%)\n\n"
            
            # ERRC Grid
            report += "#### ERRC Grid\n\n"
            report += result['errc_grid'] + "\n\n"
            
            # Filtered Ideas
            report += f"#### Selected Ideas ({result['ideas_kept']} of {result['ideas_total']})\n\n"
            
            for j, idea in enumerate(result['filtered_ideas'], 1):
                report += f"**{j}. {idea.get('name', 'Unnamed')}**\n"
                report += f"- Value: {idea.get('value_proposition', 'N/A')}\n"
                report += f"- Viability: {idea.get('viability_score', 0)}/10\n"
                report += f"- Innovation: {idea.get('innovation_score', 0)}/10\n\n"
            
            report += "---\n\n"
        
        # Implementation Roadmap
        report += "## Suggested Implementation Roadmap\n\n"
        report += "1. **Immediate (0-3 months)**: Focus on highest viability score ideas\n"
        report += "2. **Short-term (3-6 months)**: Prototype top 2-3 concepts\n"
        report += "3. **Medium-term (6-12 months)**: Market test and iterate\n"
        report += "4. **Long-term (12+ months)**: Scale successful concepts\n"
        
        return report
    
    def save_results(self, results: List[Dict], report: str,
                    json_output: str = "product_ideas.json",
                    report_output: str = "product_ideas_report.md"):
        """Save results to files"""
        # Save JSON data
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "zones_processed": len(results),
                "total_ideas": sum(r['ideas_total'] for r in results),
                "filtered_ideas": sum(r['ideas_kept'] for r in results)
            },
            "results": results
        }
        
        with open(json_output, 'w') as f:
            json.dump(output_data, f, indent=2)
        console.print(f"[green]✅ Results saved to {json_output}[/green]")
        
        # Save markdown report
        with open(report_output, 'w') as f:
            f.write(report)
        console.print(f"[green]✅ Report saved to {report_output}[/green]")
    
    def run(self, value_curves_file: str = "value_curves.json",
            json_output: str = "product_ideas.json",
            report_output: str = "product_ideas_report.md"):
        """Main execution flow"""
        console.print(Panel.fit(
            "[bold green]Product Idea Generation Pipeline[/bold green]\n"
            "ERRC Analysis → Idea Generation → Viability Scoring → Filtering",
            border_style="green"
        ))
        
        # Load value curves
        value_curves_data = self.load_value_curves(value_curves_file)
        analyses = value_curves_data.get('analyses', [])
        
        if not analyses:
            console.print("[red]Error: No analyses found in value curves file[/red]")
            sys.exit(1)
        
        console.print(f"\n[cyan]Found {len(analyses)} opportunity zones to process[/cyan]")
        
        # Process each zone
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=False
        ) as progress:
            
            task = progress.add_task("Processing zones...", total=len(analyses))
            
            for analysis in analyses:
                zone_name = analysis['zone']['name']
                progress.update(task, description=f"Processing {zone_name}...")
                
                result = self.process_opportunity_zone(analysis)
                results.append(result)
                
                progress.update(task, advance=1)
        
        # Generate report
        console.print("\n[cyan]📊 Generating final report...[/cyan]")
        report = self.generate_final_report(results)
        
        # Save results
        self.save_results(results, report, json_output, report_output)
        
        # Display summary
        total_ideas = sum(r['ideas_total'] for r in results)
        filtered_ideas = sum(r['ideas_kept'] for r in results)
        
        console.print(Panel(
            f"✅ Pipeline complete!\n\n"
            f"• Zones processed: {len(results)}\n"
            f"• Ideas generated: {total_ideas}\n"
            f"• Ideas after filtering: {filtered_ideas}\n"
            f"• Reduction rate: {(1 - filtered_ideas/total_ideas)*100:.1f}%\n\n"
            f"Top ideas saved to: {report_output}",
            title="Product Innovation Results",
            border_style="green"
        ))

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
  
  # Test API connections
  python product_idea_generator.py --test
        """
    )
    
    parser.add_argument("--input", type=str, default="value_curves.json",
                       help="Input value curves JSON file")
    parser.add_argument("--json-output", type=str, default="product_ideas.json",
                       help="Output JSON file")
    parser.add_argument("--report-output", type=str, default="product_ideas_report.md",
                       help="Output report file")
    parser.add_argument("--test", action="store_true", help="Test API connections")
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = ProductIdeaGenerator()
    
    if args.test:
        # Test mode
        console.print("[cyan]Testing API connections...[/cyan]")
        
        # Test OpenAI
        try:
            response = generator.openai_client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for test since o1 might have restrictions
                messages=[{"role": "user", "content": "Say 'OpenAI connected!'"}],
                max_tokens=10
            )
            console.print(f"[green]✅ OpenAI: {response.choices[0].message.content}[/green]")
        except Exception as e:
            console.print(f"[red]❌ OpenAI test failed: {e}[/red]")
        
        # Test Anthropic Opus
        try:
            response = generator.anthropic_client.messages.create(
                model=generator.model_opus,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Opus connected!'"}]
            )
            console.print(f"[green]✅ Claude Opus: {response.content[0].text}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Opus test failed: {e}[/red]")
        
        return
    
    # Run product idea generation
    generator.run(args.input, args.json_output, args.report_output)

if __name__ == "__main__":
    main()