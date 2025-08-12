#!/usr/bin/env python3
"""
Lambda-compatible Idea Consolidator
Refactored from idea_consolidator.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- Memory-efficient portfolio analysis
- Comprehensive consolidation logic
- Proper error handling for complex data structures
- Cold start optimization
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handler for connection reuse)
s3_client = None
secrets_client = None

def initialize_clients():
    """Initialize AWS clients with retry configuration"""
    global s3_client, secrets_client
    
    if s3_client is None:
        s3_client = boto3.client('s3',
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )
    
    if secrets_client is None:
        secrets_client = boto3.client('secretsmanager',
            config=boto3.session.Config(
                retries={'max_attempts': 2, 'mode': 'standard'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )

def read_s3_object(bucket: str, key: str) -> str:
    """Read text content from S3 object"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read S3 object s3://{bucket}/{key}: {e}")
        raise

def read_s3_json(bucket: str, key: str) -> Dict[str, Any]:
    """Read JSON content from S3 object"""
    content = read_s3_object(bucket, key)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from s3://{bucket}/{key}: {e}")
        raise

def write_s3_object(bucket: str, key: str, content: str, content_type: str = 'text/plain'):
    """Write content to S3 object"""
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )
        logger.info(f"Successfully wrote to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"Failed to write S3 object s3://{bucket}/{key}: {e}")
        raise

def extract_complete_journey(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the complete journey metadata from all pipeline steps"""
    
    metadata = product_data.get("metadata", {})
    
    journey = {
        "pipeline_completion_timestamp": datetime.now().isoformat(),
        "total_ideas_generated": metadata.get("total_ideas_generated", 0),
        "ideas_after_filtering": metadata.get("ideas_after_filtering", 0),
        "generation_model": metadata.get("generation_model", "Unknown"),
        "enrichment_model": metadata.get("enrichment_model", "Unknown"),
        "pipeline_version": "2.0.0-lambda",
        "pipeline_steps": [
            "research_analysis",
            "jtbd_research", 
            "jtbd_clustering",
            "opportunity_zone_analysis",
            "value_curve_mapping",
            "product_idea_generation",
            "final_consolidation"
        ],
        "processing_mode": "AWS Lambda Serverless Pipeline"
    }
    
    return journey

def create_exhaustive_idea_details(idea: Dict[str, Any], idea_index: int) -> Dict[str, Any]:
    """Create exhaustive details for a single product idea"""
    
    timestamp = datetime.now().isoformat()
    
    return {
        "idea_id": f"IDEA-{idea_index+1:03d}",
        "metadata": {
            "generated_timestamp": timestamp,
            "composite_score": idea.get("composite_score", 0),
            "innovation_score": idea.get("innovation_score", 0),
            "viability_score": idea.get("viability_score", 0),
            "filtering_survived": True,
            "enrichment_completed": bool(idea.get("technical_architecture"))
        },
        "core_concept": {
            "name": idea.get("name", "Unnamed Idea"),
            "tagline": idea.get("tagline", "No tagline provided"),
            "value_proposition": idea.get("value_proposition", "No value proposition provided"),
            "target_segment": idea.get("target_segment", "Not specified"),
            "business_model": idea.get("business_model", "Not specified")
        },
        "scores": {
            "innovation_score": idea.get("innovation_score", 0),
            "viability_score": idea.get("viability_score", 0),
            "composite_score": idea.get("composite_score", 0)
        },
        "features": idea.get("features", []),
        "business_details": {
            "go_to_market": idea.get("go_to_market", "Not specified"),
            "development_effort": idea.get("development_effort", "Not specified"),
            "revenue_potential": idea.get("revenue_potential", "Not specified")
        },
        "technical_analysis": {
            "architecture": idea.get("technical_architecture", "Architecture analysis not available"),
            "competitive_moat": idea.get("competitive_moat", "Competitive analysis not available")
        },
        "risk_assessment": {
            "primary_risks": idea.get("risk_assessment", {}).get("risks", ["Risk analysis not available"]),
            "mitigation_strategies": idea.get("risk_assessment", {}).get("mitigations", ["Mitigation analysis not available"])
        },
        "success_metrics": idea.get("success_metrics", ["Success metrics not available"]),
        "partnerships": idea.get("partnerships", ["Partnership analysis not available"]),
        "market_sizing": idea.get("market_sizing", "Market sizing analysis not available")
    }

def calculate_portfolio_value(ideas: List[Dict[str, Any]]) -> float:
    """Calculate total potential value for the portfolio"""
    if not ideas:
        return 0.0
    
    total_value = 0.0
    for idea in ideas:
        innovation = idea.get("innovation_score", 0)
        viability = idea.get("viability_score", 0)
        # Weight innovation slightly lower than viability for practical value
        idea_value = (viability * 0.6) + (innovation * 0.4)
        total_value += idea_value
    
    return round(total_value / len(ideas), 2)

def find_highest_scoring_idea(ideas: List[Dict[str, Any]], score_type: str) -> Dict[str, Any]:
    """Find highest scoring idea by specified score type"""
    if not ideas:
        return {}
    
    score_key = f"{score_type}_score"
    return max(ideas, key=lambda x: x.get(score_key, 0))

def find_quickest_to_market(ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find idea with shortest time to market"""
    if not ideas:
        return {}
    
    # Simple heuristic based on development effort text
    time_priority = {}
    for idea in ideas:
        effort = idea.get("development_effort", "").lower()
        if "3-6 months" in effort or "6 months" in effort:
            time_priority[idea["idea_id"]] = 1
        elif "6-12 months" in effort or "12 months" in effort:
            time_priority[idea["idea_id"]] = 2
        elif "12-18 months" in effort or "18 months" in effort:
            time_priority[idea["idea_id"]] = 3
        else:
            time_priority[idea["idea_id"]] = 4
    
    if not time_priority:
        return ideas[0]  # Return first idea as fallback
    
    quickest_id = min(time_priority.items(), key=lambda x: x[1])[0]
    return next((idea for idea in ideas if idea["idea_id"] == quickest_id), ideas[0])

def analyze_portfolio_themes(ideas: List[Dict[str, Any]]) -> List[str]:
    """Analyze common themes across the portfolio"""
    
    # Extract key terms from names and value propositions
    all_text = []
    for idea in ideas:
        name = idea.get("name", "").lower()
        value_prop = idea.get("value_proposition", "").lower()
        all_text.append(f"{name} {value_prop}")
    
    # Simple keyword extraction for themes
    common_themes = []
    
    # Technology themes
    tech_keywords = ["ai", "automation", "integration", "platform", "api", "analytics", "intelligence"]
    for keyword in tech_keywords:
        if sum(1 for text in all_text if keyword in text) >= 2:
            common_themes.append(f"{keyword.title()}-powered solutions")
    
    # Business themes
    business_keywords = ["workflow", "collaboration", "decision", "management", "optimization"]
    for keyword in business_keywords:
        if sum(1 for text in all_text if keyword in text) >= 2:
            common_themes.append(f"{keyword.title()} enhancement")
    
    return common_themes[:5]  # Top 5 themes

def create_implementation_roadmap(ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create an implementation roadmap based on scores and complexity"""
    
    # Sort ideas by composite score for prioritization
    sorted_ideas = sorted(ideas, key=lambda x: x.get("composite_score", 0), reverse=True)
    
    # Distribute ideas across phases based on viability and complexity
    phase1_ideas = []  # Quick wins - high viability, shorter development
    phase2_ideas = []  # Strategic builds - high innovation
    phase3_ideas = []  # Long-term bets
    
    for idea in sorted_ideas:
        viability = idea.get("viability_score", 0)
        innovation = idea.get("innovation_score", 0)
        effort = idea.get("development_effort", "").lower()
        
        # Phase 1: High viability + shorter development
        if viability >= 7 and ("6 months" in effort or "quick" in effort):
            phase1_ideas.append(idea)
        # Phase 2: Balanced or high innovation
        elif innovation >= 7 or (viability >= 6 and innovation >= 6):
            phase2_ideas.append(idea)
        # Phase 3: Everything else
        else:
            phase3_ideas.append(idea)
    
    # Ensure balanced distribution
    if len(phase1_ideas) > 3:
        phase2_ideas.extend(phase1_ideas[3:])
        phase1_ideas = phase1_ideas[:3]
    
    if len(phase2_ideas) > 3:
        phase3_ideas.extend(phase2_ideas[3:])
        phase2_ideas = phase2_ideas[:3]
    
    return {
        "phase_1": {
            "duration": "0-6 months",
            "focus": "Quick wins and validation",
            "ideas": [idea["idea_id"] for idea in phase1_ideas],
            "rationale": "High viability ideas for immediate market entry"
        },
        "phase_2": {
            "duration": "6-18 months", 
            "focus": "Strategic development and scaling",
            "ideas": [idea["idea_id"] for idea in phase2_ideas],
            "rationale": "Balanced innovation and viability for growth"
        },
        "phase_3": {
            "duration": "18+ months",
            "focus": "Long-term innovation and expansion",
            "ideas": [idea["idea_id"] for idea in phase3_ideas],
            "rationale": "High-innovation plays for market differentiation"
        }
    }

def suggest_resource_allocation(ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Suggest resource allocation across the portfolio"""
    
    if not ideas:
        return {"message": "No ideas to allocate resources for"}
    
    total_score = sum(idea.get("composite_score", 0) for idea in ideas)
    
    allocations = []
    for idea in ideas:
        score = idea.get("composite_score", 0)
        percentage = (score / total_score * 100) if total_score > 0 else 0
        
        allocations.append({
            "idea_id": idea["idea_id"],
            "idea_name": idea.get("name", "Unknown"),
            "resource_percentage": round(percentage, 1),
            "priority": "High" if percentage > 20 else "Medium" if percentage > 10 else "Low",
            "justification": f"Composite score {score}/10"
        })
    
    # Sort by percentage
    allocations.sort(key=lambda x: x["resource_percentage"], reverse=True)
    
    return {
        "allocation_strategy": "Score-weighted distribution with viability emphasis",
        "total_portfolio_value": calculate_portfolio_value(ideas),
        "allocations": allocations,
        "recommended_budget": "$2M-5M for complete portfolio development",
        "timeline": "18-36 months for full implementation"
    }

def create_final_output(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create the final comprehensive output"""
    
    # Extract ideas from product data structure
    if "filtered_ideas" in product_data:
        ideas = product_data["filtered_ideas"]
    elif "ideas" in product_data:
        ideas = product_data["ideas"]
    elif isinstance(product_data, list):
        ideas = product_data
    else:
        ideas = []
    
    if not ideas:
        logger.warning("No ideas found in product data")
        ideas = []
    
    # Create exhaustive details for each idea
    all_ideas = []
    for idx, idea in enumerate(ideas):
        exhaustive_details = create_exhaustive_idea_details(idea, idx)
        all_ideas.append(exhaustive_details)
    
    # Portfolio analysis
    portfolio_themes = analyze_portfolio_themes(ideas)
    implementation_roadmap = create_implementation_roadmap(ideas)
    resource_allocation = suggest_resource_allocation(ideas)
    
    # Find key ideas
    highest_scoring = find_highest_scoring_idea(ideas, "composite") if ideas else {}
    most_innovative = find_highest_scoring_idea(ideas, "innovation") if ideas else {}
    quickest_to_market = find_quickest_to_market(ideas) if ideas else {}
    
    # Create final structure
    final_output = {
        "pipeline_metadata": extract_complete_journey(product_data),
        "executive_summary": {
            "total_innovation_ideas": len(all_ideas),
            "portfolio_value_score": calculate_portfolio_value(ideas),
            "portfolio_themes": portfolio_themes,
            "highest_scoring_idea": {
                "name": highest_scoring.get("name", "N/A"),
                "composite_score": highest_scoring.get("composite_score", 0)
            },
            "most_innovative_idea": {
                "name": most_innovative.get("name", "N/A"), 
                "innovation_score": most_innovative.get("innovation_score", 0)
            },
            "quickest_to_market": {
                "name": quickest_to_market.get("name", "N/A"),
                "development_effort": quickest_to_market.get("development_effort", "N/A")
            },
            "recommendation": "Evaluate portfolio based on strategic fit and resource availability. Focus on Phase 1 ideas for immediate impact."
        },
        "implementation_roadmap": implementation_roadmap,
        "resource_allocation": resource_allocation,
        "all_filtered_ideas": all_ideas,
        "portfolio_metrics": {
            "average_innovation_score": round(sum(i.get("innovation_score", 0) for i in ideas) / len(ideas), 2) if ideas else 0,
            "average_viability_score": round(sum(i.get("viability_score", 0) for i in ideas) / len(ideas), 2) if ideas else 0,
            "average_composite_score": round(sum(i.get("composite_score", 0) for i in ideas) / len(ideas), 2) if ideas else 0
        },
        "success_metrics": {
            "short_term": ["User adoption rates", "Feature utilization", "Customer feedback scores"],
            "medium_term": ["Revenue growth", "Market penetration", "Customer retention"],
            "long_term": ["Market leadership", "Platform expansion", "Category dominance"]
        }
    }
    
    return final_output

def create_summary_report(final_data: Dict[str, Any]) -> str:
    """Create a human-readable summary report"""
    
    timestamp = final_data["pipeline_metadata"]["pipeline_completion_timestamp"]
    ideas = final_data["all_filtered_ideas"]
    exec_summary = final_data["executive_summary"]
    
    report = f"""# Innovation Portfolio Summary Report

**Generated:** {timestamp}  
**Processing Mode:** AWS Lambda Serverless Pipeline  
**Portfolio Value Score:** {exec_summary.get('portfolio_value_score', 0)}/10  

## Executive Summary

This portfolio contains **{len(ideas)} high-quality product ideas** generated through comprehensive market analysis and value curve mapping. The ideas have been filtered, ranked, and enriched with detailed implementation guidance.

### Portfolio Highlights

- **Top Opportunity:** {exec_summary['highest_scoring_idea']['name']} (Score: {exec_summary['highest_scoring_idea']['composite_score']})
- **Most Innovative:** {exec_summary['most_innovative_idea']['name']} (Innovation: {exec_summary['most_innovative_idea']['innovation_score']}/10)
- **Quickest to Market:** {exec_summary['quickest_to_market']['name']} ({exec_summary['quickest_to_market']['development_effort']})

### Common Themes
{chr(10).join([f'- {theme}' for theme in exec_summary.get('portfolio_themes', [])])}

## All Ideas Ranked by Composite Score

"""
    
    # Sort ideas by composite score
    sorted_ideas = sorted(ideas, key=lambda x: x.get("scores", {}).get("composite_score", 0), reverse=True)
    
    for i, idea in enumerate(sorted_ideas, 1):
        core = idea.get("core_concept", {})
        scores = idea.get("scores", {})
        business = idea.get("business_details", {})
        
        report += f"""### {i}. {core.get('name', 'Unknown')}

- **Tagline:** {core.get('tagline', 'N/A')}
- **Value Proposition:** {core.get('value_proposition', 'N/A')[:100]}...
- **Composite Score:** {scores.get('composite_score', 0)}/10
- **Innovation Score:** {scores.get('innovation_score', 0)}/10  
- **Viability Score:** {scores.get('viability_score', 0)}/10
- **Development Effort:** {business.get('development_effort', 'N/A')}
- **Revenue Potential:** {business.get('revenue_potential', 'N/A')}

"""
    
    # Implementation roadmap
    roadmap = final_data.get("implementation_roadmap", {})
    report += f"""## Recommended Implementation Roadmap

### Phase 1: {roadmap.get('phase_1', {}).get('focus', 'Quick Wins')} ({roadmap.get('phase_1', {}).get('duration', '0-6 months')})
Ideas: {len(roadmap.get('phase_1', {}).get('ideas', []))}
{roadmap.get('phase_1', {}).get('rationale', '')}

### Phase 2: {roadmap.get('phase_2', {}).get('focus', 'Strategic Development')} ({roadmap.get('phase_2', {}).get('duration', '6-18 months')})
Ideas: {len(roadmap.get('phase_2', {}).get('ideas', []))}
{roadmap.get('phase_2', {}).get('rationale', '')}

### Phase 3: {roadmap.get('phase_3', {}).get('focus', 'Long-term Innovation')} ({roadmap.get('phase_3', {}).get('duration', '18+ months')})
Ideas: {len(roadmap.get('phase_3', {}).get('ideas', []))}
{roadmap.get('phase_3', {}).get('rationale', '')}

## Portfolio Metrics

- **Average Innovation Score:** {final_data.get('portfolio_metrics', {}).get('average_innovation_score', 0)}/10
- **Average Viability Score:** {final_data.get('portfolio_metrics', {}).get('average_viability_score', 0)}/10
- **Average Composite Score:** {final_data.get('portfolio_metrics', {}).get('average_composite_score', 0)}/10

## Next Steps

{exec_summary.get('recommendation', 'Evaluate ideas based on strategic priorities and available resources.')}

---

*This report was generated by the AWS Lambda Multi-Step LLM Pipeline.*
"""
    
    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for idea consolidation
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "products/ideas.json",
        "output_keys": {
            "portfolio": "final/portfolio.json",
            "summary": "final/summary.md"
        },
        "job_id": "job-123",
        "metadata": {...}
    }
    """
    start_time = time.time()
    
    try:
        # Initialize AWS clients
        initialize_clients()
        
        # Extract event parameters
        bucket = event.get('bucket')
        input_key = event.get('input_key')
        output_keys = event.get('output_keys', {})
        job_id = event.get('job_id', 'unknown')
        metadata = event.get('metadata', {})
        
        if not bucket or not input_key:
            raise ValueError("Missing required parameters: bucket and input_key")
        
        logger.info(f"Processing idea consolidation for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        
        # Read product ideas from S3
        logger.info("Loading product ideas from S3...")
        product_data = read_s3_json(bucket, input_key)
        
        # Create final comprehensive output
        logger.info("Consolidating innovation portfolio...")
        final_output = create_final_output(product_data)
        
        # Create human-readable summary
        logger.info("Generating summary report...")
        summary_report = create_summary_report(final_output)
        
        # Save outputs to S3
        outputs_created = []
        
        if 'portfolio' in output_keys:
            write_s3_object(bucket, output_keys['portfolio'], 
                          json.dumps(final_output, indent=2), 'application/json')
            outputs_created.append(f"s3://{bucket}/{output_keys['portfolio']}")
        
        if 'summary' in output_keys:
            write_s3_object(bucket, output_keys['summary'], summary_report, 'text/markdown')
            outputs_created.append(f"s3://{bucket}/{output_keys['summary']}")
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'job_id': job_id,
            'execution_time': round(execution_time, 2),
            'output_locations': outputs_created,
            'total_ideas_consolidated': len(final_output.get('all_filtered_ideas', [])),
            'portfolio_value_score': final_output.get('executive_summary', {}).get('portfolio_value_score', 0),
            'top_idea': final_output.get('executive_summary', {}).get('highest_scoring_idea', {}).get('name', 'N/A'),
            'implementation_phases': len(final_output.get('implementation_roadmap', {})),
            'portfolio_themes_identified': len(final_output.get('executive_summary', {}).get('portfolio_themes', [])),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Idea consolidation completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Idea consolidation failed: {e}")
        
        return {
            'statusCode': 500,
            'error': str(e),
            'job_id': event.get('job_id', 'unknown'),
            'execution_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

# For local testing
if __name__ == "__main__":
    test_event = {
        "bucket": "test-bucket",
        "input_key": "products/ideas.json",
        "output_keys": {
            "portfolio": "final/portfolio.json",
            "summary": "final/summary.md"
        },
        "job_id": "test-job-123",
        "metadata": {"stage": "consolidation"}
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_consolidator"
            self.memory_limit_in_mb = 1024
            self.remaining_time_in_millis = lambda: 300000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))