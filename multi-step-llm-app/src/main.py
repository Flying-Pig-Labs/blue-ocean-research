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

# Import logging system
from src.utils.pipeline_logger import initialize_logger, get_logger, close_logger
from src.models.logging_models import ComponentType, ModelProvider
from src.config import Config

# Import debug system
from src.utils.debug_config import initialize_debug_config, is_debug_mode
from src.utils.debug_logger import initialize_debug_logger, close_debug_logger
from src.utils.debug_dashboard import get_debug_dashboard
from src.utils.debug_aware_component import DebugAwareComponent

# Import AWS secrets manager
try:
    from src.utils.secrets_manager import load_aws_secrets, get_api_key
    AWS_SECRETS_AVAILABLE = True
except ImportError:
    AWS_SECRETS_AVAILABLE = False

# Load environment variables
load_dotenv()

# Try to load AWS secrets if available
if AWS_SECRETS_AVAILABLE and not os.getenv("ANTHROPIC_API_KEY"):
    try:
        load_aws_secrets(profile="mvp")
    except Exception as e:
        print(f"Note: Could not load AWS secrets: {e}")

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


class MultiStepLLMApp(DebugAwareComponent):
    """Main application class for multi-step LLM workflows"""

    def __init__(self, api_key: Optional[str] = None, logger=None):
        """Initialize the app with Anthropic client"""
        # Initialize debug-aware component
        super().__init__(ComponentType.MAIN_PIPELINE, logger)

        # Initialize logger if not provided
        self.logger = logger or get_logger()
        if not self.logger:
            # Initialize a new logger for this component
            config = Config()
            self.logger = initialize_logger(config)

        self.logger.info(
            "Initializing Multi-step LLM Application", ComponentType.MAIN_PIPELINE
        )

        # Show debug mode status
        if self.debug_enabled:
            console.print(
                Panel.fit(
                    "[bold yellow]🐛 DEBUG MODE ENABLED[/bold yellow]\n"
                    "Using cost-effective model switching and token limits\n"
                    "See debug logs for detailed cost tracking",
                    border_style="yellow",
                )
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.logger.error(
                "ANTHROPIC_API_KEY not found in environment variables",
                ComponentType.MAIN_PIPELINE,
            )
            console.print(
                "[red]Error: ANTHROPIC_API_KEY not found![/red]"
            )
            console.print(
                "Please either:\n"
                "1. Set AWS_PROFILE=mvp to load from AWS Secrets Manager\n"
                "2. Create a .env file with your API key\n"
                "3. Set it as an environment variable"
            )
            sys.exit(1)

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.production_model = "claude-3-5-sonnet-20241022"

            # Get the actual model to use (debug or production)
            self.model = self.get_debug_model(self.production_model, "main_workflow")

            if self.debug_enabled and self.model != self.production_model:
                console.print(
                    f"[cyan]Model switched for debug: {self.production_model} → {self.model}[/cyan]"
                )

            self.logger.info(
                "Anthropic client initialized successfully",
                ComponentType.MAIN_PIPELINE,
                metadata={
                    "production_model": self.production_model,
                    "actual_model": self.model,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Error initializing Anthropic client: {e}", ComponentType.MAIN_PIPELINE
            )
            console.print(f"[red]Error initializing Anthropic client: {e}[/red]")
            sys.exit(1)

    def get_default_model(self) -> str:
        """Get the default production model for this component"""
        return self.production_model

    def create_workflow_steps(self) -> List[WorkflowStep]:
        """Define the multi-step workflow"""
        return [
            WorkflowStep(
                name="Story Ideation",
                system_prompt="You are a creative writing assistant specializing in story ideation.",
                user_prompt="Generate a unique story concept about a programmer who discovers their code is changing reality. Include genre, main character, and central conflict.",
                max_tokens=500,
            ),
            WorkflowStep(
                name="Character Development",
                system_prompt="You are a character development expert. Based on the previous story concept, develop the main character.",
                user_prompt="Develop the main character from the previous concept. Include their background, personality traits, motivations, and character arc.",
                max_tokens=700,
            ),
            WorkflowStep(
                name="Plot Outline",
                system_prompt="You are a plot structure specialist. Based on the story concept and character, create a detailed plot outline.",
                user_prompt="Create a three-act plot outline with key turning points, based on the concept and character developed previously.",
                max_tokens=1000,
            ),
            WorkflowStep(
                name="Opening Scene",
                system_prompt="You are a narrative writer. Based on all previous elements, write an engaging opening scene.",
                user_prompt="Write the opening scene (500-700 words) that introduces the character and hints at the central conflict.",
                max_tokens=1200,
            ),
            WorkflowStep(
                name="Story Analysis",
                system_prompt="You are a literary critic and editor.",
                user_prompt="Analyze the story elements created so far. Identify strengths, potential weaknesses, and suggest improvements.",
                max_tokens=800,
            ),
        ]

    def execute_step(self, step: WorkflowStep, context: str = "") -> str:
        """Execute a single workflow step with debug-aware processing"""
        # Prepare the full prompt with context from previous steps
        full_prompt = step.user_prompt
        if context:
            full_prompt = (
                f"Previous context:\n{context}\n\nCurrent task:\n{step.user_prompt}"
            )

        # Apply debug content truncation if needed
        if self.debug_enabled:
            full_prompt = self.truncate_content_for_debug(
                full_prompt, f"workflow_step_{step.name}"
            )
            # Add debug prompt suffix to encourage concise responses
            step.system_prompt += self.create_debug_prompt_suffix()

        # Check token limits before proceeding
        estimated_tokens = (
            len(full_prompt) + len(step.system_prompt) + step.max_tokens
        ) // 4
        if not self.check_token_limits(estimated_tokens, f"workflow_step_{step.name}"):
            console.print(
                f"[red]Skipping step {step.name} - would exceed debug limits[/red]"
            )
            return (
                f"[STEP SKIPPED IN DEBUG MODE: {step.name} - would exceed token limits]"
            )

        self.logger.info(
            f"Starting workflow step: {step.name}",
            ComponentType.MAIN_PIPELINE,
            "workflow_step",
            metadata={"step": step.name, "max_tokens": step.max_tokens},
        )

        # Use debug-aware API call tracking
        with self.debug_api_call(
            self.model, f"workflow_step_{step.name}", len(full_prompt) // 4
        ) as call_data:
            try:
                # Calculate approximate input tokens
                estimated_prompt_tokens = len(full_prompt + step.system_prompt) // 4
                call_data["actual_prompt_tokens"] = estimated_prompt_tokens

                # Make API call with progress tracking
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
                        messages=[{"role": "user", "content": full_prompt}],
                    )

                    progress.update(task, completed=True)

                response_text = message.content[0].text

                # Update call data with response information
                call_data["completion_tokens"] = len(response_text) // 4

                self.logger.info(
                    f"Completed workflow step: {step.name} ({len(response_text)} chars)",
                    ComponentType.MAIN_PIPELINE,
                    "workflow_step",
                    metadata={"step": step.name, "response_length": len(response_text)},
                )

                return response_text

            except anthropic.RateLimitError as e:
                self.logger.warning(
                    f"Rate limit reached for step {step.name}",
                    ComponentType.MAIN_PIPELINE,
                    "workflow_step",
                )
                console.print(
                    "[yellow]Rate limit reached. Please wait a moment and try again.[/yellow]"
                )
                sys.exit(1)

            except Exception as e:
                self.logger.error(
                    f"Error during API call for step {step.name}: {e}",
                    ComponentType.MAIN_PIPELINE,
                    "workflow_step",
                )
                console.print(f"[red]Error during API call: {e}[/red]")
                sys.exit(1)

    def run_interactive(self):
        """Run the workflow in interactive mode"""
        with self.logger.log_operation(
            ComponentType.MAIN_PIPELINE, "interactive_workflow"
        ) as op:
            self.logger.info(
                "Starting interactive workflow",
                ComponentType.MAIN_PIPELINE,
                "interactive_workflow",
            )

            console.print(
                Panel.fit(
                    "[bold green]Multi-Step LLM Workflow - Interactive Mode[/bold green]\n"
                    "Press Enter after each step to continue, or 'q' to quit.",
                    border_style="green",
                )
            )

            steps = self.create_workflow_steps()
            context = ""
            results = {}

            # Create progress tracker
            progress_id = self.logger.create_progress_bar(
                "Interactive workflow progress", len(steps), ComponentType.MAIN_PIPELINE
            )

            for i, step in enumerate(steps, 1):
                self.logger.info(
                    f"Starting step {i}/{len(steps)}: {step.name}",
                    ComponentType.MAIN_PIPELINE,
                    "interactive_workflow",
                    metadata={"step_number": i, "step_name": step.name},
                )

                console.print(
                    f"\n[bold cyan]Step {i}/{len(steps)}: {step.name}[/bold cyan]"
                )
                console.print(f"[dim]{step.user_prompt}[/dim]\n")

                # Execute the step
                result = self.execute_step(step, context)
                results[step.name] = result

                # Update progress
                self.logger.update_progress(progress_id, advance=1)

                # Display the result
                console.print(
                    Panel(
                        Markdown(result),
                        title=f"[bold]{step.name} Result[/bold]",
                        border_style="blue",
                    )
                )

                # Update context for next step
                context += f"\n\n{step.name}:\n{result}"

                # Wait for user input
                if i < len(steps):
                    user_input = console.input(
                        "\n[yellow]Press Enter to continue to next step, or 'q' to quit: [/yellow]"
                    )
                    if user_input.lower() == "q":
                        self.logger.warning(
                            "Workflow interrupted by user",
                            ComponentType.MAIN_PIPELINE,
                            "interactive_workflow",
                        )
                        console.print("[red]Workflow interrupted by user.[/red]")
                        break

            # Complete progress tracking
            self.logger.complete_progress(progress_id)

            # Update operation metadata
            op.records_processed = len(results)
            total_output_size = sum(len(result) for result in results.values())
            op.output_data_size = total_output_size

            if len(results) == len(steps):
                self.logger.info(
                    "Interactive workflow completed successfully",
                    ComponentType.MAIN_PIPELINE,
                    "interactive_workflow",
                    metadata={
                        "steps_completed": len(results),
                        "total_output_chars": total_output_size,
                    },
                )
                console.print(
                    "\n[bold green]✅ Workflow completed successfully![/bold green]"
                )
                self._save_results(results)
            else:
                self.logger.warning(
                    f"Interactive workflow incomplete: {len(results)}/{len(steps)} steps",
                    ComponentType.MAIN_PIPELINE,
                    "interactive_workflow",
                )

    def run_headless(self):
        """Run the workflow in headless mode (no user interaction)"""
        with self.logger.log_operation(
            ComponentType.MAIN_PIPELINE, "headless_workflow"
        ) as op:
            self.logger.info(
                "Starting headless workflow",
                ComponentType.MAIN_PIPELINE,
                "headless_workflow",
            )

            console.print(
                Panel.fit(
                    "[bold green]Multi-Step LLM Workflow - Headless Mode[/bold green]\n"
                    "Running all steps automatically...",
                    border_style="green",
                )
            )

            steps = self.create_workflow_steps()
            context = ""
            results = {}

            # Create progress tracker
            progress_id = self.logger.create_progress_bar(
                "Headless workflow progress", len(steps), ComponentType.MAIN_PIPELINE
            )

            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Processing workflow...", total=len(steps)
                )

                for step in steps:
                    self.logger.info(
                        f"Executing step: {step.name}",
                        ComponentType.MAIN_PIPELINE,
                        "headless_workflow",
                        metadata={"step_name": step.name},
                    )
                    console.print(f"\n[bold cyan]Executing: {step.name}[/bold cyan]")

                    # Execute the step
                    result = self.execute_step(step, context)
                    results[step.name] = result

                    # Update context for next step
                    context += f"\n\n{step.name}:\n{result}"

                    # Update progress bars
                    progress.update(task, advance=1)
                    self.logger.update_progress(progress_id, advance=1)

                    # Brief summary (not full result in headless mode)
                    console.print(
                        f"[green]✓[/green] {step.name} completed ({len(result)} chars)"
                    )

            # Complete progress tracking
            self.logger.complete_progress(progress_id)

            # Update operation metadata
            op.records_processed = len(results)
            total_output_size = sum(len(result) for result in results.values())
            op.output_data_size = total_output_size

            self.logger.info(
                "Headless workflow completed successfully",
                ComponentType.MAIN_PIPELINE,
                "headless_workflow",
                metadata={
                    "steps_completed": len(results),
                    "total_output_chars": total_output_size,
                },
            )
            console.print(
                "\n[bold green]✅ All steps completed successfully![/bold green]"
            )
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
  DEBUG=true python main.py         # Run in debug mode with cost tracking
        """,
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no user interaction)",
    )
    parser.add_argument("--test", action="store_true", help="Test API connection")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--session-id", type=str, help="Custom session ID")
    parser.add_argument(
        "--debug-config", type=str, help="Debug configuration file path"
    )
    parser.add_argument(
        "--debug-dashboard",
        action="store_true",
        help="Show live debug dashboard (requires DEBUG=true)",
    )

    args = parser.parse_args()

    # Initialize debug system first (checks DEBUG environment variable)
    debug_config = initialize_debug_config(args.debug_config)
    if debug_config.enabled:
        debug_logger = initialize_debug_logger()
        dashboard = get_debug_dashboard()
        console.print("[cyan]Debug system initialized[/cyan]")

    # Initialize logging configuration
    config = Config(args.config) if args.config else Config()

    # Initialize the pipeline logger with session management
    logger = initialize_logger(config, args.session_id)

    try:
        # Initialize the app with logger
        app = MultiStepLLMApp(logger=logger)

        if args.test:
            # Test mode with logging
            logger.info(
                "Starting API connection test",
                ComponentType.MAIN_PIPELINE,
                "connection_test",
            )
            console.print("[cyan]Testing Anthropic API connection...[/cyan]")

            try:
                # Use debug-aware API call if debug mode is enabled
                if debug_config.enabled:
                    with app.debug_api_call(
                        app.model, "connection_test", 5
                    ) as call_data:
                        call_data["actual_prompt_tokens"] = 5
                        response = app.client.messages.create(
                            model=app.model,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'API connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5
                else:
                    with logger.track_api_call(
                        ComponentType.MAIN_PIPELINE, ModelProvider.ANTHROPIC, app.model
                    ) as call_data:
                        call_data["prompt_tokens"] = 5
                        response = app.client.messages.create(
                            model=app.model,
                            max_tokens=10,
                            messages=[
                                {"role": "user", "content": "Say 'API connected!'"}
                            ],
                        )
                        call_data["completion_tokens"] = 5

                logger.info(
                    "API connection test successful",
                    ComponentType.MAIN_PIPELINE,
                    "connection_test",
                )
                console.print(f"[green]✅ {response.content[0].text}[/green]")

                # Show debug summary if in debug mode
                if debug_config.enabled:
                    debug_summary = app.get_debug_summary()
                    console.print(
                        f"[dim]Debug session cost: ${debug_summary['session_stats']['session_cost']:.4f}[/dim]"
                    )

            except Exception as e:
                logger.error(
                    f"API connection test failed: {e}",
                    ComponentType.MAIN_PIPELINE,
                    "connection_test",
                )
                console.print(f"[red]❌ Connection failed: {e}[/red]")

            logger.info(
                "Connection test completed",
                ComponentType.MAIN_PIPELINE,
                "connection_test",
            )
            return

        # Run the appropriate mode with comprehensive logging
        logger.info(
            "Starting multi-step LLM application",
            ComponentType.MAIN_PIPELINE,
            metadata={
                "mode": "headless" if args.headless else "interactive",
                "debug_mode": debug_config.enabled,
            },
        )

        # Use debug dashboard if requested and debug mode is enabled
        if args.debug_dashboard and debug_config.enabled:
            dashboard = get_debug_dashboard()
            with dashboard.live_dashboard():
                if args.headless:
                    app.run_headless()
                else:
                    app.run_interactive()
        else:
            if args.headless:
                app.run_headless()
            else:
                app.run_interactive()

        logger.info(
            "Multi-step LLM application completed successfully",
            ComponentType.MAIN_PIPELINE,
        )

        # Show final debug summary if debug mode was used
        if debug_config.enabled:
            debug_summary = app.get_debug_summary()
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
                ComponentType.MAIN_PIPELINE,
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
