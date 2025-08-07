#!/usr/bin/env python3
"""
Main Lambda Handler for Multi-Step LLM Pipeline
Orchestrates the complete pipeline execution across multiple Lambda functions

This handler manages:
- API Gateway endpoints (/start-pipeline, /status/{jobId}, /logs/{jobId})
- Job state management in DynamoDB
- Pipeline orchestration across individual Lambda functions
- Error handling and progress tracking
"""

import json
import os
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (outside handlers for connection reuse)
dynamodb = None
lambda_client = None
s3_client = None

def initialize_clients():
    """Initialize AWS clients with retry configuration"""
    global dynamodb, lambda_client, s3_client
    
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb',
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )
    
    if lambda_client is None:
        lambda_client = boto3.client('lambda',
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )
    
    if s3_client is None:
        s3_client = boto3.client('s3',
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
        )

def get_cors_headers():
    """Get CORS headers for API responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def create_job_record(job_id: str, job_data: Dict[str, Any]) -> None:
    """Create initial job record in DynamoDB"""
    initialize_clients()
    
    table = dynamodb.Table(os.environ['JOBS_TABLE'])
    
    # TTL for 30 days from now
    ttl = int((datetime.now() + timedelta(days=30)).timestamp())
    
    item = {
        'jobId': job_id,
        'status': 'INITIATED',
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat(),
        'ttl': ttl,
        'pipeline_config': job_data,
        'current_stage': 'research_analysis',
        'stages_completed': [],
        'total_stages': 8,
        'progress_percentage': 0,
        'logs': [{
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': 'Pipeline job initiated',
            'stage': 'orchestrator'
        }]
    }
    
    table.put_item(Item=item)
    logger.info(f"Created job record for {job_id}")

def update_job_status(job_id: str, status: str, current_stage: str = None, 
                     progress: int = None, logs: List[Dict] = None) -> None:
    """Update job status in DynamoDB"""
    initialize_clients()
    
    table = dynamodb.Table(os.environ['JOBS_TABLE'])
    
    update_expression = "SET #status = :status, updatedAt = :updated"
    expression_values = {
        ':status': status,
        ':updated': datetime.now().isoformat()
    }
    expression_names = {'#status': 'status'}
    
    if current_stage:
        update_expression += ", current_stage = :stage"
        expression_values[':stage'] = current_stage
    
    if progress is not None:
        update_expression += ", progress_percentage = :progress"
        expression_values[':progress'] = progress
    
    if logs:
        update_expression += ", logs = list_append(logs, :logs)"
        expression_values[':logs'] = logs
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_names,
        ExpressionAttributeValues=expression_values
    )

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status from DynamoDB"""
    initialize_clients()
    
    table = dynamodb.Table(os.environ['JOBS_TABLE'])
    
    try:
        response = table.get_item(Key={'jobId': job_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        return None

def invoke_lambda_stage(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a specific Lambda function for a pipeline stage"""
    initialize_clients()
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response.get('StatusCode') == 200:
            return response_payload
        else:
            raise Exception(f"Lambda invocation failed with status {response.get('StatusCode')}")
            
    except Exception as e:
        logger.error(f"Failed to invoke {function_name}: {e}")
        return {'statusCode': 500, 'error': str(e)}

def execute_pipeline_stage(job_id: str, stage_name: str, stage_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single pipeline stage"""
    
    bucket = os.environ['S3_BUCKET']
    function_prefix = os.environ.get('FUNCTION_PREFIX', 'multi-step-llm-')
    
    # Map stage names to Lambda function names
    stage_function_map = {
        'research_analysis': f'{function_prefix}research-analyzer',
        'jobs_research': f'{function_prefix}jobs-researcher', 
        'jobs_to_reddit': f'{function_prefix}jobs-to-reddit',
        'clustering': f'{function_prefix}cluster-jtbd',
        'opportunity_zones': f'{function_prefix}opportunity-zones',
        'value_curves': f'{function_prefix}value-curves',
        'product_ideas': f'{function_prefix}product-ideas',
        'consolidation': f'{function_prefix}consolidator'
    }
    
    function_name = stage_function_map.get(stage_name)
    if not function_name:
        raise ValueError(f"Unknown stage: {stage_name}")
    
    # Build stage payload
    payload = {
        'bucket': bucket,
        'job_id': job_id,
        'stage_name': stage_name,
        **stage_config
    }
    
    logger.info(f"Executing stage {stage_name} for job {job_id}")
    
    # Invoke the stage Lambda function
    result = invoke_lambda_stage(function_name, payload)
    
    # Log stage completion
    update_job_status(
        job_id,
        'RUNNING',
        logs=[{
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': f'Completed stage: {stage_name}',
            'stage': stage_name,
            'execution_time': result.get('execution_time', 0),
            'status_code': result.get('statusCode', 500)
        }]
    )
    
    return result

def orchestrator_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main orchestrator handler - executes the complete pipeline"""
    
    job_id = event.get('job_id')
    pipeline_config = event.get('pipeline_config', {})
    
    if not job_id:
        return {'statusCode': 400, 'error': 'Missing job_id'}
    
    logger.info(f"Starting pipeline orchestration for job {job_id}")
    
    bucket = os.environ['S3_BUCKET']
    
    try:
        # Update job status to RUNNING
        update_job_status(job_id, 'RUNNING', 'research_analysis', 0)
        
        # Pipeline stages configuration
        stages = [
            {
                'name': 'research_analysis',
                'config': {
                    'input_key': pipeline_config.get('input_key', 'input/research.json'),
                    'output_key': f'jobs/{job_id}/analysis/results.md'
                },
                'progress': 12
            },
            {
                'name': 'jobs_research',
                'config': {
                    'input_key': f'jobs/{job_id}/analysis/results.md',
                    'output_keys': {
                        'jtbd_report': f'jobs/{job_id}/jtbd/research.md',
                        'pain_points': f'jobs/{job_id}/jtbd/pain_points.txt'
                    }
                },
                'progress': 25
            },
            {
                'name': 'jobs_to_reddit',
                'config': {
                    'input_key': f'jobs/{job_id}/analysis/results.md',
                    'output_keys': {
                        'jtbds': f'jobs/{job_id}/jtbd/extracted.txt',
                        'reddit_discussions': f'jobs/{job_id}/reddit/discussions.csv'
                    },
                    'max_jtbds': pipeline_config.get('max_jtbds', 20)
                },
                'progress': 37
            },
            {
                'name': 'clustering',
                'config': {
                    'input_key': f'jobs/{job_id}/jtbd/pain_points.txt',
                    'output_key': f'jobs/{job_id}/clusters/opportunity_zones.json',
                    'clustering_params': {
                        'min_cluster_size': 3,
                        'max_clusters': pipeline_config.get('max_clusters', 8)
                    }
                },
                'progress': 50
            },
            {
                'name': 'opportunity_zones',
                'config': {
                    'input_keys': {
                        'jtbds': f'jobs/{job_id}/jtbd/extracted.txt',
                        'reddit_discussions': f'jobs/{job_id}/reddit/discussions.csv'
                    },
                    'output_key': f'jobs/{job_id}/zones/advanced_analysis.json',
                    'analysis_params': {
                        'n_zones': pipeline_config.get('max_clusters', 8),
                        'max_discussions_per_jtbd': 3
                    }
                },
                'progress': 62
            },
            {
                'name': 'value_curves',
                'config': {
                    'input_key': f'jobs/{job_id}/zones/advanced_analysis.json',
                    'output_keys': {
                        'value_curves': f'jobs/{job_id}/value_curves/analysis.json',
                        'report': f'jobs/{job_id}/value_curves/report.md'
                    }
                },
                'progress': 75
            },
            {
                'name': 'product_ideas',
                'config': {
                    'input_key': f'jobs/{job_id}/value_curves/analysis.json',
                    'output_keys': {
                        'ideas': f'jobs/{job_id}/products/ideas.json',
                        'report': f'jobs/{job_id}/products/report.md'
                    },
                    'generation_params': {
                        'target_count': pipeline_config.get('target_ideas', 12),
                        'final_count': pipeline_config.get('final_ideas', 8)
                    }
                },
                'progress': 87
            },
            {
                'name': 'consolidation',
                'config': {
                    'input_key': f'jobs/{job_id}/products/ideas.json',
                    'output_keys': {
                        'portfolio': f'jobs/{job_id}/final/portfolio.json',
                        'summary': f'jobs/{job_id}/final/summary.md'
                    }
                },
                'progress': 100
            }
        ]
        
        # Execute stages sequentially
        completed_stages = []
        
        for stage in stages:
            stage_name = stage['name']
            stage_config = stage['config']
            progress = stage['progress']
            
            try:
                logger.info(f"Starting stage: {stage_name}")
                update_job_status(job_id, 'RUNNING', stage_name, progress)
                
                # Execute the stage
                result = execute_pipeline_stage(job_id, stage_name, stage_config)
                
                if result.get('statusCode') != 200:
                    raise Exception(f"Stage {stage_name} failed: {result.get('error', 'Unknown error')}")
                
                completed_stages.append(stage_name)
                logger.info(f"Completed stage: {stage_name}")
                
            except Exception as e:
                logger.error(f"Stage {stage_name} failed: {e}")
                
                # Update job with failure
                update_job_status(
                    job_id, 
                    'FAILED',
                    stage_name,
                    progress,
                    [{
                        'timestamp': datetime.now().isoformat(),
                        'level': 'ERROR',
                        'message': f'Stage {stage_name} failed: {str(e)}',
                        'stage': stage_name
                    }]
                )
                
                return {
                    'statusCode': 500,
                    'job_id': job_id,
                    'error': f'Pipeline failed at stage {stage_name}: {str(e)}',
                    'completed_stages': completed_stages
                }
        
        # Pipeline completed successfully
        update_job_status(
            job_id,
            'COMPLETED',
            'finished',
            100,
            [{
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Pipeline completed successfully',
                'stage': 'orchestrator'
            }]
        )
        
        logger.info(f"Pipeline completed successfully for job {job_id}")
        
        return {
            'statusCode': 200,
            'job_id': job_id,
            'message': 'Pipeline completed successfully',
            'completed_stages': completed_stages,
            'results_location': f's3://{bucket}/jobs/{job_id}/final/'
        }
        
    except Exception as e:
        logger.error(f"Pipeline orchestration failed for job {job_id}: {e}")
        
        update_job_status(
            job_id,
            'FAILED',
            logs=[{
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'message': f'Pipeline orchestration failed: {str(e)}',
                'stage': 'orchestrator'
            }]
        )
        
        return {
            'statusCode': 500,
            'job_id': job_id,
            'error': f'Pipeline orchestration failed: {str(e)}'
        }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main Lambda handler for API Gateway endpoints"""
    
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    try:
        # Start pipeline endpoint
        if path == '/start-pipeline' and method == 'POST':
            return handle_start_pipeline(event, context)
        
        # Get job status endpoint
        elif path.startswith('/status/') and method == 'GET':
            job_id = path.split('/')[-1]
            return handle_get_status(job_id)
        
        # Get job logs endpoint
        elif path.startswith('/logs/') and method == 'GET':
            job_id = path.split('/')[-1]
            return handle_get_logs(job_id)
        
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def handle_start_pipeline(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle pipeline start request"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Generate unique job ID
        job_id = f"job-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # Validate required parameters
        input_data = body.get('input_data')
        if not input_data:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing input_data'})
            }
        
        # Pipeline configuration
        pipeline_config = {
            'input_key': f'jobs/{job_id}/input/research.json',
            'max_jtbds': body.get('max_jtbds', 20),
            'max_clusters': body.get('max_clusters', 8),
            'target_ideas': body.get('target_ideas', 12),
            'final_ideas': body.get('final_ideas', 8)
        }
        
        # Store input data in S3
        initialize_clients()
        bucket = os.environ['S3_BUCKET']
        
        s3_client.put_object(
            Bucket=bucket,
            Key=pipeline_config['input_key'],
            Body=json.dumps(input_data).encode('utf-8'),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        
        # Create job record
        create_job_record(job_id, pipeline_config)
        
        # Invoke orchestrator Lambda asynchronously
        orchestrator_function = os.environ['ORCHESTRATOR_FUNCTION_NAME']
        
        orchestrator_payload = {
            'job_id': job_id,
            'pipeline_config': pipeline_config
        }
        
        lambda_client.invoke(
            FunctionName=orchestrator_function,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(orchestrator_payload)
        )
        
        return {
            'statusCode': 202,  # Accepted
            'headers': get_cors_headers(),
            'body': json.dumps({
                'job_id': job_id,
                'status': 'INITIATED',
                'message': 'Pipeline started successfully',
                'status_url': f'/status/{job_id}'
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to start pipeline: {str(e)}'})
        }

def handle_get_status(job_id: str) -> Dict[str, Any]:
    """Handle get job status request"""
    
    job_data = get_job_status(job_id)
    
    if not job_data:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Job not found'})
        }
    
    # Clean up response
    response_data = {
        'job_id': job_data['jobId'],
        'status': job_data['status'],
        'current_stage': job_data.get('current_stage', 'unknown'),
        'progress_percentage': job_data.get('progress_percentage', 0),
        'created_at': job_data['createdAt'],
        'updated_at': job_data['updatedAt'],
        'stages_completed': job_data.get('stages_completed', []),
        'total_stages': job_data.get('total_stages', 8)
    }
    
    # Add results location if completed
    if job_data['status'] == 'COMPLETED':
        bucket = os.environ['S3_BUCKET']
        response_data['results_location'] = f's3://{bucket}/jobs/{job_id}/final/'
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(response_data)
    }

def handle_get_logs(job_id: str) -> Dict[str, Any]:
    """Handle get job logs request"""
    
    job_data = get_job_status(job_id)
    
    if not job_data:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Job not found'})
        }
    
    logs = job_data.get('logs', [])
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'job_id': job_id,
            'logs': logs,
            'total_logs': len(logs)
        })
    }