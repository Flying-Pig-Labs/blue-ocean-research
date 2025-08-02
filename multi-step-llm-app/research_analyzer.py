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
    system_prompt: str = "You are an expert analyst providing detailed, actionable insights."
    max_tokens: int = 2000
    temperature: float = 0.7

class ResearchAnalyzer:
    """Main application for parallel research analysis"""
    
    def __init__(self):
        """Initialize AWS S3 and Anthropic clients"""
        # Anthropic setup
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not found![/red]")
            sys.exit(1)
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model_sonnet = "claude-3-5-sonnet-20241022"
            self.model_opus = "claude-3-opus-20240229"
        except Exception as e:
            console.print(f"[red]Error initializing Anthropic client: {e}[/red]")
            sys.exit(1)
        
        # AWS S3 setup
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.file_key = os.getenv("S3_FILE_KEY")
        
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            console.print("[yellow]Warning: AWS credentials not fully configured. Use --local flag for local file.[/yellow]")
            self.s3_client = None
        else:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )
            except Exception as e:
                console.print(f"[red]Error initializing S3 client: {e}[/red]")
                self.s3_client = None
    
    def pull_from_s3(self, bucket: Optional[str] = None, key: Optional[str] = None) -> Dict:
        """Pull JSON file from S3"""
        bucket = bucket or self.bucket_name
        key = key or self.file_key
        
        if not self.s3_client:
            console.print("[red]S3 client not initialized. Check AWS credentials.[/red]")
            sys.exit(1)
        
        console.print(f"[cyan]Pulling file from S3: s3://{bucket}/{key}[/cyan]")
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            console.print("[green]✅ Successfully pulled file from S3[/green]")
            return data
        except ClientError as e:
            console.print(f"[red]Error pulling from S3: {e}[/red]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            sys.exit(1)
    
    def load_local_file(self, filepath: str) -> Dict:
        """Load JSON file from local filesystem"""
        console.print(f"[cyan]Loading local file: {filepath}[/cyan]")
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            console.print("[green]✅ Successfully loaded local file[/green]")
            return data
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            sys.exit(1)
    
    def extract_content(self, data: Dict) -> str:
        """Extract content attribute from JSON data"""
        if 'content' in data:
            return data['content']
        elif 'research' in data and 'content' in data['research']:
            return data['research']['content']
        else:
            # Try to find content in nested structure
            console.print("[yellow]'content' attribute not found at expected location. Searching...[/yellow]")
            content = self._find_content_recursive(data)
            if content:
                return content
            else:
                console.print("[red]Error: Could not find 'content' attribute in JSON[/red]")
                console.print("JSON structure:", data.keys() if isinstance(data, dict) else type(data))
                sys.exit(1)
    
    def _find_content_recursive(self, obj, depth=0, max_depth=5):
        """Recursively search for content attribute"""
        if depth > max_depth:
            return None
        
        if isinstance(obj, dict):
            if 'content' in obj:
                return obj['content']
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
                model="sonnet"
            ),
            AnalysisTask(
                name="User Personas",
                prompt=(
                    "Given this research document, what are some of the customer or user personas "
                    "that you can identify? These should reflect the types of people who would want "
                    "help with your product or who need assistance in this space. "
                    "Please describe each persona with demographics, needs, goals, and pain points."
                ),
                model="sonnet"
            ),
            AnalysisTask(
                name="Pain Points",
                prompt=(
                    "Within this research document, what are the key pain points that you observe "
                    "or can infer based on the research presented? Please categorize these pain points "
                    "by severity, frequency, and impact on users. Include both explicit and implicit "
                    "pain points you can deduce from the research."
                ),
                model="opus"
            ),
            AnalysisTask(
                name="Solution Types",
                prompt=(
                    "What are the solution types that you see described or that can be inferred "
                    "from this research? Please categorize these solutions by approach, technology, "
                    "implementation complexity, and potential effectiveness. Include both existing "
                    "and potential solutions that could address the identified needs."
                ),
                model="opus"
            )
        ]
    
    def analyze_with_llm(self, task: AnalysisTask, research_content: str) -> Tuple[str, str]:
        """Execute a single analysis task with the appropriate model"""
        try:
            # Select the appropriate model
            model = self.model_sonnet if task.model == "sonnet" else self.model_opus
            model_display = "Sonnet" if task.model == "sonnet" else "Opus"
            
            # Prepare the prompt with research content
            full_prompt = f"Research Document:\n\n{research_content}\n\n{task.prompt}"
            
            console.print(f"[cyan]Running {task.name} analysis with Claude {model_display}...[/cyan]")
            
            # Make API call
            message = self.client.messages.create(
                model=model,
                max_tokens=task.max_tokens,
                temperature=task.temperature,
                system=task.system_prompt,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            return (task.name, message.content[0].text)
            
        except anthropic.RateLimitError:
            console.print(f"[yellow]Rate limit reached for {task.name}. Retrying...[/yellow]")
            import time
            time.sleep(5)
            return self.analyze_with_llm(task, research_content)
        except Exception as e:
            console.print(f"[red]Error in {task.name} analysis: {e}[/red]")
            return (task.name, f"Error: {str(e)}")
    
    def run_parallel_analysis(self, research_content: str) -> Dict[str, str]:
        """Run all analysis tasks in parallel"""
        tasks = self.create_analysis_tasks()
        results = {}
        
        console.print("\n[bold cyan]Starting parallel analysis with 4 LLM calls...[/bold cyan]")
        
        # Create a summary table
        table = Table(title="Analysis Tasks")
        table.add_column("Task", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Status", style="green")
        
        for task in tasks:
            table.add_row(task.name, f"Claude {task.model.title()}", "Queued")
        
        console.print(table)
        console.print()
        
        # Execute tasks in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            
            progress_task = progress.add_task("[cyan]Running parallel analysis...", total=len(tasks))
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self.analyze_with_llm, task, research_content): task
                    for task in tasks
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    task_name, result = future.result()
                    results[task_name] = result
                    progress.update(progress_task, advance=1)
                    console.print(f"[green]✅ Completed: {task_name}[/green]")
        
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
    
    def save_results(self, combined_results: str, output_file: str = "analysis_results.md"):
        """Save combined results to file"""
        with open(output_file, 'w') as f:
            f.write(combined_results)
        console.print(f"\n[green]✅ Results saved to {output_file}[/green]")
    
    def run(self, source: str, is_s3: bool = True, bucket: Optional[str] = None, 
            key: Optional[str] = None, output_file: str = "analysis_results.md"):
        """Main execution flow"""
        console.print(Panel.fit(
            "[bold green]Research Analysis with Parallel LLM Processing[/bold green]\n"
            "Using Claude Sonnet and Opus for comprehensive analysis",
            border_style="green"
        ))
        
        # Step 1: Load data
        if is_s3:
            data = self.pull_from_s3(bucket, key)
        else:
            data = self.load_local_file(source)
        
        # Step 2: Extract content
        research_content = self.extract_content(data)
        console.print(f"\n[green]✅ Extracted research content ({len(research_content)} characters)[/green]")
        
        # Step 3: Run parallel analysis
        results = self.run_parallel_analysis(research_content)
        
        # Step 4: Combine results
        combined_results = self.combine_results(results)
        
        # Step 5: Display summary
        console.print("\n[bold green]Analysis Complete![/bold green]")
        console.print(Panel(
            f"• Industry Verticals: {len(results.get('Industry Verticals', '').split())} words\n"
            f"• User Personas: {len(results.get('User Personas', '').split())} words\n"
            f"• Pain Points: {len(results.get('Pain Points', '').split())} words\n"
            f"• Solution Types: {len(results.get('Solution Types', '').split())} words\n"
            f"\nTotal output: {len(combined_results.split())} words",
            title="Summary",
            border_style="blue"
        ))
        
        # Step 6: Save results
        self.save_results(combined_results, output_file)
        
        # Optional: Display preview
        if console.input("\n[yellow]Display preview of results? (y/n): [/yellow]").lower() == 'y':
            preview = combined_results[:1000] + "..." if len(combined_results) > 1000 else combined_results
            console.print(Panel(Markdown(preview), title="Preview", border_style="dim"))
        
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
        """
    )
    
    parser.add_argument("--local", type=str, help="Use local file instead of S3")
    parser.add_argument("--bucket", type=str, help="S3 bucket name (overrides .env)")
    parser.add_argument("--key", type=str, help="S3 object key (overrides .env)")
    parser.add_argument("--output", type=str, default="analysis_results.md", 
                       help="Output file name (default: analysis_results.md)")
    parser.add_argument("--test", action="store_true", help="Test connections only")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ResearchAnalyzer()
    
    if args.test:
        # Test mode
        console.print("[cyan]Testing connections...[/cyan]")
        
        # Test Anthropic
        try:
            response = analyzer.client.messages.create(
                model=analyzer.model_sonnet,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Sonnet connected!'"}]
            )
            console.print(f"[green]✅ Claude Sonnet: {response.content[0].text}[/green]")
            
            response = analyzer.client.messages.create(
                model=analyzer.model_opus,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Opus connected!'"}]
            )
            console.print(f"[green]✅ Claude Opus: {response.content[0].text}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Anthropic test failed: {e}[/red]")
        
        # Test S3
        if analyzer.s3_client:
            try:
                analyzer.s3_client.head_bucket(Bucket=analyzer.bucket_name)
                console.print(f"[green]✅ S3 bucket accessible: {analyzer.bucket_name}[/green]")
            except Exception as e:
                console.print(f"[red]❌ S3 test failed: {e}[/red]")
        else:
            console.print("[yellow]⚠️  S3 not configured[/yellow]")
        
        return
    
    # Run analysis
    if args.local:
        analyzer.run(args.local, is_s3=False, output_file=args.output)
    else:
        analyzer.run("", is_s3=True, bucket=args.bucket, key=args.key, output_file=args.output)

if __name__ == "__main__":
    main()