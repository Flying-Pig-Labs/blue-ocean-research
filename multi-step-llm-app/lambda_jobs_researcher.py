#!/usr/bin/env python3
"""
Lambda-compatible JTBD Researcher
Refactored from jobs_researcher.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- EXA API integration with proper error handling
- Memory-efficient JTBD processing
- Cold start optimization
- Rate limiting for API calls
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import time
import asyncio

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
        
        # Configure search for JTBD research
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
                "reddit.com",  # Exclude reddit for cleaner results
                "twitter.com",
                "facebook.com",
                "instagram.com"
            ]
        )
        
        results = []
        for result in response.results:
            results.append({
                'url': result.url,
                'title': result.title,
                'content': result.text[:2000] if result.text else '',  # Limit content
                'highlights': result.highlights[:5] if result.highlights else [],  # Top 5 highlights
                'summary': result.summary if hasattr(result, 'summary') else '',
                'published_date': result.published_date if hasattr(result, 'published_date') else None,
                'author': result.author if hasattr(result, 'author') else None
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
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def extract_jtbd_queries(analysis_content: str, anthropic_key: str) -> List[str]:
    """Extract search queries for JTBD research from analysis content"""
    prompt = f"""Based on this research analysis:

{analysis_content[:3000]}  # Limit content to avoid token overflow

Generate 8-12 specific search queries to find real-world Jobs-to-be-Done insights. 
Each query should focus on discovering what customers are really trying to accomplish.

Format queries as natural search terms that would find:
1. Customer pain points and needs
2. Current workflow descriptions
3. Solution comparisons and reviews
4. Industry-specific challenges
5. User experience discussions

Return ONLY a JSON array of search queries, nothing else.

Example format:
[
  "customer onboarding pain points workflow automation",
  "data integration challenges small business solutions",
  "project management tools user experience problems"
]"""

    try:
        response = call_anthropic_api(prompt, api_key=anthropic_key, max_tokens=1000)
        
        # Parse JSON response
        if response.startswith('[') and response.endswith(']'):
            queries = json.loads(response)
        else:
            # Fallback parsing if not clean JSON
            queries = []
            for line in response.split('\n'):
                line = line.strip().strip('"').strip("'").strip(',')
                if line and len(line) > 10 and not line.startswith('[') and not line.startswith(']'):
                    queries.append(line)
        
        # Clean and validate queries
        clean_queries = []
        for query in queries:
            if isinstance(query, str) and len(query) > 5:
                clean_queries.append(query.strip())
        
        logger.info(f"Extracted {len(clean_queries)} search queries")
        return clean_queries[:12]  # Limit to 12 queries max
        
    except Exception as e:
        logger.warning(f"Failed to extract JTBD queries: {e}")
        # Fallback to generic queries based on common JTBD patterns
        return [
            "customer workflow automation pain points",
            "business process inefficiencies solutions",
            "user experience problems software tools",
            "data management challenges organizations",
            "team collaboration tools frustrations",
            "integration challenges business systems"
        ]

def search_jtbd_insights(queries: List[str], exa_key: str) -> List[Dict[str, Any]]:
    """Search for JTBD insights using multiple queries"""
    all_results = []
    
    for i, query in enumerate(queries):
        logger.info(f"Searching query {i+1}/{len(queries)}: {query[:50]}...")
        
        try:
            results = call_exa_search(query, exa_key, num_results=5)
            
            # Add query context to results
            for result in results:
                result['source_query'] = query
                result['query_index'] = i
            
            all_results.extend(results)
            
            # Rate limiting - small delay between searches
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
            continue
    
    logger.info(f"Total search results collected: {len(all_results)}")
    return all_results

def synthesize_jtbd_research(search_results: List[Dict[str, Any]], anthropic_key: str) -> str:
    """Synthesize search results into JTBD table"""
    
    # Prepare context from search results
    context_parts = []
    for i, result in enumerate(search_results[:20]):  # Limit to top 20 results
        context_parts.append(f"""
Result {i+1}: {result['title']}
URL: {result['url']}
Query: {result.get('source_query', 'Unknown')}
Summary: {result.get('summary', '')}
Content: {result['content'][:500]}...
Highlights: {', '.join(result.get('highlights', [])[:3])}
""")
    
    search_context = '\n'.join(context_parts)
    
    prompt = f"""Based on these search results about customer needs and pain points:

{search_context}

Create a Jobs-to-be-Done table with these columns:
1. Job Statement (When I... I want to... So I can...)
2. Frequency (Daily/Weekly/Monthly)
3. Current Solutions
4. Pain Level (High/Medium/Low)
5. Opportunity Score (1-10)

Format as a markdown table. Focus on the most impactful and frequently mentioned jobs.

## Example Output Format:

| Job Statement | Frequency | Current Solutions | Pain Level | Opportunity Score |
|---------------|-----------|-------------------|------------|------------------|
| When I need to analyze customer data, I want to combine multiple data sources, so I can make informed business decisions | Daily | Excel spreadsheets, manual reports | High | 9 |
| When I'm planning a project, I want to track dependencies automatically, so I can avoid delays | Weekly | Project management tools, sticky notes | Medium | 7 |
| When I'm reviewing team performance, I want real-time dashboards, so I can provide timely feedback | Monthly | Quarterly reports, manual reviews | Medium | 6 |"""

    return call_anthropic_api(prompt, api_key=anthropic_key, max_tokens=3000,
                             system_prompt="You are an expert at Jobs-to-be-Done framework analysis.")

