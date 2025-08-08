#!/usr/bin/env python3
"""
Product Idea Generator - Innovation Creation & GitHub Publishing

This module represents the culmination of the innovation pipeline, transforming 
opportunity zones into concrete product ideas with sophisticated scoring and 
automatic GitHub repository creation.

Key Features:
- Generates ERRC (Eliminate-Reduce-Raise-Create) grids for strategic positioning
- Creates 10 product ideas per opportunity zone using Claude Opus
- Evaluates viability with multi-dimensional scoring (market, technical, competitive)
- Applies smart filtering based on zone importance percentages
- Publishes complete innovation portfolio to GitHub with issues for each idea

Sophisticated Scoring System:
- IdeaScore: Comprehensive scoring across multiple dimensions
- BreakthroughDetector: Identifies potential game-changers
- SmartFilterer: Dynamically adjusts filtering based on zone importance
- CrossZoneOptimizer: Finds synergies across multiple zones
- ConfidenceScorer: Calculates confidence levels for each idea
- FinalSelector: Makes strategic selection decisions

GitHub Integration:
- Creates comprehensive README with all research insights
- Generates individual issues for each product idea
- Applies smart labeling (priority, category, phase)
- Links issues back to source JTBDs and opportunity zones

Recent Fixes (Dec 2024):
- Fixed GitHub integration method call from create_research_repository to create_github_project
- Corrected parameter passing for repository creation
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Tuple, Optional, Any
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
        
        # GPT-5 model for high-intelligence synthesis
        self.model_gpt5 = "gpt-5"

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

    def synthesize_innovation_portfolio_gpt5(
        self, 
        final_selection: List[Dict],
        zone_results: List[Dict],
        filtering_results: Any,
        optimization_results: Dict,
        jtbd_data: Dict = None,
        research_analysis: Dict = None
    ) -> Dict:
        """
        Use GPT-5 with maximum context for ultra-high-intelligence portfolio synthesis.
        This leverages GPT-5's advanced reasoning capabilities to identify breakthrough opportunities.
        """
        console.print("[cyan]🧠 Invoking GPT-5 for ultra-high-intelligence portfolio synthesis...[/cyan]")
        
        # Prepare comprehensive context - inject EVERYTHING we know
        
        # 1. Full idea details with all scoring and metadata
        ideas_full_context = []
        for idea in final_selection[:10]:  # Top 10 ideas
            idea_context = {
                "name": idea.get("name"),
                "zone": idea.get("zone_name"),
                "value_proposition": idea.get("value_proposition"),
                "description": idea.get("description", ""),
                "key_features": idea.get("key_features", []),
                "target_market": idea.get("target_market"),
                "scores": {
                    "viability": idea.get("viability_score", 0),
                    "innovation": idea.get("innovation_score", 0),
                    "composite": idea.get("scoring", {}).get("composite_score", 0),
                    "market_opportunity": idea.get("market_opportunity", 0),
                    "technical_feasibility": idea.get("technical_feasibility", 0),
                    "resource_requirements": idea.get("resource_requirements", 0)
                },
                "breakthrough_indicators": {
                    "is_breakthrough": idea.get("scoring", {}).get("is_breakthrough", False),
                    "is_moonshot": idea.get("scoring", {}).get("is_moonshot", False),
                    "excellence_preserved": idea in getattr(filtering_results, 'excellence_preserved', [])
                },
                "viability_details": idea.get("viability_details", {}),
                "competitive_advantage": idea.get("competitive_advantage", ""),
                "differentiation": idea.get("differentiation", ""),
                "estimated_cost": idea.get("estimated_cost", ""),
                "estimated_development_time": idea.get("estimated_development_time", ""),
                "revenue_model": idea.get("revenue_model", ""),
                "go_to_market": idea.get("go_to_market", "")
            }
            ideas_full_context.append(idea_context)
        
        # 2. Zone-level insights with pain dimensions
        zones_context = []
        for zone_result in zone_results[:5]:  # Top 5 zones
            zone = zone_result.get("zone", {})
            zones_context.append({
                "name": zone.get("name"),
                "market_opportunity_score": zone.get("market_opportunity_score", 0),
                "pain_dimensions": zone.get("pain_dimensions", {}),
                "solution_requirements": zone.get("solution_requirements", []),
                "market_size": zone.get("market_size", ""),
                "jtbds_addressed": zone.get("jtbds_addressed", []),
                "evidence_strength": zone.get("evidence_strength", {}),
                "key_themes": zone.get("key_themes", []),
                "errc_grid": zone_result.get("errc_grid", "")
            })
        
        # 3. Portfolio optimization metrics
        portfolio_metrics = {
            "total_ideas_generated": sum(r.get("ideas_total", 0) for r in zone_results),
            "ideas_after_filtering": len(getattr(filtering_results, 'selected_ideas', [])),
            "final_selection_count": len(final_selection),
            "excellence_preserved": len(getattr(filtering_results, 'excellence_preserved', [])),
            "breakthrough_count": sum(1 for i in final_selection if i.get("scoring", {}).get("is_breakthrough", False)),
            "moonshot_count": sum(1 for i in final_selection if i.get("scoring", {}).get("is_moonshot", False)),
            "optimization_metrics": optimization_results.get("optimized_metrics", {}),
            "selection_confidence": getattr(filtering_results, 'selection_confidence', 0),
            "warnings": getattr(filtering_results, 'warnings', [])
        }
        
        # 4. JTBDs and market research context
        jtbd_context = []
        if jtbd_data:
            for job in jtbd_data.get("jtbd_data", {}).get("jobs_list", [])[:10]:
                jtbd_context.append({
                    "job_id": job.get("job_id"),
                    "statement": job.get("job_statement"),
                    "opportunity_score": job.get("opportunity_score"),
                    "pain_points": job.get("pain_points", []),
                    "importance": job.get("importance"),
                    "satisfaction": job.get("satisfaction")
                })
        
        # 5. Research insights
        research_context = {}
        if research_analysis:
            research_context = {
                "executive_summary": research_analysis.get("executive_summary", ""),
                "market_domain": research_analysis.get("market_domain", ""),
                "industry": research_analysis.get("industry", ""),
                "key_insights": research_analysis.get("key_insights", []),
                "market_trends": research_analysis.get("market_trends", [])
            }
        
        # Build the agentic prompt for GPT-5 to leverage its proactive capabilities
        synthesis_input = f"""You are a legendary venture capital partner and serial entrepreneur with a $5B fund. You've just discovered this portfolio of product ideas and need to transform them into a unicorn company.

