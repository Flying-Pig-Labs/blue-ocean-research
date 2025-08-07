#!/usr/bin/env python3
"""
Enhanced AWS Lambda handler with GraphQL integration for real-time updates.
Integrates with AppSync to provide real-time pipeline execution updates.
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from decimal import Decimal
import logging
import traceback
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'PipelineJobs-production')
ORCHESTRATOR_FUNCTION = os.environ.get('ORCHESTRATOR_FUNCTION_NAME', 'pipeline-orchestrator-production')
GRAPHQL_API_URL = os.environ.get('GRAPHQL_API_URL')
GRAPHQL_API_ID = os.environ.get('GRAPHQL_API_ID')

class GraphQLClient:
    """Client for making authenticated requests to AppSync GraphQL API"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session = boto3.Session()
        
    def execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL mutation with AWS IAM authentication"""
        try:
            request_body = {
                'query': mutation,
                'variables': variables
            }
            
            # Create AWS request for signing
            request = AWSRequest(
                method='POST',
                url=self.api_url,
                data=json.dumps(request_body),
                headers={
                    'Content-Type': 'application/json'
                }
            )
            
            # Sign the request
            credentials = self.session.get_credentials()
            SigV4Auth(credentials, 'appsync', self.session.region_name).add_auth(request)
            
            # Make the request
            response = requests.post(
                request.url,
                data=request.body,
                headers=dict(request.headers)
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'errors' in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise Exception(f"GraphQL errors: {result['errors']}")
                
            return result.get('data', {})
            
        except Exception as e:
            logger.error(f"GraphQL request failed: {str(e)}")
            raise

def lambda_handler(event, context):
    """Main Lambda handler with GraphQL integration."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
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
            return enhanced_orchestrator_handler(event, context)
            
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

def start_pipeline_handler(event, context):
    """Enhanced start pipeline handler with GraphQL mutation trigger"""
    try:
        body = json.loads(event.get('body', '{}'))
        research_doc_id = body.get('researchDocId', '').strip()
        
        if not research_doc_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'researchDocId is required'})
            }
        
        username = body.get('username', 'fprior')
        
        # Check for existing running job
        existing_job = check_existing_job(research_doc_id, username)
        if existing_job):
            return handle_existing_job_response(existing_job)
        
        # Create new job
        job_id = f"job-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        job_record = create_job_record(job_id, research_doc_id, username)
        
        # Store job in DynamoDB
        table = dynamodb.Table(JOBS_TABLE)
        table.put_item(Item=job_record)
        
        # Trigger GraphQL mutation for real-time updates
        if GRAPHQL_API_URL:
            try:
                graphql_client = GraphQLClient(GRAPHQL_API_URL)
                mutation = """
                mutation StartExecution($input: StartExecutionInput!) {
                    startExecution(input: $input) {
                        jobId
                        status
                        timestamp
                    }
                }
                """
                variables = {
                    'input': {
                        'researchDocId': research_doc_id,
                        'username': username,
                        'pipelineConfig': body.get('pipelineConfig', {})
                    }
                }
                graphql_client.execute_mutation(mutation, variables)
                logger.info(f"GraphQL start execution mutation triggered for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to trigger GraphQL mutation: {str(e)}")
        
        # Start orchestrator
        lambda_client.invoke(
            FunctionName=ORCHESTRATOR_FUNCTION,
            InvocationType='Event',
            Payload=json.dumps({
                'jobId': job_id,
                'researchDocId': research_doc_id,
                'username': username,
                'action': 'start_pipeline'
            })
        )
        
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

