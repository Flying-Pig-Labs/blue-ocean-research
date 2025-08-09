#!/usr/bin/env python3
"""
Multi-Step LLM Pipeline Runner - THE ONE SCRIPT (PRAW-Based, No Exa)

This is THE ONE SCRIPT that orchestrates the entire 7-stage innovation pipeline.
It serves as the central coordinator for transforming raw market research into 
actionable product innovations with automatic GitHub repository creation.

ARCHITECTURAL CONTEXT:
This script is the core orchestrator for a sophisticated market research and product
innovation pipeline. It's designed to be called directly in development environments,
or wrapped by batch_wrapper.py for AWS Batch deployments. The pipeline leverages
multiple AI models (Claude Sonnet/Opus, GPT-4o, OpenAI o1, GPT-5, Cohere) and
Reddit's PRAW API to generate exactly 10 high-quality product ideas distributed
across opportunity zones based on market potential.

KEY DESIGN DECISIONS:
- SINGLE ENTRY POINT: This script must remain the only way to run the full pipeline
- NO MODIFICATIONS: batch_wrapper.py calls this script unmodified for deployment
- PRAW-BASED: Uses Reddit's native API instead of Exa for authentic discussions
- WEIGHTED DISTRIBUTION: Zones get ideas proportional to market opportunity
- QUALITY OVER QUANTITY: Generate 10 ideas per zone, select top N based on weight

INTEGRATION POINTS:
- Called by: batch_wrapper.py (AWS Batch), test suites, CI/CD pipelines
- Imports: research_analyzer, jobs_to_reddit, opportunity_zone_analyzer, 
          product_idea_generator, idea_consolidator
- AWS Services: Secrets Manager (API keys), S3 (when wrapped for Batch)
- External APIs: Anthropic Claude, OpenAI, Cohere, Reddit PRAW, GitHub

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
5. Idea Consolidation (idea_consolidator) - Enriches and packages the innovation portfolio
6. GitHub Repository Creation (github_integration) - Creates public/private repo with issues

Usage:
    python run_pipeline.py                    # Headless mode (default)
    python run_pipeline.py --interactive      # Interactive mode with user prompts
    python run_pipeline.py --verbose          # Show all LLM prompts and responses
    python run_pipeline.py --input file.json  # Custom input file
    python run_pipeline.py --use-cache        # Use existing files, skip GitHub creation
    python run_pipeline.py --skip-github      # Skip GitHub repo creation for testing
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
# Each module represents a distinct stage in the innovation pipeline.
# These modules are designed to be called independently or orchestrated
# through this script. They communicate through file I/O to maintain
# loose coupling and enable parallel development.
import research_analyzer          # Stage 1: Analyzes raw market research from S3/local files
import jobs_to_reddit            # Stage 2: PRAW-based JTBD extraction and Reddit discovery
import opportunity_zone_analyzer  # Stage 3: Advanced clustering and opportunity zone discovery
import product_idea_generator     # Stage 4 & 6: Idea generation and GitHub repo creation
import idea_consolidator         # Stage 5: Portfolio enrichment and consolidation

# ANSI color codes for verbose output
# Used to enhance readability in terminal output, especially when debugging
# LLM interactions. Colors chosen for accessibility and visual distinction.
class Colors:
    """ANSI color codes for terminal output formatting.
    
    This class provides a centralized definition of color codes used throughout
    the pipeline for consistent visual feedback. The color scheme is designed
    to help developers quickly identify different types of output:
    - Cyan: LLM prompts being sent to AI models
    - Salmon: Responses received from AI models
    - Yellow: Module execution status and transitions
    - Red: Errors and critical warnings
    - Bold: Headers and important status messages
    """
    CYAN = '\033[36m'      # Cyan for prompts sent to LLMs
    SALMON = '\033[38;5;209m'  # Salmon for LLM responses (distinctive warm color)
    YELLOW = '\033[33m'    # Yellow for module calls and stage transitions
    RED = '\033[31m'       # Red for errors and failures
    BOLD = '\033[1m'       # Bold text for emphasis on headers
    RESET = '\033[0m'      # Reset to default terminal colors

def colored_print(text: str, color: str, verbose: bool = True):
    """Print colored text if verbose mode is enabled.
    
    This utility function handles conditional colored output based on the
    verbose flag. It's used throughout the pipeline to provide enhanced
    debugging information when needed without cluttering normal output.
    
    Args:
        text: The text to print
        color: ANSI color code from the Colors class
        verbose: If True, apply color formatting; if False, print plain text
    
    Note:
        Color output is only applied when verbose=True to keep logs clean
        in production environments where ANSI codes might not be supported.
    """
    if verbose:
        print(f"{color}{text}{Colors.RESET}")
    else:
        print(text)

def load_secrets_from_aws():
    """Load all required secrets from AWS Secrets Manager.
    
    This function retrieves API keys and tokens from AWS Secrets Manager,
    providing secure credential management for the pipeline. It handles
    multiple secret formats (plain strings and JSON) and uses AWS profiles
    for authentication.
    
    The function is designed to be resilient, continuing execution even if
    some secrets fail to load (though the pipeline may fail later without
    required credentials).
    
    Returns:
        bool: True if all secrets loaded successfully, False otherwise
    
    Environment Variables Set:
        ANTHROPIC_API_KEY: For Claude API access
        OPENAI_API_KEY: For GPT models including GPT-5
        COHERE_API_KEY: For Cohere embeddings and models
        GITHUB_TOKEN: For repository creation and issue management
        PERPLEXITY_KEY: For web search capabilities (optional)
    
    Note:
        EXA_API_KEY was removed in Dec 2024 when switching to PRAW-based
        Reddit discovery, eliminating that external dependency.
    """
    print("Loading secrets from AWS Secrets Manager...")
    
    # Get AWS profile and region from environment or use defaults
    # In AWS Batch/ECS, don't use a profile - use the task role
    # Only use a profile if explicitly set in environment
    aws_profile = os.environ.get('AWS_PROFILE', None)
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if aws_profile:
        print(f"Using AWS Profile: {aws_profile}")
    else:
        print("Using IAM role credentials (no profile)")
    print(f"Using AWS Region: {aws_region}")
    
    # Mapping of environment variable names to AWS Secrets Manager ARNs
    # These ARNs are specific to the production AWS account (984906149037)
    # Each secret contains API credentials for external services used by the pipeline
    secrets_arns = {
        'ANTHROPIC_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6',
        'OPENAI_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY',
        'COHERE_API_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j',
        'GITHUB_TOKEN': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token_blue_ocean-uv7Z1l',
        'PERPLEXITY_KEY': 'arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM'
        # Note: EXA_API_KEY removed in Dec 2024 - PRAW-based Reddit discovery eliminates this dependency
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
            # AWS Secrets Manager can store secrets as either plain strings
            # or JSON objects. This code handles both formats gracefully.
            try:
                secret_dict = json.loads(secret_value)
                # Get the first value from the dict (AWS often stores as {"key": "value"})
                # This handles the common pattern where the secret name is the key
                secret_value = list(secret_dict.values())[0]
            except (json.JSONDecodeError, AttributeError, IndexError):
                # Secret is already a plain string - use as-is
                # This is the preferred format for API keys
                pass
            
            os.environ[env_var] = secret_value
            print(f"✓ Loaded {env_var}")
            loaded_count += 1
            
        except ClientError as e:
            # Common causes: wrong ARN, no permissions, secret doesn't exist
            # The pipeline may still work if this secret isn't needed for the current run
            print(f"✗ Failed to load {env_var}: {e}")
        except Exception as e:
            # Catch-all for unexpected errors (network issues, malformed responses, etc.)
            print(f"✗ Unexpected error loading {env_var}: {e}")
    
    print(f"\nSuccessfully loaded {loaded_count} secrets to environment\n")
    return loaded_count == len(secrets_arns)

def run_module(module_name: str, inputs: Dict[str, str], outputs: List[str], 
               verbose: bool = False, interactive: bool = False, **kwargs) -> bool:
    """
    Execute a module by calling its Python function directly.
    
    This is the core orchestration function that handles the execution of each
    pipeline stage. It simulates command-line arguments for each module,
    manages the execution context, and verifies outputs. The function is
    designed to handle both file-based outputs and special cases like
    GitHub repository creation.
    
    IMPORTANT DESIGN DECISIONS:
    - Modules are called via their main() functions with simulated sys.argv
    - Each module is responsible for its own error handling and logging
    - Output verification supports wildcards for timestamp-based filenames
    - The function maintains backward compatibility with all module versions
    
    Args:
        module_name: Name of the Python module to run (e.g., 'research_analyzer')
        inputs: Dict mapping input names to file paths (e.g., {'research': 'data.json'})
        outputs: List of expected output file paths (supports wildcards like 'jtbds_*.txt')
        verbose: Whether to show LLM prompts and responses (sets PIPELINE_VERBOSE env var)
        interactive: Whether to run in interactive mode with user prompts
        **kwargs: Additional arguments for specific modules (e.g., n_zones, max_discussions)
        
    Returns:
        True if successful and all outputs exist, False otherwise
    
    Side Effects:
        - Sets/clears PIPELINE_VERBOSE environment variable
        - Modifies sys.argv to simulate command-line arguments
        - Creates output files as specified by each module
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
        # Each module expects to be called as if from command line, so we
        # simulate sys.argv to maintain compatibility with standalone execution
        if module_name == "research_analyzer":
            # Stage 1: Extract insights from research document using Claude
            # The --local flag indicates we're using a local file, not S3
            input_file = list(inputs.values())[0] if inputs else "tests/fixtures/sample_research.json"
            # Mock command line args for the module to process
            if interactive:
                sys.argv = ['research_analyzer.py', '--local', input_file, '--interactive']
            else:
                sys.argv = ['research_analyzer.py', '--local', input_file]
            research_analyzer.main()  # Calls the module's main orchestration function
            result = True
            
        elif module_name == "jobs_to_reddit":
            # Stage 2: Extract JTBDs using Claude and search Reddit using PRAW
            # This module creates timestamped output files, hence the wildcard
            # pattern support in output verification
            input_file = inputs.get("analysis", "analysis_results.md")
            sys.argv = ['jobs_to_reddit.py', '--input', input_file]
            jobs_to_reddit.main()  # Generates jtbds_*.txt and reddit_discussions_*.csv
            result = True
            
        elif module_name == "opportunity_zone_analyzer":
            # Stage 3: Cluster JTBDs and Reddit discussions into opportunity zones
            # Each zone gets a market opportunity score (percentage) that determines
            # how many of the 10 total ideas it will receive
            jtbd_file = inputs.get("jtbds", "jtbds_20250806_203749.txt")
            reddit_file = inputs.get("reddit", "reddit_discussions_20250806_203749.csv")
            n_zones = kwargs.get("n_zones", 7)  # Default to 7 opportunity zones
            max_discussions = kwargs.get("max_discussions", 3)  # Limit for performance
            sys.argv = ['opportunity_zone_analyzer.py', 
                       '--jtbd-file', jtbd_file,
                       '--reddit-file', reddit_file,
                       '--n-zones', str(n_zones),
                       '--max-discussions', str(max_discussions),
                       '--output', 'opportunity_zones_advanced.json']
            opportunity_zone_analyzer.main()  # Creates zones with weighted scoring
            result = True
            
        elif module_name == "product_idea_generator":
            # Stage 4: Generate exactly 10 product ideas distributed by zone weights
            # Uses o1 for ERRC strategy, Claude Opus for idea generation
            # Internal: Generates 10 ideas per zone, selects top N based on weight
            input_file = inputs.get("opportunity_zones", "opportunity_zones.json")
            sys.argv = ['product_idea_generator.py', '--input', input_file]
            product_idea_generator.main()  # Outputs exactly 10 ideas total
            result = True
            
        elif module_name == "idea_consolidator":
            # Stage 5: Enrich and package the innovation portfolio
            # Adds metadata, creates summaries, and prepares for GitHub
            sys.argv = ['idea_consolidator.py']
            idea_consolidator.main()  # Creates final_innovation_portfolio.json
            result = True
            
        elif module_name == "github_integration":
            # Stage 6: Create GitHub repository with GPT-5 generated content
            # The --github flag triggers repository creation mode in product_idea_generator
            # GPT-5 makes 11 total calls: 1 for README, 10 for issue descriptions
            extra_args = kwargs.get('extra_args', '')  # May include --github-private
            sys.argv = ['product_idea_generator.py', '--github'] + extra_args.split()
            product_idea_generator.main()  # Creates repo in ocean-studio-repos org
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
            # Critical fix for Stage 2 (jobs_to_reddit) which generates timestamped files
            # like jtbds_20241207_123456.txt and reddit_discussions_20241207_123456.csv
            # Without this, the pipeline would fail to detect these outputs and halt
            if '*' in output_file:
                import glob
                # Use glob to find files matching the wildcard pattern
                # This is essential for Stage 2 outputs with timestamps
                matching_files = glob.glob(output_file)
                if matching_files:
                    # Found files matching the pattern - report all of them
                    # Usually just one file, but report all matches for transparency
                    for matched_file in matching_files:
                        size = os.path.getsize(matched_file)
                        print(f"  ✅ Created: {matched_file} ({size:,} bytes)")
                else:
                    # No files found matching the wildcard pattern
                    # This is a critical failure - the module didn't create expected outputs
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
        # Module execution failed - this is a critical error
        # Common causes: missing dependencies, API errors, file I/O issues
        print(f"\n{Colors.RED}❌ Error executing module {module_name}: {e}{Colors.RESET}")
        if verbose:
            # In verbose mode, show full stack trace for debugging
            # This is essential for diagnosing issues in production
            import traceback
            print(f"{Colors.RED}{traceback.format_exc()}{Colors.RESET}")
        return False
    finally:
        # Clear verbose env var to prevent it from affecting subsequent modules
        # This ensures each module starts with a clean environment
        if 'PIPELINE_VERBOSE' in os.environ:
            del os.environ['PIPELINE_VERBOSE']

