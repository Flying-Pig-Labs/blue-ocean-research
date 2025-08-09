#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Lambda-compatible Research Analyzer
Refactored from research_analyzer.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- Proper error handling and retries
- Memory-optimized data structures
- Cold start optimization
- Environment variable configuration
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    
    # Get secret ARNs from environment variables
    anthropic_arn = os.environ.get('ANTHROPIC_SECRET_ARN')
    openai_arn = os.environ.get('OPENAI_SECRET_ARN')
    exa_arn = os.environ.get('EXA_SECRET_ARN')
    cohere_arn = os.environ.get('COHERE_SECRET_ARN')
    github_arn = os.environ.get('GITHUB_SECRET_ARN')
    
    # Load Anthropic API key (JSON format with lowercase key)
    if anthropic_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=anthropic_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['ANTHROPIC_API_KEY'] = secret_data.get('anthropic_key', '')
            except json.JSONDecodeError:
                secrets['ANTHROPIC_API_KEY'] = secret_value
            logger.info("Loaded Anthropic key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Anthropic secret: {e}")
    
    # Load OpenAI API key (JSON format with lowercase key)
    if openai_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=openai_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['OPENAI_API_KEY'] = secret_data.get('openai_key', '')
            except json.JSONDecodeError:
                secrets['OPENAI_API_KEY'] = secret_value
            logger.info("Loaded OpenAI key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load OpenAI secret: {e}")
    
    # Load EXA API key (plain string format)
    if exa_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=exa_arn)
            secret_value = response.get('SecretString', '')
            # EXA key is stored as plain string
            secrets['EXA_API_KEY'] = secret_value
            logger.info("Loaded EXA key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load EXA secret: {e}")
    
    # Load Cohere API key (plain string format)
    if cohere_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=cohere_arn)
            secret_value = response.get('SecretString', '')
            # Cohere key is stored as plain string
            secrets['COHERE_API_KEY'] = secret_value
            logger.info("Loaded Cohere key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Cohere secret: {e}")
    
    # Load GitHub token (JSON format with lowercase key)
    if github_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=github_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['GITHUB_TOKEN'] = secret_data.get('github_token', '')
            except json.JSONDecodeError:
                secrets['GITHUB_TOKEN'] = secret_value
            logger.info("Loaded GitHub token from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load GitHub secret: {e}")
    
    # Fallback to environment variables
    if not secrets.get('ANTHROPIC_API_KEY'):
        secrets['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
    if not secrets.get('OPENAI_API_KEY'):
        secrets['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
    if not secrets.get('EXA_API_KEY'):
        secrets['EXA_API_KEY'] = os.environ.get('EXA_API_KEY', '')
    if not secrets.get('COHERE_API_KEY'):
        secrets['COHERE_API_KEY'] = os.environ.get('COHERE_API_KEY', '')
    if not secrets.get('GITHUB_TOKEN'):
        secrets['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN', '')
    
    return secrets
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

def analyze_verticals(research_content: str, api_key: str) -> str:
    """Analyze industry verticals from research content"""
    prompt = f"""Research Document:

{research_content}

Within this research document, what distinct industry verticals can you identify?

Please analyze and identify:
1. Primary industry verticals and market segments
2. Sub-verticals or niche markets
3. Key characteristics that differentiate each vertical
4. Market dynamics and growth factors for each

Focus on being comprehensive but distinct - avoid overlapping categorizations.

## Example Output Format:

### Primary Industry Verticals:

**1. Healthcare Technology**
- Electronic Health Records (EHR) systems
- Telemedicine platforms
- Medical device integration
- Key characteristics: Regulatory compliance requirements, patient privacy concerns
- Growth factors: Aging population, digital transformation post-COVID

**2. Financial Services**
- Digital banking platforms
- Payment processing systems
- Investment management tools
- Key characteristics: High security requirements, regulatory oversight
- Growth factors: Fintech disruption, mobile-first customer expectations"""

    return call_anthropic_api(prompt, api_key=api_key, max_tokens=2000)

def analyze_personas(research_content: str, api_key: str) -> str:
    """Analyze user personas from research content"""
    prompt = f"""Research Document:

{research_content}

Looking at this research document, what user personas or customer segments can you identify?

For each persona, include:
1. Demographics and characteristics
2. Primary needs and motivations
3. Current behaviors and preferences
4. Key goals they're trying to achieve
5. Pain points and frustrations

Be specific about what makes each persona unique and actionable for product development.

## Example Output Format:

### Persona 1: The Tech-Savvy Manager
**Demographics:** 30-45 years old, mid-level management, technical background
**Primary needs:** Efficient team coordination, data-driven decision making
**Current behaviors:** Uses multiple productivity apps, attends webinars, active on LinkedIn
**Key goals:** Improve team productivity by 25%, streamline reporting processes
**Pain points:** Tool fragmentation, manual data entry, lack of integration between systems

### Persona 2: The Budget-Conscious Small Business Owner
**Demographics:** 35-55 years old, running 5-50 employee companies, non-technical
**Primary needs:** Cost-effective solutions, simple implementation, reliable support
**Current behaviors:** Researches extensively before purchasing, relies on word-of-mouth
**Key goals:** Reduce operational costs, improve customer satisfaction
**Pain points:** Complex software, expensive solutions, poor customer support"""

    return call_anthropic_api(prompt, api_key=api_key, max_tokens=2000)

def analyze_pain_points(research_content: str, api_key: str) -> str:
    """Analyze pain points from research content"""
    prompt = f"""Research Document:

{research_content}

Within this research document, what are the key pain points that you observe or can infer based on the research presented?

Please categorize these pain points by:
1. Severity (High/Medium/Low impact on users)
2. Frequency (How often users encounter this issue)
3. Current solutions (What users do today to address this)
4. Unmet needs (What's still not solved)

Include both explicit pain points mentioned directly and implicit pain points you can deduce from the research."""

    return call_anthropic_api(prompt, model="claude-3-5-haiku-20241022", 
                            temperature=0.8, max_tokens=3000, api_key=api_key)

def analyze_solution_types(research_content: str, api_key: str) -> str:
    """Analyze potential solution types from research content"""
    prompt = f"""Research Document:

{research_content}

Based on this research document, what potential solution types or approaches could address the identified needs?

Consider:
1. Technology-based solutions (platforms, apps, tools)
2. Service-based solutions (consulting, managed services)
3. Process improvements (workflows, methodologies)
4. Hybrid approaches (combining multiple solution types)

For each solution type, briefly explain:
- What problem it addresses
- How it would work
- Why it's viable based on the research

## Example Output Format:

### Technology-Based Solutions:

**Unified Data Integration Platform**
- Problem addressed: Data silos and manual integration processes
- How it works: API-first platform that automatically syncs data between systems
- Viability: High demand shown for automated solutions in research

### Service-Based Solutions:

**Implementation Consulting Service**
- Problem addressed: Complex setup and configuration challenges
- How it works: Expert consultants guide deployment and customization
- Viability: Research shows 70% of users struggle with initial setup

### Hybrid Approaches:

**Platform + Training Program**
- Problem addressed: Technology adoption and user competency gaps
- How it works: Software platform bundled with comprehensive training
- Viability: Combines tech efficiency with human learning preferences"""

    return call_anthropic_api(prompt, model="claude-3-5-haiku-20241022",
                            temperature=0.8, max_tokens=3000, api_key=api_key)

def process_research_parallel(research_content: str, api_key: str) -> Dict[str, str]:
    """Process research analysis with parallel LLM calls for better performance"""
    analysis_tasks = {
        'verticals': lambda: analyze_verticals(research_content, api_key),
        'personas': lambda: analyze_personas(research_content, api_key),
        'pain_points': lambda: analyze_pain_points(research_content, api_key),
        'solution_types': lambda: analyze_solution_types(research_content, api_key)
    }
    
    results = {}
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_task = {
            executor.submit(task_func): task_name 
            for task_name, task_func in analysis_tasks.items()
        }
        
        for future in as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result(timeout=60)  # 60 second timeout per call
                results[task_name] = result
                logger.info(f"Completed analysis for: {task_name}")
            except Exception as e:
                logger.error(f"Failed to analyze {task_name}: {e}")
                results[task_name] = f"Error analyzing {task_name}: {str(e)}"
    
    return results

def create_analysis_report(results: Dict[str, str], research_metadata: Dict[str, Any]) -> str:
    """Create formatted analysis report"""
    timestamp = datetime.now().isoformat()
    
    report = f"""# Research Analysis Report

**Generated:** {timestamp}  
**Source:** {research_metadata.get('source', 'Unknown')}  
**Processing Mode:** Lambda Parallel Analysis  

## 🏢 Industry Verticals

{results.get('verticals', 'Analysis unavailable')}

---

## 👥 User Personas

{results.get('personas', 'Analysis unavailable')}

---

## 😣 Pain Points

{results.get('pain_points', 'Analysis unavailable')}

---

## 💡 Solution Types

{results.get('solution_types', 'Analysis unavailable')}

---

## Pipeline Metadata

- **Lambda Function:** Research Analyzer
- **Execution Time:** {timestamp}
- **Parallel Processing:** 4 concurrent LLM calls
- **Model Used:** Claude-3.5-Sonnet (main), Claude-3.5-Haiku (pain points & solutions)
"""

    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for research analysis
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "research/input.json",
        "output_key": "analysis/results.md",
        "job_id": "job-123",
        "metadata": {...}
    }
    """
    start_time = time.time()
    
    try:
        # Initialize AWS clients
        initialize_clients()
        
        # Extract event parameters - handle both Step Functions and direct invocation formats
        bucket = event.get('s3Bucket') or event.get('bucket')
        input_key = event.get('s3InputKey') or event.get('input_key')
        output_key = event.get('s3OutputKey') or event.get('output_key', 'analysis/research_summary.json')
        job_id = event.get('jobId') or event.get('job_id', 'unknown')
        metadata = event.get('metadata', {})
        
        if not bucket or not input_key:
            logger.error(f"Missing parameters. Event: {json.dumps(event)}")
            raise ValueError(f"Missing required parameters: bucket={bucket}, input_key={input_key}")
        
        logger.info(f"Processing research analysis for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        logger.info(f"Output: s3://{bucket}/{output_key}")
        
        # Load secrets
        secrets = get_secrets()
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not available")
        
        # Read research content from S3
        logger.info("Loading research content from S3...")
        research_content = read_s3_object(bucket, input_key)
        
        # Parse JSON if needed
        try:
            research_data = json.loads(research_content)
            if isinstance(research_data, dict):
                # Extract text content from JSON structure
                content_text = research_data.get('content', str(research_data))
                research_metadata = {
                    'source': research_data.get('source', 'JSON Input'),
                    'title': research_data.get('title', 'Research Document'),
                    **metadata
                }
            else:
                content_text = str(research_data)
                research_metadata = metadata
        except json.JSONDecodeError:
            # Content is plain text
            content_text = research_content
            research_metadata = metadata
        
        logger.info(f"Research content loaded: {len(content_text)} characters")
        
        # Parallel processing of research analysis
        logger.info("Starting parallel LLM analysis...")
        analysis_results = process_research_parallel(content_text, anthropic_key)
        
        # Create formatted report
        logger.info("Generating analysis report...")
        report = create_analysis_report(analysis_results, research_metadata)
        
        # Save to S3
        logger.info("Saving analysis report to S3...")
        write_s3_object(bucket, output_key, report, 'text/markdown')
        
        execution_time = time.time() - start_time
        
        # Return success response with Step Functions compatible format
        response = {
            'statusCode': 200,
            'jobId': job_id,
            's3Bucket': bucket,
            's3OutputKey': output_key,
            'execution_time': round(execution_time, 2),
            'output_location': f"s3://{bucket}/{output_key}",
            'analysis_sections': list(analysis_results.keys()),
            'content_length': len(content_text),
            'report_length': len(report),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Research analysis completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Research analysis failed: {e}")
        
        return {
            'statusCode': 500,
            'error': str(e),
            'jobId': event.get('jobId') or event.get('job_id', 'unknown'),
            'execution_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "bucket": "test-bucket",
        "input_key": "research/sample.json",
        "output_key": "analysis/results.md",
        "job_id": "test-job-123",
        "metadata": {"source": "Test Research Document"}
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_research_analyzer"
            self.memory_limit_in_mb = 3008
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))