#!/usr/bin/env python3
"""
THE ONE SCRIPT to run the complete multi-step LLM pipeline from start to finish.
This script executes all 7 stages sequentially.

Usage:
    python run_pipeline.py              # Interactive mode
    python run_pipeline.py --headless   # Headless mode for automated environments
"""

import subprocess
import sys
import os
import time
import json
import argparse
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

def load_secrets_from_aws():
    """Load all required secrets from AWS Secrets Manager."""
    print("Loading secrets from AWS Secrets Manager...")
    
    secrets_arns = {
        'ANTHROPIC_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6',
        'OPENAI_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY',
        'EXA_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-N7ylem',
        'COHERE_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j',
        'GITHUB_TOKEN': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy',
        'PERPLEXITY_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM'
    }
    
    client = boto3.client('secretsmanager', region_name='us-east-1')
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

def run_command(command, description):
    """Execute a command and handle output."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Completed in {elapsed:.1f} seconds")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error executing command: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_file_exists(filepath, description):
    """Check if output file was created."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False

def main(headless=False, input_file=None):
    """Run the complete pipeline."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Multi-Step LLM Pipeline - Full Integration            ║
║                    THE ONE SCRIPT                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Load secrets from AWS
    if not load_secrets_from_aws():
        print("⚠️  Warning: Some secrets failed to load. Pipeline may fail.")
        if not headless:
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
    
    start_time = time.time()
    stages_completed = 0
    
    # Stage 1: Research Analysis
    print("\n📌 Stage 1: Research Analysis")
    
    # Use provided input file or default sample
    input_source = input_file if input_file else "tests/fixtures/sample_research.json"
    if run_command(
        f"python research_analyzer.py --local {input_source}",
        f"Stage 1: Research Analysis from {input_source}"
    ):
        if check_file_exists("analysis_results.md", "Analysis Results"):
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 2...")
    else:
        print("⚠️  Stage 1 failed")
        return
    
    # Stage 2: JTBD Research
    if run_command(
        "python jobs_researcher.py",
        "Stage 2: Jobs-to-be-Done Research"
    ):
        if check_file_exists("jtbd_research.md", "JTBD Research"):
            check_file_exists("jtbd_research_pain_points.txt", "Pain Points")
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 3...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 3: Clustering
    if run_command(
        "python cluster_jtbd.py jtbd_research_pain_points.txt",
        "Stage 3: Pain Point Clustering"
    ):
        if check_file_exists("jtbd_clusters.json", "JTBD Clusters"):
            # Copy to expected name for next stage
            import shutil
            shutil.copy("jtbd_clusters.json", "opportunity_zones.json")
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 4...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 4: Value Curve Mapping
    if run_command(
        "python value_curve_mapper.py opportunity_zones.json",
        "Stage 4: Value Curve Mapping"
    ):
        if check_file_exists("value_curves.json", "Value Curves"):
            check_file_exists("value_curves_report.md", "Value Curves Report")
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 5...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 5: Product Idea Generation
    if run_command(
        "python product_idea_generator.py",
        "Stage 5: Product Idea Generation"
    ):
        if check_file_exists("product_ideas.json", "Product Ideas"):
            check_file_exists("product_ideas_report.md", "Product Ideas Report")
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 6...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 6: Idea Consolidation
    if run_command(
        "python idea_consolidator.py",
        "Stage 6: Idea Consolidation"
    ):
        if check_file_exists("final_innovation_portfolio.json", "Innovation Portfolio"):
            check_file_exists("final_innovation_portfolio_summary.md", "Portfolio Summary")
            stages_completed += 1
            if not headless:
                input("\nPress Enter to continue to Stage 7...")
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 7: GitHub Integration
    print(f"\n{'='*60}")
    print("🚀 Stage 7: GitHub Repository Creation")
    print(f"{'='*60}")
    
    # Let product_idea_generator.py create the creative name based on research content
    if headless:
        # In headless mode, automatically create the GitHub repo
        if run_command(
            "python product_idea_generator.py --github",
            "Stage 7: Creating GitHub Repository with Creative Name"
        ):
            print(f"✅ GitHub repository created in ocean-studio-repos organization")
            stages_completed += 1
    else:
        # In interactive mode, ask the user
        create_repo = input("\nCreate GitHub repository with results? (y/n): ")
        if create_repo.lower() == 'y':
            private = input("Make repository private? (y/n): ")
            private_flag = "--github-private" if private.lower() == 'y' else ""
            
            if run_command(
                f"python product_idea_generator.py --github {private_flag}",
                "Stage 7: Creating GitHub Repository with Creative Name"
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
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode without user interaction')
    parser.add_argument('--input', type=str, 
                       help='Path to input research JSON file (otherwise uses sample)')
    args = parser.parse_args()
    
    main(headless=args.headless, input_file=args.input)