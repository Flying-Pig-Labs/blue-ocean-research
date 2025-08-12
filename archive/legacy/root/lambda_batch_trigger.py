#!/usr/bin/env python3
"""
Lambda function to trigger AWS Batch jobs for the multi-step LLM pipeline
"""

import json
import boto3
import uuid
from datetime import datetime

batch_client = boto3.client('batch')

def lambda_handler(event, context):
    """
    Trigger an AWS Batch job for the multi-step LLM pipeline
    
    Event body can include:
    - input_file: S3 path to input research document (optional)
    - github_repo: Target GitHub repo name (optional)
    - interactive: Whether to run in interactive mode (default: false)
    """
    
    # Parse event
    body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
    
    # Generate job name
    job_name = f"pipeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # Prepare job parameters
    job_params = {
        'jobName': job_name,
        'jobQueue': 'multi-step-llm-queue',
        'jobDefinition': 'multi-step-llm-pipeline'
    }
    
    # Add environment overrides if provided
    environment = []
    
    if 'input_file' in body:
        environment.append({
            'name': 'INPUT_FILE',
            'value': body['input_file']
        })
    
    if 'github_repo' in body:
        environment.append({
            'name': 'GITHUB_REPO',
            'value': body['github_repo']
        })
    
    # Add container overrides if we have environment variables
    if environment:
        job_params['containerOverrides'] = {
            'environment': environment
        }
    
    # Add command override for interactive mode
    if body.get('interactive', False):
        job_params.setdefault('containerOverrides', {})
        job_params['containerOverrides']['command'] = ['--interactive']
    
    try:
        # Submit the job
        response = batch_client.submit_job(**job_params)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Pipeline job submitted successfully',
                'jobId': response['jobId'],
                'jobName': response['jobName'],
                'jobArn': response['jobArn']
            })
        }
        
    except Exception as e:
        print(f"Error submitting job: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to submit pipeline job',
                'message': str(e)
            })
        }

def get_job_status(job_id):
    """
    Get the status of a Batch job
    """
    try:
        response = batch_client.describe_jobs(jobs=[job_id])
        if response['jobs']:
            job = response['jobs'][0]
            return {
                'jobId': job['jobId'],
                'jobName': job['jobName'],
                'status': job['status'],
                'statusReason': job.get('statusReason', ''),
                'startedAt': job.get('startedAt', 0),
                'stoppedAt': job.get('stoppedAt', 0)
            }
        return None
    except Exception as e:
        print(f"Error getting job status: {str(e)}")
        return None