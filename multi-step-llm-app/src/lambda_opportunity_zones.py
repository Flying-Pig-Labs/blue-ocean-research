#!/usr/bin/env python3
"""
Lambda-compatible Advanced Opportunity Zone Analyzer
Refactored from opportunity_zone_analyzer.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- Memory-efficient pain dimension analysis
- Anthropic API integration for dimension scoring
- Optimized clustering for Lambda constraints
- Batch processing for large datasets
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import time
import numpy as np
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handler for connection reuse)
s3_client = None
secrets_client = None

# Pain dimensions for analyzing discussions
PAIN_DIMENSIONS = {
    "timing_coordination": ["schedule", "deadline", "timing", "delay", "simultaneous", "coordinate", "sync", "waiting"],
    "financial_stress": ["cost", "mortgage", "fee", "expensive", "afford", "price", "budget", "payment", "loan"],
    "communication_gaps": ["update", "response", "ghosted", "contact", "informed", "call", "email", "reach", "silence"],
    "process_complexity": ["confusing", "complicated", "understand", "steps", "documentation", "paperwork", "process", "unclear"],
    "trust_issues": ["lied", "scam", "manipulative", "dishonest", "sketchy", "worry", "shady", "trick", "mislead"],
    "technology_gaps": ["manual", "paper", "automate", "system", "track", "software", "app", "digital", "online"],
    "decision_anxiety": ["worried", "stressed", "nervous", "uncertain", "regret", "anxious", "panic", "overwhelm", "fear"],
    "market_dynamics": ["competitive", "outbid", "inventory", "fast", "missed", "bidding", "offer", "multiple", "rush"]
}

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

def parse_jtbds_file(jtbd_content: str) -> List[str]:
    """Parse JTBDs from text file content"""
    jtbds = []
    
    for line in jtbd_content.split('\n'):
        cleaned = line.strip()
        if cleaned and not cleaned.startswith('#'):
            # Remove numbering
            if cleaned[0].isdigit() and '. ' in cleaned[:4]:
                jtbd = cleaned.split('. ', 1)[1]
            elif cleaned.startswith('- '):
                jtbd = cleaned[2:]
            else:
                jtbd = cleaned
            
            jtbd = jtbd.strip()
            if len(jtbd) > 10:
                jtbds.append(jtbd)
    
    logger.info(f"Parsed {len(jtbds)} JTBDs from content")
    return jtbds

def parse_reddit_data(reddit_data: str) -> List[Dict[str, Any]]:
    """Parse Reddit discussions from CSV content"""
    import csv
    import io
    
    discussions = []
    csv_reader = csv.DictReader(io.StringIO(reddit_data))
    
    for row in csv_reader:
        discussions.append({
            'jtbd': row.get('jtbd', ''),
            'title': row.get('title', ''),
            'subreddit': row.get('subreddit', ''),
            'score': int(row.get('score', 0)) if row.get('score', '').isdigit() else 0,
            'num_comments': int(row.get('num_comments', 0)) if row.get('num_comments', '').isdigit() else 0,
            'selftext': row.get('selftext', ''),
            'url': row.get('url', '')
        })
    
    logger.info(f"Parsed {len(discussions)} Reddit discussions")
    return discussions

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

def extract_pain_dimensions(text: str, api_key: str) -> Dict[str, float]:
    """Extract pain dimension scores from discussion text using Claude"""
    
    prompt = f"""Analyze this discussion and score it on each pain dimension.

Discussion:
{text[:2000]}  # Limit to prevent token overflow

Score each dimension from 0.0 to 1.0 based on how strongly it's expressed:

Pain Dimensions:
- timing_coordination: Issues with scheduling, deadlines, synchronization
- financial_stress: Money concerns, costs, affordability issues  
- communication_gaps: Problems with updates, responses, being informed
- process_complexity: Confusion about steps, documentation, procedures
- trust_issues: Concerns about honesty, scams, manipulation
- technology_gaps: Frustration with manual processes, lack of automation
- decision_anxiety: Worry, stress, uncertainty about choices
- market_dynamics: Competition, bidding wars, inventory issues

