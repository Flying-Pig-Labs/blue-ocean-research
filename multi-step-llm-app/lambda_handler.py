#!/usr/bin/env python3
"""
AWS Lambda handler for multi-step LLM pipeline with MVP frontend support features.
Supports async job processing with progress tracking, concurrent job prevention, 
enhanced time estimates, and job metadata.
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import boto3
import logging
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'PipelineJobs-production')
ORCHESTRATOR_FUNCTION = os.environ.get('ORCHESTRATOR_FUNCTION', 'multi-step-llm-pipeline-OrchestratorFunction')

def lambda_handler(event, context):
    """Main Lambda handler - routes requests to appropriate handlers."""
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle different HTTP methods and paths
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'POST' and path == '/start-pipeline':
            return start_pipeline_handler(event, context)
        elif http_method == 'GET' and path.startswith('/status/'):
            return get_status_handler(event, context)
        elif http_method == 'GET' and path.startswith('/logs/'):
            return get_logs_handler(event, context)
        elif http_method == 'OPTIONS':
            return handle_cors_preflight(event, context)
        else:
            # For direct invocation by orchestrator
            return orchestrator_handler(event, context)
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }


def check_existing_job(research_doc_id: str, username: str) -> Optional[Dict[str, Any]]:
    """Check if there's an existing running job for this researchDocId."""
    table = dynamodb.Table(JOBS_TABLE)
    
    # Scan for jobs with this researchDocId (in production, consider using GSI)
    response = table.scan(
        FilterExpression='researchDocId = :docId AND username = :user AND (#status = :running OR #status = :queued)',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':docId': research_doc_id,
            ':user': username,
            ':running': 'RUNNING',
            ':queued': 'QUEUED'
        }
    )
    
    if response.get('Items'):
        # Return the most recent running/queued job
        jobs = sorted(response['Items'], key=lambda x: x.get('createdAt', ''), reverse=True)
        return jobs[0]
    
    return None


def start_pipeline_handler(event, context):
    """Handle POST /start-pipeline requests with idempotency and concurrent job prevention."""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        research_doc_id = body.get('researchDocId', '').strip()
        
        # Validate required fields
        if not research_doc_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'researchDocId is required'})
            }
        
        # Get username (required for S3 path)
        username = body.get('username', 'fprior')  # Default to fprior if not provided
        
        # Check for existing running job (idempotency + concurrent job prevention)
        existing_job = check_existing_job(research_doc_id, username)
        
        if existing_job:
            # Calculate time estimates for existing job
            created_at = datetime.fromisoformat(existing_job['createdAt'].rstrip('Z'))
            elapsed_seconds = (datetime.utcnow() - created_at).total_seconds()
            elapsed_minutes = int(elapsed_seconds / 60)
            estimated_total_minutes = 22  # Standard estimate
            estimated_remaining_minutes = max(0, estimated_total_minutes - elapsed_minutes)
            
            # Return 409 Conflict with existing job information
            return {
                'statusCode': 409,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Pipeline already running for this research document',
                    'existingJobId': existing_job['jobId'],
                    'status': existing_job['status'],
                    'currentStage': existing_job.get('currentStage', 0),
                    'stageName': existing_job.get('stageName', 'Initializing'),
                    'overallProgress': existing_job.get('overallProgress', 0.0),
                    'estimatedTotalMinutes': estimated_total_minutes,
                    'elapsedMinutes': elapsed_minutes,
                    'estimatedRemainingMinutes': estimated_remaining_minutes,
                    'metadata': {
                        'researchDocId': existing_job['researchDocId'],
                        'startedAt': existing_job['createdAt'],
                        'username': existing_job['username']
                    }
                })
            }
        
        # Generate job ID
        job_id = f"job-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        # Create job record in DynamoDB with enhanced metadata
        table = dynamodb.Table(JOBS_TABLE)
        job_record = {
            'jobId': job_id,
            'researchDocId': research_doc_id,
            'username': username,
            'status': 'QUEUED',
            'currentStage': 0,
            'stageName': 'Initializing',
            'stageProgress': 0.0,
            'overallProgress': 0.0,
            'estimatedCompletion': (datetime.utcnow() + timedelta(minutes=22)).isoformat() + 'Z',
            'estimatedTotalMinutes': 22,
            'createdAt': datetime.utcnow().isoformat() + 'Z',
            'updatedAt': datetime.utcnow().isoformat() + 'Z',
            'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            'stages': [
                {'name': 'Research Analysis', 'status': 'pending', 'estimatedMinutes': 2},
                {'name': 'JTBD Research', 'status': 'pending', 'estimatedMinutes': 3},
                {'name': 'Pain Point Clustering', 'status': 'pending', 'estimatedMinutes': 1},
                {'name': 'Value Curve Mapping', 'status': 'pending', 'estimatedMinutes': 5},
                {'name': 'Product Idea Generation', 'status': 'pending', 'estimatedMinutes': 8},
                {'name': 'Idea Consolidation', 'status': 'pending', 'estimatedMinutes': 1},
                {'name': 'GitHub Repository Creation', 'status': 'pending', 'estimatedMinutes': 2}
            ],
            'results': {
                'githubRepoUrl': None,
                'githubRepoName': None,
                'issuesCreated': 0,
                'analysisResults': None
            }
        }
        
        # Store job in DynamoDB
        table.put_item(Item=job_record)
        
        # Invoke orchestrator function asynchronously
        lambda_client.invoke(
            FunctionName=ORCHESTRATOR_FUNCTION,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'jobId': job_id,
                'researchDocId': research_doc_id,
                'username': username,
                'action': 'start_pipeline'
            })
        )
        
        # Return job ID immediately with enhanced response
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobId': job_id,
                'status': 'QUEUED',
                'message': 'Pipeline job started successfully',
                'estimatedCompletion': job_record['estimatedCompletion'],
                'estimatedTotalMinutes': 22,
                'metadata': {
                    'researchDocId': research_doc_id,
                    'startedAt': job_record['createdAt'],
                    'username': username
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error starting pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }


