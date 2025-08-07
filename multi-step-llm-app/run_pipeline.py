#!/usr/bin/env python3
"""
THE ONE SCRIPT to run the complete multi-step LLM pipeline from start to finish.
This script executes all 7 stages sequentially with explicit input/output declarations.

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

# Import all pipeline modules
import research_analyzer
import jobs_researcher
import jobs_to_reddit  # NEW: Extract JTBDs and find Reddit discussions
import cluster_jtbd
import opportunity_zone_analyzer  # NEW: Advanced opportunity zone discovery
import value_curve_mapper
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
        'EXA_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-N7ylem',
        'COHERE_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j',
        'GITHUB_TOKEN': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy',
        'PERPLEXITY_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM'
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
            
        elif module_name == "jobs_researcher":
            # Call jobs_researcher main function
            sys.argv = ['jobs_researcher.py']
            jobs_researcher.main()
            result = True
            
        elif module_name == "jobs_to_reddit":
            # Call jobs_to_reddit to extract JTBDs and find Reddit discussions
            input_file = inputs.get("analysis", "analysis_results.md")
            sys.argv = ['jobs_to_reddit.py', '--input', input_file]
            jobs_to_reddit.main()
            result = True
            
        elif module_name == "cluster_jtbd":
            # Call cluster_jtbd with input file
            input_file = inputs.get("pain_points", "jtbd_research_pain_points.txt")
            sys.argv = ['cluster_jtbd.py', input_file]
            cluster_jtbd.main()
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
            
        elif module_name == "value_curve_mapper":
            # Call value_curve_mapper with input file
            input_file = inputs.get("zones", "opportunity_zones.json")
            sys.argv = ['value_curve_mapper.py', input_file]
            value_curve_mapper.main()
            result = True
            
        elif module_name == "product_idea_generator":
            # Call product_idea_generator
            sys.argv = ['product_idea_generator.py']
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
            # Special case for GitHub output
            if output_file == "GitHub repository in ocean-studio-repos organization":
                print(f"  ✅ GitHub repository created")
                continue
                
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

def main(interactive=False, verbose=False, input_file=None):
    """Run the complete pipeline with explicit input/output declarations."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Multi-Step LLM Pipeline - Full Integration            ║