def enhanced_orchestrator_handler(event, context):
    """Enhanced orchestrator with real-time GraphQL progress updates"""
    try:
        job_id = event.get('jobId')
        research_doc_id = event.get('researchDocId')
        username = event.get('username')
        
        if not all([job_id, research_doc_id, username]):
            logger.error("Missing required parameters for orchestrator")
            return {'statusCode': 400, 'body': 'Missing required parameters'}
        
        # Initialize GraphQL client if available
        graphql_client = None
        if GRAPHQL_API_URL:
            graphql_client = GraphQLClient(GRAPHQL_API_URL)
        
        # Update job status to RUNNING
        update_job_stage(job_id, 1, 'Research Analysis', 'RUNNING', 0.0)
        
        # Trigger initial GraphQL update
        trigger_graphql_update(graphql_client, job_id, 1, 0.0, 'RUNNING')
        
        # Execute pipeline stages with real-time updates
        stages = [
            {'name': 'Research Analysis', 'duration': 2, 'function': simulate_research_analysis},
            {'name': 'JTBD Research', 'duration': 3, 'function': simulate_jtbd_research},
            {'name': 'Pain Point Clustering', 'duration': 1, 'function': simulate_clustering},
            {'name': 'Value Curve Mapping', 'duration': 5, 'function': simulate_value_curves},
            {'name': 'Product Idea Generation', 'duration': 8, 'function': simulate_idea_generation},
            {'name': 'Idea Consolidation', 'duration': 1, 'function': simulate_consolidation},
            {'name': 'GitHub Repository Creation', 'duration': 2, 'function': simulate_github_creation}
        ]
        
        for i, stage in enumerate(stages, 1):
            logger.info(f"Starting stage {i}: {stage['name']}")
            
            # Update stage status to running
            update_job_stage(job_id, i, stage['name'], 'RUNNING', 0.0)
            trigger_graphql_update(graphql_client, job_id, i, 0.0, 'RUNNING')
            
            # Execute stage with progress updates
            await execute_stage_with_updates(
                job_id, i, stage, graphql_client, 
                research_doc_id, username
            )
            
            # Mark stage as completed
            update_job_stage(job_id, i, stage['name'], 'COMPLETED', 100.0)
            trigger_graphql_update(graphql_client, job_id, i, 100.0, 'COMPLETED')
        
        # Mark job as completed
        complete_job(job_id, research_doc_id, username)
        trigger_graphql_update(graphql_client, job_id, len(stages), 100.0, 'COMPLETED')
        
        logger.info(f"Pipeline completed successfully for job {job_id}")
        return {'statusCode': 200, 'body': 'Pipeline completed successfully'}
        
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Mark job as failed and trigger GraphQL update
        if 'job_id' in locals():
            fail_job(job_id, str(e))
            if 'graphql_client' in locals() and graphql_client:
                trigger_graphql_update(graphql_client, job_id, 0, 0.0, 'FAILED', str(e))
        
        return {'statusCode': 500, 'body': 'Pipeline failed'}

async def execute_stage_with_updates(
    job_id: str, 
    stage_id: int, 
    stage: Dict[str, Any], 
    graphql_client: Optional[GraphQLClient],
    research_doc_id: str,
    username: str
):
    """Execute a pipeline stage with granular progress updates"""
    
    # Record stage start time
    start_time = datetime.utcnow()
    update_stage_start_time(job_id, stage_id, start_time.isoformat() + 'Z')
    
    # Simulate stage execution with progress updates
    stage_duration = stage['duration'] * 60  # Convert to seconds
    
    # Execute the actual stage function (simulated for now)
    stage_outputs = []
    if 'function' in stage:
        stage_outputs = stage['function'](research_doc_id, username)
    
    # Progress updates throughout stage execution
    for progress in range(0, 101, 20):
        # Simulate work
        time.sleep(stage_duration / 5 * 0.1)  # Faster for demo
        
        # Update progress in DynamoDB
        update_job_stage(job_id, stage_id, stage['name'], 'RUNNING', float(progress))
        
        # Trigger real-time GraphQL update
        trigger_graphql_update(
            graphql_client, job_id, stage_id, float(progress), 'RUNNING',
            outputs=stage_outputs if progress == 100 else None
        )
    
    # Record stage completion time and outputs
    end_time = datetime.utcnow()
    actual_duration = int((end_time - start_time).total_seconds() / 60)
    
    update_stage_completion(job_id, stage_id, end_time.isoformat() + 'Z', 
                           actual_duration, stage_outputs)

def trigger_graphql_update(
    graphql_client: Optional[GraphQLClient],
    job_id: str,
    stage_id: int,
    progress: float,
    status: str,
    error: Optional[str] = None,
    outputs: Optional[List[Dict[str, Any]]] = None
):
    """Trigger GraphQL subscription update"""
    if not graphql_client:
        return
        
    try:
        mutation = """
        mutation UpdateStageProgress($input: UpdateStageProgressInput!) {
            updateStageProgress(input: $input) {
                jobId
                status
                currentStage
                stageProgress
                overallProgress
                timestamp
            }
        }
        """
        
        variables = {
            'input': {
                'jobId': job_id,
                'stageId': stage_id,
                'progress': progress,
                'status': status.upper()
            }
        }
        
        # Add outputs if provided
        if outputs:
            variables['input']['outputs'] = outputs
            
        # Add error if provided
        if error:
            variables['input']['metadata'] = {'error': error}
        
        graphql_client.execute_mutation(mutation, variables)
        logger.info(f"GraphQL update triggered for job {job_id}, stage {stage_id}, progress {progress}%")
        
    except Exception as e:
        logger.warning(f"Failed to trigger GraphQL update: {str(e)}")

