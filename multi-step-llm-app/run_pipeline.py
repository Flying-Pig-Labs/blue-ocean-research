#!/usr/bin/env python3
"""
Multi-Step LLM Pipeline Runner - THE ONE SCRIPT (PRAW-Based, No Exa)

This is THE ONE SCRIPT that orchestrates the entire 7-stage innovation pipeline.
It coordinates the transformation of raw market research into actionable product 
innovations with automatic GitHub repository creation.

Key Features:
- Runs all 7 stages sequentially with proper error handling
- Supports both headless (automated) and interactive modes  
- Handles wildcard file patterns for dynamically-named outputs
- Integrates with AWS Secrets Manager for secure API key management
- PRAW-based Reddit discovery (no Exa dependency)

Pipeline Stages:
1. Research Analysis (research_analyzer) - Extracts insights from raw market research
2. JTBD & Reddit Discovery (jobs_to_reddit) - Identifies jobs-to-be-done with authentic user discussions  
3. Opportunity Zone Discovery (opportunity_zone_analyzer) - Clusters JTBDs into market opportunities
4. Product Idea Generation (product_idea_generator) - Creates innovative product concepts
5. Idea Consolidation (idea_consolidator)
6. GitHub Repository Creation (product_idea_generator --github)

Usage:
    python run_pipeline.py                    # Headless mode (default)
    python run_pipeline.py --interactive      # Interactive mode with user prompts
    python run_pipeline.py --verbose          # Show all LLM prompts and responses
    python run_pipeline.py --input file.json  # Custom input file
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Any
import shutil

# Import pipeline modules (PRAW-based flow, no Exa dependencies)
import research_analyzer
import jobs_to_reddit  # PRAW-based JTBD extraction and Reddit discovery
import opportunity_zone_analyzer  # Advanced opportunity zone discovery
import product_idea_generator
import idea_consolidator

# ANSI color codes for verbose output
class Colors:
    CYAN = '\033[36m'      # Cyan for prompts
    SALMON = '\033[38;5;209m'  # Salmon for LLM responses  
    YELLOW = '\033[33m'    # Yellow for module calls
    RED = '\033[31m'       # Red for errors
    BOLD = '\033[1m'       # Bold text
    RESET = '\033[0m'      # Reset to default

def colored_print(text: str, color: str, verbose: bool = True):
    """Print colored text if verbose mode is enabled."""
    if verbose:
        print(f"{color}{text}{Colors.RESET}")
    else:
        print(text)

def load_secrets_from_aws():
    """Load all required secrets from AWS Secrets Manager."""
    print("Loading secrets from AWS Secrets Manager...")
    
    # Get AWS profile and region from environment or use defaults
    aws_profile = os.environ.get('AWS_PROFILE', 'mvp')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    print(f"Using AWS Profile: {aws_profile}")
    print(f"Using AWS Region: {aws_region}")
    
    secrets_arns = {
        'ANTHROPIC_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6',
        'OPENAI_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY',
        'COHERE_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j',
        'GITHUB_TOKEN': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token_blue_ocean-uv7Z1l',
        'PERPLEXITY_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM'
        # Removed EXA_API_KEY - no longer needed with PRAW-based flow
    }
    
    # Create session with profile if specified
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
        client = session.client('secretsmanager')
    else:
        client = boto3.client('secretsmanager', region_name=aws_region)
    loaded_count = 0
    
    for env_var, secret_arn in secrets_arns.items():
        try:
            response = client.get_secret_value(SecretId=secret_arn)
            secret_value = response.get('SecretString')
            
            # Parse JSON if the secret is JSON formatted
            try:
                secret_dict = json.loads(secret_value)
                # Get the first value from the dict (AWS often stores as {"key": "value"})
                secret_value = list(secret_dict.values())[0]
            except (json.JSONDecodeError, AttributeError, IndexError):
                # Secret is already a plain string
                pass
            
            os.environ[env_var] = secret_value
            print(f"✓ Loaded {env_var}")
            loaded_count += 1
            
        except ClientError as e:
            print(f"✗ Failed to load {env_var}: {e}")
        except Exception as e:
            print(f"✗ Unexpected error loading {env_var}: {e}")
    
    print(f"\nSuccessfully loaded {loaded_count} secrets to environment\n")
    return loaded_count == len(secrets_arns)

def run_module(module_name: str, inputs: Dict[str, str], outputs: List[str], 
               verbose: bool = False, interactive: bool = False, **kwargs) -> bool:
    """
    Execute a module by calling its Python function directly.
    
    Args:
        module_name: Name of the Python module to run
        inputs: Dict mapping input names to file paths
        outputs: List of expected output file paths
        verbose: Whether to show LLM prompts and responses
        **kwargs: Additional arguments for specific modules
        
    Returns:
        True if successful, False otherwise
    """
    # Build input display string
    input_display = ", ".join([f"{k}={v}" for k, v in inputs.items()])
    output_display = ", ".join(outputs)
    
    # Print module call in consistent format
    if verbose:
        print(f"\n{Colors.YELLOW}{'='*70}")
        print(f"📦 MODULE: {module_name}")
        print(f"   inputs=[{input_display}]")
        print(f"   outputs=[{output_display}]")
        print(f"{'='*70}{Colors.RESET}")
    else:
        print(f"\n📦 {module_name}(inputs=[{input_display}], outputs=[{output_display}])")
    
    # Set verbose environment variable if needed
    if verbose:
        os.environ['PIPELINE_VERBOSE'] = '1'
    
    start_time = time.time()
    
    try:
        # Call the appropriate module function directly
        if module_name == "research_analyzer":
            # Use the first input file (research document)
            input_file = list(inputs.values())[0] if inputs else "tests/fixtures/sample_research.json"
            # Mock command line args for the module
            if interactive:
                sys.argv = ['research_analyzer.py', '--local', input_file, '--interactive']
            else:
                sys.argv = ['research_analyzer.py', '--local', input_file]
            research_analyzer.main()
            result = True
            
        elif module_name == "jobs_to_reddit":
            # Call jobs_to_reddit to extract JTBDs and find Reddit discussions
            input_file = inputs.get("analysis", "analysis_results.md")
            sys.argv = ['jobs_to_reddit.py', '--input', input_file]
            jobs_to_reddit.main()
            result = True
            
        elif module_name == "opportunity_zone_analyzer":
            # Call opportunity zone analyzer with JTBDs and Reddit data
            jtbd_file = inputs.get("jtbds", "jtbds_20250806_203749.txt")
            reddit_file = inputs.get("reddit", "reddit_discussions_20250806_203749.csv")
            n_zones = kwargs.get("n_zones", 7)
            max_discussions = kwargs.get("max_discussions", 3)
            sys.argv = ['opportunity_zone_analyzer.py', 
                       '--jtbd-file', jtbd_file,
                       '--reddit-file', reddit_file,
                       '--n-zones', str(n_zones),
                       '--max-discussions', str(max_discussions),
                       '--output', 'opportunity_zones_advanced.json']
            opportunity_zone_analyzer.main()
            result = True
            
        elif module_name == "product_idea_generator":
            # Call product_idea_generator with opportunity zones
            input_file = inputs.get("opportunity_zones", "opportunity_zones.json")
            sys.argv = ['product_idea_generator.py', '--input', input_file]
            product_idea_generator.main()
            result = True
            
        elif module_name == "idea_consolidator":
            # Call idea_consolidator
            sys.argv = ['idea_consolidator.py']
            idea_consolidator.main()
            result = True
            
        elif module_name == "github_integration":
            # Call product_idea_generator with github flag
            extra_args = kwargs.get('extra_args', '')
            sys.argv = ['product_idea_generator.py', '--github'] + extra_args.split()
            product_idea_generator.main()
            result = True
            
        else:
            print(f"{Colors.RED}Unknown module: {module_name}{Colors.RESET}")
            return False
        
        elapsed = time.time() - start_time
        
        # Check outputs exist
        all_outputs_exist = True
        for output_file in outputs:
            # Special case for GitHub output (not a file)
            if output_file == "GitHub repository in ocean-studio-repos organization":
                print(f"  ✅ GitHub repository created")
                continue
            
            # ENHANCEMENT (Dec 2024): Handle wildcard patterns for dynamically-named files
            # Some modules generate files with timestamps (e.g., jtbds_20241207_123456.txt)
            # This fix allows the pipeline to correctly detect these files using glob patterns
            if '*' in output_file:
                import glob
                matching_files = glob.glob(output_file)
                if matching_files:
                    # Found files matching the pattern - report all of them
                    for matched_file in matching_files:
                        size = os.path.getsize(matched_file)
                        print(f"  ✅ Created: {matched_file} ({size:,} bytes)")
                else:
                    # No files found matching the wildcard pattern
                    print(f"  ❌ No files matching pattern: {output_file}")
                    all_outputs_exist = False
            else:
                # Regular file check for non-wildcard filenames
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    print(f"  ✅ Created: {output_file} ({size:,} bytes)")
                else:
                    print(f"  ❌ Missing: {output_file}")
                    all_outputs_exist = False
        
        if all_outputs_exist:
            print(f"  ⏱️  Module completed in {elapsed:.1f} seconds")
            return True
        else:
            print(f"  ⚠️  Module completed but some outputs missing")
            return False
            
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error executing module {module_name}: {e}{Colors.RESET}")
        if verbose:
            import traceback
            print(f"{Colors.RED}{traceback.format_exc()}{Colors.RESET}")
        return False
    finally:
        # Clear verbose env var
        if 'PIPELINE_VERBOSE' in os.environ:
            del os.environ['PIPELINE_VERBOSE']

def check_file_exists(filepath, description):
    """Check if output file was created."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False

