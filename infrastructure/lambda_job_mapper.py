#!/usr/bin/env python3
"""
Lambda Job Mapper - AWS Batch Job Tracking and Mapping Service

Purpose: Provides RESTful API endpoints for tracking AWS Batch jobs and mapping them
         to research IDs, enabling the frontend to monitor pipeline execution progress.

This Lambda function serves as the bridge between the frontend application and the
AWS Batch job execution system. It maintains the relationship between research IDs
(from the frontend) and AWS Batch job IDs, providing real-time status updates.

Key Responsibilities:
1. Map AWS Batch job IDs to research document IDs
2. Provide real-time job status and progress information
3. List all jobs associated with a research document
4. Track running jobs across the system
5. Calculate elapsed time and estimated completion

API Endpoints:
- GET /job/{jobId} - Get complete job details including research ID
- GET /job/{jobId}/research - Get just the research ID for a job
- GET /research/{researchId}/jobs - List all jobs for a research
- GET /status/running - Get all currently running jobs

DynamoDB Table: InnovationPipelineJobs
Schema:
  - jobId (PK): AWS Batch job ID
  - researchId: Associated research document ID
  - status: PENDING|RUNNING|SUCCEEDED|FAILED
  - overallProgress: 0-100 percentage
  - currentStage: Current pipeline stage (1-7)
  - startTime: ISO timestamp
  - endTime: ISO timestamp (when complete)
  - s3OutputPath: Location of results

Integration:
- Called by: Frontend React application
- Calls: DynamoDB for job data
- Related: lambda_pipeline_status.py for detailed progress

Author: Multi-Step LLM Pipeline Team
Date: January 2025
Runtime: Python 3.11
Timeout: 30 seconds
Memory: 256 MB
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("InnovationPipelineJobs")


def decimal_default(obj):
    """Helper to handle Decimal types in JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """
    Main Lambda handler for job mapping and status queries.

    Routes API Gateway requests to appropriate handlers based on path.
    All responses include CORS headers for frontend compatibility.

    Args:
        event: API Gateway event containing:
            - path: Request path
            - pathParameters: URL path parameters
            - httpMethod: HTTP method (GET/OPTIONS)
            - headers: Request headers
        context: Lambda context (request ID, remaining time, etc.)

    Returns:
        Dict with:
            - statusCode: HTTP status code
            - headers: Response headers including CORS
            - body: JSON response body

    Error Handling:
        - 400: Missing required parameters
        - 404: Job or research not found
        - 500: Internal server error
    """

    # CORS headers for all responses - Critical for frontend integration
    # Allow all origins (*) for development, restrict in production
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # TODO: Restrict to frontend domain
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }

    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        path = event.get("path", "")
        path_params = event.get("pathParameters", {})

        # Route: GET /job/{jobId} - Get complete job details
        # Returns all job metadata including progress, timing, and output location
        if path.startswith("/job/") and path.count("/") == 2:
            job_id = path_params.get("jobId")
            if not job_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Job ID required"}),
                }

            # Get job from DynamoDB
            response = table.get_item(Key={"jobId": job_id})
            job = response.get("Item")

            if not job:
                return {
                    "statusCode": 404,
                    "headers": headers,
                    "body": json.dumps({"error": f"Job {job_id} not found"}),
                }

            # Calculate elapsed time for active monitoring
            # Shows how long job has been running or total runtime if complete
            if "startTime" in job:
                start = datetime.fromisoformat(job["startTime"].replace("Z", "+00:00"))
                if "endTime" in job:
                    end = datetime.fromisoformat(job["endTime"].replace("Z", "+00:00"))
                    elapsed = (end - start).total_seconds() / 60
                else:
                    elapsed = (
                        datetime.utcnow() - start.replace(tzinfo=None)
                    ).total_seconds() / 60
                job["elapsedMinutes"] = round(elapsed, 1)

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(job, default=decimal_default),
            }

        # Route: GET /job/{jobId}/research
        elif path.endswith("/research"):
            job_id = path.split("/")[2] if len(path.split("/")) > 2 else None
            if not job_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Job ID required"}),
                }

            # Get job from DynamoDB
            response = table.get_item(Key={"jobId": job_id})
            job = response.get("Item")

            if not job:
                return {
                    "statusCode": 404,
                    "headers": headers,
                    "body": json.dumps({"error": f"Job {job_id} not found"}),
                }

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "jobId": job_id,
                        "researchId": job.get("researchId"),
                        "status": job.get("status"),
                        "progress": job.get("overallProgress", 0),
                    },
                    default=decimal_default,
                ),
            }

        # Route: GET /research/{researchId}/jobs - List all jobs for a research
        # Uses GSI (Global Secondary Index) for efficient query by research ID
        # Returns newest jobs first for recent activity display
        elif path.startswith("/research/") and path.endswith("/jobs"):
            research_id = path.split("/")[2] if len(path.split("/")) > 2 else None
            if not research_id:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "Research ID required"}),
                }

            # Query jobs by research ID using GSI
            response = table.query(
                IndexName="researchId-startTime-index",
                KeyConditionExpression="researchId = :rid",
                ExpressionAttributeValues={":rid": research_id},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=20,
            )

            jobs = response.get("Items", [])

            # Calculate elapsed times
            for job in jobs:
                if "startTime" in job:
                    start = datetime.fromisoformat(
                        job["startTime"].replace("Z", "+00:00")
                    )
                    if "endTime" in job:
                        end = datetime.fromisoformat(
                            job["endTime"].replace("Z", "+00:00")
                        )
                        elapsed = (end - start).total_seconds() / 60
                    else:
                        elapsed = (
                            datetime.utcnow() - start.replace(tzinfo=None)
                        ).total_seconds() / 60
                    job["elapsedMinutes"] = round(elapsed, 1)

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {"researchId": research_id, "jobs": jobs, "count": len(jobs)},
                    default=decimal_default,
                ),
            }

        # Route: GET /status/running
        elif path == "/status/running":
            # Query running jobs using GSI
            response = table.query(
                IndexName="status-startTime-index",
                KeyConditionExpression="#status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": "RUNNING"},
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=50,
            )

            jobs = response.get("Items", [])

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {"status": "RUNNING", "jobs": jobs, "count": len(jobs)},
                    default=decimal_default,
                ),
            }

        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Endpoint not found"}),
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
