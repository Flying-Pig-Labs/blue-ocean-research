#!/usr/bin/env python3
"""
Lambda-compatible Jobs-to-Reddit Pipeline
Refactored from jobs_to_reddit.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- Memory-efficient JTBD extraction
- PRAW Reddit API integration
- Cold start optimization
- Proper rate limiting
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time
import csv
import io

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
        secrets['ANTHROPIC_API_KEY'] = secret_data.get('ANTHROPIC_API_KEY')
        secrets['REDDIT_CLIENT_ID'] = secret_data.get('REDDIT_CLIENT_ID', 'GGd87bgymw6r_8dZuJihLw')
        secrets['REDDIT_CLIENT_SECRET'] = secret_data.get('REDDIT_CLIENT_SECRET', 'YSCmPQ5BXkV4_otAW_jXiFbrnCC5gA')
        secrets['REDDIT_USER_AGENT'] = secret_data.get('REDDIT_USER_AGENT', 'JTBD_Finder/1.0 by oceanstudio')
        
        logger.info("Successfully loaded secrets from Secrets Manager")
        return secrets
        
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        # Fallback to environment variables and defaults
        return {
            'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
            'REDDIT_CLIENT_ID': os.environ.get('REDDIT_CLIENT_ID', 'GGd87bgymw6r_8dZuJihLw'),
            'REDDIT_CLIENT_SECRET': os.environ.get('REDDIT_CLIENT_SECRET', 'YSCmPQ5BXkV4_otAW_jXiFbrnCC5gA'),
            'REDDIT_USER_AGENT': os.environ.get('REDDIT_USER_AGENT', 'JTBD_Finder/1.0 by oceanstudio')
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

def initialize_reddit(secrets: Dict[str, str]):
    """Initialize Reddit connection"""
    try:
        import praw
        
        reddit = praw.Reddit(
            client_id=secrets['REDDIT_CLIENT_ID'],
            client_secret=secrets['REDDIT_CLIENT_SECRET'],
            user_agent=secrets['REDDIT_USER_AGENT']
        )
        
        # Test connection (this will raise exception if invalid credentials)
        _ = reddit.user.me()
        logger.info("Successfully connected to Reddit API")
        return reddit
        
    except Exception as e:
        logger.warning(f"Reddit connection failed: {e}")
        return None

def extract_jtbds_from_analysis(analysis_content: str, anthropic_key: str, max_jtbds: int = 25) -> List[str]:
    """Extract JTBDs from analysis using Claude"""
    
    prompt = f"""Based on this comprehensive market analysis, extract {max_jtbds} specific Jobs-to-be-Done (JTBD) statements.

Each JTBD should follow one of these formats:
1. "When I [situation], I want to [motivation], so I can [expected outcome]"
2. "[Action verb] [object] without/while/before [constraint or context]"

Focus on extracting JTBDs that represent real customer needs from the pain points, personas, and verticals described.
Make them specific and actionable.

Analysis document:
{analysis_content[:4000]}  # Limit to avoid token overflow

Return ONLY a numbered list of JTBD statements, one per line. Nothing else."""
    
    try:
        response = call_anthropic_api(prompt, api_key=anthropic_key, 
                                    temperature=0.7, max_tokens=3000)
        
        # Parse the numbered list
        jtbds = []
        for line in response.split('\n'):
            cleaned = line.strip()
            if cleaned and (cleaned[0].isdigit() or cleaned.startswith('-')):
                # Remove numbering
                if '. ' in cleaned[:4]:
                    jtbd = cleaned.split('. ', 1)[1]
                elif cleaned.startswith('- '):
                    jtbd = cleaned[2:]
                else:
                    jtbd = cleaned
                
                jtbd = jtbd.strip('"').strip("'").strip()
                if len(jtbd) > 10:
                    jtbds.append(jtbd)
        
        logger.info(f"Extracted {len(jtbds)} JTBDs from analysis")
        return jtbds[:max_jtbds]  # Limit to requested number
        
    except Exception as e:
        logger.error(f"Failed to extract JTBDs: {e}")
        return []

def translate_jtbd_to_reddit_queries(jtbd: str, anthropic_key: str) -> List[str]:
    """Translate JTBD to authentic Reddit search queries"""
    
    prompt = f"""Transform this Jobs-to-be-Done into Reddit search queries for real estate discussions.