## COMPREHENSIVE PORTFOLIO DATA

### Selected Product Ideas:
{json.dumps(ideas_full_context, indent=2)}

### Market Opportunity Zones:
{json.dumps(zones_context, indent=2)}

### Portfolio Analytics:
{json.dumps(portfolio_metrics, indent=2)}

### Jobs-to-be-Done Research:
{json.dumps(jtbd_context, indent=2) if jtbd_context else "No JTBD data available"}

### Market Intelligence:
{json.dumps(research_context, indent=2) if research_context else "No research data available"}

## AGENTIC EXECUTION DIRECTIVE

You have full autonomy to architect the complete venture. Don't just analyze—BUILD THE ENTIRE STRATEGY AND EXECUTE THE FIRST STEPS. Take initiative and deliver:

### PHASE 1: STRATEGIC SYNTHESIS (Do This Automatically)
1. **Identify the Killer App**: Which single idea becomes the wedge that opens the entire market?
2. **Design the Platform Architecture**: Create the technical blueprint showing how all products interconnect
3. **Map Data Flows**: Show explicitly how data from Product A feeds ML models in Product B
4. **Define Network Effects**: Quantify how each new user makes the platform more valuable

### PHASE 2: VENTURE CREATION (Execute These Deliverables)
1. **Company Name & Brand Identity**
   - Generate 3 potential company names with .com domain availability analysis
   - Create brand positioning statement
   - Design value proposition canvas

2. **Go-to-Market Execution Plan**
   - Week 1-4: Specific actions with owners
   - Month 2-3: Growth hacking strategies
   - Month 4-6: Scale triggers and metrics