║                    THE ONE SCRIPT                             ║
║                                                               ║
║  Mode: """ + ("INTERACTIVE" if interactive else "HEADLESS   ") + """                                   ║
║  Verbose: """ + ("YES" if verbose else "NO ") + """                                        ║
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
    
    # Stage 2: JTBD Research
    print(f"\n{Colors.BOLD}📌 Stage 2: Jobs-to-be-Done Research{Colors.RESET}")
    
    if run_module(
        module_name="jobs_researcher",
        inputs={"analysis": "analysis_results.md"},
        outputs=["jtbd_research.md", "jtbd_research_pain_points.txt"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 2.5...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 2.5: Extract JTBDs and Find Reddit Discussions
    print(f"\n{Colors.BOLD}📌 Stage 2.5: JTBD Extraction & Reddit Discovery{Colors.RESET}")
    
    # Check if we already have the Reddit data files
    import glob
    jtbd_files = glob.glob("jtbds_*.txt")
    reddit_files = glob.glob("reddit_discussions_*.csv")
    
    if jtbd_files and reddit_files:
        print(f"  ✅ Using existing JTBD file: {jtbd_files[0]}")
        print(f"  ✅ Using existing Reddit file: {reddit_files[0]}")
        jtbd_file = jtbd_files[0]
        reddit_file = reddit_files[0]
    else:
        # Run jobs_to_reddit to generate the files
        if run_module(
            module_name="jobs_to_reddit",
            inputs={"analysis": "analysis_results.md"},
            outputs=["jtbds_*.txt", "reddit_discussions_*.csv"],
            verbose=verbose,
            interactive=interactive
        ):
            # Find the generated files
            jtbd_files = glob.glob("jtbds_*.txt")
            reddit_files = glob.glob("reddit_discussions_*.csv")
            if jtbd_files and reddit_files:
                jtbd_file = jtbd_files[0]
                reddit_file = reddit_files[0]
            else:
                print("⚠️  Failed to generate JTBD and Reddit files")
                return
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    stages_completed += 0.5  # Half stage
    if interactive:
        input("\nPress Enter to continue to Stage 3...")
    
    # Stage 3: Clustering (Basic)
    print(f"\n{Colors.BOLD}📌 Stage 3: Pain Point Clustering (Basic){Colors.RESET}")
    
    if run_module(
        module_name="cluster_jtbd",
        inputs={"pain_points": "jtbd_research_pain_points.txt"},
        outputs=["jtbd_clusters.json"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 3.5...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 3.5: Advanced Opportunity Zone Analysis
    print(f"\n{Colors.BOLD}📌 Stage 3.5: Advanced Opportunity Zone Discovery{Colors.RESET}")
    print("  🧠 Analyzing pain dimensions across JTBDs and Reddit discussions...")
    
    # Use the files from Stage 2.5
    if 'jtbd_file' in locals() and 'reddit_file' in locals():
        if run_module(
            module_name="opportunity_zone_analyzer",
            inputs={"jtbds": jtbd_file, "reddit": reddit_file},
            outputs=["opportunity_zones_advanced.json"],
            verbose=verbose,
            interactive=interactive,
            n_zones=7,
            max_discussions=3  # Limit for speed
        ):
            # Copy to expected name for next stage
            shutil.copy("opportunity_zones_advanced.json", "opportunity_zones.json")
            print("  📄 Using advanced opportunity zones for value curve mapping")
            stages_completed += 0.5
        else:
            # Fallback to basic clustering
            print("  ⚠️  Advanced analysis failed, using basic clustering")
            shutil.copy("jtbd_clusters.json", "opportunity_zones.json")
            print("  📄 Copied jtbd_clusters.json → opportunity_zones.json")
    else:
        # No Reddit data, use basic clustering
        print("  ℹ️  No Reddit data available, using basic clustering")
        shutil.copy("jtbd_clusters.json", "opportunity_zones.json")
        print("  📄 Copied jtbd_clusters.json → opportunity_zones.json")
    
    if interactive:
        input("\nPress Enter to continue to Stage 4...")
    
    # Stage 4: Value Curve Mapping
    print(f"\n{Colors.BOLD}📌 Stage 4: Value Curve Mapping{Colors.RESET}")
    
    if run_module(
        module_name="value_curve_mapper",
        inputs={"zones": "opportunity_zones.json"},
        outputs=["value_curves.json", "value_curves_report.md"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 5...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 5: Product Idea Generation
    print(f"\n{Colors.BOLD}📌 Stage 5: Product Idea Generation{Colors.RESET}")
    
    if run_module(
        module_name="product_idea_generator",
        inputs={"value_curves": "value_curves.json"},
        outputs=["product_ideas.json", "product_ideas_report.md"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 6...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 6: Idea Consolidation
    print(f"\n{Colors.BOLD}📌 Stage 6: Idea Consolidation{Colors.RESET}")
    
    if run_module(
        module_name="idea_consolidator",
        inputs={"product_ideas": "product_ideas.json"},
        outputs=["final_innovation_portfolio.json", "final_innovation_portfolio_summary.md"],
        verbose=verbose,
        interactive=interactive
    ):
        stages_completed += 1
        if interactive:
            input("\nPress Enter to continue to Stage 7...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 7: GitHub Integration
    print(f"\n{Colors.BOLD}📌 Stage 7: GitHub Repository Creation{Colors.RESET}")
    
    # Let product_idea_generator.py create the creative name based on research content
    if not interactive:
        # In headless mode, automatically create the GitHub repo
        if run_module(
            module_name="github_integration",
            inputs={
                "analysis": "analysis_results.md",
                "jtbd": "jtbd_research.md",
                "clusters": "jtbd_clusters.json",
                "value_curves": "value_curves.json",
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
                    "jtbd": "jtbd_research.md",
                    "clusters": "jtbd_clusters.json",
                    "value_curves": "value_curves.json",
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
╚══════════════════════════════════════════════════════════════╝

📊 Summary:
   - Stages Completed: {stages_completed}/7
   - Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)
   
📁 Generated Files:
   - analysis_results.md (mock)
   - jtbd_research.md
   - pain_points.txt
   - opportunity_zones.json
   - value_curves.json
   - value_curves_report.md
   - product_ideas.json
   - product_ideas_report.md
   - final_innovation_portfolio.json
   - final_innovation_portfolio_summary.md

🧹 To clean up all generated files:
   python cleanup_pipeline.py

🚀 To create GitHub repository:
   python product_idea_generator.py --github --repo-name 'innovation-{datetime.now().strftime("%Y%m%d")}'
""")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='THE ONE SCRIPT to run the complete multi-step LLM pipeline')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode with user prompts between stages (default: headless)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show all LLM prompts in cyan and responses in salmon')
    parser.add_argument('--input', type=str, 
                       help='Path to input research JSON file (otherwise uses sample)')
    args = parser.parse_args()
    
    main(interactive=args.interactive, verbose=args.verbose, input_file=args.input)