# Stage simulation functions (replace with actual pipeline logic)
def simulate_research_analysis(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate research analysis stage"""
    return [
        {
            'fileName': 'analysis_results.md',
            'fileSize': 15234,
            'contentPreview': 'Market research analysis with 4 key findings...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/analysis_results.md'
        }
    ]

def simulate_jtbd_research(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate JTBD research stage"""
    return [
        {
            'fileName': 'jtbd_research.md',
            'fileSize': 8756,
            'contentPreview': 'Jobs-to-be-Done analysis with 23 identified jobs...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/jtbd_research.md'
        },
        {
            'fileName': 'pain_points.txt',
            'fileSize': 2341,
            'contentPreview': 'Extracted pain points for clustering analysis...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/pain_points.txt'
        }
    ]

def simulate_clustering(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate clustering stage"""
    return [
        {
            'fileName': 'opportunity_zones.json',
            'fileSize': 4523,
            'contentPreview': '{"opportunity_zones": [7 zones identified]}',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/opportunity_zones.json'
        }
    ]

def simulate_value_curves(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate value curve mapping"""
    return [
        {
            'fileName': 'value_curves.json',
            'fileSize': 12456,
            'contentPreview': 'Strategic value curve analysis for 7 opportunity zones...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/value_curves.json'
        }
    ]

def simulate_idea_generation(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate product idea generation"""
    return [
        {
            'fileName': 'product_ideas.json',
            'fileSize': 18923,
            'contentPreview': 'Generated 15 innovative product ideas across opportunity zones...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/product_ideas.json'
        }
    ]

def simulate_consolidation(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate idea consolidation"""
    return [
        {
            'fileName': 'final_portfolio.json',
            'fileSize': 25678,
            'contentPreview': 'Consolidated innovation portfolio with 12 prioritized ideas...',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/final_portfolio.json'
        }
    ]

def simulate_github_creation(research_doc_id: str, username: str) -> List[Dict[str, Any]]:
    """Simulate GitHub repository creation"""
    return [
        {
            'fileName': 'github_repo_summary.json',
            'fileSize': 1245,
            'contentPreview': f'GitHub repository created: innovation-{research_doc_id[:8]}',
            's3Location': f's3://pipeline-data/{username}/{research_doc_id}/github_summary.json'
        }
    ]

# Helper functions for DynamoDB updates
def update_job_stage(job_id: str, stage: int, stage_name: str, status: str, progress: float):
    """Update job stage information in DynamoDB"""
    table = dynamodb.Table(JOBS_TABLE)
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET currentStage = :stage, stageName = :stageName, stageProgress = :stageProgress, overallProgress = :overallProgress, #status = :status, updatedAt = :updatedAt',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':stage': stage,
            ':stageName': stage_name,
            ':stageProgress': Decimal(str(progress)),
            ':overallProgress': Decimal(str((stage - 1 + progress / 100) / 7 * 100)),
            ':status': status,
            ':updatedAt': datetime.utcnow().isoformat() + 'Z'
        }
    )

def update_stage_start_time(job_id: str, stage_id: int, start_time: str):
    """Update stage start time"""
    table = dynamodb.Table(JOBS_TABLE)
    # This would need a more complex update for nested stage data
    # For now, we'll track this in the main job record
    pass

def update_stage_completion(job_id: str, stage_id: int, end_time: str, 
                          actual_duration: int, outputs: List[Dict[str, Any]]):
    """Update stage completion details"""
    table = dynamodb.Table(JOBS_TABLE)
    # Complex nested update - would need careful DynamoDB path handling
    pass

def complete_job(job_id: str, research_doc_id: str, username: str):
    """Mark job as completed"""
    table = dynamodb.Table(JOBS_TABLE)
    github_repo_url = f"https://github.com/{username}/innovation-analysis-{research_doc_id[:8]}"
    
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET #status = :status, overallProgress = :progress, completedAt = :completedAt, updatedAt = :updatedAt, results.githubRepoUrl = :githubUrl, results.githubRepoName = :githubName, results.issuesCreated = :issuesCreated',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'COMPLETED',
            ':progress': Decimal('100.0'),
            ':completedAt': datetime.utcnow().isoformat() + 'Z',
            ':updatedAt': datetime.utcnow().isoformat() + 'Z',
            ':githubUrl': github_repo_url,
            ':githubName': f"innovation-analysis-{research_doc_id[:8]}",
            ':issuesCreated': 12
        }
    )

