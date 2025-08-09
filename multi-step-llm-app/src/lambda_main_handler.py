#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Main Lambda Handler for Multi-Step LLM Pipeline
Handles API Gateway requests to start pipeline and check status
"""

import json
import os
import uuid
import boto3
from datetime import datetime
import traceback

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')

# Environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'PipelineJobs-production')
S3_BUCKET = os.environ.get('S3_BUCKET')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    """
    Main Lambda handler for API Gateway events
    """
    try:
        # Parse the incoming request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        # CORS headers for all responses
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
        
        # Handle OPTIONS request for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight response'})
            }
        
        # Route based on path and method
        if path == '/start-pipeline' and http_method == 'POST':
            return start_pipeline(event, headers)
        elif path.startswith('/status/') and http_method == 'GET':
            job_id = path.split('/')[-1]
            return get_job_status(job_id, headers)
        elif path.startswith('/logs/') and http_method == 'GET':
            job_id = path.split('/')[-1]
            return get_job_logs(job_id, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def start_pipeline(event, headers):
    """
    Start a new pipeline execution
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Generate unique job ID
        job_id = f"job-{uuid.uuid4()}"
        timestamp = datetime.utcnow().isoformat()
        
        # Extract parameters
        input_data = body.get('input_data', {})
        max_jtbds = body.get('max_jtbds', 20)
        target_ideas = body.get('target_ideas', 12)
        n_zones = body.get('n_zones', 7)
        username = body.get('username', 'anonymous')
        
        # Create job record in DynamoDB
        table = dynamodb.Table(JOBS_TABLE)
        table.put_item(
            Item={
                'jobId': job_id,
                'status': 'INITIALIZING',
                'createdAt': timestamp,
                'updatedAt': timestamp,
                'username': username,
                'currentStage': 0,
                'totalStages': 8,
                'stageProgress': 0,
                'overallProgress': 0,
                'parameters': {
                    'max_jtbds': max_jtbds,
                    'target_ideas': target_ideas,
                    'n_zones': n_zones
                },
                'metadata': input_data,
                'ttl': int((datetime.utcnow().timestamp())) + 2592000  # 30 days
            }
        )
        
        # Upload input data to S3
        s3_key = f"jobs/{job_id}/input/research_data.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(input_data),
            ContentType='application/json'
        )
        
        # Start Step Functions execution
        execution_input = {
            'jobId': job_id,
            'username': username,
            's3Bucket': S3_BUCKET,
            's3InputKey': s3_key,
            'parameters': {
                'max_jtbds': max_jtbds,
                'target_ideas': target_ideas,
                'n_zones': n_zones
            }
        }
        
        sfn_response = sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"pipeline-{job_id}",
            input=json.dumps(execution_input)
        )
        
        # Update job with execution ARN
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET executionArn = :arn, #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':arn': sfn_response['executionArn'],
                ':status': 'RUNNING'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'jobId': job_id,
                'status': 'RUNNING',
                'execution_arn': sfn_response['executionArn'],
                'message': 'Pipeline started successfully'
            })
        }
        
    except Exception as e:
        print(f"Error starting pipeline: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Failed to start pipeline: {str(e)}'})
        }

def get_job_status(job_id, headers):
    """
    Get the status of a pipeline job
    """
    try:
        table = dynamodb.Table(JOBS_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Job not found'})
            }
        
        job = response['Item']
        
        # Check Step Functions execution status if running
        if job.get('executionArn') and job['status'] == 'RUNNING':
            try:
                exec_response = sfn.describe_execution(
                    executionArn=job['executionArn']
                )
                
                # Update status based on Step Functions state
                sf_status = exec_response['status']
                if sf_status == 'SUCCEEDED':
                    job['status'] = 'COMPLETED'
                elif sf_status == 'FAILED':
                    job['status'] = 'FAILED'
                elif sf_status == 'TIMED_OUT':
                    job['status'] = 'TIMEOUT'
                    
            except Exception as e:
                print(f"Error checking Step Functions status: {str(e)}")
        
        # Get output files from S3 if completed
        if job['status'] == 'COMPLETED':
            try:
                prefix = f"jobs/{job_id}/output/"
                s3_response = s3.list_objects_v2(
                    Bucket=S3_BUCKET,
                    Prefix=prefix
                )
                
                if 'Contents' in s3_response:
                    job['outputs'] = [
                        {
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'lastModified': obj['LastModified'].isoformat()
                        }
                        for obj in s3_response['Contents']
                    ]
            except Exception as e:
                print(f"Error listing S3 outputs: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(job, default=str)
        }
        
    except Exception as e:
        print(f"Error getting job status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Failed to get job status: {str(e)}'})
        }

def get_job_logs(job_id, headers):
    """
    Get logs for a pipeline job
    """
    try:
        # Get job record
        table = dynamodb.Table(JOBS_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Job not found'})
            }
        
        job = response['Item']
        
        # Get execution history from Step Functions
        logs = []
        if job.get('executionArn'):
            try:
                history = sfn.get_execution_history(
                    executionArn=job['executionArn'],
                    maxResults=100
                )
                
                for event in history.get('events', []):
                    if event['type'] in ['TaskStateEntered', 'TaskStateExited', 'TaskFailed']:
                        logs.append({
                            'timestamp': event['timestamp'].isoformat(),
                            'type': event['type'],
                            'details': event.get('stateEnteredEventDetails', 
                                                event.get('stateExitedEventDetails', 
                                                        event.get('taskFailedEventDetails', {})))
                        })
                        
            except Exception as e:
                print(f"Error getting Step Functions history: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'jobId': job_id,
                'status': job['status'],
                'logs': logs
            }, default=str)
        }
        
    except Exception as e:
        print(f"Error getting job logs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Failed to get job logs: {str(e)}'})
        }