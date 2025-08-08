#!/usr/bin/env python3
"""
AWS Batch Wrapper for Multi-Step LLM Pipeline

This wrapper script enables the pipeline to run in AWS Batch by handling:
1. S3 input/output operations
2. DynamoDB job status tracking
3. Pipeline invocation with proper parameters
4. Result aggregation and upload

Critical Design Decision:
The wrapper calls run_pipeline.py WITHOUT modifications, maintaining
the integrity of the original script. All cloud-specific logic is
contained in this wrapper.

Environment Variables Expected:
- S3_INPUT_KEY: S3 key of input research file
- RESEARCH_ID: Unique identifier for this research
- JOB_ID: Batch job ID for status tracking
- RESEARCH_BUCKET: S3 bucket for outputs
- RESEARCH_TABLE: DynamoDB table for research data
- JOBS_TABLE: DynamoDB table for job tracking

Author: Multi-Step LLM Pipeline Team
Date: December 2024
"""

import os
import sys
import json
import boto3
import argparse
from datetime import datetime, timedelta
import subprocess
import traceback
from typing import Optional

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def download_from_s3(s3_path: str, local_path: str) -> str:
    """
    Download a file from S3 to local storage.
    
    Args:
        s3_path: S3 path (can be s3://bucket/key or bucket/key format)
        local_path: Local file path to save the downloaded file
    
    Returns:
        str: Local path where file was saved
    
    Raises:
        botocore.exceptions.ClientError: If S3 download fails
    """
    if s3_path.startswith('s3://'):
        s3_path = s3_path[5:]
    
    parts = s3_path.split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ''
    
    print(f"Downloading from S3: {bucket}/{key} to {local_path}")
    s3_client.download_file(bucket, key, local_path)
    return local_path

def upload_to_s3(local_path: str, s3_bucket: str, s3_key: str) -> str:
    """
    Upload a local file to S3.
    
    Args:
        local_path: Path to local file to upload
        s3_bucket: S3 bucket name
        s3_key: S3 key (path) for the uploaded file
    
    Returns:
        str: Full S3 URI of uploaded file (s3://bucket/key)
    
    Raises:
        botocore.exceptions.ClientError: If S3 upload fails
    """
    print(f"Uploading to S3: {local_path} to {s3_bucket}/{s3_key}")
    s3_client.upload_file(local_path, s3_bucket, s3_key)
    return f"s3://{s3_bucket}/{s3_key}"

def update_job_status(job_id: str, status: str, message: Optional[str] = None) -> None:
    """
    Update job status in DynamoDB tracking table.
    
    Args:
        job_id: Unique job identifier
        status: Job status (RUNNING, SUCCEEDED, FAILED)
        message: Optional status message or error details
    
    Note:
        Silently continues if JOBS_TABLE environment variable not set.
        This allows local testing without DynamoDB.
    """
    jobs_table_name = os.environ.get('JOBS_TABLE')
    if not jobs_table_name:
        print(f"Warning: JOBS_TABLE not set, skipping status update")
        return
    
    try:
        table = dynamodb.Table(jobs_table_name)
        update_expr = "SET #s = :status, updatedAt = :updated"
        expr_values = {
            ':status': status,
            ':updated': datetime.now().isoformat()
        }
        expr_names = {'#s': 'status'}
        
        if message:
            update_expr += ", message = :message"
            expr_values[':message'] = message
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        print(f"Updated job {job_id} status to {status}")
    except Exception as e:
        print(f"Error updating job status: {str(e)}")

def main() -> None:
    """
    Main entry point for AWS Batch execution.
    
    Workflow:
    1. Parse arguments and environment variables
    2. Update job status to RUNNING
    3. Download input from S3 if provided
    4. Execute run_pipeline.py with appropriate flags
    5. Upload results to S3
    6. Update job status to SUCCEEDED or FAILED
    
    Exit Codes:
        0: Success
        1: Pipeline execution failed
    """
    parser = argparse.ArgumentParser(description='AWS Batch wrapper for Multi-Step LLM Pipeline')
    parser.add_argument('--s3-input', type=str, help='S3 path to input research file')
    parser.add_argument('--research-id', type=str, help='Research ID')
    parser.add_argument('--job-id', type=str, help='Job ID')
    args, unknown = parser.parse_known_args()
    
    # Get environment variables
    research_id = args.research_id or os.environ.get('RESEARCH_ID')
    job_id = args.job_id or os.environ.get('JOB_ID', 'unknown')
    s3_input = args.s3_input or os.environ.get('S3_INPUT_KEY')
    
    print(f"Starting pipeline for Research ID: {research_id}, Job ID: {job_id}")
    
    try:
        # Update status to RUNNING
        update_job_status(job_id, 'RUNNING', 'Pipeline started')
        
        # Download input from S3 if provided
        local_input = None
        if s3_input:
            # Use .md extension since we're downloading markdown directly
            local_input = '/tmp/research_input.md'
            download_from_s3(s3_input, local_input)
            print(f"Downloaded input to {local_input}")
        
        # Build command for pipeline
        cmd = ['python', 'run_pipeline.py']
        
        # Add input file if we downloaded one
        if local_input:
            cmd.extend(['--input', local_input])
        
        # Pass through any other arguments
        cmd.extend(unknown)
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run the pipeline
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            raise Exception(f"Pipeline failed with exit code {result.returncode}")
        
        # Upload results to S3
        output_bucket = os.environ.get('RESEARCH_BUCKET')
        if output_bucket and research_id:
            # Upload key output files
            output_files = [
                'analysis_results.md',
                'opportunity_zones.json',
                'product_ideas.json',
                'final_innovation_portfolio.json',
                'final_innovation_portfolio_summary.md'
            ]
            
            for filename in output_files:
                if os.path.exists(filename):
                    s3_key = f"outputs/{research_id}/{filename}"
                    upload_to_s3(filename, output_bucket, s3_key)
                    print(f"Uploaded {filename} to s3://{output_bucket}/{s3_key}")
            
            # Also upload any JTBD and Reddit files (with timestamps)
            import glob
            for pattern in ['jtbds_*.txt', 'reddit_discussions_*.csv']:
                for filepath in glob.glob(pattern):
                    s3_key = f"outputs/{research_id}/{os.path.basename(filepath)}"
                    upload_to_s3(filepath, output_bucket, s3_key)
                    print(f"Uploaded {filepath} to s3://{output_bucket}/{s3_key}")
        
        # Update status to SUCCEEDED
        update_job_status(job_id, 'SUCCEEDED', 'Pipeline completed successfully')
        print("Pipeline completed successfully!")
        
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        update_job_status(job_id, 'FAILED', error_msg[:1000])  # DynamoDB has attribute size limits
        sys.exit(1)

if __name__ == "__main__":
    main()