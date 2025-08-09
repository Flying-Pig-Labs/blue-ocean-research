#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Step Functions API handlers for pipeline orchestration.
Provides REST endpoints for starting, monitoring, and resuming pipeline executions.
"""

import json
import os
import uuid
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

# Environment variables
STEP_FUNCTION_ARN = os.environ.get('STEP_FUNCTION_ARN')
CHECKPOINT_TABLE = os.environ.get('CHECKPOINT_TABLE')

def create_cors_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized CORS-enabled API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }

def start_pipeline_handler(event, context):
    """
    Start a new pipeline execution via Step Functions.
    
    Request body:
    {
        "input": {
            "researchData": "...",
            "createGitHubRepo": true,
            "repoVisibility": "public",
            "customConfig": {}
        },
        "name": "optional-execution-name"
    }
    """
    try:
        logger.info(f"Starting pipeline execution: {json.dumps(event)}")
        
        # Parse request body
        if 'body' not in event:
            return create_cors_response(400, {'error': 'Missing request body'})
        
        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            return create_cors_response(400, {'error': 'Invalid JSON in request body'})
        
        # Extract input data
        pipeline_input = request_body.get('input', {})
        execution_name = request_body.get('name')
        
        # Generate execution name if not provided
        if not execution_name:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            execution_name = f"pipeline-{timestamp}-{str(uuid.uuid4())[:8]}"
        
        # Validate required Step Function ARN
        if not STEP_FUNCTION_ARN:
            return create_cors_response(500, {
                'error': 'Step Function ARN not configured',
                'details': 'STEP_FUNCTION_ARN environment variable is missing'
            })
        
        # Add execution metadata to input
        enhanced_input = {
            **pipeline_input,
            'executionMetadata': {
                'requestId': context.aws_request_id if context else str(uuid.uuid4()),
                'startTime': datetime.now(timezone.utc).isoformat(),
                'apiVersion': '2.0',
                'source': 'api-gateway'
            }
        }
        
        # Start Step Function execution
        response = stepfunctions.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            name=execution_name,
            input=json.dumps(enhanced_input)
        )
        
        logger.info(f"Started execution: {response['executionArn']}")
        
        # Return execution details
        return create_cors_response(200, {
            'success': True,
            'executionArn': response['executionArn'],
            'executionName': execution_name,
            'startDate': response['startDate'].isoformat(),
            'status': 'RUNNING',
            'message': 'Pipeline execution started successfully',
            'estimatedDuration': '15-20 minutes',
            'stages': 7,
            'monitoringEndpoint': f"/pipeline/status/{response['executionArn'].split(':')[-1]}"
        })
        
    except stepfunctions.exceptions.ExecutionLimitExceeded:
        return create_cors_response(429, {
            'error': 'Execution limit exceeded',
            'message': 'Too many concurrent executions. Please wait and try again.',
            'retryAfter': 300
        })
        
    except stepfunctions.exceptions.InvalidArn:
        return create_cors_response(500, {
            'error': 'Invalid Step Function ARN',
            'details': 'The configured Step Function ARN is invalid'
        })
        
    except stepfunctions.exceptions.StateMachineDoesNotExist:
        return create_cors_response(500, {
            'error': 'Step Function not found',
            'details': 'The specified Step Function does not exist'
        })
        
    except Exception as e:
        logger.error(f"Error starting pipeline: {str(e)}")
        return create_cors_response(500, {
            'error': 'Failed to start pipeline execution',
            'details': str(e)
        })

def get_status_handler(event, context):
    """
    Get the status of a pipeline execution.
    
    Path parameter: executionArn (URL encoded)
    """
    try:
        logger.info(f"Getting pipeline status: {json.dumps(event)}")
        
        # Extract execution ARN from path parameters
        path_parameters = event.get('pathParameters', {})
        execution_arn_part = path_parameters.get('executionArn')
        
        if not execution_arn_part:
            return create_cors_response(400, {
                'error': 'Missing execution ARN',
                'message': 'Execution ARN must be provided as a path parameter'
            })
        
        # Reconstruct full execution ARN
        # Handle both full ARN and just the execution name
        if execution_arn_part.startswith('arn:aws:states:'):
            execution_arn = execution_arn_part
        else:
            # Construct ARN from execution name
            if not STEP_FUNCTION_ARN:
                return create_cors_response(500, {
                    'error': 'Step Function ARN not configured'
                })
            
            # Extract region and account from state machine ARN
            state_machine_parts = STEP_FUNCTION_ARN.split(':')
            region = state_machine_parts[3]
            account = state_machine_parts[4]
            
            execution_arn = f"arn:aws:states:{region}:{account}:execution:{STEP_FUNCTION_ARN.split(':')[-1]}:{execution_arn_part}"
        
        # Get execution details
        response = stepfunctions.describe_execution(
            executionArn=execution_arn
        )
        
        # Parse output if execution is completed
        output_data = None
        if response['status'] in ['SUCCEEDED', 'FAILED'] and response.get('output'):
            try:
                output_data = json.loads(response['output'])
            except json.JSONDecodeError:
                output_data = {'rawOutput': response['output']}
        
        # Get execution history for stage progress
        history_response = stepfunctions.get_execution_history(
            executionArn=execution_arn,
            maxResults=50,
            reverseOrder=True
        )
        
        # Analyze stage progress from execution history
        stage_progress = analyze_execution_progress(history_response.get('events', []))
        
        # Calculate duration
        duration_seconds = None
        if response.get('stopDate'):
            duration = response['stopDate'] - response['startDate']
            duration_seconds = duration.total_seconds()
        
        return create_cors_response(200, {
            'executionArn': execution_arn,
            'name': response['name'],
            'status': response['status'],
            'startDate': response['startDate'].isoformat(),
            'stopDate': response.get('stopDate').isoformat() if response.get('stopDate') else None,
            'durationSeconds': duration_seconds,
            'input': json.loads(response['input']),
            'output': output_data,
            'stageProgress': stage_progress,
            'currentStage': get_current_stage(stage_progress),
            'estimatedTimeRemaining': estimate_time_remaining(stage_progress),
            'lastUpdated': datetime.now(timezone.utc).isoformat()
        })
        
    except stepfunctions.exceptions.ExecutionDoesNotExist:
        return create_cors_response(404, {
            'error': 'Execution not found',
            'message': 'The specified pipeline execution does not exist'
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        return create_cors_response(500, {
            'error': 'Failed to get pipeline status',
            'details': str(e)
        })

def resume_pipeline_handler(event, context):
    """
    Resume a failed pipeline execution from a checkpoint.
    
    Request body:
    {
        "executionId": "original-execution-id",
        "resumeFromStage": 3,
        "newExecutionName": "optional-new-name"
    }
    """
    try:
        logger.info(f"Resuming pipeline execution: {json.dumps(event)}")
        
        # Parse request body
        if 'body' not in event:
            return create_cors_response(400, {'error': 'Missing request body'})
        
        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            return create_cors_response(400, {'error': 'Invalid JSON in request body'})
        
        execution_id = request_body.get('executionId')
        resume_stage = request_body.get('resumeFromStage')
        new_execution_name = request_body.get('newExecutionName')
        
        # Validate required parameters
        if not execution_id or not resume_stage:
            return create_cors_response(400, {
                'error': 'Missing required parameters',
                'message': 'executionId and resumeFromStage are required'
            })
        
        if resume_stage < 1 or resume_stage > 7:
            return create_cors_response(400, {
                'error': 'Invalid resume stage',
                'message': 'resumeFromStage must be between 1 and 7'
            })
        
        # Validate checkpoint table configuration
        if not CHECKPOINT_TABLE:
            return create_cors_response(500, {
                'error': 'Checkpoint table not configured'
            })
        
        # Retrieve checkpoint data
        checkpoint_data = get_checkpoint_data(execution_id, resume_stage - 1)
        if not checkpoint_data:
            return create_cors_response(404, {
                'error': 'Checkpoint not found',
                'message': f'No checkpoint found for execution {execution_id} at stage {resume_stage - 1}'
            })
        
        # Generate new execution name
        if not new_execution_name:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            new_execution_name = f"pipeline-resume-{timestamp}-{str(uuid.uuid4())[:8]}"
        
        # Prepare resume input
        resume_input = {
            'resumeFromStage': resume_stage,
            'checkpointData': checkpoint_data,
            'originalExecutionId': execution_id,
            'executionMetadata': {
                'requestId': context.aws_request_id if context else str(uuid.uuid4()),
                'startTime': datetime.now(timezone.utc).isoformat(),
                'apiVersion': '2.0',
                'source': 'api-gateway-resume',
                'resumedFromStage': resume_stage
            }
        }
        
        # Start new execution
        response = stepfunctions.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            name=new_execution_name,
            input=json.dumps(resume_input)
        )
        
        logger.info(f"Resumed execution: {response['executionArn']}")
        
        return create_cors_response(200, {
            'success': True,
            'executionArn': response['executionArn'],
            'executionName': new_execution_name,
            'startDate': response['startDate'].isoformat(),
            'status': 'RUNNING',
            'resumedFromStage': resume_stage,
            'originalExecutionId': execution_id,
            'message': f'Pipeline execution resumed from stage {resume_stage}',
            'estimatedDuration': calculate_remaining_duration(resume_stage)
        })
        
    except Exception as e:
        logger.error(f"Error resuming pipeline: {str(e)}")
        return create_cors_response(500, {
            'error': 'Failed to resume pipeline execution',
            'details': str(e)
        })

def analyze_execution_progress(events: list) -> Dict[str, Any]:
    """Analyze Step Function execution events to determine stage progress."""
    stage_info = {
        'Stage1_ResearchAnalysis': {'stage': 1, 'name': 'Research Analysis'},
        'Stage2_JTBDResearch': {'stage': 2, 'name': 'JTBD Research'},
        'Stage3_Clustering': {'stage': 3, 'name': 'JTBD Clustering'},
        'Stage4_ValueCurveMapping': {'stage': 4, 'name': 'Value Curve Mapping'},
        'Stage5_ProductIdeaGeneration': {'stage': 5, 'name': 'Product Idea Generation'},
        'Stage6_IdeaConsolidation': {'stage': 6, 'name': 'Idea Consolidation'},
        'Stage7_GitHubIntegration': {'stage': 7, 'name': 'GitHub Integration'}
    }
    
    progress = {
        'completedStages': [],
        'currentStage': None,
        'failedStage': None,
        'totalStages': 7
    }
    
    for event in reversed(events):  # Process in chronological order
        event_type = event.get('type')
        state_name = event.get('stateEnteredEventDetails', {}).get('name') or \
                    event.get('stateExitedEventDetails', {}).get('name')
        
        if state_name in stage_info:
            stage = stage_info[state_name]
            
            if event_type == 'TaskStateEntered':
                progress['currentStage'] = {
                    'stage': stage['stage'],
                    'name': stage['name'],
                    'startTime': event['timestamp'].isoformat()
                }
            elif event_type == 'TaskStateSucceeded':
                progress['completedStages'].append({
                    'stage': stage['stage'],
                    'name': stage['name'],
                    'completedAt': event['timestamp'].isoformat()
                })
                progress['currentStage'] = None
            elif event_type == 'TaskStateFailed':
                progress['failedStage'] = {
                    'stage': stage['stage'],
                    'name': stage['name'],
                    'failedAt': event['timestamp'].isoformat(),
                    'error': event.get('taskStateFailedEventDetails', {}).get('error', 'Unknown error')
                }
                break
    
    return progress

def get_current_stage(progress: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get the current stage information from progress data."""
    if progress.get('failedStage'):
        return progress['failedStage']
    elif progress.get('currentStage'):
        return progress['currentStage']
    elif progress.get('completedStages'):
        # All stages completed
        return {
            'stage': 'completed',
            'name': 'Pipeline Completed',
            'status': 'SUCCESS'
        }
    else:
        # Not started yet
        return {
            'stage': 1,
            'name': 'Research Analysis',
            'status': 'PENDING'
        }

