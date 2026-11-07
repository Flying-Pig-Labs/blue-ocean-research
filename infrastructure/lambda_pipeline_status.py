#!/usr/bin/env python3
"""
Lambda function for Innovation Pipeline Status API
Provides exact compatibility with frontend expectations

Author: Multi-Step LLM Pipeline Team
Date: January 2025
"""

import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("PipelineBatchJobs")
batch_client = boto3.client("batch")


def decimal_default(obj):
    """Helper to handle Decimal types in JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


# Status value mapping (backend -> frontend)
STATUS_MAP = {
    "SUBMITTED": "QUEUED",
    "PENDING": "QUEUED",
    "RUNNABLE": "QUEUED",
    "STARTING": "QUEUED",
    "RUNNING": "RUNNING",
    "SUCCEEDED": "COMPLETED",
    "FAILED": "FAILED",
}

# Stage information mapping
STAGE_INFO = {
    "Starting pipeline": {"number": 0, "name": "Initialization", "estimatedMinutes": 1},
    "Stage 1: Research Analysis": {
        "number": 1,
        "name": "Research Analysis",
        "estimatedMinutes": 3,
    },
    "Stage 2: JTBD Extraction": {
        "number": 2,
        "name": "Innovation Ideation",
        "estimatedMinutes": 5,
    },
    "Stage 3: Opportunity Zones": {
        "number": 3,
        "name": "Opportunity Mapping",
        "estimatedMinutes": 4,
    },
    "Stage 4: Product Ideas": {
        "number": 4,
        "name": "Product Generation",
        "estimatedMinutes": 6,
    },
    "Stage 5: Consolidation": {
        "number": 5,
        "name": "Portfolio Assembly",
        "estimatedMinutes": 2,
    },
    "Stage 6: GitHub Integration": {
        "number": 6,
        "name": "Repository Creation",
        "estimatedMinutes": 2,
    },
    "Pipeline complete": {"number": 7, "name": "Complete", "estimatedMinutes": 0},
}

# Progress mapping for stages
STAGE_PROGRESS = {0: 0, 1: 10, 2: 25, 3: 40, 4: 60, 5: 75, 6: 90, 7: 100}


def get_stage_info(current_stage: str) -> Dict[str, Any]:
    """Get stage number and info from stage string"""
    if not current_stage:
        return STAGE_INFO["Starting pipeline"]

    # Try exact match first
    if current_stage in STAGE_INFO:
        return STAGE_INFO[current_stage]

    # Try partial match
    for key, value in STAGE_INFO.items():
        if key.lower() in current_stage.lower() or current_stage.lower() in key.lower():
            return value

    # Default to first stage
    return STAGE_INFO["Starting pipeline"]


def calculate_time_estimates(
    elapsed_minutes: float, overall_progress: int
) -> Dict[str, int]:
    """Calculate time estimates based on progress"""
    AVERAGE_TOTAL = 20  # Average pipeline takes 20 minutes

    if overall_progress > 0 and elapsed_minutes > 0:
        # Estimate based on current progress rate
        estimated_total = (elapsed_minutes / overall_progress) * 100
        estimated_remaining = estimated_total - elapsed_minutes
    else:
        # Use average estimates
        estimated_total = AVERAGE_TOTAL
        estimated_remaining = AVERAGE_TOTAL

    return {
        "estimatedRemainingMinutes": max(0, round(estimated_remaining)),
        "estimatedTotalMinutes": round(estimated_total),
    }


def format_job_for_status_endpoint(job: Dict[str, Any]) -> Dict[str, Any]:
    """Format job data for /api/plan/async/status/{jobId} endpoint"""

    # Get current stage info
    current_stage_str = job.get("currentStage", "Starting pipeline")
    stage_info = get_stage_info(current_stage_str)

    # Use actual AWS Batch status without mapping
    status = job.get("status")

    # Calculate elapsed time
    elapsed_minutes = 0
    if "startTime" in job:
        start = datetime.fromisoformat(job["startTime"].replace("Z", "+00:00"))
        if "endTime" in job:
            end = datetime.fromisoformat(job["endTime"].replace("Z", "+00:00"))
            elapsed_minutes = (end - start).total_seconds() / 60
        else:
            elapsed_minutes = (
                datetime.utcnow() - start.replace(tzinfo=None)
            ).total_seconds() / 60

    # Calculate progress (handle Decimal type from DynamoDB)
    overall_progress = float(job.get("overallProgress", 0))
    stage_number = stage_info["number"]

    # Calculate stage progress (0-100 within current stage)
    if stage_number < 7:
        stage_start_progress = STAGE_PROGRESS.get(stage_number, 0)
        stage_end_progress = STAGE_PROGRESS.get(stage_number + 1, 100)
        stage_range = stage_end_progress - stage_start_progress
        stage_progress = (
            min(100, ((overall_progress - stage_start_progress) / stage_range * 100))
            if stage_range > 0
            else 0
        )
    else:
        stage_progress = 100

    # Calculate time estimates
    time_estimates = calculate_time_estimates(elapsed_minutes, overall_progress)

    # Build stages array
    stages = []
    for key, info in STAGE_INFO.items():
        if info["number"] < 7:  # Don't include "Complete" as a stage
            stage_status = "pending"
            if info["number"] < stage_number:
                stage_status = "completed"
            elif info["number"] == stage_number:
                stage_status = "running"

            stages.append(
                {
                    "name": info["name"],
                    "status": stage_status,
                    "estimatedMinutes": info["estimatedMinutes"],
                }
            )

    # Build response
    response = {
        "jobId": job.get("jobId"),
        "status": status,
        "currentStage": stage_number,
        "stageName": stage_info["name"],
        "stageProgress": round(stage_progress),
        "overallProgress": overall_progress,
        "elapsedMinutes": round(elapsed_minutes, 1),
        "estimatedRemainingMinutes": time_estimates["estimatedRemainingMinutes"],
        "estimatedTotalMinutes": time_estimates["estimatedTotalMinutes"],
        "metadata": {
            "researchDocId": job.get("researchId"),
            "startedAt": job.get("startTime"),
            "username": job.get("username", "unknown"),
            "jobId": job.get("jobId"),
        },
        "stages": stages,
        "results": {
            "githubRepoUrl": job.get("githubRepoUrl"),
            "githubRepoName": job.get("githubRepoName"),
            "issuesCreated": job.get("issuesCreated", 0),
            "analysisResults": None,  # Could add S3 links here
        },
    }

    # Add completion time if finished
    if status == "SUCCEEDED":
        response["completedAt"] = job.get("endTime")
        response["actualDurationMinutes"] = round(elapsed_minutes, 1)

    # Add error if failed
    if status == "FAILED":
        response["error"] = job.get("error", "Pipeline failed")

    return response


def format_job_for_running_endpoint(job: Dict[str, Any]) -> Dict[str, Any]:
    """Format job data for /api/status/running endpoint"""

    # Calculate elapsed time using startTime or createdAt
    elapsed_minutes = 0
    start_time_field = job.get("startTime") or job.get("createdAt")
    if start_time_field:
        start = datetime.fromisoformat(start_time_field.replace("Z", "+00:00"))
        if "endTime" in job:
            end = datetime.fromisoformat(job["endTime"].replace("Z", "+00:00"))
            elapsed_minutes = (end - start).total_seconds() / 60
        else:
            elapsed_minutes = (
                datetime.utcnow() - start.replace(tzinfo=None)
            ).total_seconds() / 60

    return {
        "jobId": job.get("jobId"),
        "researchId": job.get("researchId"),
        "username": job.get("username"),
        "startTime": start_time_field,  # Use the field we found (startTime or createdAt)
        "endTime": job.get("endTime"),
        "status": job.get("status"),  # Keep backend status for this endpoint
        "currentStage": job.get("currentStage"),
        "overallProgress": job.get("overallProgress", 0),
        "elapsedMinutes": round(elapsed_minutes, 1),
        "githubRepoUrl": job.get("githubRepoUrl"),
        "issuesCreated": job.get("issuesCreated", 0),
        "error": job.get("error") or job.get("message"),  # Also check 'message' field
    }


def lambda_handler(event, context):
    """
    Main Lambda handler for pipeline status API

    Endpoints:
    - GET /api/status/running - Get all recent jobs (last 48 hours)
    - GET /api/plan/async/status/{jobId} - Get detailed status for a job
    """

    # CORS headers for all responses
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }

    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        path = event.get("path", "")
        path_params = event.get("pathParameters", {})

        # Route: GET /api/status/running or /api/status/all
        if path in [
            "/api/status/running",
            "/status/running",
            "/api/status/all",
            "/status/all",
        ]:
            # Get jobs from last 48 hours
            cutoff_time = (datetime.utcnow() - timedelta(hours=48)).isoformat() + "Z"

            # Query multiple statuses to get recent jobs
            all_jobs = []

            # We need to scan the table since we can't query by time alone
            # Check for either startTime or createdAt field for compatibility
            response = table.scan(
                FilterExpression="attribute_exists(startTime) AND startTime > :cutoff OR attribute_exists(createdAt) AND createdAt > :cutoff",
                ExpressionAttributeValues={":cutoff": cutoff_time},
            )

            all_jobs = response.get("Items", [])

            # Sort by startTime or createdAt descending (newest first)
            all_jobs.sort(
                key=lambda x: x.get("startTime") or x.get("createdAt", ""), reverse=True
            )

            # Format jobs for frontend
            formatted_jobs = [
                format_job_for_running_endpoint(job) for job in all_jobs[:50]
            ]

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"jobs": formatted_jobs}, default=decimal_default),
            }

        # Route: GET /api/plan/async/status/{jobId}
        elif path.startswith("/api/plan/async/status/") or path.startswith(
            "/plan/async/status/"
        ):
            # Extract jobId from path
            job_id = path.split("/")[-1]

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
                # Try to get from AWS Batch directly
                try:
                    batch_response = batch_client.describe_jobs(jobs=[job_id])
                    if batch_response["jobs"]:
                        batch_job = batch_response["jobs"][0]
                        # Create a minimal response from Batch data
                        return {
                            "statusCode": 200,
                            "headers": headers,
                            "body": json.dumps(
                                {
                                    "jobId": job_id,
                                    "status": STATUS_MAP.get(
                                        batch_job["status"], batch_job["status"]
                                    ),
                                    "currentStage": 0,
                                    "stageName": "Initializing",
                                    "stageProgress": 0,
                                    "overallProgress": 0,
                                    "elapsedMinutes": 0,
                                    "estimatedRemainingMinutes": 20,
                                    "estimatedTotalMinutes": 20,
                                    "metadata": {
                                        "jobId": job_id,
                                        "startedAt": batch_job.get("startedAt", 0),
                                    },
                                    "stages": [
                                        {
                                            "name": s["name"],
                                            "status": "pending",
                                            "estimatedMinutes": s["estimatedMinutes"],
                                        }
                                        for s in STAGE_INFO.values()
                                        if s["number"] < 7
                                    ],
                                    "results": {
                                        "githubRepoUrl": None,
                                        "githubRepoName": None,
                                        "issuesCreated": 0,
                                        "analysisResults": None,
                                    },
                                },
                                default=decimal_default,
                            ),
                        }
                except:
                    pass

                return {
                    "statusCode": 404,
                    "headers": headers,
                    "body": json.dumps({"error": f"Job {job_id} not found"}),
                }

            # Format job for frontend
            formatted_job = format_job_for_status_endpoint(job)

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(formatted_job, default=decimal_default),
            }

        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Endpoint not found", "path": path}),
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