def main(interactive=False, verbose=False, input_file=None, use_cache=False, skip_github=False):
    """Run the complete pipeline with PRAW-based flow (no Exa dependency).
    
    Args:
        interactive: Run with user prompts between stages
        verbose: Show LLM prompts and responses
        input_file: Custom input research file
        use_cache: Use existing output files if they exist (default: False - always regenerate)
        skip_github: Skip GitHub repository creation (useful for testing)
    """
    mode_str = "INTERACTIVE" if interactive else "HEADLESS"
    verbose_str = "YES" if verbose else "NO"
    cache_str = "ENABLED" if use_cache else "DISABLED"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     Multi-Step LLM Pipeline - PRAW-Based Flow (No Exa)       ║
║                    THE ONE SCRIPT                             ║
║                                                               ║
║  Mode: {mode_str:<15}  Verbose: {verbose_str:<5}  Cache: {cache_str:<8} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Load secrets from AWS
    if not load_secrets_from_aws():
        print("⚠️  Warning: Some secrets failed to load. Pipeline may fail.")
        if interactive:
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
    
    start_time = time.time()
    stages_completed = 0
    
    # Stage 1: Research Analysis
    print(f"\n{Colors.BOLD}📌 Stage 1: Research Analysis{Colors.RESET}")
    
    # Use provided input file or default sample
    input_source = input_file if input_file else "tests/fixtures/sample_research.json"
    
    if run_module(
        module_name="research_analyzer",
        inputs={"research": input_source},
        outputs=["analysis_results.md"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 2...")
    else:
        print("⚠️  Stage 1 failed")
        return
    
    # Stage 2: JTBD Extraction & Reddit Discovery (PRAW-based)
    print(f"\n{Colors.BOLD}📌 Stage 2: JTBD Extraction & Reddit Discovery (PRAW){Colors.RESET}")
    print("  🔍 Extracting JTBDs from analysis using Claude...")
    print("  🌐 Searching Reddit for authentic user discussions...")
    
    # Check if we should use cached files
    import glob
    jtbd_files = glob.glob("jtbds_*.txt") if use_cache else []
    reddit_files = glob.glob("reddit_discussions_*.csv") if use_cache else []
    
    if use_cache and jtbd_files and reddit_files:
        print(f"  📂 Using cached JTBD file: {jtbd_files[0]}")
        print(f"  📂 Using cached Reddit file: {reddit_files[0]}")
        jtbd_file = jtbd_files[0]
        reddit_file = reddit_files[0]
        stages_completed += 1
    else:
        # Clean up old files if not using cache
        if not use_cache:
            for pattern in ["jtbds_*.txt", "reddit_discussions_*.csv", "reddit_analysis_*.xlsx"]:
                for file in glob.glob(pattern):
                    os.remove(file)
                    print(f"  🗑️  Removed old file: {file}")
        
        # Run jobs_to_reddit to generate fresh files
        print("  🔄 Generating fresh JTBD and Reddit data...")
        if run_module(
            module_name="jobs_to_reddit",
            inputs={"analysis": "analysis_results.md"},
            outputs=["jtbds_*.txt", "reddit_discussions_*.csv"],
            verbose=verbose,
            interactive=interactive
        ):
            # Find the newly generated files
            jtbd_files = glob.glob("jtbds_*.txt")
            reddit_files = glob.glob("reddit_discussions_*.csv")
            if jtbd_files and reddit_files:
                jtbd_file = jtbd_files[0]
                reddit_file = reddit_files[0]
                stages_completed += 1
                print(f"  ✅ Generated: {jtbd_file}")
                print(f"  ✅ Generated: {reddit_file}")
            else:
                print("⚠️  Failed to generate JTBD and Reddit files")
                return
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    if interactive:
        input("\nPress Enter to continue to Stage 3...")
    
    # Stage 3: Advanced Opportunity Zone Discovery
    print(f"\n{Colors.BOLD}📌 Stage 3: Advanced Opportunity Zone Discovery{Colors.RESET}")
    print("  🧠 Analyzing pain dimensions across JTBDs and Reddit discussions...")
    print("  📊 Creating weighted opportunity zones...")
    
    # Check if we should use cached opportunity zones
    if use_cache and os.path.exists("opportunity_zones.json"):
        print(f"  📂 Using cached opportunity zones file")
        print(f"  ✅ Found: opportunity_zones.json ({os.path.getsize('opportunity_zones.json'):,} bytes)")
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 4...")
    else:
        # Generate fresh opportunity zones
        if run_module(
            module_name="opportunity_zone_analyzer",
            inputs={"jtbds": jtbd_file, "reddit": reddit_file},
            outputs=["opportunity_zones_advanced.json"],
            verbose=verbose,
            interactive=interactive,
            n_zones=7,
            max_discussions=3  # Limit for speed
        ):
            # Copy to standard name for next stage
            shutil.copy("opportunity_zones_advanced.json", "opportunity_zones.json")
            print("  📄 Created opportunity_zones.json for next stage")
            stages_completed += 1
            if interactive:
                input("\nPress Enter to continue to Stage 4...")
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    # Stage 4: Product Idea Generation
    print(f"\n{Colors.BOLD}📌 Stage 4: Product Idea Generation{Colors.RESET}")
    print("  💡 Generating innovative product ideas from opportunity zones...")
    
    # Check if we should use cached product ideas
    if use_cache and os.path.exists("product_ideas.json") and os.path.exists("product_ideas_report.md"):
        print(f"  📂 Using cached product ideas files")
        print(f"  ✅ Found: product_ideas.json ({os.path.getsize('product_ideas.json'):,} bytes)")
        print(f"  ✅ Found: product_ideas_report.md ({os.path.getsize('product_ideas_report.md'):,} bytes)")
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 5...")
    else:
        # Generate fresh product ideas
        if run_module(
            module_name="product_idea_generator",
            inputs={"opportunity_zones": "opportunity_zones.json"},
            outputs=["product_ideas.json", "product_ideas_report.md"],
            verbose=verbose,
            interactive=interactive
        ):
            stages_completed += 1
            if interactive:
                input("\nPress Enter to continue to Stage 5...")
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    # Stage 5: Idea Consolidation
    print(f"\n{Colors.BOLD}📌 Stage 5: Idea Consolidation{Colors.RESET}")
    print("  🎯 Consolidating and enriching product portfolio...")
    
    # Check if we should use cached portfolio files
    if use_cache and os.path.exists("final_innovation_portfolio.json") and os.path.exists("final_innovation_portfolio_summary.md"):
        print(f"  📂 Using cached portfolio files")
        print(f"  ✅ Found: final_innovation_portfolio.json ({os.path.getsize('final_innovation_portfolio.json'):,} bytes)")
        print(f"  ✅ Found: final_innovation_portfolio_summary.md ({os.path.getsize('final_innovation_portfolio_summary.md'):,} bytes)")
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 6...")
    else:
        # Generate fresh portfolio
        if run_module(
            module_name="idea_consolidator",
            inputs={"product_ideas": "product_ideas.json"},
            outputs=["final_innovation_portfolio.json", "final_innovation_portfolio_summary.md"],
            verbose=verbose,
            interactive=interactive
        ):
            stages_completed += 1
            if interactive:
                input("\nPress Enter to continue to Stage 6...")
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    # Stage 6: GitHub Integration
    print(f"\n{Colors.BOLD}📌 Stage 6: GitHub Repository Creation{Colors.RESET}")
    
    if skip_github:
        print("  ⏭️  Skipping GitHub repository creation (--skip-github flag)")
        stages_completed += 1
    elif use_cache:
        print("  ⏭️  Skipping GitHub repository creation (using cached files)")
        print("     To create a GitHub repo, run without --use-cache flag")
        stages_completed += 1
    elif not interactive:
        # In headless mode, automatically create the GitHub repo
        if run_module(
            module_name="github_integration",
            inputs={
                "analysis": "analysis_results.md",
                "jtbds": jtbd_file,
                "reddit": reddit_file,
                "opportunity_zones": "opportunity_zones.json",
                "product_ideas": "product_ideas.json",
                "portfolio": "final_innovation_portfolio.json"
            },
            outputs=["GitHub repository in ocean-studio-repos organization"],
            verbose=verbose,
            interactive=interactive
        ):
            print(f"✅ GitHub repository created in ocean-studio-repos organization")
            stages_completed += 1
    else:
        # In interactive mode, ask the user
        create_repo = input("\nCreate GitHub repository with results? (y/n): ")
        if create_repo.lower() == 'y':
            private = input("Make repository private? (y/n): ")
            private_flag = "--github-private" if private.lower() == 'y' else ""
            
            if run_module(
                module_name="github_integration",
                inputs={
                    "analysis": "analysis_results.md",
                    "jtbds": jtbd_file,
                    "reddit": reddit_file,
                    "opportunity_zones": "opportunity_zones.json",
                    "product_ideas": "product_ideas.json",
                    "portfolio": "final_innovation_portfolio.json"
                },
                outputs=["GitHub repository in ocean-studio-repos organization"],
                verbose=verbose,
                interactive=interactive,
                extra_args=private_flag
            ):
                print(f"✅ GitHub repository created in ocean-studio-repos organization")
                stages_completed += 1
        else:
            print("Skipped GitHub repository creation")
            stages_completed += 1
    
    # Summary
    total_time = time.time() - start_time
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Pipeline Complete!                         ║
║                  PRAW-Based Flow (No Exa)                     ║
╚══════════════════════════════════════════════════════════════╝

📊 Summary:
   - Stages Completed: {stages_completed}/6
   - Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)
   
📁 Generated Files:
   - analysis_results.md
   - jtbds_*.txt (extracted JTBDs)
   - reddit_discussions_*.csv (Reddit data via PRAW)
   - opportunity_zones.json (weighted zones)
   - product_ideas.json
   - product_ideas_report.md
   - final_innovation_portfolio.json
   - final_innovation_portfolio_summary.md

🎯 Pipeline Flow Used:
   1. Research Analysis → analysis_results.md
   2. JTBD + Reddit (PRAW) → jtbds & discussions
   3. Opportunity Zones → weighted zones
   4. Product Ideas → innovative solutions
   5. Consolidation → final portfolio
   6. GitHub → repository created

🧹 To clean up all generated files:
   python cleanup_pipeline.py

✅ No Exa API dependency required!
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='THE ONE SCRIPT to run the complete multi-step LLM pipeline')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode with user prompts between stages (default: headless)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show all LLM prompts in cyan and responses in salmon')
    parser.add_argument('--input', type=str, 
                       help='Path to input research JSON file (otherwise uses sample)')
    parser.add_argument('--use-cache', action='store_true',
                       help='Use existing output files if they exist (default: always regenerate fresh)')
    parser.add_argument('--skip-github', action='store_true',
                       help='Skip GitHub repository creation (useful for testing)')
    args = parser.parse_args()
    
    main(interactive=args.interactive, verbose=args.verbose, input_file=args.input, 
         use_cache=args.use_cache, skip_github=args.skip_github)