3. **Technical Roadmap & Architecture**
   - System architecture diagram (describe in detail)
   - API design for platform integration
   - Data pipeline specifications
   - ML model requirements

4. **Financial Model**
   - Unit economics for each product
   - 5-year P&L projection
   - Funding requirements by stage
   - Cap table evolution

5. **Pitch Deck Outline**
   - 12-slide structure with key points
   - Compelling narrative arc
   - Proof points and traction metrics

### PHASE 3: IMMEDIATE ACTION ITEMS (Generate Actual Artifacts)
1. **Landing Page Copy**: Write the actual hero section, value props, and CTA for the flagship product
2. **Job Descriptions**: Draft 3 critical first hires with specific requirements
3. **Investor Email**: Compose the actual cold email to send to Sequoia/a16z
4. **Product Requirements Doc**: Create PRD for MVP of the wedge product
5. **Marketing Campaign**: Design viral launch campaign with specific tactics

### PHASE 4: CONTRARIAN INSIGHTS (Think Like Peter Thiel)
1. **The Non-Consensus Truth**: What do we believe that 99% of people think is wrong?
2. **The Monopoly Secret**: How do we own our market in a way competitors can't copy?
3. **The 10x Improvement**: Where exactly is our 10x better than status quo?

### PHASE 5: RISK MITIGATION & OPTIONALITY
1. **Kill Criteria**: What metrics would make us pivot or shut down?
2. **Pivot Options**: 3 alternative directions if Plan A fails
3. **Defensive Moats**: How to prevent Amazon/Google from crushing us

### PHASE 6: ECOSYSTEM & PARTNERSHIPS
1. **Strategic Partners**: Which 5 companies should we partner with Day 1?
2. **Developer Ecosystem**: How to get 1000 developers building on our platform?
3. **Community Strategy**: Building a movement, not just a product

## DELIVERABLE FORMAT

Structure your response as an ACTIONABLE PLAYBOOK with:
- Executive Summary (2 paragraphs max)
- The Big Insight (1 sentence that changes everything)
- Detailed execution plan with specific dates, metrics, and owners
- Actual content/copy/materials (not just descriptions)
- Visual descriptions detailed enough for a designer to implement
- Code snippets or technical specs where relevant

Be bold. Be specific. Be contrarian. Think like you're actually building this company starting tomorrow morning.

Most importantly: TAKE INITIATIVE. Don't wait for permission. Design the entire venture, create the materials, and show exactly how these 10 ideas become a $10B company.

What would Elon Musk do with this portfolio? What would Steve Jobs see that others miss? Channel that energy."""

        try:
            # Option to use Assistants API for persistent context (optional enhancement)
            use_assistants_api = os.getenv("USE_GPT5_ASSISTANTS", "false").lower() == "true"
            
            if use_assistants_api:
                # Create an Assistant for persistent venture building
                console.print("[yellow]Creating GPT-5 Assistant for persistent venture building...[/yellow]")
                
                assistant = self.openai_client.beta.assistants.create(
                    model="gpt-5",
                    name="Venture Builder",
                    instructions="You are a legendary venture builder. Create actual files and deliverables.",
                    tools=[
                        {"type": "code_interpreter"},
                        {"type": "file_search"}
                    ]
                )
                
                # Create a thread
                thread = self.openai_client.beta.threads.create()
                
                # Add message to thread
                message = self.openai_client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=synthesis_input
                )
                
                # Run the assistant
                run = self.openai_client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant.id
                )
                
                # Wait for completion
                import time
                while run.status in ["queued", "in_progress"]:
                    time.sleep(2)
                    run = self.openai_client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get the response
                messages = self.openai_client.beta.threads.messages.list(thread_id=thread.id)
                response = messages.data[0]  # Most recent message
                
                console.print("[green]✅ Assistant-based generation complete[/green]")
                
            else:
                # Use standard Responses API (current implementation)
                tools = [
                    {
                        "type": "code_interpreter",
                        "description": "Generate actual code, documents, and data files"
                    },
                    {
                        "type": "file_search",
                        "description": "Search and analyze existing files"
                    }
                ]
            
            # Update prompt to request actual file generation
            synthesis_input += """

