#!/usr/bin/env python3
"""
Research Analysis Application with S3 Integration and Parallel LLM Calls
Pulls research from S3 and performs parallel analysis using Claude Sonnet and Opus
"""

import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

# Import logging system
from src.utils.pipeline_logger import initialize_logger, get_logger, close_logger
from src.models.logging_models import ComponentType, ModelProvider
from src.config import Config

# Import debug system
from src.utils.debug_config import initialize_debug_config, is_debug_mode
from src.utils.debug_logger import initialize_debug_logger, close_debug_logger
from src.utils.debug_aware_component import DebugAwareComponent

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()


@dataclass
class AnalysisTask:
    """Represents a single analysis task"""

    name: str
    prompt: str
    model: str  # "sonnet" or "opus"
    system_prompt: str = (
        "You are an expert analyst providing detailed, actionable insights."
    )
    max_tokens: int = 2000
    temperature: float = 0.7


class ResearchAnalyzer(DebugAwareComponent):
    """Main application for parallel research analysis"""

    def __init__(self, logger=None):
        """Initialize AWS S3 and Anthropic clients"""
        # Initialize debug-aware component
        super().__init__(ComponentType.RESEARCH_ANALYZER, logger)

        # Initialize logger if not provided
        self.logger = logger or get_logger()
        if not self.logger:
            # Initialize a new logger for this component
            config = Config()
            self.logger = initialize_logger(config)

        self.logger.info(
            "Initializing Research Analyzer", ComponentType.RESEARCH_ANALYZER
        )

        # Show debug mode status
        if self.debug_enabled:
            console.print("[yellow]🐛 Research Analyzer: DEBUG MODE ENABLED[/yellow]")

        # Anthropic setup
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.logger.error(
                "ANTHROPIC_API_KEY not found in environment variables",
                ComponentType.RESEARCH_ANALYZER,
            )
            console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
            sys.exit(1)

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)

            # Production models
            self.production_model_sonnet = "claude-3-5-sonnet-20241022"
            self.production_model_opus = "claude-3-opus-20240229"

            # Get debug-aware models
            self.model_sonnet = self.get_debug_model(
                self.production_model_sonnet, "research_analysis"
            )
            self.model_opus = self.get_debug_model(
                self.production_model_opus, "complex_analysis"
            )

            if self.debug_enabled:
                console.print(
                    f"[cyan]Sonnet model: {self.production_model_sonnet} → {self.model_sonnet}[/cyan]"
                )
                console.print(
                    f"[cyan]Opus model: {self.production_model_opus} → {self.model_opus}[/cyan]"
                )

            self.logger.info(
                "Anthropic client initialized successfully",
                ComponentType.RESEARCH_ANALYZER,
                metadata={
                    "sonnet_model": self.model_sonnet,
                    "opus_model": self.model_opus,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Error initializing Anthropic client: {e}",
                ComponentType.RESEARCH_ANALYZER,
            )
            console.print(f"[red]Error initializing Anthropic client: {e}[/red]")
            sys.exit(1)

        # AWS S3 setup
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.file_key = os.getenv("S3_FILE_KEY")

        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            self.logger.warning(
                "AWS credentials not fully configured. S3 functionality disabled",
                ComponentType.RESEARCH_ANALYZER,
            )
            console.print(
                "[yellow]Warning: AWS credentials not fully configured. Use --local flag for local file.[/yellow]"
            )
            self.s3_client = None
        else:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region,
                )
                self.logger.info(
                    "S3 client initialized successfully",
                    ComponentType.RESEARCH_ANALYZER,
                )
            except Exception as e:
                self.logger.error(
                    f"Error initializing S3 client: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                )
                console.print(f"[red]Error initializing S3 client: {e}[/red]")
                self.s3_client = None

    def get_default_model(self) -> str:
        """Get the default production model for this component"""
        return self.production_model_sonnet

    def pull_from_s3(
        self, bucket: Optional[str] = None, key: Optional[str] = None
    ) -> Dict:
        """Pull JSON file from S3"""
        bucket = bucket or self.bucket_name
        key = key or self.file_key

        if not self.s3_client:
            self.logger.error(
                "S3 client not initialized. Check AWS credentials",
                ComponentType.RESEARCH_ANALYZER,
            )
            console.print(
                "[red]S3 client not initialized. Check AWS credentials.[/red]"
            )
            sys.exit(1)

        with self.logger.log_operation(
            ComponentType.RESEARCH_ANALYZER,
            "s3_download",
            metadata={"bucket": bucket, "key": key},
        ) as op:
            self.logger.info(
                f"Pulling file from S3: s3://{bucket}/{key}",
                ComponentType.RESEARCH_ANALYZER,
                "s3_download",
            )
            console.print(f"[cyan]Pulling file from S3: s3://{bucket}/{key}[/cyan]")

            try:
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                content = response["Body"].read().decode("utf-8")
                data = json.loads(content)

                # Update operation metadata
                op.output_data_size = len(content)
                op.records_processed = 1

                self.logger.info(
                    f"Successfully pulled file from S3 ({len(content)} bytes)",
                    ComponentType.RESEARCH_ANALYZER,
                    "s3_download",
                )
                console.print("[green]✅ Successfully pulled file from S3[/green]")
                return data

            except ClientError as e:
                self.logger.error(
                    f"S3 ClientError: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                    "s3_download",
                )
                console.print(f"[red]Error pulling from S3: {e}[/red]")
                sys.exit(1)
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"JSON parsing error: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                    "s3_download",
                )
                console.print(f"[red]Error parsing JSON: {e}[/red]")
                sys.exit(1)

    def load_local_file(self, filepath: str) -> Dict:
        """Load JSON file from local filesystem"""
        with self.logger.log_operation(
            ComponentType.RESEARCH_ANALYZER,
            "file_load",
            metadata={"filepath": filepath},
        ) as op:
            self.logger.info(
                f"Loading local file: {filepath}",
                ComponentType.RESEARCH_ANALYZER,
                "file_load",
            )
            console.print(f"[cyan]Loading local file: {filepath}[/cyan]")

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                # Update operation metadata
                op.output_data_size = len(json.dumps(data))
                op.records_processed = 1

                self.logger.info(
                    f"Successfully loaded local file ({len(json.dumps(data))} bytes)",
                    ComponentType.RESEARCH_ANALYZER,
                    "file_load",
                )
                console.print("[green]✅ Successfully loaded local file[/green]")
                return data

            except FileNotFoundError:
                self.logger.error(
                    f"File not found: {filepath}",
                    ComponentType.RESEARCH_ANALYZER,
                    "file_load",
                )
                console.print(f"[red]Error: File not found: {filepath}[/red]")
                sys.exit(1)
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"JSON parsing error: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                    "file_load",
                )
                console.print(f"[red]Error parsing JSON: {e}[/red]")
                sys.exit(1)

    def extract_content(self, data: Dict) -> str:
        """Extract content attribute from JSON data"""
        if "content" in data:
            return data["content"]
        elif "research" in data and "content" in data["research"]:
            return data["research"]["content"]
        else:
            # Try to find content in nested structure
            console.print(
                "[yellow]'content' attribute not found at expected location. Searching...[/yellow]"
            )
            content = self._find_content_recursive(data)
            if content:
                return content
            else:
                console.print(
                    "[red]Error: Could not find 'content' attribute in JSON[/red]"
                )
                console.print(
                    "JSON structure:",
                    data.keys() if isinstance(data, dict) else type(data),
                )
                sys.exit(1)

    def _find_content_recursive(self, obj, depth=0, max_depth=5):
        """Recursively search for content attribute"""
        if depth > max_depth:
            return None

        if isinstance(obj, dict):
            if "content" in obj:
                return obj["content"]
            for value in obj.values():
                result = self._find_content_recursive(value, depth + 1, max_depth)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_content_recursive(item, depth + 1, max_depth)
                if result:
                    return result

        return None

    def create_analysis_tasks(self) -> List[AnalysisTask]:
        """Create the four parallel analysis tasks"""
        return [
            AnalysisTask(
                name="Industry Verticals",
                prompt=(
                    "Given this research document, which industry verticals or domains do you see "
                    "emerging as distinct from the others with regard to dynamic factors and other "
                    "differentiating characteristics you believe are worthy of setting them as unique verticals? "
                    "Please provide a structured analysis with clear categories and reasoning."
                ),
                model="sonnet",
            ),
            AnalysisTask(
                name="User Personas",
                prompt=(
                    "Given this research document, what are some of the customer or user personas "
                    "that you can identify? These should reflect the types of people who would want "
                    "help with your product or who need assistance in this space. "
                    "Please describe each persona with demographics, needs, goals, and pain points."
                ),
                model="sonnet",
            ),
            AnalysisTask(
                name="Pain Points",
                prompt=(
                    "Within this research document, what are the key pain points that you observe "
                    "or can infer based on the research presented? Please categorize these pain points "
                    "by severity, frequency, and impact on users. Include both explicit and implicit "
                    "pain points you can deduce from the research."
                ),
                model="opus",
            ),
            AnalysisTask(
                name="Solution Types",
                prompt=(
                    "What are the solution types that you see described or that can be inferred "
                    "from this research? Please categorize these solutions by approach, technology, "
                    "implementation complexity, and potential effectiveness. Include both existing "
                    "and potential solutions that could address the identified needs."
                ),
                model="opus",
            ),
        ]

    def analyze_with_llm(
        self, task: AnalysisTask, research_content: str
    ) -> Tuple[str, str]:
        """Execute a single analysis task with debug-aware processing"""
        # Select the appropriate model (already debug-aware from initialization)
        model = self.model_sonnet if task.model == "sonnet" else self.model_opus
        model_display = "Sonnet" if task.model == "sonnet" else "Opus"

        # Apply debug content truncation if needed
        if self.debug_enabled:
            research_content = self.truncate_content_for_debug(
                research_content, f"analysis_{task.name.lower().replace(' ', '_')}"
            )
            # Add debug prompt suffix
            task.system_prompt += self.create_debug_prompt_suffix()

        # Prepare the prompt with research content
        full_prompt = f"Research Document:\n\n{research_content}\n\n{task.prompt}"

        # Check token limits before proceeding
        estimated_tokens = (
            len(full_prompt) + len(task.system_prompt) + task.max_tokens
        ) // 4
        if not self.check_token_limits(estimated_tokens, f"analysis_{task.name}"):
            console.print(
                f"[red]Skipping {task.name} analysis - would exceed debug limits[/red]"
            )
            return (
                task.name,
                f"[ANALYSIS SKIPPED IN DEBUG MODE: {task.name} - would exceed token limits]",
            )

        self.logger.info(
            f"Starting {task.name} analysis with Claude {model_display}",
            ComponentType.RESEARCH_ANALYZER,
            "llm_analysis",
            metadata={"task": task.name, "model": model},
        )
        console.print(
            f"[cyan]Running {task.name} analysis with Claude {model_display}...[/cyan]"
        )

        # Use debug-aware API call tracking
        with self.debug_api_call(
            model, f"analysis_{task.name}", len(full_prompt) // 4
        ) as call_data:
            try:
                # Calculate approximate input tokens
                estimated_prompt_tokens = len(full_prompt + task.system_prompt) // 4
                call_data["actual_prompt_tokens"] = estimated_prompt_tokens

                # Make API call
                message = self.client.messages.create(
                    model=model,
                    max_tokens=task.max_tokens,
                    temperature=task.temperature,
                    system=task.system_prompt,
                    messages=[{"role": "user", "content": full_prompt}],
                )

                response_text = message.content[0].text

                # Update call data with response information
                call_data["completion_tokens"] = len(response_text) // 4

                self.logger.info(
                    f"Completed {task.name} analysis ({len(response_text)} chars)",
                    ComponentType.RESEARCH_ANALYZER,
                    "llm_analysis",
                    metadata={"task": task.name, "response_length": len(response_text)},
                )

                return (task.name, response_text)

            except anthropic.RateLimitError as e:
                self.logger.warning(
                    f"Rate limit reached for {task.name}. Retrying in 5s...",
                    ComponentType.RESEARCH_ANALYZER,
                    "llm_analysis",
                )
                console.print(
                    f"[yellow]Rate limit reached for {task.name}. Retrying...[/yellow]"
                )

                # In debug mode, don't retry to avoid exceeding limits
                if self.debug_enabled:
                    return (task.name, f"[RATE LIMITED IN DEBUG MODE: {task.name}]")

                # Re-raise for normal retry logic
                raise

            except Exception as e:
                self.logger.error(
                    f"Error in {task.name} analysis: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                    "llm_analysis",
                    metadata={"task": task.name},
                )
                console.print(f"[red]Error in {task.name} analysis: {e}[/red]")
                raise

    def run_parallel_analysis(self, research_content: str) -> Dict[str, str]:
        """Run all analysis tasks in parallel"""
        with self.logger.log_operation(
            ComponentType.RESEARCH_ANALYZER,
            "parallel_analysis",
            input_data_size=len(research_content),
            metadata={"task_count": 4},
        ) as op:
            tasks = self.create_analysis_tasks()
            results = {}

            self.logger.info(
                "Starting parallel analysis with 4 LLM calls",
                ComponentType.RESEARCH_ANALYZER,
                "parallel_analysis",
            )
            console.print(
                "\n[bold cyan]Starting parallel analysis with 4 LLM calls...[/bold cyan]"
            )

            # Create a summary table
            table = Table(title="Analysis Tasks")
            table.add_column("Task", style="cyan")
            table.add_column("Model", style="magenta")
            table.add_column("Status", style="green")

            for task in tasks:
                table.add_row(task.name, f"Claude {task.model.title()}", "Queued")

            console.print(table)
            console.print()

            # Create progress tracker
            progress_id = self.logger.create_progress_bar(
                "Running parallel analysis", len(tasks), ComponentType.RESEARCH_ANALYZER
            )

            # Execute tasks in parallel
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=False,
            ) as progress:
                progress_task = progress.add_task(
                    "[cyan]Running parallel analysis...", total=len(tasks)
                )

                with ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit all tasks
                    future_to_task = {
                        executor.submit(
                            self.analyze_with_llm, task, research_content
                        ): task
                        for task in tasks
                    }

                    # Process completed tasks
                    for future in as_completed(future_to_task):
                        task_name, result = future.result()
                        results[task_name] = result

                        # Update progress bars
                        progress.update(progress_task, advance=1)
                        self.logger.update_progress(progress_id, advance=1)

                        self.logger.info(
                            f"Completed analysis task: {task_name}",
                            ComponentType.RESEARCH_ANALYZER,
                            "parallel_analysis",
                            metadata={"task": task_name, "result_length": len(result)},
                        )
                        console.print(f"[green]✅ Completed: {task_name}[/green]")

            # Complete progress tracking
            self.logger.complete_progress(progress_id)

            # Update operation metadata
            op.records_processed = len(results)
            total_output_size = sum(len(result) for result in results.values())
            op.output_data_size = total_output_size

            self.logger.info(
                f"Parallel analysis completed. Processed {len(results)} tasks, generated {total_output_size} chars",
                ComponentType.RESEARCH_ANALYZER,
                "parallel_analysis",
            )

            return results

    def combine_results(self, results: Dict[str, str]) -> str:
        """Combine all analysis results into a single document"""
        combined = f"# Research Analysis Results\n\n"
        combined += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        combined += "---\n\n"

        # Add each analysis section
        for task_name, content in results.items():
            combined += f"## {task_name}\n\n"
            combined += f"{content}\n\n"
            combined += "---\n\n"

        return combined

    def save_results(
        self, combined_results: str, output_file: str = "analysis_results.md"
    ):
        """Save combined results to file"""
        with open(output_file, "w") as f:
            f.write(combined_results)
        console.print(f"\n[green]✅ Results saved to {output_file}[/green]")

    def run(
        self,
        source: str,
        is_s3: bool = True,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        output_file: str = "analysis_results.md",
    ):
        """Main execution flow"""
        with self.logger.log_operation(
            ComponentType.RESEARCH_ANALYZER, "research_analysis_pipeline"
        ) as op:
            self.logger.info(
                "Starting Research Analysis Pipeline",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )

            console.print(
                Panel.fit(
                    "[bold green]Research Analysis with Parallel LLM Processing[/bold green]\n"
                    "Using Claude Sonnet and Opus for comprehensive analysis",
                    border_style="green",
                )
            )

            # Step 1: Load data
            self.logger.info(
                "Step 1: Loading data",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            if is_s3:
                data = self.pull_from_s3(bucket, key)
            else:
                data = self.load_local_file(source)

            # Step 2: Extract content
            self.logger.info(
                "Step 2: Extracting content",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            research_content = self.extract_content(data)
            op.input_data_size = len(research_content)

            self.logger.info(
                f"Extracted research content ({len(research_content)} characters)",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            console.print(
                f"\n[green]✅ Extracted research content ({len(research_content)} characters)[/green]"
            )

            # Step 3: Run parallel analysis
            self.logger.info(
                "Step 3: Running parallel analysis",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            results = self.run_parallel_analysis(research_content)

            # Step 4: Combine results
            self.logger.info(
                "Step 4: Combining results",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            combined_results = self.combine_results(results)
            op.output_data_size = len(combined_results)
            op.records_processed = len(results)

            # Step 5: Display summary
            self.logger.info(
                "Step 5: Displaying summary",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            console.print("\n[bold green]Analysis Complete![/bold green]")

            summary_stats = {
                "industry_verticals_words": len(
                    results.get("Industry Verticals", "").split()
                ),
                "user_personas_words": len(results.get("User Personas", "").split()),
                "pain_points_words": len(results.get("Pain Points", "").split()),
                "solution_types_words": len(results.get("Solution Types", "").split()),
                "total_words": len(combined_results.split()),
            }

            console.print(
                Panel(
                    f"• Industry Verticals: {summary_stats['industry_verticals_words']} words\n"
                    f"• User Personas: {summary_stats['user_personas_words']} words\n"
                    f"• Pain Points: {summary_stats['pain_points_words']} words\n"
                    f"• Solution Types: {summary_stats['solution_types_words']} words\n"
                    f"\nTotal output: {summary_stats['total_words']} words",
                    title="Summary",
                    border_style="blue",
                )
            )

            self.logger.info(
                "Analysis summary generated",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
                metadata=summary_stats,
            )

            # Step 6: Save results
            self.logger.info(
                "Step 6: Saving results",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )
            self.save_results(combined_results, output_file)

            # Optional: Display preview
            if (
                console.input(
                    "\n[yellow]Display preview of results? (y/n): [/yellow]"
                ).lower()
                == "y"
            ):
                preview = (
                    combined_results[:1000] + "..."
                    if len(combined_results) > 1000
                    else combined_results
                )
                console.print(
                    Panel(Markdown(preview), title="Preview", border_style="dim")
                )

            self.logger.info(
                "Research Analysis Pipeline completed successfully",
                ComponentType.RESEARCH_ANALYZER,
                "research_analysis_pipeline",
            )

            return combined_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Research Analysis with S3 Integration and Parallel LLM Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pull from S3 (using .env configuration)
  python research_analyzer.py
  
  # Pull from S3 with custom bucket/key
  python research_analyzer.py --bucket my-bucket --key path/to/file.json
  
  # Use local file instead of S3
  python research_analyzer.py --local research.json
  
  # Specify output file
  python research_analyzer.py --output custom_results.md
  
  # Test mode
  python research_analyzer.py --test
        """,
    )

    parser.add_argument("--local", type=str, help="Use local file instead of S3")
    parser.add_argument("--bucket", type=str, help="S3 bucket name (overrides .env)")
    parser.add_argument("--key", type=str, help="S3 object key (overrides .env)")
    parser.add_argument(
        "--output",
        type=str,
        default="analysis_results.md",
        help="Output file name (default: analysis_results.md)",
    )
    parser.add_argument("--test", action="store_true", help="Test connections only")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--session-id", type=str, help="Custom session ID")

    args = parser.parse_args()

    # Initialize debug system first
    debug_config = initialize_debug_config()
    if debug_config.enabled:
        debug_logger = initialize_debug_logger()
        console.print("[cyan]Debug system initialized for research analyzer[/cyan]")

    # Initialize logging configuration
    config = Config(args.config) if args.config else Config()

    # Initialize the pipeline logger with session management
    logger = initialize_logger(config, args.session_id)

    try:
        # Initialize analyzer with logger
        analyzer = ResearchAnalyzer(logger)

        if args.test:
            # Test mode with logging
            logger.info(
                "Starting connection tests",
                ComponentType.RESEARCH_ANALYZER,
                "connection_test",
            )
            console.print("[cyan]Testing connections...[/cyan]")

            # Test Anthropic with debug-aware calls
            try:
                # Test Sonnet
                if debug_config.enabled:
                    with analyzer.debug_api_call(
                        analyzer.model_sonnet, "connection_test", 5
                    ) as call_data:
                        call_data["actual_prompt_tokens"] = 5
                        response = analyzer.client.messages.create(
                            model=analyzer.model_sonnet,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'Sonnet connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5
                else:
                    with logger.track_api_call(
                        ComponentType.RESEARCH_ANALYZER,
                        ModelProvider.ANTHROPIC,
                        analyzer.model_sonnet,
                    ) as call_data:
                        call_data["prompt_tokens"] = 5
                        response = analyzer.client.messages.create(
                            model=analyzer.model_sonnet,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'Sonnet connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5

                logger.info(
                    "Claude Sonnet connection test successful",
                    ComponentType.RESEARCH_ANALYZER,
                    "connection_test",
                )
                console.print(
                    f"[green]✅ Claude Sonnet: {response.content[0].text}[/green]"
                )

                # Test Opus
                if debug_config.enabled:
                    with analyzer.debug_api_call(
                        analyzer.model_opus, "connection_test", 5
                    ) as call_data:
                        call_data["actual_prompt_tokens"] = 5
                        response = analyzer.client.messages.create(
                            model=analyzer.model_opus,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'Opus connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5
                else:
                    with logger.track_api_call(
                        ComponentType.RESEARCH_ANALYZER,
                        ModelProvider.ANTHROPIC,
                        analyzer.model_opus,
                    ) as call_data:
                        call_data["prompt_tokens"] = 5
                        response = analyzer.client.messages.create(
                            model=analyzer.model_opus,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'Opus connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5

                logger.info(
                    "Claude Opus connection test successful",
                    ComponentType.RESEARCH_ANALYZER,
                    "connection_test",
                )
                console.print(
                    f"[green]✅ Claude Opus: {response.content[0].text}[/green]"
                )

            except Exception as e:
                logger.error(
                    f"Anthropic connection test failed: {e}",
                    ComponentType.RESEARCH_ANALYZER,
                    "connection_test",
                )
                console.print(f"[red]❌ Anthropic test failed: {e}[/red]")

            # Test S3
            if analyzer.s3_client:
                try:
                    with logger.log_operation(
                        ComponentType.RESEARCH_ANALYZER, "s3_test"
                    ) as op:
                        analyzer.s3_client.head_bucket(Bucket=analyzer.bucket_name)
                        op.records_processed = 1

                    logger.info(
                        f"S3 bucket access test successful: {analyzer.bucket_name}",
                        ComponentType.RESEARCH_ANALYZER,
                        "connection_test",
                    )
                    console.print(
                        f"[green]✅ S3 bucket accessible: {analyzer.bucket_name}[/green]"
                    )
                except Exception as e:
                    logger.error(
                        f"S3 connection test failed: {e}",
                        ComponentType.RESEARCH_ANALYZER,
                        "connection_test",
                    )
                    console.print(f"[red]❌ S3 test failed: {e}[/red]")
            else:
                logger.warning(
                    "S3 not configured",
                    ComponentType.RESEARCH_ANALYZER,
                    "connection_test",
                )
                console.print("[yellow]⚠️  S3 not configured[/yellow]")

            logger.info(
                "Connection tests completed",
                ComponentType.RESEARCH_ANALYZER,
                "connection_test",
            )
            return

        # Run analysis with comprehensive logging
        logger.info(
            "Starting research analysis application", ComponentType.RESEARCH_ANALYZER
        )

        if args.local:
            analyzer.run(args.local, is_s3=False, output_file=args.output)
        else:
            analyzer.run(
                "",
                is_s3=True,
                bucket=args.bucket,
                key=args.key,
                output_file=args.output,
            )

        logger.info(
            "Research analysis application completed successfully",
            ComponentType.RESEARCH_ANALYZER,
        )

        # Show final debug summary if debug mode was used
        if debug_config.enabled:
            debug_summary = analyzer.get_debug_summary()
            console.print("\n[bold cyan]Debug Session Summary:[/bold cyan]")
            console.print(
                f"Cost: ${debug_summary['session_stats']['session_cost']:.4f}"
            )
            console.print(
                f"Tokens: {debug_summary['session_stats']['session_tokens']:,}"
            )
            console.print(
                f"API Calls: {debug_summary['session_stats']['session_api_calls']}"
            )

            if debug_summary["cost_tracker_summary"].get("debug_mode"):
                savings = debug_summary["cost_tracker_summary"]["costs"][
                    "estimated_savings"
                ]
                console.print(f"Estimated Savings: ${savings:.4f}")

    except Exception as e:
        # Log any uncaught exceptions
        if logger:
            logger.critical(
                f"Unhandled exception in main: {e}",
                ComponentType.RESEARCH_ANALYZER,
                stack_trace=str(e),
            )
        console.print(f"[red]Critical error: {e}[/red]")
        raise

    finally:
        # Always close the logger and debug system to ensure data is saved
        if logger:
            close_logger()

        if debug_config.enabled:
            close_debug_logger()


if __name__ == "__main__":
    main()