def estimate_time_remaining(progress: Dict[str, Any]) -> Optional[str]:
    """Estimate remaining execution time based on current progress."""
    # Average stage durations in minutes
    stage_durations = {
        1: 2,   # Research Analysis
        2: 3,   # JTBD Research
        3: 4,   # Clustering
        4: 6,   # Value Curve Mapping
        5: 8,   # Product Idea Generation
        6: 3,   # Idea Consolidation
        7: 2    # GitHub Integration
    }
    
    completed_stages = len(progress.get('completedStages', []))
    current_stage = progress.get('currentStage', {}).get('stage')
    
    if completed_stages == 7:
        return "0 minutes"
    
    remaining_time = 0
    for stage in range(completed_stages + 1, 8):
        if stage == current_stage:
            # Assume half time remaining for current stage
            remaining_time += stage_durations.get(stage, 3) / 2
        else:
            remaining_time += stage_durations.get(stage, 3)
    
    return f"{int(remaining_time)}-{int(remaining_time * 1.5)} minutes"

def get_checkpoint_data(execution_id: str, stage: int) -> Optional[Dict[str, Any]]:
    """Retrieve checkpoint data from DynamoDB."""
    try:
        table = dynamodb.Table(CHECKPOINT_TABLE)
        response = table.get_item(
            Key={
                'executionId': execution_id,
                'stage': stage
            }
        )
        
        if 'Item' in response:
            checkpoint = response['Item']
            # Parse JSON strings back to objects
            for key in ['output', 'clusters', 'valueCurves', 'productIdeas', 'consolidatedPortfolio']:
                if key in checkpoint and isinstance(checkpoint[key], str):
                    try:
                        checkpoint[key] = json.loads(checkpoint[key])
                    except json.JSONDecodeError:
                        pass
            return checkpoint
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving checkpoint: {str(e)}")
        return None

def calculate_remaining_duration(resume_stage: int) -> str:
    """Calculate estimated duration for remaining stages."""
    stage_durations = {1: 2, 2: 3, 3: 4, 4: 6, 5: 8, 6: 3, 7: 2}
    
    remaining_time = sum(stage_durations.get(stage, 3) for stage in range(resume_stage, 8))
    return f"{remaining_time}-{int(remaining_time * 1.5)} minutes"

# Handle CORS preflight requests
def handle_cors_preflight(event, context):
    """Handle CORS preflight OPTIONS requests."""
    return create_cors_response(200, {
        'message': 'CORS preflight successful'
    })