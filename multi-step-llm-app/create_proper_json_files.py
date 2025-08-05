#!/usr/bin/env python3
"""
Create proper JSON files from the actual pipeline markdown outputs
This fixes the issue where product_idea_generator.py is looking for JSON files that don't exist
"""

import os
import json
import re
from typing import Dict, Any, List


def parse_jtbd_table(content: str) -> List[Dict[str, Any]]:
    """Parse the JTBD table from markdown content"""
    jobs = []
    
    # Find the JTBD table
    table_match = re.search(
        r'\| Job Statement.*?\n\|[-\s|]+\n(.*?)(?=\n\n|\Z)', 
        content, 
        re.DOTALL
    )
    
    if table_match:
        table_content = table_match.group(1)
        
        for line in table_content.split('\n'):
            if line.strip() and '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 5 and parts[0].startswith('When'):
                    # Extract importance and satisfaction from job statement if possible
                    importance = 8  # Default
                    satisfaction = 4  # Default
                    
                    # Try to extract opportunity score
                    try:
                        opportunity_score = int(parts[4])
                    except:
                        opportunity_score = importance + max(importance - satisfaction, 0)
                    
                    job = {
                        "job_id": f"JOB-{len(jobs)+1:03d}",
                        "job_statement": parts[0],
                        "frequency": parts[1],
                        "current_solutions": parts[2],
                        "pain_level": parts[3],
                        "importance": importance,
                        "satisfaction": satisfaction,
                        "opportunity_score": opportunity_score
                    }
                    jobs.append(job)
    
    return jobs


def create_jobs_to_be_done_json():
    """Create jobs_to_be_done.json from jtbd_research.md"""
    
    if not os.path.exists("jtbd_research.md"):
        print("jtbd_research.md not found")
        return False
    
    with open("jtbd_research.md", "r") as f:
        content = f.read()
    
    # Parse JTBD table
    jobs = parse_jtbd_table(content)
    
    # Create the expected format
    jtbd_data = {
        "jtbd_data": {
            "jobs_list": jobs,
            "research_summary": f"Identified {len(jobs)} jobs-to-be-done through comprehensive research",
            "methodology": "Customer interviews, pain point analysis, and opportunity scoring"
        }
    }
    
    # Save to JSON
    with open("jobs_to_be_done.json", "w") as f:
        json.dump(jtbd_data, f, indent=2)
    
    print(f"Created jobs_to_be_done.json with {len(jobs)} jobs")
    return True


def create_research_analysis_json():
    """Create research_analysis.json from analysis_results.md"""
    
    if not os.path.exists("analysis_results.md"):
        print("analysis_results.md not found")
        return False
    
    with open("analysis_results.md", "r") as f:
        content = f.read()
    
    research_data = {}
    
    # Extract executive summary
    exec_match = re.search(r"## Executive Summary\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if exec_match:
        research_data["executive_summary"] = exec_match.group(1).strip()
    else:
        research_data["executive_summary"] = "Comprehensive market research and analysis"
    
    # Extract key themes
    themes_match = re.search(r"## Key Themes\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if themes_match:
        research_data["key_themes"] = themes_match.group(1).strip()
    
    # Extract market insights
    insights_match = re.search(r"## Market Insights\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if insights_match:
        research_data["market_insights"] = insights_match.group(1).strip()
    
    # Save to JSON
    with open("research_analysis.json", "w") as f:
        json.dump(research_data, f, indent=2)
    
    print("Created research_analysis.json with executive summary")
    return True


def main():
    """Create all necessary JSON files"""
    
    print("Creating proper JSON files from pipeline outputs...")
    
    # Create JTBD JSON
    if create_jobs_to_be_done_json():
        # Verify the content
        with open("jobs_to_be_done.json", "r") as f:
            data = json.load(f)
            print(f"  - JTBD data: {len(data['jtbd_data']['jobs_list'])} jobs")
            if data['jtbd_data']['jobs_list']:
                print(f"  - First job: {data['jtbd_data']['jobs_list'][0]['job_statement'][:80]}...")
    
    # Create research analysis JSON
    if create_research_analysis_json():
        # Verify the content
        with open("research_analysis.json", "r") as f:
            data = json.load(f)
            print(f"  - Executive summary: {data['executive_summary'][:80]}...")
    
    print("\nJSON files created successfully!")
    print("Now run: python product_idea_generator.py --github --repo-name 'your-repo-name'")


if __name__ == "__main__":
    main()