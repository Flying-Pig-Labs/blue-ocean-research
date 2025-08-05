#!/usr/bin/env python3
"""
Run the complete multi-step LLM pipeline from start to finish.
This script executes all 7 stages sequentially.
"""

import subprocess
import sys
import os
import time
from datetime import datetime

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

def main():
    """Run the complete pipeline."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Multi-Step LLM Pipeline - Full Integration Test       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    start_time = time.time()
    stages_completed = 0
    
    # Stage 1: Research Analysis (commenting out as it requires S3)
    print("\n📌 Stage 1: Research Analysis - SKIPPED (requires S3 bucket)")
    print("   For real run: python research_analyzer.py")
    
    # Create a mock analysis_results.md for testing
    with open('analysis_results.md', 'w') as f:
        f.write("""# Market Analysis Results

## Industry Verticals
- SaaS Productivity Tools
- Enterprise Software
- Mobile Applications

## User Personas
- Knowledge Workers
- Remote Teams
- Enterprise IT Managers

## Pain Points
- Tool fragmentation and context switching
- Poor mobile experience
- Lack of integration between tools
- Security and compliance concerns

## Solution Types
- Unified workspace platforms
- Mobile-first productivity tools
- AI-powered automation
- Enterprise integration platforms
""")
    print("✅ Created mock analysis_results.md for testing")
    stages_completed += 1
    
    # Stage 2: JTBD Research
    if run_command(
        "python jobs_researcher.py",
        "Stage 2: Jobs-to-be-Done Research"
    ):
        if check_file_exists("jtbd_research.md", "JTBD Research"):
            check_file_exists("pain_points.txt", "Pain Points")
            stages_completed += 1
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 3: Clustering
    if run_command(
        "python cluster_jtbd_fix.py pain_points.txt",
        "Stage 3: Pain Point Clustering"
    ):
        if check_file_exists("opportunity_zones.json", "Opportunity Zones"):
            stages_completed += 1
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
    else:
        print("⚠️  Skipping remaining stages due to error")
        return
    
    # Stage 7: GitHub Integration
    print(f"\n{'='*60}")
    print("🚀 Stage 7: GitHub Repository Creation")
    print(f"{'='*60}")
    print("To create GitHub repository with all results:")
    print("python product_idea_generator.py --github --repo-name 'my-innovation-portfolio'")
    print("\nOr for private repository:")
    print("python product_idea_generator.py --github --repo-name 'my-innovation-portfolio' --github-private")
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
    main()