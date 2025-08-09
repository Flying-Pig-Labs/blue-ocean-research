#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Pipeline Job Tracker for DynamoDB

This module handles all interactions with the InnovationPipelineJobs DynamoDB table,
tracking AWS Batch jobs and mapping them to research IDs for the frontend.

Author: Multi-Step LLM Pipeline Team
Date: January 2025
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from decimal import Decimal
import os

# Initialize DynamoDB client and resource
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb_resource.Table('InnovationPipelineJobs')


def decimal_default(obj):
    """Helper to handle Decimal types in JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


class PipelineJobTracker:
    """Manages job tracking in DynamoDB for the Innovation Pipeline"""
    
    def __init__(self, table_name: str = 'InnovationPipelineJobs'):
        """Initialize the job tracker with DynamoDB table"""
        self.table = dynamodb_resource.Table(table_name)
    
    def create_job(self, job_id: str, research_id: str, username: str = None, 
                   job_name: str = None) -> Dict[str, Any]:
        """
        Create a new job record when pipeline starts
        
        Args:
            job_id: AWS Batch job ID
            research_id: Research report ID from frontend
            username: User who started the job
            job_name: AWS Batch job name
            
        Returns:
            The created job record
        """
        now = datetime.utcnow().isoformat() + 'Z'
        
        item = {
            'jobId': job_id,
            'researchId': research_id,
            'startTime': now,
            'lastUpdated': now,
            'status': 'SUBMITTED',
            'overallProgress': 0
        }
        
        if username:
            item['username'] = username
        if job_name:
            item['jobName'] = job_name
            
        self.table.put_item(Item=item)
        print(f"Created job tracking record: {job_id} -> {research_id}")
        return item
    
    def update_job_status(self, job_id: str, status: str, current_stage: str = None,
                         progress: int = None, error: str = None) -> None:
        """
        Update job status and progress
        
        Args:
            job_id: AWS Batch job ID
            status: New status (PENDING, RUNNING, SUCCEEDED, FAILED, etc.)
            current_stage: Current processing stage name
            progress: Overall progress percentage (0-100)
            error: Error message if failed
        """
        update_expr_parts = ['#status = :status', 'lastUpdated = :updated']
        expr_attrs = {'#status': 'status'}
        expr_values = {
            ':status': status,
            ':updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        if current_stage is not None:
            update_expr_parts.append('currentStage = :stage')
            expr_values[':stage'] = current_stage
            
        if progress is not None:
            update_expr_parts.append('overallProgress = :progress')
            expr_values[':progress'] = progress
            
        if error:
            update_expr_parts.append('error = :error')
            expr_values[':error'] = error
            
        # Set endTime if job is complete
        if status in ['SUCCEEDED', 'FAILED']:
            update_expr_parts.append('endTime = :endTime')
            expr_values[':endTime'] = datetime.utcnow().isoformat() + 'Z'
            
            # Set TTL to 30 days from completion
            ttl_time = int((datetime.utcnow() + timedelta(days=30)).timestamp())
            update_expr_parts.append('ttl = :ttl')
            expr_values[':ttl'] = ttl_time
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET ' + ', '.join(update_expr_parts),
            ExpressionAttributeNames=expr_attrs,
            ExpressionAttributeValues=expr_values
        )
        print(f"Updated job {job_id}: status={status}, stage={current_stage}, progress={progress}")
    
    def update_job_results(self, job_id: str, github_repo_url: str = None,
                          github_repo_name: str = None, issues_created: int = None) -> None:
        """
        Update job with final results
        
        Args:
            job_id: AWS Batch job ID
            github_repo_url: URL of created GitHub repository
            github_repo_name: Name of created repository
            issues_created: Number of issues created
        """
        update_expr_parts = ['lastUpdated = :updated']
        expr_values = {':updated': datetime.utcnow().isoformat() + 'Z'}
        
        if github_repo_url:
            update_expr_parts.append('githubRepoUrl = :repo_url')
            expr_values[':repo_url'] = github_repo_url
            
        if github_repo_name:
            update_expr_parts.append('githubRepoName = :repo_name')
            expr_values[':repo_name'] = github_repo_name
            
        if issues_created is not None:
            update_expr_parts.append('issuesCreated = :issues')
            expr_values[':issues'] = issues_created
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET ' + ', '.join(update_expr_parts),
            ExpressionAttributeValues=expr_values
        )
        print(f"Updated job {job_id} with results: repo={github_repo_url}")
    
    def update_batch_metadata(self, job_id: str, batch_job_arn: str = None,
                            log_stream_name: str = None, log_group_name: str = None) -> None:
        """
        Update job with AWS Batch metadata
        
        Args:
            job_id: AWS Batch job ID
            batch_job_arn: AWS Batch job ARN
            log_stream_name: CloudWatch log stream name
            log_group_name: CloudWatch log group name
        """
        update_expr_parts = ['lastUpdated = :updated']
        expr_values = {':updated': datetime.utcnow().isoformat() + 'Z'}
        
        if batch_job_arn:
            update_expr_parts.append('batchJobArn = :arn')
            expr_values[':arn'] = batch_job_arn
            
        if log_stream_name:
            update_expr_parts.append('logStreamName = :stream')
            expr_values[':stream'] = log_stream_name
            
        if log_group_name:
            update_expr_parts.append('logGroupName = :group')
            expr_values[':group'] = log_group_name
        
        self.table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET ' + ', '.join(update_expr_parts),
            ExpressionAttributeValues=expr_values
        )
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID
        
        Args:
            job_id: AWS Batch job ID
            
        Returns:
            Job record or None if not found
        """
        try:
            response = self.table.get_item(Key={'jobId': job_id})
            item = response.get('Item')
            
            # Calculate elapsed time if job is running
            if item and 'startTime' in item:
                start = datetime.fromisoformat(item['startTime'].replace('Z', '+00:00'))
                if 'endTime' in item:
                    end = datetime.fromisoformat(item['endTime'].replace('Z', '+00:00'))
                    elapsed = (end - start).total_seconds() / 60
                else:
                    elapsed = (datetime.utcnow() - start.replace(tzinfo=None)).total_seconds() / 60
                item['elapsedMinutes'] = round(elapsed, 1)
            
            return item
        except Exception as e:
            print(f"Error getting job {job_id}: {e}")
            return None
    
    def get_job_research_id(self, job_id: str) -> Optional[str]:
        """
        Get research ID for a given job ID (key mapping function)
        
        Args:
            job_id: AWS Batch job ID
            
        Returns:
            Research ID or None if not found
        """
        job = self.get_job(job_id)
        return job.get('researchId') if job else None
    
    def get_jobs_by_research(self, research_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific research ID
        
        Args:
            research_id: Research report ID
            limit: Maximum number of jobs to return
            
        Returns:
            List of job records sorted by start time (newest first)
        """
        try:
            response = self.table.query(
                IndexName='researchId-startTime-index',
                KeyConditionExpression='researchId = :rid',
                ExpressionAttributeValues={':rid': research_id},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # Calculate elapsed times
            for item in items:
                if 'startTime' in item:
                    start = datetime.fromisoformat(item['startTime'].replace('Z', '+00:00'))
                    if 'endTime' in item:
                        end = datetime.fromisoformat(item['endTime'].replace('Z', '+00:00'))
                        elapsed = (end - start).total_seconds() / 60
                    else:
                        elapsed = (datetime.utcnow() - start.replace(tzinfo=None)).total_seconds() / 60
                    item['elapsedMinutes'] = round(elapsed, 1)
            
            return items
        except Exception as e:
            print(f"Error getting jobs for research {research_id}: {e}")
            return []
    
    def get_jobs_by_status(self, status: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all jobs with a specific status
        
        Args:
            status: Job status (RUNNING, SUCCEEDED, FAILED, etc.)
            limit: Maximum number of jobs to return
            
        Returns:
            List of job records sorted by start time (newest first)
        """
        try:
            response = self.table.query(
                IndexName='status-startTime-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting jobs by status {status}: {e}")
            return []
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Get all currently running jobs"""
        return self.get_jobs_by_status('RUNNING')
    
    def get_recent_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent jobs across all statuses
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of recent job records
        """
        try:
            # Since we can't sort a scan, we'll get recent from each status
            # and merge them
            statuses = ['RUNNING', 'SUCCEEDED', 'FAILED', 'SUBMITTED', 'PENDING']
            all_jobs = []
            
            for status in statuses:
                jobs = self.get_jobs_by_status(status, limit=10)
                all_jobs.extend(jobs)
            
            # Sort by startTime descending
            all_jobs.sort(key=lambda x: x.get('startTime', ''), reverse=True)
            
            return all_jobs[:limit]
        except Exception as e:
            print(f"Error getting recent jobs: {e}")
            return []


# Stage progress mapping for the pipeline
STAGE_PROGRESS_MAP = {
    'Starting pipeline': 0,
    'Stage 1: Research Analysis': 10,
    'Stage 2: JTBD Extraction': 25,
    'Stage 3: Opportunity Zones': 40,
    'Stage 4: Product Ideas': 60,
    'Stage 5: Consolidation': 75,
    'Stage 6: GitHub Integration': 90,
    'Pipeline complete': 100
}


def get_progress_for_stage(stage_name: str) -> int:
    """
    Get progress percentage for a given stage
    
    Args:
        stage_name: Name of the pipeline stage
        
    Returns:
        Progress percentage (0-100)
    """
    # Try exact match first
    if stage_name in STAGE_PROGRESS_MAP:
        return STAGE_PROGRESS_MAP[stage_name]
    
    # Try partial match
    for key, value in STAGE_PROGRESS_MAP.items():
        if key.lower() in stage_name.lower() or stage_name.lower() in key.lower():
            return value
    
    # Default to 0 if no match
    return 0


# Example usage and testing
if __name__ == "__main__":
    tracker = PipelineJobTracker()
    
    # Test creating a job
    test_job_id = f"test-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    test_research_id = "test-research-001"
    
    print("Creating test job...")
    job = tracker.create_job(
        job_id=test_job_id,
        research_id=test_research_id,
        username="test-user",
        job_name="Test Pipeline Run"
    )
    print(f"Created: {json.dumps(job, indent=2, default=decimal_default)}")
    
    # Test updating status
    print("\nUpdating job status...")
    tracker.update_job_status(
        job_id=test_job_id,
        status='RUNNING',
        current_stage='Stage 1: Research Analysis',
        progress=10
    )
    
    # Test getting job
    print("\nRetrieving job...")
    retrieved = tracker.get_job(test_job_id)
    print(f"Retrieved: {json.dumps(retrieved, indent=2, default=decimal_default)}")
    
    # Test getting research ID
    print("\nGetting research ID from job ID...")
    research_id = tracker.get_job_research_id(test_job_id)
    print(f"Research ID: {research_id}")
    
    # Clean up - mark as completed
    print("\nMarking job as completed...")
    tracker.update_job_status(
        job_id=test_job_id,
        status='SUCCEEDED',
        current_stage='Pipeline complete',
        progress=100
    )
    tracker.update_job_results(
        job_id=test_job_id,
        github_repo_url='https://github.com/test/repo',
        github_repo_name='test-repo',
        issues_created=10
    )
    
    print("\nTest complete!")