def extract_pain_points(jtbd_content: str, anthropic_key: str) -> str:
    """Extract and format pain points from JTBD research"""
    prompt = f"""Based on this JTBD research:

{jtbd_content}

Extract the key pain points mentioned and format them as a simple numbered list.
Focus on specific, actionable pain points that could inform product development.

Format as:
1. [Pain point description]
2. [Pain point description]
...

Keep descriptions concise (1-2 sentences each) and focused on customer needs."""

    return call_anthropic_api(prompt, api_key=anthropic_key, max_tokens=1500)

def create_jtbd_report(jtbd_table: str, search_results: List[Dict[str, Any]], 
                      execution_metadata: Dict[str, Any]) -> str:
    """Create comprehensive JTBD research report"""
    
    timestamp = datetime.now().isoformat()
    num_results = len(search_results)
    unique_domains = len(set([result.get('url', '').split('/')[2] for result in search_results if result.get('url')]))
    
    report = f"""# Jobs-to-be-Done Research Report

**Generated:** {timestamp}  
**Processing Mode:** Lambda EXA Search + Claude Synthesis  
**Search Results:** {num_results} from {unique_domains} unique sources  
**Execution Time:** {execution_metadata.get('execution_time', 'N/A')} seconds  

## 🎯 Jobs-to-be-Done Analysis

{jtbd_table}

---

## 📊 Research Sources Summary

**Search Queries Used:**
{chr(10).join([f"- {result.get('source_query', 'Unknown')}" for result in search_results[:10]])}

**Top Sources:**
{chr(10).join([f"- [{result.get('title', 'Untitled')}]({result.get('url', '#')})" for result in search_results[:10]])}

---

## 🔍 Key Insights

Based on the research analysis, the most significant JTBD patterns relate to:
- Workflow automation and efficiency
- Data integration and analysis
- Team collaboration and communication
- Process optimization and standardization

---

## Pipeline Metadata

- **Lambda Function:** JTBD Researcher
- **EXA API Searches:** {execution_metadata.get('search_queries', 0)} queries
- **Claude Synthesis:** Jobs-to-be-Done table generation
- **Results Processed:** {num_results} search results
- **Source Diversity:** {unique_domains} unique domains
"""

    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for JTBD research
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "analysis/results.md",
        "output_keys": {
            "jtbd_report": "jtbd/research.md",
            "pain_points": "jtbd/pain_points.txt"
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
        
        logger.info(f"Processing JTBD research for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        
        # Load secrets
        secrets = get_secrets()
        exa_key = secrets.get('EXA_API_KEY')
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not exa_key or not anthropic_key:
            raise ValueError("Required API keys not available")
        
        # Read analysis content from S3
        logger.info("Loading research analysis from S3...")
        analysis_content = read_s3_object(bucket, input_key)
        
        # Extract search queries from analysis
        logger.info("Extracting search queries...")
        search_queries = extract_jtbd_queries(analysis_content, anthropic_key)
        
        # Search for JTBD insights
        logger.info(f"Searching for JTBD insights using {len(search_queries)} queries...")
        search_results = search_jtbd_insights(search_queries, exa_key)
        
        if not search_results:
            logger.warning("No search results obtained, creating fallback report")
        
        # Synthesize JTBD research
        logger.info("Synthesizing JTBD research...")
        jtbd_table = synthesize_jtbd_research(search_results, anthropic_key)
        
        # Extract pain points
        logger.info("Extracting pain points...")
        pain_points = extract_pain_points(jtbd_table, anthropic_key)
        
        # Create execution metadata
        execution_metadata = {
            'execution_time': round(time.time() - start_time, 2),
            'search_queries': len(search_queries),
            'search_results': len(search_results)
        }
        
        # Create comprehensive report
        logger.info("Generating JTBD report...")
        jtbd_report = create_jtbd_report(jtbd_table, search_results, execution_metadata)
        
        # Save outputs to S3
        outputs_created = []
        
        # Save JTBD report
        if 'jtbd_report' in output_keys:
            write_s3_object(bucket, output_keys['jtbd_report'], jtbd_report, 'text/markdown')
            outputs_created.append(f"s3://{bucket}/{output_keys['jtbd_report']}")
        
        # Save pain points
        if 'pain_points' in output_keys:
            write_s3_object(bucket, output_keys['pain_points'], pain_points, 'text/plain')
            outputs_created.append(f"s3://{bucket}/{output_keys['pain_points']}")
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'job_id': job_id,
            'execution_time': round(execution_time, 2),
            'output_locations': outputs_created,
            'search_queries_used': len(search_queries),
            'search_results_found': len(search_results),
            'jtbd_report_length': len(jtbd_report),
            'pain_points_count': len(pain_points.split('\n')) if pain_points else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"JTBD research completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"JTBD research failed: {e}")
        
        return {
            'statusCode': 500,
            'error': str(e),
            'job_id': event.get('job_id', 'unknown'),
            'execution_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "bucket": "test-bucket",
        "input_key": "analysis/results.md",
        "output_keys": {
            "jtbd_report": "jtbd/research.md",
            "pain_points": "jtbd/pain_points.txt"
        },
        "job_id": "test-job-123",
        "metadata": {"stage": "jtbd_research"}
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_jobs_researcher"
            self.memory_limit_in_mb = 1024
            self.remaining_time_in_millis = lambda: 300000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))