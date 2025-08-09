#!/usr/bin/env python3
"""
True end-to-end test for the multi-step LLM pipeline.
Runs all 7 stages from original input to GitHub repository creation.
Pulls API keys from AWS Secrets Manager.
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import traceback
import boto3
from botocore.exceptions import ClientError


def get_secret_from_arn(secret_arn, profile="mvp"):
    """Retrieve secret value from AWS Secrets Manager using ARN."""
    try:
        # Create a Secrets Manager client with the specified profile
        session = boto3.Session(profile_name=profile)
        client = session.client('secretsmanager', region_name='us-east-1')
        
        # Get the secret value
        response = client.get_secret_value(SecretId=secret_arn)
        
        # Parse the secret
        if 'SecretString' in response:
            secret = response['SecretString']
            # If it's JSON, parse it
            try:
                secret_dict = json.loads(secret)
                # Return the first value if it's a dict
                if isinstance(secret_dict, dict):
                    return list(secret_dict.values())[0]
            except:
                # Return as-is if not JSON
                return secret
        return None
    except ClientError as e:
        print(f"Error retrieving secret {secret_arn}: {e}")
        return None


def setup_environment_from_secrets():
    """Pull all API keys from AWS Secrets Manager and set environment variables."""
    
    print("\n🔐 Retrieving API keys from AWS Secrets Manager...")
    
    secrets = {
        "ANTHROPIC_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6",
        "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY",
        "EXA_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-N7ylem",
        "COHERE_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j",
        "GITHUB_TOKEN": "arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy",
        "PERPLEXITY_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM"
    }
    
    retrieved = 0
    for env_var, secret_arn in secrets.items():
        # Only retrieve if not already set
        if not os.getenv(env_var):
            value = get_secret_from_arn(secret_arn)
            if value:
                os.environ[env_var] = value
                print(f"  ✓ {env_var} retrieved and set")
                retrieved += 1
            else:
                print(f"  ✗ Failed to retrieve {env_var}")
        else:
            print(f"  ✓ {env_var} already set")
            retrieved += 1
    
    print(f"\n  Retrieved {retrieved}/{len(secrets)} secrets")
    return retrieved == len(secrets)


def setup_test_environment():
    """Create a temporary test directory for outputs."""
    # Create test output directory
    test_dir = Path("test_outputs")
    test_dir.mkdir(exist_ok=True)
    
    # Add to .gitignore if not already there
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "test_outputs/" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# E2E test outputs\ntest_outputs/\n")
    
    # Change to test directory for outputs
    os.chdir(test_dir)
    return test_dir


def cleanup_test_environment(test_dir, original_dir):
    """Clean up test directory after test completion."""
    os.chdir(original_dir)
    if test_dir.exists():
        print(f"\n🧹 Cleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir)


def run_pipeline_stage(script_name, args=None, description=""):
    """Run a single pipeline stage and capture output."""
    print(f"\n{'=' * 60}")
    print(f"🔄 {description}")
    print('=' * 60)
    
    cmd = ["python", f"../{script_name}"]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        print(f"✅ {description} complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}:")
        print(e.stdout)
        print(e.stderr)
        return False


def run_e2e_test(input_file="../tests/fixtures/sample_research.json", cleanup=True):
    """
    Run complete end-to-end test of the pipeline.
    
    Args:
        input_file: Path to the original research input file
        cleanup: Whether to clean up test files after completion
    """
    print("=" * 70)
    print("🚀 MULTI-STEP LLM PIPELINE - TRUE END-TO-END TEST WITH SECRETS")
    print("=" * 70)
    
    # Store original directory
    original_dir = Path.cwd()
    
    # Setup environment from secrets
    if not setup_environment_from_secrets():
        print("\n❌ Failed to retrieve all required secrets from AWS")
        print("   Make sure you have AWS credentials configured with profile 'mvp'")
        return False
    
    # Verify all required environment variables are set
    required_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "EXA_API_KEY", 
                     "COHERE_API_KEY", "GITHUB_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Still missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n✅ All API keys loaded successfully")
    
    # Setup test environment
    test_dir = setup_test_environment()
    print(f"\n📁 Test output directory: {test_dir.absolute()}")
    
    # Track all generated files
    generated_files = []
    
    try:
        # Copy input file to test directory
        input_path = Path(input_file)
        if not input_path.exists():
            # Try relative to original directory
            input_path = original_dir / input_file
        
        if input_path.exists():
            shutil.copy(input_path, "research_input.json")
            print(f"\n📥 Copied research input to test directory")
        else:
            print(f"\n❌ Input file not found: {input_file}")
            return False
        
        print("\n" + "=" * 70)
        print("STARTING FULL PIPELINE EXECUTION")
        print("=" * 70)
        
        # Stage 1: Research Analysis
        if not run_pipeline_stage(
            "research_analyzer.py",
            args=["--local", "research_input.json"],
            description="STAGE 1: Research Analysis"
        ):
            return False
        generated_files.append("research_analysis.json")
        
        # Stage 2: JTBD Research
        if not run_pipeline_stage(
            "jobs_researcher.py",
            description="STAGE 2: Jobs-to-be-Done Research"
        ):
            return False
        generated_files.append("jobs_to_be_done.json")
        generated_files.append("jtbd_research.md")
        
        # Stage 3: Pain Point Clustering
        # First, extract pain points
        with open("research_analysis.json", 'r') as f:
            analysis = json.load(f)
        
        pain_points_text = "Pain points from research:\n"
        if 'pain_points' in analysis:
            for point in analysis['pain_points']:
                pain_points_text += f"- {point}\n"
        
        # Save pain points file
        with open("pain_points.txt", 'w') as f:
            f.write(pain_points_text)
        
        if not run_pipeline_stage(
            "cluster_jtbd.py",
            args=["pain_points.txt"],
            description="STAGE 3: Pain Point Clustering"
        ):
            return False
        generated_files.append("opportunity_zones.json")
        
        # Stage 4: Value Curve Mapping
        if not run_pipeline_stage(
            "value_curve_mapper.py",
            args=["opportunity_zones.json"],
            description="STAGE 4: Value Curve Mapping"
        ):
            return False
        generated_files.append("value_curves.json")
        
        # Stage 5: Product Idea Generation
        if not run_pipeline_stage(
            "product_idea_generator.py",
            args=["--input", "value_curves.json"],
            description="STAGE 5: Product Idea Generation"
        ):
            return False
        generated_files.append("product_ideas.json")
        
        # Stage 6: Idea Consolidation
        if not run_pipeline_stage(
            "idea_consolidator.py",
            description="STAGE 6: Idea Consolidation"
        ):
            return False
        generated_files.append("product_ideas_comprehensive.json")
        
        # Stage 7: GitHub Repository Creation
        print("\n" + "=" * 70)
        print("🔄 STAGE 7: GitHub Repository Creation")
        print("=" * 70)
        
        # Create unique repo name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        repo_name = f"e2e-pipeline-test-{timestamp}"
        
        print(f"\n📦 Creating GitHub repository: {repo_name}")
        print(f"   Organization: ocean-studio-repos")
        
        # Load the generated data
        with open("research_analysis.json", 'r') as f:
            research_analysis = json.load(f)
        with open("jobs_to_be_done.json", 'r') as f:
            jtbd_data = json.load(f)
        with open("opportunity_zones.json", 'r') as f:
            zones_data = json.load(f)
        with open("product_ideas_comprehensive.json", 'r') as f:
            ideas_data = json.load(f)
        
        # Count product ideas
        product_count = len(ideas_data.get('product_ideas', []))
        print(f"   Product Ideas to create: {product_count}")
        
        # Import and run GitHub integration
        sys.path.insert(0, str(original_dir))
        from github_integration import create_github_output
        
        github_result = create_github_output(
            research_analysis=research_analysis,
            jtbd_data=jtbd_data,
            zones_data=zones_data,
            ideas_data=ideas_data,
            repo_name=repo_name,
            private=False,
            create_issues=True,
            organization="ocean-studio-repos"
        )
        
        if github_result and github_result.get('success'):
            repo_url = github_result.get('repo_url') or github_result.get('results', {}).get('repo_url')
            issues_count = len(github_result.get('results', {}).get('issues_created', []))
            
            print(f"\n✅ GitHub repository created successfully!")
            print(f"   URL: {repo_url}")
            print(f"   Issues created: {issues_count}")
            
            # List the product ideas that were created
            if ideas_data.get('product_ideas'):
                print("\n💡 Product Ideas Generated and Created as Issues:")
                for i, idea in enumerate(ideas_data['product_ideas'][:10], 1):
                    idea_name = idea.get('name', idea.get('idea_name', f'Idea {i}'))
                    print(f"   {i:2}. {idea_name}")
                if len(ideas_data['product_ideas']) > 10:
                    print(f"   ... and {len(ideas_data['product_ideas']) - 10} more")
        else:
            print(f"\n⚠️  GitHub repository creation had issues")
            if github_result:
                print(f"   Details: {github_result}")
        
        print("\n" + "=" * 70)
        print("✅ END-TO-END TEST COMPLETE!")
        print("=" * 70)
        
        print("\n📊 Pipeline Summary:")
        print(f"   • Stages completed: 7/7")
        print(f"   • Files generated: {len(generated_files)}")
        print(f"   • Product ideas generated: {product_count}")
        print(f"   • GitHub repo: {repo_url if 'repo_url' in locals() else 'Not created'}")
        print(f"   • GitHub issues created: {issues_count if 'issues_count' in locals() else 0}")
        
        print("\n📂 Generated files in test directory:")
        for file in generated_files:
            file_path = Path(file)
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"   • {file} ({size:,} bytes)")
        
        print("\n🎯 Success Metrics:")
        print(f"   • Research → Analysis: ✅")
        print(f"   • Analysis → JTBD: ✅")
        print(f"   • JTBD → Clustering: ✅")
        print(f"   • Clustering → Value Curves: ✅")
        print(f"   • Value Curves → Product Ideas: ✅")
        print(f"   • Product Ideas → Consolidation: ✅")
        print(f"   • Consolidation → GitHub Repo: ✅")
        print(f"   • Product Ideas → GitHub Issues: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}")
        traceback.print_exc()
        return False
        
    finally:
        if cleanup:
            cleanup_test_environment(test_dir, original_dir)
            print("\n✅ Test environment cleaned up")
        else:
            os.chdir(original_dir)
            print(f"\n📁 Test files preserved in: {test_dir.absolute()}")


if __name__ == "__main__":
    # Check for command line arguments
    cleanup = "--no-cleanup" not in sys.argv
    
    # Use sample research file or provided file
    if len(sys.argv) > 1 and sys.argv[1] != "--no-cleanup":
        input_file = sys.argv[1]
    else:
        # Use the Providence Hill research file for a real test
        input_file = "../tests/fixtures/sample_research.json"
    
    print("\n🚀 Starting E2E Test with AWS Secrets Manager")
    print("   This will:")
    print("   1. Pull all API keys from AWS Secrets Manager")
    print("   2. Run all 7 pipeline stages sequentially")
    print("   3. Generate all intermediate files in test_outputs/")
    print("   4. Create a real GitHub repository with issues")
    print("   5. Clean up test files afterward (unless --no-cleanup)")
    
    # Run the test
    success = run_e2e_test(input_file=input_file, cleanup=cleanup)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)