Return ONLY a JSON object with dimension names as keys and scores as values.
Example: {{"timing_coordination": 0.7, "financial_stress": 0.3, "communication_gaps": 0.5, "process_complexity": 0.8, "trust_issues": 0.2, "technology_gaps": 0.6, "decision_anxiety": 0.9, "market_dynamics": 0.4}}"""

    try:
        response = call_anthropic_api(prompt, temperature=0, max_tokens=500, api_key=api_key)
        
        # Clean up response
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
            
        scores = json.loads(response)
        
        # Ensure all dimensions are present
        for dim in PAIN_DIMENSIONS:
            if dim not in scores:
                scores[dim] = 0.0
                
        return scores
        
    except Exception as e:
        logger.warning(f"Error extracting pain dimensions: {e}")
        return {dim: 0.0 for dim in PAIN_DIMENSIONS}

def calculate_jtbd_vectors(jtbds: List[str], reddit_discussions: List[Dict[str, Any]], 
                         api_key: str, max_discussions_per_jtbd: int = 3) -> Dict[int, Dict[str, float]]:
    """Calculate pain dimension vectors for each JTBD"""
    
    jtbd_vectors = {}
    
    for idx, jtbd in enumerate(jtbds):
        logger.info(f"Processing JTBD {idx+1}/{len(jtbds)}")
        
        # Find discussions for this JTBD
        jtbd_discussions = [d for d in reddit_discussions if d['jtbd'] == jtbd]
        
        if not jtbd_discussions:
            logger.warning(f"No discussions found for JTBD {idx+1}")
            jtbd_vectors[idx] = {dim: 0.0 for dim in PAIN_DIMENSIONS}
            continue
        
        # Sample discussions if too many
        if len(jtbd_discussions) > max_discussions_per_jtbd:
            # Sort by score and take top discussions
            jtbd_discussions.sort(key=lambda x: x['score'], reverse=True)
            jtbd_discussions = jtbd_discussions[:max_discussions_per_jtbd]
        
        # Collect pain scores
        dimension_scores = defaultdict(list)
        
        for discussion in jtbd_discussions:
            # Prepare text for analysis
            text = f"""
