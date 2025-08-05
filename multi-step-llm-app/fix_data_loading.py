#!/usr/bin/env python3
"""
Fix for product_idea_generator.py to load actual pipeline data instead of dummy JSON files
"""

import os
import json
import re
from typing import Dict, Any

def load_actual_pipeline_data() -> Dict[str, Any]:
    """Load real data from actual pipeline output files"""
    
    # Load research analysis from markdown
    research_analysis = {"executive_summary": "Market research analysis"}
    if os.path.exists("analysis_results.md"):
        with open("analysis_results.md", "r") as f:
            content = f.read()
            # Extract executive summary
            exec_match = re.search(r"## Executive Summary\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
            if exec_match:
                research_analysis["executive_summary"] = exec_match.group(1).strip()
    
    # Load JTBD data from markdown
    jtbd_data = {"jtbd_data": {"jobs_list": []}}
    if os.path.exists("jtbd_research.md"):
        with open("jtbd_research.md", "r") as f:
            content = f.read()
            
            # Parse the JTBD table if it exists
            table_match = re.search(r"\| Job ID.*?\n\|[-\s|]+\n(.*?)(?=\n\n|\Z)", content, re.DOTALL)
            if table_match:
                table_content = table_match.group(1)
                jobs = []
                
                for line in table_content.split("\n"):
                    if line.strip() and "|" in line:
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        if len(parts) >= 5 and parts[0].startswith("JOB-"):
                            job = {
                                "job_id": parts[0],
                                "job_statement": parts[1],
                                "frequency": parts[2],
                                "importance": 8,  # Default since not in this format
                                "satisfaction": 4,  # Default
                                "opportunity_score": 12  # Default
                            }
                            jobs.append(job)
                
                jtbd_data["jtbd_data"]["jobs_list"] = jobs
    
    # Load zones data from opportunity_zones.json
    zones_data = {"clustered_zones": {}}
    if os.path.exists("opportunity_zones.json"):
        with open("opportunity_zones.json", "r") as f:
            zones_data = json.load(f)
    
    # Create the complete data package
    return {
        "research_analysis": research_analysis,
        "jtbd_data": jtbd_data,
        "zones_data": zones_data
    }


def update_product_idea_generator():
    """Update the product_idea_generator.py file to use actual data loading"""
    
    # Read the current file
    with open("product_idea_generator.py", "r") as f:
        content = f.read()
    
    # Find the section that loads data (around line 820-842)
    old_loading = """            # Load JTBD data from the pipeline
            jtbd_file = "jobs_to_be_done.json"
            if os.path.exists(jtbd_file):
                with open(jtbd_file, "r") as f:
                    jtbd_data = json.load(f)
            else:
                jtbd_data = {"jtbd_data": {"jobs_list": []}}

            # Load research analysis
            research_file = "research_analysis.json"
            if os.path.exists(research_file):
                with open(research_file, "r") as f:
                    research_analysis = json.load(f)
            else:
                research_analysis = {"executive_summary": "Market research analysis"}"""
    
    new_loading = """            # Load JTBD data from actual pipeline output
            jtbd_data = {"jtbd_data": {"jobs_list": []}}
            if os.path.exists("jtbd_research.md"):
                # Parse JTBD from markdown - the actual output format
                with open("jtbd_research.md", "r") as f:
                    jtbd_content = f.read()
                    # Simple extraction of JTBD patterns
                    jobs = []
                    for match in re.finditer(r'- \*\*Pattern\*\*: "([^"]+)".*?Context: ([^\n]+)', jtbd_content, re.DOTALL):
                        pattern = match.group(1)
                        context = match.group(2)
                        jobs.append({
                            "job_id": f"JOB-{len(jobs)+1:03d}",
                            "job_statement": f"When {pattern}, {context}",
                            "importance": 8,
                            "satisfaction": 4,
                            "opportunity_score": 12
                        })
                    if jobs:
                        jtbd_data["jtbd_data"]["jobs_list"] = jobs

            # Load research analysis from actual markdown output
            research_analysis = {"executive_summary": "Market research analysis"}
            if os.path.exists("analysis_results.md"):
                with open("analysis_results.md", "r") as f:
                    content = f.read()
                    # Extract executive summary
                    exec_match = re.search(r"## Executive Summary\s*\\n(.*?)(?=\\n##|\\Z)", content, re.DOTALL)
                    if exec_match:
                        research_analysis["executive_summary"] = exec_match.group(1).strip()"""
    
    # Replace the old loading code with the new one
    if old_loading in content:
        content = content.replace(old_loading, new_loading)
        # Also need to add re import at the top
        if "import re" not in content:
            content = content.replace("import json", "import json\nimport re")
        
        # Write the updated file
        with open("product_idea_generator_fixed.py", "w") as f:
            f.write(content)
        
        print("Created product_idea_generator_fixed.py with proper data loading")
        return True
    else:
        print("Could not find the data loading section to replace")
        return False


if __name__ == "__main__":
    # Test the data loading
    data = load_actual_pipeline_data()
    
    print("Research Analysis Executive Summary:")
    print(data["research_analysis"]["executive_summary"][:200] + "...")
    print(f"\nJTBD Jobs Found: {len(data['jtbd_data']['jtbd_data']['jobs_list'])}")
    print(f"Zones Found: {len(data['zones_data'].get('clustered_zones', {}))}")
    
    # Optionally update the file
    # update_product_idea_generator()