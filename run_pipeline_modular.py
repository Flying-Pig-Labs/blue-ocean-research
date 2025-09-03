#!/usr/bin/env python3
"""
Modular Pipeline Runner - Flavor-Driven Ideation Pipeline

This is the NEW modular entry point that supports multiple ideation "flavors"
while maintaining 100% backward compatibility with the baseline behavior.

CRITICAL: The 'baseline' flavor reproduces the EXACT current pipeline behavior.
No prompts, parameters, or logic changes - this is a pure refactor for modularity.

Usage:
    python run_pipeline_modular.py --flavor baseline     # EXACT current behavior  
    python run_pipeline_modular.py --flavor site_location  # New site analysis flavor
    python run_pipeline_modular.py --list-flavors       # Show available flavors
    
Backward Compatibility:
    The baseline flavor ensures existing users get identical results.
    All current command-line arguments are preserved and respected.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from glob import glob
import shutil

# Import the flavor system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flavors.config_schema import FlavorRegistry, FlavorConfig
from run_pipeline import main as original_main, run_module
from flavors.framework_adapter import analyze_zones_with_framework
from flavors.opportunity_synthesis import synthesize_opportunities_from_zones
from flavors.github_writer import write_github_artifacts

import research_analyzer
import jobs_to_reddit
import opportunity_zone_analyzer

def load_flavor_config(flavor_name: str) -> FlavorConfig:
    """Load and validate a flavor configuration."""
    registry = FlavorRegistry(flavors_dir="flavors")
    flavor = registry.get_flavor(flavor_name)
    
    if not flavor:
        available = registry.list_flavors()
        print(f"Error: Flavor '{flavor_name}' not found.")
        print(f"Available flavors: {', '.join(available)}")
        sys.exit(1)
    
    # Validate the flavor
    errors = flavor.validate()
    if errors:
        print(f"Error: Flavor '{flavor_name}' has validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
        
    return flavor

def configure_pipeline_for_flavor(flavor: FlavorConfig):
    """Configure the pipeline environment based on flavor settings."""
    
    # Set model environment variables that modules will read
    for stage, model in flavor.default_models.items():
        env_var = f"FLAVOR_{stage.upper()}_MODEL"
        os.environ[env_var] = model
    
    # Set stage override parameters
    for stage, overrides in flavor.stage_overrides.items():
        for param, value in overrides.items():
            env_var = f"FLAVOR_{stage.upper()}_{param.upper()}"
            os.environ[env_var] = str(value)
    
    # Store flavor config in environment for modules to access
    os.environ["CURRENT_FLAVOR_NAME"] = flavor.name
    os.environ["CURRENT_FLAVOR_CONFIG"] = json.dumps({
        "name": flavor.name,
        "description": flavor.description,
        "framework_type": flavor.framework.framework_type.value,
        "output_schema": flavor.output.schema_type.value,
        "reddit_strategy": flavor.reddit_strategy.__dict__,
        "stage_overrides": flavor.stage_overrides,
        "current_prompts": flavor.custom_prompts if hasattr(flavor, 'custom_prompts') else {}
    })

def main(flavor=None, interactive=False, verbose=False, input_file=None, use_cache=False, skip_github=False):
    """Main entry point for the modular pipeline runner.
    
    Can be called programmatically or from command line.
    """
    
    # If called programmatically, use provided parameters
    if flavor is not None:
        args = type('Args', (), {
            'flavor': flavor,
            'interactive': interactive,
            'verbose': verbose,
            'input': input_file,
            'use_cache': use_cache,
            'skip_github': skip_github,
            'list_flavors': False
        })()
    else:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
        description="Multi-Step LLM Pipeline with Flavor Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Flavors:
  baseline       - Original ERRC-based real estate pipeline (EXACT current behavior)
  site_location  - Site location analysis for commercial real estate
  
Examples:
  python run_pipeline_modular.py --flavor baseline                    # Current behavior
  python run_pipeline_modular.py --flavor baseline --interactive      # Interactive mode
  python run_pipeline_modular.py --flavor site_location --verbose     # New flavor
  python run_pipeline_modular.py --list-flavors                       # Show all flavors
        """
    )
    
    # Flavor selection
    parser.add_argument(
        "--flavor", 
        type=str, 
        default="baseline",
        help="Ideation flavor to use (default: baseline - maintains exact current behavior)"
    )
    
    parser.add_argument(
        "--list-flavors",
        action="store_true",
        help="List all available flavors and exit"
    )
    
    # Pass through all existing arguments for backward compatibility
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with user prompts between stages"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true", 
        help="Show all LLM prompts and responses"
    )
    
    parser.add_argument(
        "--input",
        type=str,
        help="Path to input research JSON file",
    )

    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use existing output files if they exist",
    )

    parser.add_argument(
        "--skip-github",
        action="store_true",
        help="Skip GitHub repository creation",
    )

    args = parser.parse_args()

    # Handle list flavors command
    if args.list_flavors:
        registry = FlavorRegistry(flavors_dir="flavors")
        flavors = registry.list_flavors()

        print("\nAvailable Ideation Flavors:")
        print("=" * 50)

        for flavor_name in sorted(flavors):
            flavor = registry.get_flavor(flavor_name)
            print(f"\n{flavor_name}:")
            print(f"  Description: {flavor.description}")
            print(f"  Framework: {flavor.framework.framework_type.value.upper()}")
            print(f"  Output: {flavor.output.schema_type.value}")

            if flavor_name == "baseline":
                print("  ⭐ EXACT reproduction of current pipeline behavior")

        print(f"\nUsage: python run_pipeline_modular.py --flavor <flavor_name>")
        return
    
    # Load and configure the selected flavor
    print(f"Loading flavor: {args.flavor}")
    flavor = load_flavor_config(args.flavor)
    configure_pipeline_for_flavor(flavor)
    
    print(f"✅ Configured pipeline for flavor: {flavor.name}")
    print(f"   Description: {flavor.description}")
    print(f"   Framework: {flavor.framework.framework_type.value.upper()}")
    print(f"   Output Schema: {flavor.output.schema_type.value}")
    
    if args.flavor == "baseline":
        print("   🎯 EXACT current behavior - no changes to prompts or logic")
    
    # For baseline flavor, use the original pipeline exactly as-is
    # This ensures 100% backward compatibility
    if args.flavor == "baseline":
        print("\n🔄 Running baseline pipeline (original behavior)...")
        original_main(
            interactive=args.interactive,
            verbose=args.verbose,
            input_file=args.input,
            use_cache=args.use_cache,
            skip_github=args.skip_github
        )
    else:
        print(f"\n🔄 Running {args.flavor} flavor pipeline...")

        # Stage 1: Research analysis
        run_module(
            "research_analyzer",
            inputs={},
            outputs=["analysis_results.md"],
            verbose=args.verbose,
            interactive=args.interactive,
        )

        # Stage 2: JTBD extraction and Reddit discovery
        run_module(
            "jobs_to_reddit",
            inputs={"analysis": "analysis_results.md"},
            outputs=["jtbds_*.txt", "reddit_discussions_*.csv"],
            verbose=args.verbose,
            interactive=args.interactive,
        )

        jtbd_file = sorted(glob("jtbds_*.txt"))[-1]
        reddit_file = sorted(glob("reddit_discussions_*.csv"))[-1]

        # Stage 3: Opportunity zone analysis
        n_zones = getattr(getattr(flavor.framework, "clustering", None), "n_zones", 7)
        run_module(
            "opportunity_zone_analyzer",
            inputs={"jtbds": jtbd_file, "reddit": reddit_file},
            outputs=["opportunity_zones_advanced.json"],
            verbose=args.verbose,
            interactive=args.interactive,
            n_zones=n_zones,
        )

        # Standardize output filename
        if Path("opportunity_zones_advanced.json").exists():
            shutil.copy("opportunity_zones_advanced.json", "opportunity_zones.json")

        # Load opportunity zones
        with open("opportunity_zones.json", "r", encoding="utf-8") as f:
            opportunity_zones = json.load(f)

        # Framework analysis
        framework_type = flavor.framework.framework_type.value
        framework_results = analyze_zones_with_framework(
            opportunity_zones,
            framework_type,
            config=getattr(flavor.framework, "params", {}),
        )

        # Opportunity synthesis
        total_ideas = (
            flavor.stage_overrides.get("idea_generation", {}).get("total_ideas", 10)
        )
        opportunities = synthesize_opportunities_from_zones(
            opportunity_zones,
            framework_results,
            flavor,
            total_count=total_ideas,
        )

        with open("opportunities.json", "w", encoding="utf-8") as f:
            json.dump(opportunities, f, indent=2)

        # GitHub artifact creation
        if not args.skip_github:
            write_github_artifacts(opportunities, flavor, framework_results)

if __name__ == "__main__":
    main()