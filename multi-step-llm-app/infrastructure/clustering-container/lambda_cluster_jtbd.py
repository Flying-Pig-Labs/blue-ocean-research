#!/usr/bin/env python3
"""
Lambda-compatible JTBD Clustering
Refactored from cluster_jtbd.py for AWS Lambda deployment

Key Lambda optimizations:
- S3-based file I/O instead of local files
- Memory-efficient clustering with HDBSCAN
- Cohere embeddings with batch processing
- Cold start optimization
- Proper error handling for ML operations
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import time
import numpy as np

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

def parse_pain_points(pain_points_content: str) -> List[str]:
    """Parse pain points from text file"""
    pain_points = []
    
    for line in pain_points_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove numbering if present
            if line[0].isdigit() and '.' in line[:5]:
                line = line.split('.', 1)[1].strip()
            elif line.startswith('- '):
                line = line[2:].strip()
            
            if len(line) > 10:  # Filter out very short entries
                pain_points.append(line)
    
    logger.info(f"Parsed {len(pain_points)} pain points from input")
    return pain_points

def get_cohere_embeddings(texts: List[str], api_key: str, batch_size: int = 96) -> np.ndarray:
    """Get embeddings from Cohere API with batching for efficiency"""
    import cohere
    
    client = cohere.Client(api_key=api_key)
    all_embeddings = []
    
    # Process in batches to handle rate limits
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        try:
            response = client.embed(
                texts=batch_texts,
                model="embed-english-v3.0",
                input_type="search_document"
            )
            
            batch_embeddings = response.embeddings
            all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts) - 1)//batch_size + 1}")
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}: {e}")
            # Create zero embeddings as fallback
            fallback_embeddings = [[0.0] * 1024 for _ in batch_texts]  # Cohere embedding dimension
            all_embeddings.extend(fallback_embeddings)
    
    return np.array(all_embeddings)

def perform_clustering(embeddings: np.ndarray, pain_points: List[str], 
                      min_cluster_size: int = 3, max_clusters: int = 10) -> Tuple[List[int], int]:
    """Perform HDBSCAN clustering on embeddings"""
    try:
        from sklearn.cluster import HDBSCAN
        from sklearn.preprocessing import StandardScaler
        
        # Standardize embeddings
        scaler = StandardScaler()
        scaled_embeddings = scaler.fit_transform(embeddings)
        
        # Adaptive clustering parameters based on data size
        n_points = len(pain_points)
        adjusted_min_size = max(2, min(min_cluster_size, n_points // 5))
        
        # Perform clustering
        clusterer = HDBSCAN(
            min_cluster_size=adjusted_min_size,
            min_samples=max(1, adjusted_min_size - 1),
            cluster_selection_epsilon=0.1,
            cluster_selection_method='eom'
        )
        
        cluster_labels = clusterer.fit_predict(scaled_embeddings)
        
        # Count unique clusters (excluding noise points marked as -1)
        unique_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        # If too many clusters, merge smallest ones
        if unique_clusters > max_clusters:
            # Reassign clusters to limit count
            cluster_counts = {}
            for label in cluster_labels:
                if label != -1:
                    cluster_counts[label] = cluster_counts.get(label, 0) + 1
            
            # Sort clusters by size (largest first)
            sorted_clusters = sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Keep only top clusters
            clusters_to_keep = [cluster[0] for cluster in sorted_clusters[:max_clusters]]
            
            # Reassign labels
            for i, label in enumerate(cluster_labels):
                if label not in clusters_to_keep and label != -1:
                    cluster_labels[i] = -1  # Assign to noise
        
        final_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        
        logger.info(f"Clustering completed: {final_clusters} clusters from {n_points} pain points")
        return cluster_labels.tolist(), final_clusters
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        # Fallback to simple size-based clustering
        cluster_size = max(3, len(pain_points) // 5)
        fallback_labels = [i // cluster_size for i in range(len(pain_points))]
        return fallback_labels, max(fallback_labels) + 1

def call_openai_api(prompt: str, model: str = "gpt-4o", temperature: float = 0.5,
                   max_tokens: int = 1500, api_key: str = None) -> str:
    """Call OpenAI API with retry logic"""
    import openai
    
    client = openai.OpenAI(api_key=api_key)
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def analyze_cluster(cluster_items: List[str], openai_key: str) -> Dict[str, Any]:
    """Analyze a cluster of pain points using GPT-4o"""
    
    cluster_text = '\n'.join([f"- {item}" for item in cluster_items])
    
    prompt = f"""Based on these pain points:
{cluster_text}