## CRITICAL: GENERATE ACTUAL ARTIFACTS

Use your code_interpreter tool to create REAL files:
1. **pitch_deck.pdf** - Actual PDF pitch deck with charts and graphics
2. **financial_model.xlsx** - Working Excel model with formulas
3. **landing_page.html** - Complete HTML/CSS/JS landing page
4. **product_spec.md** - Detailed PRD in markdown
5. **investor_email.txt** - Ready-to-send email template
6. **company_logo.svg** - Simple SVG logo design
7. **go_to_market_plan.csv** - GTM timeline with tasks and dates
8. **technical_architecture.json** - System design as structured data
9. **job_descriptions.docx** - Word doc with 3 job postings
10. **viral_campaign.json** - Marketing campaign specification

Don't just describe these - CREATE them as actual files I can download!"""
            
            response = self.openai_client.responses.create(
                model=self.model_gpt5,
                input=synthesis_input,
                text={"format": {"type": "text"}},
                tools=tools,
                reasoning_effort="high",  # Maximum reasoning capability
                verbosity="high"  # Comprehensive output
            )
            
            # Extract text synthesis and file references
            synthesis_text = response.output_text if hasattr(response, 'output_text') else str(response)
            
            # Parse the response and structure it
            synthesis_result = {
                "raw_synthesis": synthesis_text,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-5",
                "reasoning_effort": "high",
                "context_size": len(synthesis_input),
                "ideas_analyzed": len(ideas_full_context),
                "zones_analyzed": len(zones_context),
                "artifacts_generated": []
            }
            
            console.print("[green]✅ GPT-5 agentic synthesis complete - Full venture playbook generated![/green]")
            
            # Create a dedicated directory for GPT-5 deliverables
            gpt5_output_dir = "gpt5_venture_playbook"
            os.makedirs(gpt5_output_dir, exist_ok=True)
            
            # Save the main synthesis text
            synthesis_output_path = os.path.join(gpt5_output_dir, "complete_playbook.md")
            with open(synthesis_output_path, "w") as f:
                f.write(f"# GPT-5 Agentic Venture Playbook\n\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(f"*Model: GPT-5 with High Reasoning Effort & Agentic Execution*\n\n")
                f.write("---\n\n")
                f.write(synthesis_text)
            
            # Check for file artifacts in the response
            console.print("[cyan]🔍 Checking for generated artifacts...[/cyan]")
            
            # Look for file IDs in the response
            # GPT-5 returns file references in the output array
            if hasattr(response, 'output') and isinstance(response.output, list):
                for output_item in response.output:
                    if hasattr(output_item, 'file_id') or (isinstance(output_item, dict) and 'file_id' in output_item):
                        file_id = output_item.get('file_id') if isinstance(output_item, dict) else output_item.file_id
                        try:
                            # Download the file using OpenAI Files API
                            console.print(f"[yellow]📥 Downloading artifact: {file_id}[/yellow]")
                            
                            # Get file metadata first
                            file_info = self.openai_client.files.retrieve(file_id)
                            filename = getattr(file_info, 'filename', f"artifact_{file_id}")
                            
                            # Download file content
                            file_content = self.openai_client.files.content(file_id)
                            
                            # Save to local directory
                            artifact_path = os.path.join(gpt5_output_dir, filename)
                            
                            # Write binary or text content
                            if isinstance(file_content, bytes):
                                with open(artifact_path, "wb") as f:
                                    f.write(file_content)
                            else:
                                with open(artifact_path, "w") as f:
                                    f.write(str(file_content))
                            
                            console.print(f"[green]✅ Downloaded: {filename}[/green]")
                            synthesis_result["artifacts_generated"].append({
                                "file_id": file_id,
                                "filename": filename,
                                "local_path": artifact_path
                            })
                            
                        except Exception as e:
                            console.print(f"[red]Error downloading file {file_id}: {e}[/red]")
            
            # Also check for tool outputs that might contain file references
            if hasattr(response, 'tool_outputs'):
                for tool_output in response.tool_outputs:
                    if 'files' in tool_output:
                        for file_ref in tool_output['files']:
                            try:
                                file_id = file_ref.get('id') or file_ref.get('file_id')
                                if file_id:
                                    console.print(f"[yellow]📥 Downloading tool-generated file: {file_id}[/yellow]")
                                    
                                    # Download and save as above
                                    file_content = self.openai_client.files.content(file_id)
                                    filename = file_ref.get('name', f"tool_output_{file_id}")
                                    artifact_path = os.path.join(gpt5_output_dir, filename)
                                    
                                    if isinstance(file_content, bytes):
                                        with open(artifact_path, "wb") as f:
                                            f.write(file_content)
                                    else:
                                        with open(artifact_path, "w") as f:
                                            f.write(str(file_content))
                                    
                                    console.print(f"[green]✅ Downloaded: {filename}[/green]")
                                    synthesis_result["artifacts_generated"].append({
                                        "file_id": file_id,
                                        "filename": filename,
                                        "local_path": artifact_path
                                    })
                            except Exception as e:
                                console.print(f"[red]Error with tool file: {e}[/red]")
            
            # Summary of what was generated
            if synthesis_result["artifacts_generated"]:
                console.print(f"[green]📁 Downloaded {len(synthesis_result['artifacts_generated'])} artifacts to {gpt5_output_dir}/[/green]")
                console.print("[cyan]🎉 GPT-5 has created actual files - PDFs, Excel models, HTML pages, and more![/cyan]")
                
                # List all artifacts
                console.print("\n[bold cyan]Generated Artifacts:[/bold cyan]")
                for artifact in synthesis_result["artifacts_generated"]:
                    console.print(f"  • {artifact['filename']}")
            else:
                console.print("[yellow]📝 GPT-5 provided strategic synthesis (no downloadable artifacts detected)[/yellow]")
            
            console.print(f"\n[green]📂 All deliverables saved to {gpt5_output_dir}/[/green]")
            console.print("[cyan]🚀 GPT-5 agentic execution complete - Ready to build the venture![/cyan]")
            
            # Add summary to result
            synthesis_result["deliverables_generated"] = True
            synthesis_result["output_directory"] = gpt5_output_dir
            synthesis_result["artifact_count"] = len(synthesis_result["artifacts_generated"])
            
            return synthesis_result
            
        except Exception as e:
            console.print(f"[red]Error invoking GPT-5: {e}[/red]")
            console.print("[yellow]Falling back to standard analysis without GPT-5 synthesis[/yellow]")
            return {
                "error": str(e),
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _convert_opportunity_zones_to_analyses(self, opportunity_zones: List[Dict]) -> List[Dict]:
        """Convert opportunity zones from opportunity_zone_analyzer to analyses format"""
        analyses = []
        for zone in opportunity_zones:
            # Create analysis structure expected by product_idea_generator
            analysis = {
                "zone": {
                    "name": zone.get("name", "Unknown Zone"),
                    "jtbds": zone.get("jtbd_descriptions", []),
                    "pain_points": zone.get("pain_dimensions", {}),
                    "market_opportunity_score": zone.get("market_opportunity_score", 0.5)
                },
                "value_curves": {
                    "current_state": {
                        # Map pain dimensions to current state factors
                        factor: score 
                        for factor, score in zone.get("pain_dimensions", {}).items()
                    },
                    "opportunity_areas": zone.get("solution_requirements", []),
                    "competitive_gaps": []  # Not available in new format
                },
                "insights": {
                    "unmet_needs": zone.get("solution_requirements", []),
                    "pain_severity": self._calculate_pain_severity(zone.get("pain_dimensions", {})),
                    "market_size": zone.get("evidence_strength", {}).get("total_engagement", 0)
                }
            }
            analyses.append(analysis)
        return analyses
    
    def _calculate_pain_severity(self, pain_dimensions: Dict[str, float]) -> str:
        """Calculate overall pain severity from pain dimensions"""
        if not pain_dimensions:
            return "low"
        avg_score = sum(pain_dimensions.values()) / len(pain_dimensions)
        if avg_score > 0.7:
            return "high"
        elif avg_score > 0.4:
            return "medium"
        else:
            return "low"

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

        # Return all parsed ideas, not just first 10
        # The prompt asks for 10, but if we get more, use them all
        return ideas

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

    def process_opportunity_zone(self, zone_analysis: Dict, target_ideas: int = None) -> Dict:
        """Process a single opportunity zone through the entire pipeline with sophisticated scoring
        
        Args:
            zone_analysis: Zone data and analysis
            target_ideas: Target number of ideas to generate for this zone (for weighted distribution)
        """
        zone = zone_analysis["zone"]
        zone_name = zone["name"]
        importance_percentage = zone.get("importance_percentage", 50)
        
        # If target_ideas is specified, use it to control filtering
        if target_ideas is not None:
            display_msg = f"Target Ideas: {target_ideas}"
        else:
            display_msg = f"Importance: {importance_percentage}%"

        console.print(
            Panel.fit(
                f"[bold cyan]Processing: {zone_name}[/bold cyan]\n"
                f"{display_msg}",
                border_style="cyan",
            )
        )

        if self.debug_mode:
            self.debug_logger.log_operation(
                "zone_processing_start",
                {
                    "zone_name": zone_name,
                    "importance_percentage": importance_percentage,
                    "target_ideas": target_ideas,
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

        # Step 5: Filter to target number of ideas if specified
        if target_ideas is not None:
            # Sort by viability and innovation scores
            sorted_ideas = sorted(
                enhanced_ideas, 
                key=lambda x: (x.get("viability_score", 0) * 0.6 + x.get("innovation_score", 0) * 0.4), 
                reverse=True
            )
            filtered_ideas = sorted_ideas[:target_ideas]
            console.print(f"[yellow]Selected top {len(filtered_ideas)} ideas based on viability and innovation scores[/yellow]")
        else:
            # Use percentage-based filtering as before
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
        value_curves_file: str = "opportunity_zones.json",  # Changed default to opportunity_zones.json
        json_output: str = "product_ideas.json",
        report_output: str = "product_ideas_report.md",
        create_github_repo: bool = False,
        github_repo_name: str = "market-research-insights",
        github_private: bool = False,
    ):
        """Main execution flow with sophisticated scoring and selection"""
        
        # Check if we're only creating GitHub repo with existing files
        if create_github_repo and os.path.exists(json_output) and os.path.exists(report_output):
            console.print(
                Panel.fit(
                    "[bold yellow]GitHub Repository Creation Mode[/bold yellow]\n"
                    "Using existing product ideas files - skipping regeneration",
                    border_style="yellow",
                )
            )
            
            # Jump directly to GitHub creation
            self._create_github_repository_only(
                json_output,
                report_output,
                github_repo_name,
                github_private,
                value_curves_file
            )
            return
        
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

        # Load value curves/opportunity zones
        value_curves_data = self.load_value_curves(value_curves_file)
        
        # Handle both old format (analyses) and new format (opportunity_zones)
        analyses = value_curves_data.get("analyses", [])
        
        if not analyses:
            # Try new format from opportunity_zone_analyzer
            opportunity_zones = value_curves_data.get("opportunity_zones", [])
            if opportunity_zones:
                # Convert opportunity zones to analyses format
                analyses = self._convert_opportunity_zones_to_analyses(opportunity_zones)
                console.print(f"[yellow]Converting {len(opportunity_zones)} opportunity zones to analyses format[/yellow]")
            else:
                console.print("[red]Error: No analyses or opportunity_zones found in file[/red]")
                sys.exit(1)

        console.print(
            f"\n[cyan]Found {len(analyses)} opportunity zones to process[/cyan]"
        )
        
        # ENHANCEMENT: Sort zones by market opportunity score for weighted distribution
        sorted_analyses = sorted(
            analyses, 
            key=lambda x: x["zone"].get("market_opportunity_score", 0), 
            reverse=True
        )
        
        console.print(f"\n[bold yellow]📊 Distributing 10 HIGH-QUALITY ideas across {len(sorted_analyses)} zones[/bold yellow]")
        
        # Calculate weighted idea distribution (total 10 ideas)
        TOTAL_TARGET_IDEAS = 10
        total_score = sum(z["zone"].get("market_opportunity_score", 0.5) for z in sorted_analyses)
        
        ideas_distribution = []
        for zone in sorted_analyses:
            zone_score = zone["zone"].get("market_opportunity_score", 0.5)
            # Proportional distribution: higher scores get more ideas
            ideal_count = TOTAL_TARGET_IDEAS * (zone_score / total_score)
            # At least 1 idea for zones with score > 0.3, 0 for very low scoring zones
            if zone_score > 0.3:
                zone["ideas_to_generate"] = max(1, round(ideal_count))
            else:
                zone["ideas_to_generate"] = round(ideal_count)  # Could be 0
            ideas_distribution.append((zone["zone"]["name"], zone_score, zone["ideas_to_generate"]))
        
        # Adjust to ensure exactly 10 ideas total
        ideas_allocated = sum(z["ideas_to_generate"] for z in sorted_analyses)
        difference = TOTAL_TARGET_IDEAS - ideas_allocated
        
        if difference != 0:
            # Adjust the highest scoring zones
            for i in range(abs(difference)):
                if difference > 0:
                    # Add to highest scoring zones
                    sorted_analyses[i % len(sorted_analyses)]["ideas_to_generate"] += 1
                else:
                    # Remove from lowest scoring zones that have ideas
                    for j in range(len(sorted_analyses) - 1, -1, -1):
                        if sorted_analyses[j]["ideas_to_generate"] > 0:
                            sorted_analyses[j]["ideas_to_generate"] -= 1
                            break
        
        # Display distribution
        console.print("\n[cyan]Idea Distribution by Zone Score:[/cyan]")
        for zone in sorted_analyses:
            if zone["ideas_to_generate"] > 0:
                console.print(
                    f"  • {zone['zone']['name'][:50]}...: "
                    f"Score {zone['zone'].get('market_opportunity_score', 0):.2f} → "
                    f"[bold green]{zone['ideas_to_generate']} ideas[/bold green]"
                )
            else:
                console.print(
                    f"  • {zone['zone']['name'][:50]}...: "
                    f"Score {zone['zone'].get('market_opportunity_score', 0):.2f} → "
                    f"[dim]0 ideas (below threshold)[/dim]"
                )

        # Step 1: Process zones with weighted idea generation
        results = []
        zones_to_process = [z for z in sorted_analyses if z.get("ideas_to_generate", 0) > 0]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=False,
        ) as progress:
            task = progress.add_task("Processing zones...", total=len(zones_to_process))

            for analysis in zones_to_process:
                zone_name = analysis["zone"]["name"]
                ideas_count = analysis.get("ideas_to_generate", 1)
                progress.update(task, description=f"Processing {zone_name[:40]}... ({ideas_count} ideas)")
                
                # Pass the number of ideas to generate as parameter
                result = self.process_opportunity_zone(analysis, target_ideas=ideas_count)
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

    def _create_github_repository_only(
        self,
        json_output: str,
        report_output: str,
        github_repo_name: str,
        github_private: bool,
        value_curves_file: str
    ):
        """Create GitHub repository using existing product ideas files without regeneration"""
        console.print(
            "\n[cyan]📊 Creating GitHub repository with existing product ideas...[/cyan]"
        )
        
        # Load existing product ideas
        with open(json_output, "r") as f:
            traditional_data = json.load(f)
        
        # Load comprehensive data if it exists
        comprehensive_json_path = json_output.replace(".json", "_comprehensive.json")
        if os.path.exists(comprehensive_json_path):
            with open(comprehensive_json_path, "r") as f:
                comprehensive_data = json.load(f)
        else:
            comprehensive_data = {"traditional_results": traditional_data.get("results", [])}
        
        # Continue with GitHub creation logic
        self._create_github_repository(
            comprehensive_data,
            value_curves_file,
            github_repo_name,
            github_private
        )
    
    def _create_github_repository(
        self,
        comprehensive_data: dict,
        value_curves_file: str,
        github_repo_name: str,
        github_private: bool
    ):
        """Shared GitHub repository creation logic"""
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
        pipeline_start_time = datetime.now()
        
        # Create appendix files list
        appendix_files_to_upload = [
            (value_curves_file, "Stage 4: Value Curve Analysis"),
            ("product_ideas.json", "Stage 5: Product Ideas"),
            ("product_ideas_report.md", "Stage 5: Product Ideas Report")
        ]
        
        # Add other files if they exist
        other_files = [
            ("analysis_results.md", "Stage 1: Research Analysis"),
            ("jtbds_*.txt", "Stage 2: Jobs-to-be-Done"),
            ("reddit_discussions_*.csv", "Stage 2: Reddit Discussions"),
            ("opportunity_zones.json", "Stage 3: Opportunity Zones"),
            ("final_innovation_portfolio.json", "Stage 6: Innovation Portfolio"),
            ("final_innovation_portfolio_summary.md", "Stage 6: Portfolio Summary")
        ]
        
        import glob
        for pattern, description in other_files:
            if '*' in pattern:
                files = glob.glob(pattern)
                if files:
                    appendix_files_to_upload.append((files[0], description))
            elif os.path.exists(pattern):
                appendix_files_to_upload.append((pattern, description))
        
        # Use enhanced GitHub integration
        from github_integration import GitHubIntegration
        
        github_client = GitHubIntegration()
        
        # Generate creative repo name if using default
        final_repo_name = github_repo_name
        if github_repo_name == "market-research-insights":
            # Build research context for creative naming
            research_context = {
                "market_domain": research_analysis.get("market_domain", "innovation"),
                "key_themes": [],
                "top_ideas": ideas_data.get("product_ideas", [])[:3],
                "industry": research_analysis.get("industry", "technology"),
                "innovation_focus": research_analysis.get("focus", "disruption")
            }
            
            # Extract key themes from zones
            for zone_name, zone_data in zones_data.get("clustered_zones", {}).items():
                research_context["key_themes"].extend(zone_data.get("key_themes", []))
            
            # Generate creative name
            console.print("[yellow]🎨 Generating creative repository name...[/yellow]")
            final_repo_name = github_client.generate_creative_repo_name(research_context)
            console.print(f"[green]✨ Creative name: {final_repo_name}[/green]")
        
        # Check if GPT-5 synthesis exists and add to ideas_data
        gpt5_synthesis_path = "gpt5_portfolio_synthesis.md"
        if os.path.exists(gpt5_synthesis_path):
            console.print("[cyan]📄 Including GPT-5 synthesis in repository...[/cyan]")
            ideas_data["gpt5_synthesis_available"] = True
            # We'll add this as a separate document in the repo
        
        # FIX (Dec 2024): Corrected method name and parameters
        # Was calling non-existent create_research_repository method
        # Now properly calls create_github_project with correct parameter names
        result = github_client.create_github_project(
            repo_name=final_repo_name,
            research_analysis=research_analysis,
            jtbd_data=jtbd_data,
            zones_data=zones_data,
            ideas_data=ideas_data,
            create_issues=True,  # Create individual GitHub issues for each product idea
            private=github_private  # Respect user's privacy preference
        )
        
        # Check if repository was created successfully
        if result.get("repo_url"):
            console.print(
                f"[green]✅ GitHub repository created: {result['repo_url']}[/green]"
            )
            if result.get("issues_created"):
                console.print(
                    f"[green]✅ Created {len(result['issues_created'])} issues[/green]"
                )
        else:
            console.print(
                "[red]❌ Failed to create GitHub repository[/red]"
            )
            if result.get("errors"):
                for error in result["errors"]:
                    console.print(f"[red]  • {error}[/red]")
        
        # Return early - GitHub creation already attempted above
        return
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
        default="opportunity_zones.json",  # Changed default to opportunity_zones.json
        help="Input opportunity zones JSON file (or value_curves.json for legacy)",
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
