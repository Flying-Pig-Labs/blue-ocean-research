#!/usr/bin/env python3
"""
Integration Testing CLI for Individual Component Testing

This CLI provides comprehensive testing capabilities for individual components
of the multi-step LLM pipeline with debug mode integration.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm

# Import our testing components
from src.testing.integration_test_runner import IntegrationTestRunner
from src.testing.component_validator import ComponentValidator
from src.testing.performance_monitor import PerformanceMonitor
from src.testing.report_generator import ReportGenerator

# Import logging and debug systems
from src.utils.pipeline_logger import initialize_logger, get_logger, close_logger
from src.models.logging_models import ComponentType
from src.config import Config
from src.utils.debug_config import initialize_debug_config, is_debug_mode
from src.utils.debug_logger import initialize_debug_logger, close_debug_logger

console = Console()


class IntegrationTestCLI:
    """Main CLI class for integration testing"""

    def __init__(self):
        """Initialize the CLI with all required components"""
        self.config = Config()
        self.logger = initialize_logger(self.config)

        # Initialize debug system
        self.debug_config = initialize_debug_config()
        if self.debug_config.enabled:
            self.debug_logger = initialize_debug_logger()
            console.print("[cyan]Debug mode enabled for testing[/cyan]")

        # Initialize testing components
        self.test_runner = IntegrationTestRunner(self.logger)
        self.validator = ComponentValidator(self.logger)
        self.performance_monitor = PerformanceMonitor(self.logger)
        self.report_generator = ReportGenerator(self.logger)

        # Load test scenarios
        self.scenarios = self._load_test_scenarios()

        console.print("[green]Integration testing CLI initialized[/green]")

    def _load_test_scenarios(self) -> Dict[str, Any]:
        """Load test scenarios from YAML file"""
        scenarios_file = Path("test_scenarios.yaml")
        if not scenarios_file.exists():
            console.print(
                "[yellow]No test_scenarios.yaml found - will use default scenarios[/yellow]"
            )
            return self._get_default_scenarios()

        try:
            import yaml

            with open(scenarios_file, "r") as f:
                scenarios = yaml.safe_load(f)
            console.print(
                f"[green]Loaded {len(scenarios.get('scenarios', {}))} test scenarios[/green]"
            )
            return scenarios
        except ImportError:
            console.print(
                "[yellow]PyYAML not available - using default scenarios[/yellow]"
            )
            return self._get_default_scenarios()
        except Exception as e:
            console.print(f"[red]Error loading scenarios: {e}[/red]")
            return self._get_default_scenarios()

    def _get_default_scenarios(self) -> Dict[str, Any]:
        """Get default test scenarios when YAML file is not available"""
        return {
            "scenarios": {
                "research_analyzer_basic": {
                    "description": "Basic research analysis test",
                    "component": "research_analyzer",
                    "input_file": "tests/fixtures/sample_research.json",
                    "expected_outputs": ["pain_points", "personas", "solutions"],
                    "timeout": 60,
                },
                "jobs_researcher_basic": {
                    "description": "Basic jobs researcher test",
                    "component": "jobs_researcher",
                    "input_data": {"analysis": "test data"},
                    "expected_outputs": ["jtbd_table"],
                    "timeout": 45,
                },
                "cluster_jtbd_basic": {
                    "description": "Basic JTBD clustering test",
                    "component": "cluster_jtbd",
                    "input_file": "tests/fixtures/sample_zones.json",
                    "expected_outputs": ["clustered_zones"],
                    "timeout": 30,
                },
            }
        }

    def list_scenarios(self) -> None:
        """List all available test scenarios"""
        scenarios = self.scenarios.get("scenarios", {})
        if not scenarios:
            console.print("[red]No test scenarios available[/red]")
            return

        table = Table(title="Available Test Scenarios")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Component", style="green")
        table.add_column("Timeout", style="yellow")

        for name, scenario in scenarios.items():
            table.add_row(
                name,
                scenario.get("description", "No description"),
                scenario.get("component", "Unknown"),
                f"{scenario.get('timeout', 30)}s",
            )

        console.print(table)

    def list_components(self) -> None:
        """List all available components for testing"""
        components = [
            "research_analyzer",
            "jobs_researcher",
            "cluster_jtbd",
            "value_curve_mapper",
            "product_idea_generator",
            "idea_consolidator",
            "main_pipeline",
        ]

        table = Table(title="Available Components")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Description", style="white")

        for component in components:
            # Check if component file exists
            component_file = Path(f"{component}.py")
            if component_file.exists():
                status = "[green]Available[/green]"
            else:
                status = "[red]Not Found[/red]"

            # Get description from component
            description = self._get_component_description(component)
            table.add_row(component, status, description)

        console.print(table)

    def _get_component_description(self, component: str) -> str:
        """Get description for a component"""
        descriptions = {
            "research_analyzer": "Analyzes research data and extracts insights",
            "jobs_researcher": "Researches Jobs-to-be-Done using external APIs",
            "cluster_jtbd": "Clusters JTBD data into zones",
            "value_curve_mapper": "Maps value curves for product positioning",
            "product_idea_generator": "Generates product ideas based on analysis",
            "idea_consolidator": "Consolidates and refines product ideas",
            "main_pipeline": "Main orchestration pipeline",
        }
        return descriptions.get(component, "No description available")

    def run_component_test(
        self, component: str, scenario: Optional[str] = None, debug_mode: bool = False
    ) -> Dict[str, Any]:
        """Run test for a specific component"""
        console.print(f"\n[bold cyan]Testing Component: {component}[/bold cyan]")

        if debug_mode or self.debug_config.enabled:
            console.print(
                "[yellow]Running in debug mode - cost tracking enabled[/yellow]"
            )

        # Start performance monitoring
        test_session = self.performance_monitor.start_session(
            f"component_test_{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task(f"Testing {component}...", total=4)

                # Step 1: Load and validate component
                progress.update(task, description="Loading component...")
                result = self.test_runner.load_component(component)
                if not result.success:
                    return result.to_dict()
                progress.advance(task)

                # Step 2: Prepare test data
                progress.update(task, description="Preparing test data...")
                test_data = self._prepare_test_data(component, scenario)
                progress.advance(task)

                # Step 3: Execute test
                progress.update(task, description="Executing test...")
                execution_result = self.test_runner.execute_test(
                    component, test_data, debug_mode
                )
                progress.advance(task)

                # Step 4: Validate results
                progress.update(task, description="Validating results...")
                validation_result = self.validator.validate_component_output(
                    component,
                    execution_result.output,
                    test_data.get("expected_outputs", []),
                )
                progress.advance(task)

            # Stop performance monitoring
            performance_data = self.performance_monitor.stop_session(test_session)

            # Compile final result
            final_result = {
                "component": component,
                "scenario": scenario or "default",
                "timestamp": datetime.now().isoformat(),
                "success": execution_result.success and validation_result.is_valid,
                "execution": execution_result.to_dict(),
                "validation": validation_result.to_dict(),
                "performance": performance_data,
                "debug_mode": debug_mode or self.debug_config.enabled,
            }

            # Display summary
            self._display_test_summary(final_result)

            return final_result

        except Exception as e:
            self.logger.error(
                f"Error during component test: {e}", ComponentType.MAIN_PIPELINE
            )
            console.print(f"[red]Test failed with error: {e}[/red]")
            return {
                "component": component,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _prepare_test_data(
        self, component: str, scenario: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare test data for a component"""
        if scenario and scenario in self.scenarios.get("scenarios", {}):
            scenario_data = self.scenarios["scenarios"][scenario]

            # Load input file if specified
            if "input_file" in scenario_data:
                input_file = Path(scenario_data["input_file"])
                if input_file.exists():
                    try:
                        with open(input_file, "r") as f:
                            if input_file.suffix == ".json":
                                input_data = json.load(f)
                            else:
                                input_data = f.read()
                        scenario_data["input_data"] = input_data
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not load {input_file}: {e}[/yellow]"
                        )

            return scenario_data

        # Use default test data
        return self._get_default_test_data(component)

    def _get_default_test_data(self, component: str) -> Dict[str, Any]:
        """Get default test data for a component"""
        default_data = {
            "research_analyzer": {
                "input_data": {"research_content": "Sample research data for testing"},
                "expected_outputs": ["pain_points", "personas", "solutions"],
            },
            "jobs_researcher": {
                "input_data": {"analysis_results": "Sample analysis data"},
                "expected_outputs": ["jtbd_table"],
            },
            "cluster_jtbd": {
                "input_data": {"jtbd_data": "Sample JTBD data"},
                "expected_outputs": ["clustered_zones"],
            },
        }
        return default_data.get(component, {"input_data": {}, "expected_outputs": []})

    def _display_test_summary(self, result: Dict[str, Any]) -> None:
        """Display a summary of test results"""
        success = result.get("success", False)
        component = result.get("component", "Unknown")

        # Create summary panel
        status_text = "[green]✅ PASSED[/green]" if success else "[red]❌ FAILED[/red]"
        panel_content = f"""
**Component:** {component}
**Status:** {status_text}
**Timestamp:** {result.get("timestamp", "Unknown")}
**Debug Mode:** {"Yes" if result.get("debug_mode", False) else "No"}
        """

        # Add performance data if available
        if "performance" in result:
            perf = result["performance"]
            panel_content += f"""
**Duration:** {perf.get("duration_seconds", 0):.2f}s
**API Calls:** {perf.get("api_calls", 0)}
**Total Tokens:** {perf.get("total_tokens", 0):,}
**Estimated Cost:** ${perf.get("estimated_cost", 0):.4f}
            """

        console.print(Panel(panel_content, title=f"Test Summary: {component}"))

        # Show validation details if failed
        if not success and "validation" in result:
            validation = result["validation"]
            if validation.get("errors"):
                console.print("\n[red]Validation Errors:[/red]")
                for error in validation["errors"]:
                    console.print(f"  • {error}")

    def run_interactive_mode(self) -> None:
        """Run in interactive mode with user prompts"""
        console.print(
            Panel.fit(
                "[bold green]Integration Testing - Interactive Mode[/bold green]\n"
                "Select components and scenarios interactively",
                border_style="green",
            )
        )

        while True:
            # Show main menu
            choice = Prompt.ask(
                "\nChoose an option",
                choices=["test", "list-components", "list-scenarios", "quit"],
                default="test",
            )

            if choice == "quit":
                break
            elif choice == "list-components":
                self.list_components()
            elif choice == "list-scenarios":
                self.list_scenarios()
            elif choice == "test":
                # Get component to test
                component = Prompt.ask("Enter component name")

                # Ask about scenario
                use_scenario = Confirm.ask("Use a specific scenario?", default=False)
                scenario = None
                if use_scenario:
                    scenarios = list(self.scenarios.get("scenarios", {}).keys())
                    if scenarios:
                        scenario = Prompt.ask(
                            "Choose scenario",
                            choices=scenarios + ["none"],
                            default="none",
                        )
                        if scenario == "none":
                            scenario = None

                # Ask about debug mode
                debug_mode = Confirm.ask(
                    "Enable debug mode?", default=self.debug_config.enabled
                )

                # Run the test
                result = self.run_component_test(component, scenario, debug_mode)

                # Ask about generating report
                if Confirm.ask("Generate detailed HTML report?", default=False):
                    report_path = self.report_generator.generate_report([result])
                    console.print(f"[green]Report generated: {report_path}[/green]")

    def run_batch_tests(
        self, components: List[str], debug_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Run tests for multiple components in batch"""
        console.print(
            f"\n[bold cyan]Running Batch Tests for {len(components)} components[/bold cyan]"
        )

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ) as progress:
            batch_task = progress.add_task(
                "Running batch tests...", total=len(components)
            )

            for component in components:
                progress.update(batch_task, description=f"Testing {component}...")
                result = self.run_component_test(component, debug_mode=debug_mode)
                results.append(result)
                progress.advance(batch_task)

        # Generate batch summary
        self._display_batch_summary(results)

        return results

    def _display_batch_summary(self, results: List[Dict[str, Any]]) -> None:
        """Display summary of batch test results"""
        passed = sum(1 for r in results if r.get("success", False))
        failed = len(results) - passed

        table = Table(title="Batch Test Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Duration", style="yellow")
        table.add_column("Cost", style="green")

        total_cost = 0
        total_duration = 0

        for result in results:
            component = result.get("component", "Unknown")
            success = result.get("success", False)
            status = "[green]✅ PASSED[/green]" if success else "[red]❌ FAILED[/red]"

            perf = result.get("performance", {})
            duration = perf.get("duration_seconds", 0)
            cost = perf.get("estimated_cost", 0)

            total_duration += duration
            total_cost += cost

            table.add_row(component, status, f"{duration:.2f}s", f"${cost:.4f}")

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {passed} passed, {failed} failed")
        console.print(f"[bold]Total Duration:[/bold] {total_duration:.2f}s")
        console.print(f"[bold]Total Cost:[/bold] ${total_cost:.4f}")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description="Integration Testing CLI for Individual Component Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_integration.py --list-components           # List all available components
  python test_integration.py --list-scenarios            # List all test scenarios
  python test_integration.py --test research_analyzer    # Test specific component
  python test_integration.py --test research_analyzer --scenario basic
  python test_integration.py --interactive               # Interactive mode
  python test_integration.py --batch all                 # Run all tests
  python test_integration.py --test jobs_researcher --debug
        """,
    )

    parser.add_argument(
        "--list-components",
        action="store_true",
        help="List all available components for testing",
    )

    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List all available test scenarios",
    )

    parser.add_argument("--test", type=str, help="Test a specific component")

    parser.add_argument("--scenario", type=str, help="Use a specific test scenario")

    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )

    parser.add_argument(
        "--batch",
        type=str,
        help="Run batch tests (comma-separated component names or 'all')",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode for cost tracking"
    )

    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate HTML report of test results",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_reports",
        help="Output directory for reports (default: test_reports)",
    )

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Initialize CLI
        cli = IntegrationTestCLI()

        # Handle different command modes
        if args.list_components:
            cli.list_components()

        elif args.list_scenarios:
            cli.list_scenarios()

        elif args.interactive:
            cli.run_interactive_mode()

        elif args.test:
            result = cli.run_component_test(args.test, args.scenario, args.debug)

            if args.generate_report:
                report_path = cli.report_generator.generate_report(
                    [result], args.output_dir
                )
                console.print(f"[green]Report generated: {report_path}[/green]")

        elif args.batch:
            if args.batch == "all":
                components = [
                    "research_analyzer",
                    "jobs_researcher",
                    "cluster_jtbd",
                    "value_curve_mapper",
                    "product_idea_generator",
                    "idea_consolidator",
                ]
            else:
                components = [c.strip() for c in args.batch.split(",")]

            results = cli.run_batch_tests(components, args.debug)

            if args.generate_report:
                report_path = cli.report_generator.generate_report(
                    results, args.output_dir
                )
                console.print(f"[green]Batch report generated: {report_path}[/green]")

        else:
            # No specific command - show help
            parser.print_help()

    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        # Clean up logging
        if "cli" in locals():
            close_logger()
            if cli.debug_config.enabled:
                close_debug_logger()


if __name__ == "__main__":
    main()