def check_file_exists(filepath, description):
    """Check if output file was created.
    
    Simple utility function for verifying file creation.
    Used primarily in testing and validation scenarios.
    
    Args:
        filepath: Path to the file to check
        description: Human-readable description of the file
        
    Returns:
        True if file exists, False otherwise
    """
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False

def main(interactive=False, verbose=False, input_file=None, use_cache=False, skip_github=False):
    """Run the complete pipeline with PRAW-based flow (no Exa dependency).
    
    This is the main orchestration function that coordinates all pipeline stages.
    It manages the flow from raw research input through to GitHub repository
    creation, handling caching, error recovery, and user interaction.
    
    EXECUTION FLOW:
    1. Load AWS secrets for API authentication
    2. Stage 1: Analyze research document
    3. Stage 2: Extract JTBDs and find Reddit discussions (PRAW)
    4. Stage 3: Discover opportunity zones with weighted scoring
    5. Stage 4: Generate exactly 10 product ideas distributed by zone weights
    6. Stage 5: Consolidate and enrich the innovation portfolio
    7. Stage 6: Create GitHub repository with comprehensive documentation
    
    CACHING BEHAVIOR:
    - use_cache=True: Reuses existing files, skips GitHub creation
    - use_cache=False: Regenerates all outputs, creates new GitHub repo
    - Cached files are detected using glob patterns for timestamped outputs
    
    Args:
        interactive: Run with user prompts between stages for manual control
        verbose: Show LLM prompts (cyan) and responses (salmon) for debugging
        input_file: Custom input research file (default: tests/fixtures/sample_research.json)
        use_cache: Use existing output files if they exist (default: False - always regenerate)
        skip_github: Skip GitHub repository creation (useful for testing or when GitHub is down)
    
    Returns:
        None (exits with appropriate status)
    
    Side Effects:
        - Creates multiple output files (analysis_results.md, jtbds_*.txt, etc.)
        - May create a GitHub repository (unless cached or skipped)
        - Sets environment variables from AWS Secrets Manager
        - Prints comprehensive status information to stdout
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
    # This is critical for API access - without proper credentials,
    # most pipeline stages will fail. In interactive mode, we give
    # the user a chance to continue (useful for testing with mock data)
    if not load_secrets_from_aws():
        print("⚠️  Warning: Some secrets failed to load. Pipeline may fail.")
        if interactive:
            # Let user decide whether to continue with missing credentials
            # Useful for testing with cached data or mock responses
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
    
    start_time = time.time()
    stages_completed = 0
    
    # Stage 1: Research Analysis
    # This stage uses Claude to analyze raw research documents and extract
    # key insights including pain points, personas, solutions, and verticals.
    # It's the foundation for all subsequent stages.
    print(f"\n{Colors.BOLD}📌 Stage 1: Research Analysis{Colors.RESET}")
    
    # Use provided input file or default sample for testing
    # The sample file contains real market research data for demonstration
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
            # Pause between stages in interactive mode for user review
            input("\nPress Enter to continue to Stage 2...")
    else:
        # Critical failure - cannot proceed without research analysis
        print("⚠️  Stage 1 failed")
        return
    
    # Stage 2: JTBD Extraction & Reddit Discovery (PRAW-based)
    # Critical stage that extracts Jobs-to-be-Done from the analysis and
    # searches Reddit for authentic user discussions. This provides real-world
    # validation and insights that pure AI analysis might miss.
    # Uses PRAW (Python Reddit API Wrapper) instead of Exa for reliability.
    print(f"\n{Colors.BOLD}📌 Stage 2: JTBD Extraction & Reddit Discovery (PRAW){Colors.RESET}")
    print("  🔍 Extracting JTBDs from analysis using Claude...")
    print("  🌐 Searching Reddit for authentic user discussions...")
    
    # Check if we should use cached files from previous runs
    # This is useful for development/testing to avoid redundant API calls
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
        # This ensures we don't accidentally use stale data from previous runs
        # The xlsx files are optional analysis outputs that should also be cleaned
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
    # This stage performs sophisticated clustering of JTBDs and Reddit discussions
    # into opportunity zones. Each zone is scored across 8 pain dimensions and
    # assigned a market opportunity percentage that determines idea allocation.
    # This is where the "weighted distribution" logic begins.
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
            # The analyzer creates opportunity_zones_advanced.json but Stage 4
            # expects opportunity_zones.json for backward compatibility
            shutil.copy("opportunity_zones_advanced.json", "opportunity_zones.json")
            print("  📄 Created opportunity_zones.json for next stage")
            stages_completed += 1
            if interactive:
                input("\nPress Enter to continue to Stage 4...")
        else:
            print("⚠️  Skipping remaining stages due to error")
            return
    
    # Stage 4: Product Idea Generation
    # The heart of the pipeline - generates exactly 10 high-quality product ideas
    # distributed across zones based on their market opportunity scores.
    # Uses OpenAI o1 for ERRC strategy and Claude Opus for idea generation.
    # Internal process: Generate 10 ideas per zone, select top N based on weight.
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
    # Enriches the product ideas with additional metadata, creates a cohesive
    # portfolio narrative, and prepares the final deliverables. This stage
    # ensures all ideas are properly formatted and contextualized.
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
    # The culmination of the pipeline - creates a GitHub repository with:
    # - GPT-5 generated comprehensive README (1 call)
    # - 10 pitch-deck quality issues with GPT-5 (10 calls)
    # - Smart labels, milestones, and project structure
    # This stage is MANDATORY in production but can be skipped for testing.
    print(f"\n{Colors.BOLD}📌 Stage 6: GitHub Repository Creation{Colors.RESET}")
    
    if skip_github:
        print("  ⏭️  Skipping GitHub repository creation (--skip-github flag)")
        stages_completed += 1
    elif use_cache:
        # Important: Cached runs skip GitHub to avoid duplicate repos
        print("  ⏭️  Skipping GitHub repository creation (using cached files)")
        print("     To create a GitHub repo, run without --use-cache flag")
        stages_completed += 1
    elif not interactive:
        # In headless mode (CI/CD, batch processing), automatically create the GitHub repo
        # This is the default production behavior - no user intervention required
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
        # In interactive mode, give user control over repository creation
        # This is useful for development and demonstration purposes
        create_repo = input("\nCreate GitHub repository with results? (y/n): ")
        if create_repo.lower() == 'y':
            # Allow user to choose repository visibility
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
    
    # Summary Report
    # Calculate and display comprehensive pipeline execution metrics
    # This summary helps users understand what was accomplished and
    # provides next steps for cleanup or further analysis
    total_time = time.time() - start_time
    
    # Display formatted completion summary with visual separators
    # The box drawing characters create a professional terminal UI
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Pipeline Complete!                         ║
║                  PRAW-Based Flow (No Exa)                     ║
╚══════════════════════════════════════════════════════════════╝

📊 Summary:
   - Stages Completed: {stages_completed}/6
   - Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)
   
📁 Generated Files:
   - analysis_results.md               # Stage 1: Research insights
   - jtbds_*.txt                      # Stage 2: Jobs-to-be-Done list  
   - reddit_discussions_*.csv         # Stage 2: Reddit data via PRAW API
   - opportunity_zones.json           # Stage 3: Weighted market opportunities
   - product_ideas.json               # Stage 4: Exactly 10 innovative ideas
   - product_ideas_report.md          # Stage 4: Human-readable report
   - final_innovation_portfolio.json  # Stage 5: Enriched portfolio data
   - final_innovation_portfolio_summary.md  # Stage 5: Executive summary

🎯 Pipeline Flow Used:
   1. Research Analysis → analysis_results.md
   2. JTBD + Reddit (PRAW) → jtbds & discussions
   3. Opportunity Zones → weighted zones (market % allocation)
   4. Product Ideas → innovative solutions (10 total, distributed by weight)
   5. Consolidation → final portfolio
   6. GitHub → repository created (or skipped if cached/disabled)

🧹 To clean up all generated files:
   python cleanup_pipeline.py

✅ No Exa API dependency required - fully PRAW-based Reddit integration!
""")

if __name__ == "__main__":
    # Entry point for the pipeline script
    # This block handles command-line argument parsing and invokes the main orchestration
    # function. It's designed to be called directly or imported by other scripts.
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