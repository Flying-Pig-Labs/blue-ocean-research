#!/usr/bin/env python3
"""
Lambda function to map Batch Job IDs to Research IDs

This Lambda provides endpoints to:
1. Get research ID from job ID
2. Get job status and progress
3. List jobs for a research ID

Author: Multi-Step LLM Pipeline Team
Date: January 2025
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('InnovationPipelineJobs')


def decimal_default(obj):
    """Helper to handle Decimal types in JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """
    Main Lambda handler for job mapping and status queries
    
    Endpoints:
    - GET /job/{jobId} - Get job details including research ID
    - GET /job/{jobId}/research - Get just the research ID
    - GET /research/{researchId}/jobs - List jobs for a research
    - GET /status/running - Get all running jobs
    """
    
    # CORS headers for all responses
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        path = event.get('path', '')
        path_params = event.get('pathParameters', {})
        
        # Route: GET /job/{jobId}
        if path.startswith('/job/') and path.count('/') == 2:
            job_id = path_params.get('jobId')
            if not job_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Job ID required'})
                }
            
            # Get job from DynamoDB
            response = table.get_item(Key={'jobId': job_id})
            job = response.get('Item')
            
            if not job:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'Job {job_id} not found'})
                }
            
            # Calculate elapsed time
            if 'startTime' in job:
                start = datetime.fromisoformat(job['startTime'].replace('Z', '+00:00'))
                if 'endTime' in job:
                    end = datetime.fromisoformat(job['endTime'].replace('Z', '+00:00'))
                    elapsed = (end - start).total_seconds() / 60
                else:
                    elapsed = (datetime.utcnow() - start.replace(tzinfo=None)).total_seconds() / 60
                job['elapsedMinutes'] = round(elapsed, 1)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(job, default=decimal_default)
            }
        
        # Route: GET /job/{jobId}/research
        elif path.endswith('/research'):
            job_id = path.split('/')[2] if len(path.split('/')) > 2 else None
            if not job_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Job ID required'})
                }
            
            # Get job from DynamoDB
            response = table.get_item(Key={'jobId': job_id})
            job = response.get('Item')
            
            if not job:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'Job {job_id} not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'jobId': job_id,
                    'researchId': job.get('researchId'),
                    'status': job.get('status'),
                    'progress': job.get('overallProgress', 0)
                }, default=decimal_default)
            }
        
        # Route: GET /research/{researchId}/jobs
        elif path.startswith('/research/') and path.endswith('/jobs'):
            research_id = path.split('/')[2] if len(path.split('/')) > 2 else None
            if not research_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Research ID required'})
                }
            
            # Query jobs by research ID using GSI
            response = table.query(
                IndexName='researchId-startTime-index',
                KeyConditionExpression='researchId = :rid',
                ExpressionAttributeValues={':rid': research_id},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=20
            )
            
            jobs = response.get('Items', [])
            
            # Calculate elapsed times
            for job in jobs:
                if 'startTime' in job:
                    start = datetime.fromisoformat(job['startTime'].replace('Z', '+00:00'))
                    if 'endTime' in job:
                        end = datetime.fromisoformat(job['endTime'].replace('Z', '+00:00'))
                        elapsed = (end - start).total_seconds() / 60
                    else:
                        elapsed = (datetime.utcnow() - start.replace(tzinfo=None)).total_seconds() / 60
                    job['elapsedMinutes'] = round(elapsed, 1)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'researchId': research_id,
                    'jobs': jobs,
                    'count': len(jobs)
                }, default=decimal_default)
            }
        
        # Route: GET /status/running
        elif path == '/status/running':
            # Query running jobs using GSI
            response = table.query(
                IndexName='status-startTime-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'RUNNING'},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=50
            )
            
            jobs = response.get('Items', [])
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'RUNNING',
                    'jobs': jobs,
                    'count': len(jobs)
                }, default=decimal_default)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }