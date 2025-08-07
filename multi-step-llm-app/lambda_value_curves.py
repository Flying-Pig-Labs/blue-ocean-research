#!/usr/bin/env python3
"""
Lambda-compatible Value Curve Mapper
Refactored from value_curve_mapper.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- EXA API integration with proper rate limiting
- Memory-efficient value curve analysis
- Parallel processing of opportunity zones
- Cold start optimization
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def get_secrets() -> Dict[str, str]:
    """Load API keys from AWS Secrets Manager"""
    secrets = {}
    secret_name = os.environ.get('SECRETS_NAME', 'pipeline-secrets')
    
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        
        # Extract API keys
        secrets['EXA_API_KEY'] = secret_data.get('EXA_API_KEY')
        secrets['ANTHROPIC_API_KEY'] = secret_data.get('ANTHROPIC_API_KEY')
        
        logger.info("Successfully loaded secrets from Secrets Manager")
        return secrets
        
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        # Fallback to environment variables
        return {
            'EXA_API_KEY': os.environ.get('EXA_API_KEY'),
            'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY')
        }

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

def call_exa_search(query: str, api_key: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """Search using EXA API with error handling"""
    from exa_py import Exa
    
    try:
        exa = Exa(api_key=api_key)
        
        response = exa.search_and_contents(
            query=query,
            type="neural",
            use_autoprompt=True,
            num_results=num_results,
            text=True,
            highlights=True,
            summary=True,
            include_domains=None,
            exclude_domains=[
                "reddit.com",
                "twitter.com", 
                "facebook.com",
                "linkedin.com"  # Focus on product/company info
            ]
        )
        
        results = []
        for result in response.results:
            results.append({
                'url': result.url,
                'title': result.title,
                'content': result.text[:3000] if result.text else '',  # Limit content
                'highlights': result.highlights[:5] if result.highlights else [],
                'summary': result.summary if hasattr(result, 'summary') else '',
                'published_date': result.published_date if hasattr(result, 'published_date') else None
            })
        
        logger.info(f"EXA search returned {len(results)} results for query: {query[:50]}...")
        return results
        
    except Exception as e:
        logger.warning(f"EXA search failed for query '{query[:50]}...': {e}")
        return []

def call_anthropic_api(prompt: str, model: str = "claude-3-5-sonnet-20241022", 
                      temperature: float = 0.7, max_tokens: int = 2000,
                      api_key: str = None) -> str:
    """Call Anthropic API with retry logic"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=api_key)
    
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.warning(f"Anthropic API attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise

def generate_search_queries(zone: Dict[str, Any]) -> List[str]:
    """Generate search queries for a zone"""
    
    zone_name = zone.get('name', 'Solution')
    zone_theme = zone.get('core_theme', zone.get('description', ''))
    requirements = zone.get('solution_requirements', [])
    
    queries = [
        f"{zone_name} competitive landscape",
        f"{zone_name} market analysis solutions",
        f"{zone_theme} existing products",
        f"best {zone_name.lower()} tools platforms"
    ]
    
    # Add queries based on requirements
    for req in requirements[:2]:  # Top 2 requirements
        if len(req) > 10:
            queries.append(f"{req} software solutions")
    
    return queries[:5]  # Limit to 5 queries per zone

def analyze_zone_value_curve(zone: Dict[str, Any], search_results: List[Dict[str, Any]], 
                           anthropic_key: str) -> Dict[str, Any]:
    """Analyze value curve for a single opportunity zone"""
    
    zone_name = zone.get('name', 'Unknown Zone')
    zone_theme = zone.get('core_theme', zone.get('description', ''))
    
    # Prepare search context
    search_context = []
    for i, result in enumerate(search_results[:10]):  # Top 10 results
        search_context.append(f"""
Result {i+1}: {result['title']}
URL: {result['url']}
Summary: {result.get('summary', '')}
Key highlights: {', '.join(result.get('highlights', [])[:3])}
Content snippet: {result['content'][:300]}...
""")
    
    search_text = '\n'.join(search_context)
    
    prompt = f"""Opportunity Zone: {zone_name}
Theme: {zone_theme}

Based on market research, analyze the competitive landscape:

{search_text}

Create a value curve analysis with:
1. **Key Factors** (8-10 factors that matter in this space)
2. **Current State** (How existing solutions perform on each factor, 1-10 scale)
3. **Opportunity Gaps** (Where current solutions fall short)
4. **Innovation Potential** (Where we could dramatically improve)
5. **Strategic Canvas** (Visual representation of the value curve)

Format as JSON with this structure:
{{
  "key_factors": [
    {{
      "factor": "Factor Name",
      "current_score": 5,
      "opportunity_gap": "High/Medium/Low",
      "innovation_potential": "Description of potential improvement"
    }}
  ],
  "strategic_insights": {{
    "strengths": ["Current market strengths"],
    "gaps": ["Major opportunity gaps"],
    "innovation_opportunities": ["Areas for breakthrough innovation"]
  }},
  "market_maturity": "Early/Growing/Mature",
  "competitive_intensity": "Low/Medium/High"
}}"""

    try:
        response = call_anthropic_api(prompt, model="claude-3-5-haiku-20241022",
                                    temperature=0.5, max_tokens=3000, api_key=anthropic_key)
        
        # Try to parse as JSON
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif response.startswith('```') and response.endswith('```'):
                response = response.strip('```').strip()
            
            analysis = json.loads(response)
            
            # Validate and enrich
            if 'key_factors' not in analysis:
                analysis['key_factors'] = []
            if 'strategic_insights' not in analysis:
                analysis['strategic_insights'] = {
                    "strengths": ["Analysis unavailable"],
                    "gaps": ["Analysis unavailable"],
                    "innovation_opportunities": ["Analysis unavailable"]
                }
            
            return analysis
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse value curve analysis as JSON for {zone_name}")
            return create_fallback_analysis(zone_name)
    
    except Exception as e:
        logger.warning(f"Value curve analysis failed for {zone_name}: {e}")
        return create_fallback_analysis(zone_name)

def create_fallback_analysis(zone_name: str) -> Dict[str, Any]:
    """Create fallback analysis when API call fails"""
    return {
        "key_factors": [
            {"factor": "Ease of Use", "current_score": 5, "opportunity_gap": "High", "innovation_potential": "Simplified user interface"},
            {"factor": "Integration", "current_score": 4, "opportunity_gap": "High", "innovation_potential": "Seamless API connections"},
            {"factor": "Cost", "current_score": 6, "opportunity_gap": "Medium", "innovation_potential": "Usage-based pricing"},
            {"factor": "Performance", "current_score": 7, "opportunity_gap": "Medium", "innovation_potential": "Real-time processing"},
            {"factor": "Support", "current_score": 5, "opportunity_gap": "High", "innovation_potential": "24/7 automated assistance"}
        ],
        "strategic_insights": {
            "strengths": ["Established market presence", "Feature completeness"],
            "gaps": ["User experience complexity", "Integration challenges"],
            "innovation_opportunities": ["AI-powered automation", "No-code interfaces"]
        },
        "market_maturity": "Growing",
        "competitive_intensity": "Medium"
    }

def process_opportunity_zone(zone: Dict[str, Any], exa_key: str, anthropic_key: str) -> Dict[str, Any]:
    """Process a single opportunity zone for value curve analysis"""
    
    zone_name = zone.get('name', 'Unknown Zone')
    logger.info(f"Processing value curve for: {zone_name}")
    
    # Generate search queries
    queries = generate_search_queries(zone)
    
    # Search for competitive landscape
    all_search_results = []
    for query in queries[:3]:  # Limit queries for Lambda efficiency
        results = call_exa_search(query, exa_key, num_results=5)
        all_search_results.extend(results)
        time.sleep(0.5)  # Rate limiting
    
    # Analyze value curve
    value_curve_analysis = analyze_zone_value_curve(zone, all_search_results, anthropic_key)
    
    # Enhanced zone data
    enhanced_zone = {
        **zone,
        "value_curve": value_curve_analysis,
        "search_results": len(all_search_results),
        "search_queries_used": queries[:3],
        "competitive_sources": [r.get('url', '') for r in all_search_results[:5]]
    }
    
    return enhanced_zone

def synthesize_value_curves(enhanced_zones: List[Dict[str, Any]], anthropic_key: str) -> str:
    """Synthesize insights across all value curves"""
    
    # Prepare synthesis context
    curve_summaries = []
    for zone in enhanced_zones:
        curve = zone.get('value_curve', {})
        insights = curve.get('strategic_insights', {})
        
        curve_summaries.append(f"""
Zone: {zone.get('name', 'Unknown')}
Market Maturity: {curve.get('market_maturity', 'Unknown')}
Competitive Intensity: {curve.get('competitive_intensity', 'Unknown')}
Top Gaps: {', '.join(insights.get('gaps', [])[:3])}
Innovation Opportunities: {', '.join(insights.get('innovation_opportunities', [])[:3])}
""")
    
    all_curves_text = '\n'.join(curve_summaries)
    
    prompt = f"""Synthesize these value curves into strategic insights:

{all_curves_text}

Provide strategic synthesis covering:
1. Common patterns across all zones
2. Biggest opportunity gaps
3. Areas for radical innovation
4. Quick wins vs long-term plays
5. Risk factors to consider

Format as markdown with clear sections."""
    
    try:
        return call_anthropic_api(prompt, api_key=anthropic_key, 
                                temperature=0.6, max_tokens=3000)
    except Exception as e:
        logger.warning(f"Synthesis failed: {e}")
        return "## Strategic Synthesis\n\nSynthesis analysis unavailable due to processing limitations."

def create_value_curves_report(enhanced_zones: List[Dict[str, Any]], 
                             synthesis: str, execution_metadata: Dict[str, Any]) -> str:
    """Create comprehensive value curves report"""
    
    timestamp = datetime.now().isoformat()
    
    # Build markdown report
    report = f"""# Value Curve Analysis Report

**Generated:** {timestamp}  
**Processing Mode:** Lambda EXA Search + Claude Analysis  
**Zones Analyzed:** {len(enhanced_zones)}  
**Total Search Results:** {sum(zone.get('search_results', 0) for zone in enhanced_zones)}  
**Execution Time:** {execution_metadata.get('execution_time', 'N/A')} seconds  

{synthesis}

---

## Individual Zone Analysis

"""
    
    for zone in enhanced_zones:
        curve = zone.get('value_curve', {})
        insights = curve.get('strategic_insights', {})
        
        report += f"""### {zone.get('name', 'Unknown Zone')}

**Market Maturity:** {curve.get('market_maturity', 'Unknown')}  
**Competitive Intensity:** {curve.get('competitive_intensity', 'Unknown')}  
**Search Results:** {zone.get('search_results', 0)} sources analyzed  

#### Key Value Factors:
"""
        
        for factor in curve.get('key_factors', [])[:5]:
            report += f"- **{factor.get('factor', 'Unknown')}**: {factor.get('current_score', 0)}/10 (Gap: {factor.get('opportunity_gap', 'Unknown')})\n"
        
        report += f"""
#### Strategic Insights:
- **Strengths:** {', '.join(insights.get('strengths', ['Not available'])[:3])}
- **Gaps:** {', '.join(insights.get('gaps', ['Not available'])[:3])}
- **Innovation Opportunities:** {', '.join(insights.get('innovation_opportunities', ['Not available'])[:3])}

#### Competitive Sources:
"""
        for url in zone.get('competitive_sources', [])[:3]:
            if url:
                report += f"- {url}\n"
        
        report += "\n---\n\n"
    
    report += f"""## Pipeline Metadata

- **Lambda Function:** Value Curve Mapper
- **EXA API Searches:** {sum(len(zone.get('search_queries_used', [])) for zone in enhanced_zones)} total queries
- **Claude Analysis:** Value curve analysis for {len(enhanced_zones)} zones
- **Processing Time:** {execution_metadata.get('execution_time', 'N/A')} seconds
"""
    
    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for value curve mapping
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "clusters/opportunity_zones.json",
        "output_keys": {
            "value_curves": "value_curves/analysis.json",
            "report": "value_curves/report.md"
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
        
        logger.info(f"Processing value curve mapping for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        
        # Load secrets
        secrets = get_secrets()
        exa_key = secrets.get('EXA_API_KEY')
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not exa_key or not anthropic_key:
            raise ValueError("Required API keys not available")
        
        # Read opportunity zones from S3
        logger.info("Loading opportunity zones from S3...")
        zones_data = read_s3_json(bucket, input_key)
        
        # Extract zones from different possible structures
        if 'opportunity_zones' in zones_data:
            opportunity_zones = zones_data['opportunity_zones']
        elif 'results' in zones_data:
            opportunity_zones = [result.get('zone', result) for result in zones_data['results']]
        elif isinstance(zones_data, list):
            opportunity_zones = zones_data
        else:
            opportunity_zones = [zones_data]
        
        if not opportunity_zones:
            raise ValueError("No opportunity zones found in input data")
        
        # Limit zones for Lambda processing efficiency
        limited_zones = opportunity_zones[:8]  # Max 8 zones
        logger.info(f"Processing {len(limited_zones)} opportunity zones")
        
        # Process zones with parallel execution
        enhanced_zones = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_zone = {
                executor.submit(process_opportunity_zone, zone, exa_key, anthropic_key): zone
                for zone in limited_zones
            }
            
            for future in as_completed(future_to_zone):
                zone = future_to_zone[future]
                try:
                    enhanced_zone = future.result(timeout=180)  # 3 minute timeout per zone
                    enhanced_zones.append(enhanced_zone)
                    logger.info(f"Completed value curve for: {zone.get('name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to process zone {zone.get('name', 'Unknown')}: {e}")
                    # Add zone without value curve analysis
                    enhanced_zones.append({**zone, "value_curve": create_fallback_analysis(zone.get('name', 'Unknown'))})
        
        # Sort by opportunity score if available
        enhanced_zones.sort(key=lambda x: x.get('market_opportunity_score', x.get('opportunity_score', 0)), reverse=True)
        
        # Synthesize insights across all zones
        logger.info("Synthesizing strategic insights...")
        synthesis = synthesize_value_curves(enhanced_zones, anthropic_key)
        
        # Create execution metadata
        execution_metadata = {
            'execution_time': round(time.time() - start_time, 2),
            'zones_processed': len(enhanced_zones),
            'total_search_results': sum(zone.get('search_results', 0) for zone in enhanced_zones)
        }
        
        # Create outputs
        value_curves_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_mode": "Lambda Parallel Analysis",
                "zones_analyzed": len(enhanced_zones),
                "total_search_results": execution_metadata['total_search_results']
            },
            "synthesis": synthesis,
            "zones": enhanced_zones
        }
        
        # Create report
        report = create_value_curves_report(enhanced_zones, synthesis, execution_metadata)
        
        # Save outputs to S3
        outputs_created = []
        
        if 'value_curves' in output_keys:
            write_s3_object(bucket, output_keys['value_curves'], 
                          json.dumps(value_curves_data, indent=2), 'application/json')
            outputs_created.append(f"s3://{bucket}/{output_keys['value_curves']}")
        
        if 'report' in output_keys:
            write_s3_object(bucket, output_keys['report'], report, 'text/markdown')
            outputs_created.append(f"s3://{bucket}/{output_keys['report']}")
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'job_id': job_id,
            'execution_time': round(execution_time, 2),
            'output_locations': outputs_created,
            'zones_processed': len(enhanced_zones),
            'total_search_results': execution_metadata['total_search_results'],
            'top_opportunity': enhanced_zones[0].get('name') if enhanced_zones else 'None',
            'synthesis_length': len(synthesis),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Value curve mapping completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Value curve mapping failed: {e}")
        
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
        "input_key": "clusters/opportunity_zones.json",
        "output_keys": {
            "value_curves": "value_curves/analysis.json",
            "report": "value_curves/report.md"
        },
        "job_id": "test-job-123",
        "metadata": {"stage": "value_curves"}
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_value_curves"
            self.memory_limit_in_mb = 3008
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))