Title: {discussion['title']}
Subreddit: r/{discussion['subreddit']}
Score: {discussion['score']} upvotes, {discussion['num_comments']} comments
Content: {discussion['selftext'][:1000] if discussion['selftext'] else 'No content'}
"""
            
            # Extract pain dimensions
            scores = extract_pain_dimensions(text, api_key)
            
            for dim, score in scores.items():
                dimension_scores[dim].append(score)
            
            # Rate limit
            time.sleep(0.5)
        
        # Calculate weighted averages
        jtbd_vector = {}
        for dim in PAIN_DIMENSIONS:
            if dim in dimension_scores and dimension_scores[dim]:
                # Weight by discussion engagement
                weights = [d['score'] for d in jtbd_discussions[:len(dimension_scores[dim])]]
                weight_sum = sum(weights) if sum(weights) > 0 else len(weights)
                weights = [w / weight_sum for w in weights]
                
                jtbd_vector[dim] = sum(score * weight for score, weight in 
                                     zip(dimension_scores[dim], weights))
            else:
                jtbd_vector[dim] = 0.0
                
        jtbd_vectors[idx] = jtbd_vector
    
    return jtbd_vectors

def cluster_jtbds_by_dimensions(jtbd_vectors: Dict[int, Dict[str, float]], 
                              n_clusters: int = 5) -> Dict[int, int]:
    """Cluster JTBDs based on pain dimension similarity"""
    
    if len(jtbd_vectors) < n_clusters:
        n_clusters = len(jtbd_vectors)
        logger.warning(f"Reducing clusters to {n_clusters} due to limited data")
    
    # Convert to numpy array
    vector_array = []
    jtbd_indices = []
    
    for idx, vector in jtbd_vectors.items():
        vector_array.append([vector[dim] for dim in PAIN_DIMENSIONS])
        jtbd_indices.append(idx)
    
    vector_array = np.array(vector_array)
    
    try:
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.preprocessing import StandardScaler
        
        # Standardize features
        scaler = StandardScaler()
        scaled_vectors = scaler.fit_transform(vector_array)
        
        # Perform clustering
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        cluster_labels = clustering.fit_predict(scaled_vectors)
        
    except Exception as e:
        logger.warning(f"Scikit-learn clustering failed: {e}, using simple fallback")
        # Fallback to simple clustering
        cluster_labels = [i % n_clusters for i in range(len(jtbd_indices))]
    
    # Map to dictionary
    jtbd_clusters = {}
    for idx, label in zip(jtbd_indices, cluster_labels):
        jtbd_clusters[idx] = int(label)
    
    return jtbd_clusters

def extract_solution_requirements(jtbds: List[str], cluster_jtbd_indices: List[int], 
                                reddit_discussions: List[Dict[str, Any]], 
                                api_key: str) -> List[str]:
    """Extract solution requirements for a cluster"""
    
    # Get JTBDs in cluster
    cluster_jtbd_texts = [jtbds[idx] for idx in cluster_jtbd_indices]
    
    # Sample discussions
    sample_discussions = []
    for jtbd_text in cluster_jtbd_texts[:3]:
        jtbd_reddit = [d for d in reddit_discussions if d['jtbd'] == jtbd_text][:2]
        for discussion in jtbd_reddit:
            sample_discussions.append(f"- {discussion['title']}: {discussion['selftext'][:200] if discussion['selftext'] else 'N/A'}")
    
    prompt = f"""Based on these Jobs-to-be-Done and discussions, extract specific solution requirements.

JTBDs in this opportunity zone:
{chr(10).join(f'- {jtbd}' for jtbd in cluster_jtbd_texts)}

Sample discussions:
{chr(10).join(sample_discussions[:5])}

List 3-5 specific, actionable solution requirements that would address these needs.
Focus on technical capabilities, not vague benefits.
Return ONLY a JSON array of requirement strings.