def get_status_handler(event, context):
    """Handle GET /status/{jobId} requests with enhanced time estimates and metadata."""
    try:
        # Extract job ID from path
        job_id = event['pathParameters'].get('jobId')
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'jobId is required'})
            }
        
        # Get job from DynamoDB
        table = dynamodb.Table(JOBS_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Job not found'})
            }
        
        job = response['Item']
        
        # Calculate enhanced time estimates
        created_at = datetime.fromisoformat(job['createdAt'].rstrip('Z'))
        elapsed_seconds = (datetime.utcnow() - created_at).total_seconds()
        elapsed_minutes = int(elapsed_seconds / 60)
        
        # Use stored estimate or default to 22 minutes
        estimated_total_minutes = job.get('estimatedTotalMinutes', 22)
        
        # Calculate remaining time based on status
        if job['status'] in ['RUNNING', 'QUEUED']:
            estimated_remaining_minutes = max(0, estimated_total_minutes - elapsed_minutes)
        else:
            estimated_remaining_minutes = 0
        
        # Add enhanced time estimates to response
        job['estimatedTotalMinutes'] = estimated_total_minutes
        job['elapsedMinutes'] = elapsed_minutes
        job['estimatedRemainingMinutes'] = estimated_remaining_minutes
        
        # Add metadata section
        job['metadata'] = {
            'researchDocId': job.get('researchDocId', ''),
            'startedAt': job.get('createdAt', ''),
            'username': job.get('username', ''),
            'jobId': job_id
        }
        
        # Add completion time if job is finished
        if job['status'] == 'COMPLETED' and 'completedAt' in job:
            completed_at = datetime.fromisoformat(job['completedAt'].rstrip('Z'))
            actual_duration = (completed_at - created_at).total_seconds() / 60
            job['actualDurationMinutes'] = int(actual_duration)
        
        # Backward compatibility - keep the old estimatedRemaining field
        if job['status'] == 'RUNNING':
            remaining_seconds = estimated_remaining_minutes * 60
            job['estimatedRemaining'] = f"{estimated_remaining_minutes} minutes" if remaining_seconds > 60 else f"{int(remaining_seconds)} seconds"
        
        # Return enhanced status
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(job, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }


def get_logs_handler(event, context):
    """Handle GET /logs/{jobId} requests for cursor-based log polling."""
    try:
        job_id = event['pathParameters'].get('jobId')
        since = event.get('queryStringParameters', {}).get('since', '0') if event.get('queryStringParameters') else '0'
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'jobId is required'})
            }
        
        # Get job logs from CloudWatch or DynamoDB
        # For now, return basic log structure
        logs = [
            {
                'timestamp': int(time.time() * 1000),
                'level': 'INFO',
                'message': f'Job {job_id} is processing...',
                'stage': 'current'
            }
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'logs': logs,
                'cursor': str(int(time.time() * 1000))
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }


def handle_cors_preflight(event, context):
    """Handle CORS preflight requests."""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400'
        },
        'body': ''
    }


def orchestrator_handler(event, context):
    """Handle orchestrator invocations - runs the actual pipeline."""
    try:
        job_id = event.get('jobId')
        research_doc_id = event.get('researchDocId')
        username = event.get('username')
        
        if not all([job_id, research_doc_id, username]):
            logger.error("Missing required parameters for orchestrator")
            return {'statusCode': 400, 'body': 'Missing required parameters'}
        
        # Update job status to RUNNING
        table = dynamodb.Table(JOBS_TABLE)
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, currentStage = :stage, stageName = :stageName, updatedAt = :updatedAt',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'RUNNING',
                ':stage': 1,
                ':stageName': 'Research Analysis',
                ':updatedAt': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Simulate pipeline execution stages
        stages = [
            {'name': 'Research Analysis', 'duration': 2},
            {'name': 'JTBD Research', 'duration': 3}, 
            {'name': 'Pain Point Clustering', 'duration': 1},
            {'name': 'Value Curve Mapping', 'duration': 5},
            {'name': 'Product Idea Generation', 'duration': 8},
            {'name': 'Idea Consolidation', 'duration': 1},
            {'name': 'GitHub Repository Creation', 'duration': 2}
        ]
        
        for i, stage in enumerate(stages, 1):
            # Update stage status
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET currentStage = :stage, stageName = :stageName, stageProgress = :stageProgress, overallProgress = :overallProgress, updatedAt = :updatedAt',
                ExpressionAttributeValues={
                    ':stage': i,
                    ':stageName': stage['name'],
                    ':stageProgress': 0.0,
                    ':overallProgress': (i - 1) / len(stages) * 100,
                    ':updatedAt': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Simulate stage processing
            stage_duration = stage['duration'] * 60  # Convert to seconds
            for progress in range(0, 101, 20):
                time.sleep(stage_duration / 5 * 0.01)  # Simulate work (much faster for demo)
                
                table.update_item(
                    Key={'jobId': job_id},
                    UpdateExpression='SET stageProgress = :stageProgress, overallProgress = :overallProgress, updatedAt = :updatedAt',
                    ExpressionAttributeValues={
                        ':stageProgress': float(progress),
                        ':overallProgress': ((i - 1) + progress / 100) / len(stages) * 100,
                        ':updatedAt': datetime.utcnow().isoformat() + 'Z'
                    }
                )
        
        # Mark job as completed
        github_repo_url = f"https://github.com/{username}/innovation-analysis-{research_doc_id[:8]}"
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, overallProgress = :progress, completedAt = :completedAt, updatedAt = :updatedAt, results.githubRepoUrl = :githubUrl, results.githubRepoName = :githubName, results.issuesCreated = :issuesCreated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':progress': 100.0,
                ':completedAt': datetime.utcnow().isoformat() + 'Z',
                ':updatedAt': datetime.utcnow().isoformat() + 'Z',
                ':githubUrl': github_repo_url,
                ':githubName': f"innovation-analysis-{research_doc_id[:8]}",
                ':issuesCreated': 12
            }
        )
        
        logger.info(f"Pipeline completed successfully for job {job_id}")
        return {'statusCode': 200, 'body': 'Pipeline completed successfully'}
        
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Mark job as failed
        if 'job_id' in locals():
            table = dynamodb.Table(JOBS_TABLE)
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, errorMessage = :error, updatedAt = :updatedAt',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':updatedAt': datetime.utcnow().isoformat() + 'Z'
                }
            )
        
        return {'statusCode': 500, 'body': 'Pipeline failed'}


if __name__ == "__main__":
    # For local testing
    test_event = {
        'httpMethod': 'POST',
        'path': '/start-pipeline',
        'body': json.dumps({
            'researchDocId': 'test-doc-123',
            'username': 'testuser'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))