Analyze these items and provide:

1. **Zone Name**: A concise, strategic name for this opportunity zone (2-4 words)
2. **Core Theme**: The central problem or need (1-2 sentences)
3. **User Impact**: How this affects users (2-3 sentences)
4. **Market Opportunity**: Size and growth potential (1-2 sentences)
5. **Solution Direction**: High-level approach to address this (2-3 sentences)
6. **Key Differentiators**: What would make a solution stand out (2-3 bullet points)
7. **Estimated Opportunity Score**: Rate 1-10 based on impact and feasibility

Format your response as JSON with these exact keys: zone_name, core_theme, user_impact, market_opportunity, solution_direction, key_differentiators (as array), opportunity_score (as number)."""
    
    try:
        response = call_openai_api(prompt, api_key=openai_key)
        
        # Try to parse as JSON
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "zone_name": f"Opportunity Zone {hash(cluster_text) % 1000}",
                "core_theme": "Multiple pain points requiring integrated solution",
                "user_impact": "Significant operational challenges affecting productivity",
                "market_opportunity": "Growing market demand for comprehensive solutions",
                "solution_direction": "Platform approach addressing multiple pain points",
                "key_differentiators": ["Integrated approach", "User-centric design"],
                "opportunity_score": 6
            }
    
    except Exception as e:
        logger.warning(f"Cluster analysis failed: {e}")
        return {
            "zone_name": f"Cluster {hash(cluster_text) % 1000}",
            "core_theme": "Analysis unavailable",
            "user_impact": "Impact analysis unavailable",
            "market_opportunity": "Market analysis unavailable", 
            "solution_direction": "Solution analysis unavailable",
            "key_differentiators": ["Analysis unavailable"],
            "opportunity_score": 5
        }

def create_opportunity_zones(cluster_labels: List[int], pain_points: List[str], 
                           num_clusters: int, openai_key: str) -> List[Dict[str, Any]]:
    """Create opportunity zones from clustered pain points"""
    
    # Group pain points by cluster
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label != -1:  # Ignore noise points
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(pain_points[i])
    
    opportunity_zones = []
    
    for cluster_id, cluster_points in clusters.items():
        if len(cluster_points) >= 2:  # Only process clusters with sufficient points
            logger.info(f"Analyzing cluster {cluster_id} with {len(cluster_points)} pain points")
            
            try:
                analysis = analyze_cluster(cluster_points, openai_key)
                
                zone = {
                    "cluster_id": cluster_id,
                    "name": analysis.get("zone_name", f"Zone {cluster_id}"),
                    "core_theme": analysis.get("core_theme", ""),
                    "user_impact": analysis.get("user_impact", ""),
                    "market_opportunity": analysis.get("market_opportunity", ""),
                    "solution_direction": analysis.get("solution_direction", ""),
                    "key_differentiators": analysis.get("key_differentiators", []),
                    "opportunity_score": analysis.get("opportunity_score", 5),
                    "pain_points": cluster_points,
                    "size": len(cluster_points)
                }
                
                opportunity_zones.append(zone)
                
            except Exception as e:
                logger.error(f"Failed to analyze cluster {cluster_id}: {e}")
    
    # Sort by opportunity score
    opportunity_zones.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
    
    logger.info(f"Created {len(opportunity_zones)} opportunity zones")
    return opportunity_zones

def create_clustering_report(opportunity_zones: List[Dict[str, Any]], 
                           execution_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create comprehensive clustering report"""
    
    timestamp = datetime.now().isoformat()
    
    # Calculate summary statistics
    total_pain_points = sum(zone['size'] for zone in opportunity_zones)
    avg_score = sum(zone['opportunity_score'] for zone in opportunity_zones) / len(opportunity_zones) if opportunity_zones else 0
    top_zone = max(opportunity_zones, key=lambda x: x['opportunity_score']) if opportunity_zones else None
    
    report = {
        "metadata": {
            "timestamp": timestamp,
            "processing_mode": "Lambda HDBSCAN + GPT-4o Analysis",
            "execution_time": execution_metadata.get('execution_time', 'N/A'),
            "total_pain_points": total_pain_points,
            "clusters_found": len(opportunity_zones),
            "average_opportunity_score": round(avg_score, 2)
        },
        "summary": {
            "top_opportunity": {
                "name": top_zone['name'] if top_zone else "N/A",
                "score": top_zone['opportunity_score'] if top_zone else 0,
                "theme": top_zone['core_theme'] if top_zone else "N/A"
            },
            "cluster_distribution": [
                {
                    "cluster_id": zone['cluster_id'],
                    "name": zone['name'],
                    "size": zone['size'],
                    "score": zone['opportunity_score']
                }
                for zone in opportunity_zones
            ]
        },
        "opportunity_zones": opportunity_zones,
        "pipeline_metadata": {
            "lambda_function": "JTBD Clustering",
            "embedding_model": "Cohere embed-english-v3.0",
            "clustering_algorithm": "HDBSCAN",
            "analysis_model": "GPT-4o"
        }
    }
    
    return report

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for JTBD clustering
    
    Expected event structure:
    {
        "bucket": "pipeline-data-bucket",
        "input_key": "jtbd/pain_points.txt",
        "output_key": "clusters/opportunity_zones.json",
        "job_id": "job-123",
        "clustering_params": {
            "min_cluster_size": 3,
            "max_clusters": 8
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
        input_key = event.get('s3InputKey') or event.get('input_key')
        output_key = event.get('s3OutputKey') or event.get('output_key', 'clusters/opportunity_zones.json')
        job_id = event.get('jobId') or event.get('job_id', 'unknown')
        clustering_params = event.get('clustering_params', {})
        metadata = event.get('metadata', {})
        
        # Clustering parameters
        min_cluster_size = clustering_params.get('min_cluster_size', 3)
        max_clusters = clustering_params.get('max_clusters', 8)
        
        if not bucket or not input_key:
            raise ValueError("Missing required parameters: bucket and input_key")
        
        logger.info(f"Processing JTBD clustering for job {job_id}")
        logger.info(f"Input: s3://{bucket}/{input_key}")
        logger.info(f"Output: s3://{bucket}/{output_key}")
        logger.info(f"Clustering params: min_size={min_cluster_size}, max_clusters={max_clusters}")
        
        # Load secrets
        secrets = get_secrets()
        cohere_key = secrets.get('COHERE_API_KEY')
        openai_key = secrets.get('OPENAI_API_KEY')
        
        if not cohere_key or not openai_key:
            raise ValueError("Required API keys not available")
        
        # Read pain points from S3
        logger.info("Loading pain points from S3...")
        pain_points_content = read_s3_object(bucket, input_key)
        pain_points = parse_pain_points(pain_points_content)
        
        if len(pain_points) < 3:
            raise ValueError(f"Insufficient pain points for clustering: {len(pain_points)}")
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(pain_points)} pain points...")
        embeddings = get_cohere_embeddings(pain_points, cohere_key)
        
        # Perform clustering
        logger.info("Performing HDBSCAN clustering...")
        cluster_labels, num_clusters = perform_clustering(
            embeddings, pain_points, min_cluster_size, max_clusters
        )
        
        # Create opportunity zones
        logger.info(f"Creating opportunity zones from {num_clusters} clusters...")
        opportunity_zones = create_opportunity_zones(
            cluster_labels, pain_points, num_clusters, openai_key
        )
        
        # Create execution metadata
        execution_metadata = {
            'execution_time': round(time.time() - start_time, 2),
            'pain_points_processed': len(pain_points),
            'clusters_found': num_clusters,
            'zones_created': len(opportunity_zones)
        }
        
        # Create comprehensive report
        logger.info("Generating clustering report...")
        clustering_report = create_clustering_report(opportunity_zones, execution_metadata)
        
        # Save to S3
        logger.info("Saving clustering results to S3...")
        write_s3_object(bucket, output_key, json.dumps(clustering_report, indent=2), 'application/json')
        
        execution_time = time.time() - start_time
        
        # Return success response
        response = {
            'statusCode': 200,
            'jobId': job_id,
            'execution_time': round(execution_time, 2),
            'output_location': f"s3://{bucket}/{output_key}",
            'pain_points_processed': len(pain_points),
            'clusters_found': num_clusters,
            'opportunity_zones_created': len(opportunity_zones),
            'top_opportunity_score': max([zone['opportunity_score'] for zone in opportunity_zones]) if opportunity_zones else 0,
            'embedding_dimensions': embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"JTBD clustering completed in {execution_time:.2f} seconds")
        return response
        
    except Exception as e:
        logger.error(f"JTBD clustering failed: {e}")
        
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
        "input_key": "jtbd/pain_points.txt",
        "output_key": "clusters/opportunity_zones.json",
        "job_id": "test-job-123",
        "clustering_params": {
            "min_cluster_size": 3,
            "max_clusters": 8
        },
        "metadata": {"stage": "clustering"}
    }
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "lambda_cluster_jtbd"
            self.memory_limit_in_mb = 3008
            self.remaining_time_in_millis = lambda: 900000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))