Example: ["Real-time transaction status dashboard", "Automated document verification system", "Multi-party communication hub"]"""

    try:
        response = call_anthropic_api(prompt, temperature=0.3, max_tokens=500, api_key=api_key)
        
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
            
        requirements = json.loads(response)
        return requirements[:5]
        
    except Exception as e:
        logger.warning(f"Error extracting requirements: {e}")
        return ["Unable to extract specific requirements"]

def generate_zone_name(dominant_dimensions: Dict[str, float]) -> str:
    """Generate descriptive name for opportunity zone"""
    
    # Get top 2 dimensions
    sorted_dims = sorted(dominant_dimensions.items(), key=lambda x: x[1], reverse=True)[:2]
    
    # Map to descriptive names
    dimension_names = {
        "timing_coordination": "Transaction Coordination",
        "financial_stress": "Financial Management",
        "communication_gaps": "Communication Hub",
        "process_complexity": "Process Simplification",
        "trust_issues": "Trust & Verification",
        "technology_gaps": "Digital Transformation",
        "decision_anxiety": "Decision Support",
        "market_dynamics": "Market Intelligence"
    }
    
    primary = dimension_names.get(sorted_dims[0][0], "Solution")
    if len(sorted_dims) > 1:
        secondary = dimension_names.get(sorted_dims[1][0], "Platform")
        return f"{primary} & {secondary} Platform"
    return f"{primary} Platform"

def analyze_opportunity_zones(jtbds: List[str], reddit_discussions: List[Dict[str, Any]], 
                            api_key: str, n_zones: int = 5, 
                            max_discussions_per_jtbd: int = 3) -> Dict[str, Any]:
    """Main opportunity zone analysis"""
    
    logger.info("Starting opportunity zone analysis")
    
    # Calculate JTBD vectors
    logger.info("Calculating JTBD pain dimension vectors...")
    jtbd_vectors = calculate_jtbd_vectors(jtbds, reddit_discussions, api_key, max_discussions_per_jtbd)
    
    # Cluster JTBDs
    logger.info(f"Clustering JTBDs into {n_zones} zones...")
    jtbd_clusters = cluster_jtbds_by_dimensions(jtbd_vectors, n_zones)
    
    # Build opportunity zones
    opportunity_zones = []
    
    for zone_id in range(n_zones):
        zone_jtbd_indices = [idx for idx, cluster in jtbd_clusters.items() if cluster == zone_id]
        
        if not zone_jtbd_indices:
            continue
            
        logger.info(f"Building opportunity zone {zone_id+1} with {len(zone_jtbd_indices)} JTBDs")
        
        # Calculate aggregate pain dimensions
        zone_dimensions = defaultdict(list)
        for idx in zone_jtbd_indices:
            for dim, score in jtbd_vectors[idx].items():
                zone_dimensions[dim].append(score)
        
        # Average dimensions
        avg_dimensions = {}
        for dim, scores in zone_dimensions.items():
            avg_dimensions[dim] = np.mean(scores) if scores else 0.0
        
        # Filter significant dimensions
        significant_dims = {dim: score for dim, score in avg_dimensions.items() if score > 0.3}
        
        # Calculate evidence strength
        zone_jtbd_texts = [jtbds[idx] for idx in zone_jtbd_indices]
        zone_reddit = [d for d in reddit_discussions if d['jtbd'] in zone_jtbd_texts]
        total_engagement = sum(d['score'] + d['num_comments'] for d in zone_reddit)
        
        # Extract solution requirements
        requirements = extract_solution_requirements(jtbds, zone_jtbd_indices, reddit_discussions, api_key)
        
        # Generate zone name
        zone_name = generate_zone_name(significant_dims)
        
        # Build zone
        zone = {
            "zone_id": f"OZ_{zone_id+1:03d}",
            "name": zone_name,
            "jtbds_addressed": [f"JTBD_{idx+1:03d}" for idx in zone_jtbd_indices],
            "jtbd_descriptions": [jtbds[idx][:100] + "..." for idx in zone_jtbd_indices],
            "evidence_strength": {
                "total_threads": len(zone_reddit),
                "total_engagement": int(total_engagement),
                "avg_score_per_thread": float(np.mean([d['score'] for d in zone_reddit])) if zone_reddit else 0
            },
            "pain_dimensions": {dim: round(score, 2) for dim, score in significant_dims.items()},
            "solution_requirements": requirements,
            "market_opportunity_score": round(
                (len(zone_jtbd_indices) / len(jtbds)) * 0.3 +
                (min(total_engagement / 10000, 1.0)) * 0.4 +
                (len(significant_dims) / len(PAIN_DIMENSIONS)) * 0.3,
                2
            ),
            "importance_percentage": round((len(zone_jtbd_indices) / len(jtbds)) * 100, 1)
        }
        
        opportunity_zones.append(zone)
    
    # Sort by opportunity score
    opportunity_zones.sort(key=lambda x: x['market_opportunity_score'], reverse=True)
    
    # Build output
    output = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_jtbds": len(jtbds),
            "total_reddit_threads": len(reddit_discussions),
            "total_zones_discovered": len(opportunity_zones),
            "pain_dimensions_analyzed": list(PAIN_DIMENSIONS.keys()),
            "processing_mode": "Lambda Advanced Analysis"
        },
        "opportunity_zones": opportunity_zones,
        "zone_summary": {
            "highest_opportunity": opportunity_zones[0]['name'] if opportunity_zones else "None",
            "total_market_coverage": round(
                len(set(idx for zone in opportunity_zones 
                       for idx in [int(j.split('_')[1]) - 1 for j in zone['jtbds_addressed']])) / len(jtbds),
                2
            ),
            "strongest_pain_dimension": max(
                [(dim, np.mean([z['pain_dimensions'].get(dim, 0) for z in opportunity_zones]))
                 for dim in PAIN_DIMENSIONS.keys()],
                key=lambda x: x[1]
            )[0] if opportunity_zones else "None"
        }
    }
    
    return output

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for advanced opportunity zone analysis
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_keys": {
            "jtbds": "jtbd/extracted.txt",
            "reddit_discussions": "reddit/discussions.csv"
        },
        "output_key": "zones/advanced_analysis.json",
        "job_id": "job-123",
        "analysis_params": {
            "n_zones": 5,
            "max_discussions_per_jtbd": 3
        },
        "metadata": {...}
    }
    """
    start_time = time.time()
    
    try:
        # Initialize AWS clients
        initialize_clients()
        
        # Extract event parameters
        bucket = event.get('s3Bucket') or event.get('bucket')
        input_keys = event.get('s3InputKeys') or event.get('input_keys', {})
        output_key = event.get('s3OutputKey') or event.get('output_key', 'zones/advanced_analysis.json')
        job_id = event.get('jobId') or event.get('job_id', 'unknown')
        analysis_params = event.get('analysis_params', {})
        
        # Analysis parameters
        n_zones = analysis_params.get('n_zones', 5)
        max_discussions_per_jtbd = analysis_params.get('max_discussions_per_jtbd', 3)
        
        if not bucket or not input_keys.get('jtbds') or not input_keys.get('reddit_discussions'):
            raise ValueError("Missing required parameters: bucket and input_keys")
        
        logger.info(f"Processing advanced opportunity zone analysis for job {job_id}")
        logger.info(f"JTBD input: s3://{bucket}/{input_keys['jtbds']}")
        logger.info(f"Reddit input: s3://{bucket}/{input_keys['reddit_discussions']}")
        logger.info(f"Output: s3://{bucket}/{output_key}")
        
        # Load secrets
        secrets = get_secrets()
        anthropic_key = secrets.get('ANTHROPIC_API_KEY')
        
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not available")
        
        # Load data from S3
        logger.info("Loading JTBDs and Reddit data from S3...")
        jtbd_content = read_s3_object(bucket, input_keys['jtbds'])
        reddit_content = read_s3_object(bucket, input_keys['reddit_discussions'])
        
        # Parse data
        jtbds = parse_jtbds_file(jtbd_content)
        reddit_discussions = parse_reddit_data(reddit_content)
        
        if len(jtbds) < 3:
            raise ValueError(f"Insufficient JTBDs for analysis: {len(jtbds)}")
        
        # Perform opportunity zone analysis
        logger.info(f"Analyzing {len(jtbds)} JTBDs with {len(reddit_discussions)} Reddit discussions...")
        analysis_results = analyze_opportunity_zones(
            jtbds, reddit_discussions, anthropic_key, n_zones, max_discussions_per_jtbd
        )
        
        # Save results to S3
        logger.info("Saving analysis results to S3...")
        write_s3_object(bucket, output_key, json.dumps(analysis_results, indent=2), 'application/json')
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'jobId': job_id,
            'execution_time': round(execution_time, 2),
            'output_location': f"s3://{bucket}/{output_key}",
            'jtbds_analyzed': len(jtbds),
            'reddit_discussions_processed': len(reddit_discussions),
            'opportunity_zones_found': len(analysis_results['opportunity_zones']),
            'top_opportunity': analysis_results['zone_summary']['highest_opportunity'],
            'market_coverage': analysis_results['zone_summary']['total_market_coverage'],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Advanced opportunity zone analysis completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"Advanced opportunity zone analysis failed: {e}")
        
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
        "input_keys": {
            "jtbds": "jtbd/extracted.txt",
            "reddit_discussions": "reddit/discussions.csv"
        },
        "output_key": "zones/advanced_analysis.json",
        "job_id": "test-job-123",
        "analysis_params": {
            "n_zones": 5,
            "max_discussions_per_jtbd": 3
        }
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_opportunity_zones"
            self.memory_limit_in_mb = 3008
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))