JTBD: {jtbd}

Generate 6 SHORT search queries (2-5 words) that real Reddit users would type.
Focus on:
- Emotional language ("frustrated", "stressed", "help")
- Specific scenarios ("closing delayed", "two mortgages")
- Common abbreviations and casual language
- Real estate terminology

Examples of good queries:
- "closing delayed help"
- "bridge loan worth it"
- "sell before buying"
- "two mortgages stressed"

Return ONLY 6 queries, one per line. Keep them SHORT and authentic."""
    
    try:
        response = call_anthropic_api(prompt, api_key=anthropic_key,
                                    temperature=0.8, max_tokens=300)
        
        queries = []
        for line in response.split('\n'):
            cleaned = line.strip()
            if cleaned:
                # Remove numbering and bullets
                if cleaned[0].isdigit() and '.' in cleaned[:3]:
                    cleaned = cleaned.split('.', 1)[1].strip()
                cleaned = cleaned.lstrip('- •').strip().strip('"').strip("'")
                if cleaned and len(cleaned) > 2:
                    queries.append(cleaned)
        
        return queries[:6]  # Limit to 6 queries
        
    except Exception as e:
        logger.warning(f"Query translation failed for JTBD: {e}")
        # Simple fallback
        words = jtbd.lower().split()[:5]
        return [' '.join(words[i:i+3]) for i in range(0, len(words)-2, 2)][:3]

def search_reddit_for_jtbd(jtbd: str, queries: List[str], reddit) -> List[Dict[str, Any]]:
    """Search Reddit for discussions matching JTBD"""
    
    if not reddit:
        return []
    
    # Target subreddits for real estate
    target_subreddits = [
        'RealEstate',
        'FirstTimeHomeBuyer',
        'realestateinvesting',
        'Mortgages',
        'personalfinance'
    ]
    
    results = []
    
    # Search each subreddit with top queries
    for subreddit_name in target_subreddits[:3]:  # Top 3 subreddits for Lambda efficiency
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            for query in queries[:2]:  # Top 2 queries per subreddit
                try:
                    for submission in subreddit.search(
                        query,
                        limit=2,  # 2 results per query to stay within limits
                        sort='relevance',
                        time_filter='year'
                    ):
                        results.append({
                            'jtbd': jtbd,
                            'query': query,
                            'subreddit': subreddit_name,
                            'title': submission.title,
                            'url': f"https://reddit.com{submission.permalink}",
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'selftext': submission.selftext[:500] if submission.selftext else "",
                            'author': str(submission.author) if submission.author else "[deleted]"
                        })
                    
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception:
                    continue
                    
        except Exception:
            continue
    
    return results

def process_jtbds_with_reddit(jtbds: List[str], secrets: Dict[str, str]) -> List[Dict[str, Any]]:
    """Process JTBDs and find Reddit discussions"""
    
    anthropic_key = secrets['ANTHROPIC_API_KEY']
    reddit = initialize_reddit(secrets)
    
    all_results = []
    processed_count = 0
    
    # Limit JTBDs to prevent timeout (Lambda has 15 min limit)
    limited_jtbds = jtbds[:15]  # Process max 15 JTBDs in Lambda
    
    for i, jtbd in enumerate(limited_jtbds):
        logger.info(f"Processing JTBD {i+1}/{len(limited_jtbds)}: {jtbd[:50]}...")
        
        try:
            # Translate to Reddit queries
            queries = translate_jtbd_to_reddit_queries(jtbd, anthropic_key)
            
            # Search Reddit if available
            if reddit:
                results = search_reddit_for_jtbd(jtbd, queries, reddit)
                all_results.extend(results)
            
            processed_count += 1
            
            # Progress logging
            if i % 5 == 0:
                logger.info(f"Processed {i}/{len(limited_jtbds)} JTBDs, found {len(all_results)} threads")
        
        except Exception as e:
            logger.warning(f"Failed to process JTBD {i+1}: {e}")
            continue
    
    logger.info(f"Completed processing {processed_count} JTBDs, found {len(all_results)} Reddit discussions")
    return all_results

def create_jtbd_file_content(jtbds: List[str]) -> str:
    """Create JTBD file content"""
    content = "# Jobs-to-be-Done extracted from analysis\n\n"
    for i, jtbd in enumerate(jtbds, 1):
        content += f"{i}. {jtbd}\n"
    return content

def create_reddit_csv_content(reddit_results: List[Dict[str, Any]]) -> str:
    """Create Reddit discussions CSV content"""
    if not reddit_results:
        return "jtbd,query,subreddit,title,url,score,num_comments,created_utc,selftext,author\n"
    
    output = io.StringIO()
    fieldnames = ['jtbd', 'query', 'subreddit', 'title', 'url', 'score', 
                  'num_comments', 'created_utc', 'selftext', 'author']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for result in reddit_results:
        writer.writerow(result)
    
    return output.getvalue()

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for Jobs-to-Reddit pipeline
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "analysis/results.md",
        "output_keys": {
            "jtbds": "jtbd/extracted.txt",
            "reddit_discussions": "reddit/discussions.csv"
        },
        "job_id": "job-123",
        "max_jtbds": 20,
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
        max_jtbds = event.get('max_jtbds', 20)
        metadata = event.get('metadata', {})
        
        if not bucket or not input_key:
            raise ValueError("Missing required parameters: bucket and input_key")
        
        logger.info(f"Processing Jobs-to-Reddit pipeline for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        logger.info(f"Max JTBDs: {max_jtbds}")
        
        # Load secrets
        secrets = get_secrets()
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not available")
        
        # Read analysis content from S3
        logger.info("Loading analysis content from S3...")
        analysis_content = read_s3_object(bucket, input_key)
        
        # Extract JTBDs from analysis
        logger.info("Extracting JTBDs from analysis...")
        jtbds = extract_jtbds_from_analysis(analysis_content, anthropic_key, max_jtbds)
        
        if not jtbds:
            raise ValueError("No JTBDs extracted from analysis")
        
        # Process JTBDs and search Reddit
        logger.info(f"Processing {len(jtbds)} JTBDs with Reddit search...")
        reddit_results = process_jtbds_with_reddit(jtbds, secrets)
        
        # Create output content
        jtbd_content = create_jtbd_file_content(jtbds)
        reddit_csv_content = create_reddit_csv_content(reddit_results)
        
        # Save outputs to S3
        outputs_created = []
        
        # Save JTBDs file
        if 'jtbds' in output_keys:
            write_s3_object(bucket, output_keys['jtbds'], jtbd_content, 'text/plain')
            outputs_created.append(f"s3://{bucket}/{output_keys['jtbds']}")
        
        # Save Reddit discussions
        if 'reddit_discussions' in output_keys:
            write_s3_object(bucket, output_keys['reddit_discussions'], reddit_csv_content, 'text/csv')
            outputs_created.append(f"s3://{bucket}/{output_keys['reddit_discussions']}")
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'job_id': job_id,
            'execution_time': round(execution_time, 2),
            'output_locations': outputs_created,
            'jtbds_extracted': len(jtbds),
            'reddit_discussions_found': len(reddit_results),
            'reddit_api_available': bool(reddit_results),
            'unique_subreddits': len(set([r.get('subreddit') for r in reddit_results])) if reddit_results else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Jobs-to-Reddit pipeline completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Jobs-to-Reddit pipeline failed: {e}")
        
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
            "jtbds": "jtbd/extracted.txt",
            "reddit_discussions": "reddit/discussions.csv"
        },
        "job_id": "test-job-123",
        "max_jtbds": 10,
        "metadata": {"stage": "jobs_to_reddit"}
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_jobs_to_reddit"
            self.memory_limit_in_mb = 1024
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))