def fail_job(job_id: str, error_message: str):
    """Mark job as failed"""
    table = dynamodb.Table(JOBS_TABLE)
    table.update_item(
        Key={'jobId': job_id},
        UpdateExpression='SET #status = :status, errorMessage = :error, updatedAt = :updatedAt',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'FAILED',
            ':error': error_message,
            ':updatedAt': datetime.utcnow().isoformat() + 'Z'
        }
    )

# ... (include other existing helper functions from original lambda_handler.py)
def check_existing_job(research_doc_id: str, username: str) -> Optional[Dict[str, Any]]:
    """Check if there's an existing running job for this researchDocId."""
    table = dynamodb.Table(JOBS_TABLE)
    
    response = table.scan(
        FilterExpression='researchDocId = :docId AND username = :user AND (#status = :running OR #status = :queued)',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':docId': research_doc_id,
            ':user': username,
            ':running': 'RUNNING',
            ':queued': 'QUEUED'
        }
    )
    
    if response.get('Items'):
        jobs = sorted(response['Items'], key=lambda x: x.get('createdAt', ''), reverse=True)
        return jobs[0]
    
    return None

def handle_existing_job_response(existing_job: Dict[str, Any]) -> Dict[str, Any]:
    """Handle response for existing running job"""
    created_at = datetime.fromisoformat(existing_job['createdAt'].rstrip('Z'))
    elapsed_seconds = (datetime.utcnow() - created_at).total_seconds()
    elapsed_minutes = int(elapsed_seconds / 60)
    estimated_total_minutes = 22
    estimated_remaining_minutes = max(0, estimated_total_minutes - elapsed_minutes)
    
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
            'overallProgress': float(existing_job.get('overallProgress', 0.0)),
            'estimatedTotalMinutes': estimated_total_minutes,
            'elapsedMinutes': elapsed_minutes,
            'estimatedRemainingMinutes': estimated_remaining_minutes,
            'metadata': {
                'researchDocId': existing_job['researchDocId'],
                'startedAt': existing_job['createdAt'],
                'username': existing_job['username']
            }
        }, cls=DecimalEncoder)
    }

def create_job_record(job_id: str, research_doc_id: str, username: str) -> Dict[str, Any]:
    """Create initial job record"""
    now = datetime.utcnow().isoformat() + 'Z'
    
    return {
        'jobId': job_id,
        'researchDocId': research_doc_id,
        'username': username,
        'status': 'QUEUED',
        'currentStage': 0,
        'stageName': 'Initializing',
        'stageProgress': Decimal('0.0'),
        'overallProgress': Decimal('0.0'),
        'estimatedCompletion': (datetime.utcnow() + timedelta(minutes=22)).isoformat() + 'Z',
        'estimatedTotalMinutes': 22,
        'createdAt': now,
        'updatedAt': now,
        'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp()),
        'stages': [
            {'name': 'Research Analysis', 'status': 'PENDING', 'estimatedMinutes': 2},
            {'name': 'JTBD Research', 'status': 'PENDING', 'estimatedMinutes': 3},
            {'name': 'Pain Point Clustering', 'status': 'PENDING', 'estimatedMinutes': 1},
            {'name': 'Value Curve Mapping', 'status': 'PENDING', 'estimatedMinutes': 5},
            {'name': 'Product Idea Generation', 'status': 'PENDING', 'estimatedMinutes': 8},
            {'name': 'Idea Consolidation', 'status': 'PENDING', 'estimatedMinutes': 1},
            {'name': 'GitHub Repository Creation', 'status': 'PENDING', 'estimatedMinutes': 2}
        ],
        'metadata': {
            'researchDocId': research_doc_id,
            'username': username,
            'startedAt': now,
            'totalStages': 7,
            'estimatedTotalMinutes': 22,
            'pipelineVersion': '1.0.0'
        },
        'results': {
            'githubRepoUrl': None,
            'githubRepoName': None,
            'issuesCreated': 0,
            'analysisResults': None,
            'finalPortfolio': None
        }
    }

def get_status_handler(event, context):
    """Handle status requests (unchanged from original)"""
    # ... (original implementation)
    pass

def get_logs_handler(event, context):
    """Handle logs requests (unchanged from original)"""
    # ... (original implementation)
    pass

def handle_cors_preflight(event, context):
    """Handle CORS preflight requests (unchanged from original)"""
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