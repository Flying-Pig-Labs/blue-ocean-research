#!/usr/bin/env python3
"""
Multi-step LLM Application with Anthropic
Supports both interactive and headless modes
"""

import os
import sys
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()

# Initialize Rich console for better output
console = Console()

@dataclass
class WorkflowStep:
    """Represents a single step in the LLM workflow"""
    name: str
    system_prompt: str
    user_prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7

class MultiStepLLMApp:
    """Main application class for multi-step LLM workflows"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the app with Anthropic client"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not found in environment variables![/red]")
            console.print("Please create a .env file with your API key or set it as an environment variable.")
            sys.exit(1)
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
        except Exception as e:
            console.print(f"[red]Error initializing Anthropic client: {e}[/red]")
            sys.exit(1)
    
    def create_workflow_steps(self) -> List[WorkflowStep]:
        """Define the multi-step workflow"""
        return [
            WorkflowStep(
                name="Story Ideation",
                system_prompt="You are a creative writing assistant specializing in story ideation.",
                user_prompt="Generate a unique story concept about a programmer who discovers their code is changing reality. Include genre, main character, and central conflict.",
                max_tokens=500
            ),
            WorkflowStep(
                name="Character Development",
                system_prompt="You are a character development expert. Based on the previous story concept, develop the main character.",
                user_prompt="Develop the main character from the previous concept. Include their background, personality traits, motivations, and character arc.",
                max_tokens=700
            ),
            WorkflowStep(
                name="Plot Outline",
                system_prompt="You are a plot structure specialist. Based on the story concept and character, create a detailed plot outline.",
                user_prompt="Create a three-act plot outline with key turning points, based on the concept and character developed previously.",
                max_tokens=1000
            ),
            WorkflowStep(
                name="Opening Scene",
                system_prompt="You are a narrative writer. Based on all previous elements, write an engaging opening scene.",
                user_prompt="Write the opening scene (500-700 words) that introduces the character and hints at the central conflict.",
                max_tokens=1200
            ),
            WorkflowStep(
                name="Story Analysis",
                system_prompt="You are a literary critic and editor.",
                user_prompt="Analyze the story elements created so far. Identify strengths, potential weaknesses, and suggest improvements.",
                max_tokens=800
            )
        ]
    
    def execute_step(self, step: WorkflowStep, context: str = "") -> str:
        """Execute a single workflow step"""
        try:
            # Prepare the full prompt with context from previous steps
            full_prompt = step.user_prompt
            if context:
                full_prompt = f"Previous context:\n{context}\n\nCurrent task:\n{step.user_prompt}"
            
            # Make API call
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(f"Processing {step.name}...", total=None)
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=step.max_tokens,
                    temperature=step.temperature,
                    system=step.system_prompt,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ]
                )
                
                progress.update(task, completed=True)
            
            return message.content[0].text
            
        except anthropic.RateLimitError:
            console.print("[yellow]Rate limit reached. Please wait a moment and try again.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error during API call: {e}[/red]")
            sys.exit(1)
    
    def run_interactive(self):
        """Run the workflow in interactive mode"""
        console.print(Panel.fit(
            "[bold green]Multi-Step LLM Workflow - Interactive Mode[/bold green]\n"
            "Press Enter after each step to continue, or 'q' to quit.",
            border_style="green"
        ))
        
        steps = self.create_workflow_steps()
        context = ""
        results = {}
        
        for i, step in enumerate(steps, 1):
            console.print(f"\n[bold cyan]Step {i}/{len(steps)}: {step.name}[/bold cyan]")
            console.print(f"[dim]{step.user_prompt}[/dim]\n")
            
            # Execute the step
            result = self.execute_step(step, context)
            results[step.name] = result
            
            # Display the result
            console.print(Panel(
                Markdown(result),
                title=f"[bold]{step.name} Result[/bold]",
                border_style="blue"
            ))
            
            # Update context for next step
            context += f"\n\n{step.name}:\n{result}"
            
            # Wait for user input
            if i < len(steps):
                user_input = console.input("\n[yellow]Press Enter to continue to next step, or 'q' to quit: [/yellow]")
                if user_input.lower() == 'q':
                    console.print("[red]Workflow interrupted by user.[/red]")
                    break
        
        if len(results) == len(steps):
            console.print("\n[bold green]✅ Workflow completed successfully![/bold green]")
            self._save_results(results)
    
    def run_headless(self):
        """Run the workflow in headless mode (no user interaction)"""
        console.print(Panel.fit(
            "[bold green]Multi-Step LLM Workflow - Headless Mode[/bold green]\n"
            "Running all steps automatically...",
            border_style="green"
        ))
        
        steps = self.create_workflow_steps()
        context = ""
        results = {}
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing workflow...", total=len(steps))
            
            for step in steps:
                console.print(f"\n[bold cyan]Executing: {step.name}[/bold cyan]")
                
                # Execute the step
                result = self.execute_step(step, context)
                results[step.name] = result
                
                # Update context for next step
                context += f"\n\n{step.name}:\n{result}"
                
                # Update progress
                progress.update(task, advance=1)
                
                # Brief summary (not full result in headless mode)
                console.print(f"[green]✓[/green] {step.name} completed ({len(result)} chars)")
        
        console.print("\n[bold green]✅ All steps completed successfully![/bold green]")
        self._save_results(results)
    
    def _save_results(self, results: Dict[str, str]):
        """Save results to a file"""
        filename = "workflow_results.md"
        with open(filename, "w") as f:
            f.write("# Multi-Step LLM Workflow Results\n\n")
            for step_name, result in results.items():
                f.write(f"## {step_name}\n\n")
                f.write(f"{result}\n\n")
                f.write("---\n\n")
        console.print(f"\n[green]Results saved to {filename}[/green]")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-step LLM application with Anthropic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run in interactive mode
  python main.py --headless         # Run in headless mode
  python main.py --test             # Test API connection
        """
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no user interaction)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test API connection"
    )
    
    args = parser.parse_args()
    
    # Initialize the app
    app = MultiStepLLMApp()
    
    if args.test:
        # Test mode - just verify API connection
        console.print("[cyan]Testing Anthropic API connection...[/cyan]")
        try:
            response = app.client.messages.create(
                model=app.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'API connected!'"}]
            )
            console.print(f"[green]✅ {response.content[0].text}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Connection failed: {e}[/red]")
        return
    
    # Run the appropriate mode
    if args.headless:
        app.run_headless()
    else:
        app.run_interactive()

if __name__ == "__main__":
    main()