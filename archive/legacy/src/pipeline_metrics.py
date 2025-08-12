#!/usr/bin/env python3
# NOTE: Legacy script; no references found in repository. Consider removal.
"""
Pipeline metrics and monitoring handler for EventBridge events.
Processes pipeline events and generates CloudWatch metrics.
"""

import json
import os
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
cloudwatch = boto3.client('cloudwatch')
dynamodb = boto3.resource('dynamodb')

# Environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE')
CHECKPOINT_TABLE = os.environ.get('CHECKPOINT_TABLE')

def lambda_handler(event, context):
    """
    Process pipeline events from EventBridge and generate CloudWatch metrics.
    
    Events handled:
    - Pipeline Started
    - Pipeline Completed
    - Pipeline Failed
    - Stage Completed
    - Stage Failed
    """
    try:
        logger.info(f"Processing pipeline event: {json.dumps(event)}")
        
        # Extract event details
        detail = event.get('detail', {})
        detail_type = event.get('detail-type', '')
        source = event.get('source', '')
        
        if source != 'pipeline.multi-step-llm':
            logger.warning(f"Unexpected event source: {source}")
            return {'statusCode': 200, 'body': 'Event ignored'}
        
        # Route to appropriate handler based on event type
        if detail_type == 'Pipeline Started':
            handle_pipeline_started(detail)
        elif detail_type == 'Pipeline Completed':
            handle_pipeline_completed(detail)
        elif detail_type == 'Pipeline Failed' or detail_type == 'Pipeline Critical Failure':
            handle_pipeline_failed(detail, detail_type)
        elif detail_type == 'Stage Completed':
            handle_stage_completed(detail)
        elif detail_type == 'Stage Failed':
            handle_stage_failed(detail)
        else:
            logger.warning(f"Unknown event type: {detail_type}")
        
        return {'statusCode': 200, 'body': 'Event processed successfully'}
        
    except Exception as e:
        logger.error(f"Error processing pipeline event: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def handle_pipeline_started(detail: Dict[str, Any]):
    """Handle pipeline started events."""
    execution_id = detail.get('executionId')
    start_time = detail.get('startTime')
    input_size = detail.get('inputSize', 0)
    
    logger.info(f"Pipeline started: {execution_id}")
    
    # Send CloudWatch metrics
    metrics = [
        {
            'MetricName': 'PipelineStarted',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'PipelineVersion', 'Value': '2.0'}
            ]
        },
        {
            'MetricName': 'InputDataSize',
            'Value': input_size,
            'Unit': 'Bytes',
            'Dimensions': [
                {'Name': 'ExecutionId', 'Value': execution_id or 'unknown'}
            ]
        }
    ]
    
    send_cloudwatch_metrics('MultiStepLLMPipeline', metrics)
    
    # Update job tracking table if configured
    if JOBS_TABLE and execution_id:
        update_job_status(execution_id, 'RUNNING', {
            'startTime': start_time,
            'inputSize': input_size
        })

def handle_pipeline_completed(detail: Dict[str, Any]):
    """Handle pipeline completed events."""
    execution_id = detail.get('executionId')
    stages_completed = detail.get('stagesCompleted', 0)
    success = detail.get('success', False)
    repository_url = detail.get('finalRepositoryUrl')
    
    logger.info(f"Pipeline completed: {execution_id}, stages: {stages_completed}")
    
    # Calculate total duration if available
    # This would require retrieving the start time from DynamoDB or execution history
    
    # Send CloudWatch metrics
    metrics = [
        {
            'MetricName': 'PipelineCompleted',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Success', 'Value': str(success)},
                {'Name': 'PipelineVersion', 'Value': '2.0'}
            ]
        },
        {
            'MetricName': 'StagesCompleted',
            'Value': stages_completed,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'ExecutionId', 'Value': execution_id or 'unknown'}
            ]
        }
    ]
    
    if repository_url:
        metrics.append({
            'MetricName': 'GitHubRepoCreated',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'PipelineVersion', 'Value': '2.0'}
            ]
        })
    
    send_cloudwatch_metrics('MultiStepLLMPipeline', metrics)
    
    # Update job tracking table
    if JOBS_TABLE and execution_id:
        update_job_status(execution_id, 'COMPLETED', {
            'completedAt': datetime.now(timezone.utc).isoformat(),
            'stagesCompleted': stages_completed,
            'repositoryUrl': repository_url,
            'success': success
        })

def handle_pipeline_failed(detail: Dict[str, Any], event_type: str):
    """Handle pipeline failed events."""
    execution_id = detail.get('executionId')
    failure_reason = detail.get('failureReason', 'Unknown error')
    failed_stage = detail.get('failedStage')
    critical_failure = detail.get('criticalFailure', False)
    
    logger.error(f"Pipeline failed: {execution_id}, reason: {failure_reason}")
    
    # Send CloudWatch metrics
    metrics = [
        {
            'MetricName': 'PipelineFailed',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Critical', 'Value': str(critical_failure)},
                {'Name': 'PipelineVersion', 'Value': '2.0'}
            ]
        }
    ]
    
    if failed_stage:
        metrics.append({
            'MetricName': 'StageFailures',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Stage', 'Value': str(failed_stage)},
                {'Name': 'PipelineVersion', 'Value': '2.0'}
            ]
        })
    
    send_cloudwatch_metrics('MultiStepLLMPipeline', metrics)
    
    # Update job tracking table
    if JOBS_TABLE and execution_id:
        update_job_status(execution_id, 'FAILED', {
            'failedAt': datetime.now(timezone.utc).isoformat(),
            'failureReason': failure_reason,
            'failedStage': failed_stage,
            'criticalFailure': critical_failure
        })

def handle_stage_completed(detail: Dict[str, Any]):
    """Handle stage completed events."""
    execution_id = detail.get('executionId')
    stage = detail.get('stage')
    stage_name = detail.get('stageName')
    duration = detail.get('duration')
    output_size = detail.get('outputSize')
    
    logger.info(f"Stage {stage} completed: {execution_id}")
    
    # Send CloudWatch metrics
    metrics = [
        {
            'MetricName': 'StageCompleted',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Stage', 'Value': str(stage)},
                {'Name': 'StageName', 'Value': stage_name or f'Stage{stage}'}
            ]
        }
    ]
    
    if duration:
        metrics.append({
            'MetricName': 'StageDuration',
            'Value': duration,
            'Unit': 'Seconds',
            'Dimensions': [
                {'Name': 'Stage', 'Value': str(stage)},
                {'Name': 'StageName', 'Value': stage_name or f'Stage{stage}'}
            ]
        })
    
    if output_size:
        metrics.append({
            'MetricName': 'StageOutputSize',
            'Value': output_size,
            'Unit': 'Bytes',
            'Dimensions': [
                {'Name': 'Stage', 'Value': str(stage)}
            ]
        })
    
    send_cloudwatch_metrics('MultiStepLLMPipeline', metrics)
    
    # Track stage-specific metrics
    track_stage_specific_metrics(stage, stage_name, detail)

def handle_stage_failed(detail: Dict[str, Any]):
    """Handle stage failed events."""
    execution_id = detail.get('executionId')
    stage = detail.get('stage')
    stage_name = detail.get('stageName')
    error = detail.get('error')
    
    logger.error(f"Stage {stage} failed: {execution_id}, error: {error}")
    
    # Send CloudWatch metrics
    metrics = [
        {
            'MetricName': 'StageFailed',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Stage', 'Value': str(stage)},
                {'Name': 'StageName', 'Value': stage_name or f'Stage{stage}'}
            ]
        }
    ]
    
    send_cloudwatch_metrics('MultiStepLLMPipeline', metrics)

def track_stage_specific_metrics(stage: int, stage_name: str, detail: Dict[str, Any]):
    """Track metrics specific to individual stages."""
    metrics = []
    
    if stage == 1:  # Research Analysis
        # Track analysis tasks completed
        pass
    elif stage == 2:  # JTBD Research
        # Track search results and sources
        pass
    elif stage == 3:  # Clustering
        cluster_count = detail.get('clusterCount')
        if cluster_count:
            metrics.append({
                'MetricName': 'ClustersGenerated',
                'Value': cluster_count,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Stage', 'Value': '3'}]
            })
    elif stage == 4:  # Value Curve Mapping
        curve_count = detail.get('valueCurveCount')
        if curve_count:
            metrics.append({
                'MetricName': 'ValueCurvesGenerated',
                'Value': curve_count,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Stage', 'Value': '4'}]
            })
    elif stage == 5:  # Product Idea Generation
        idea_count = detail.get('ideaCount')
        if idea_count:
            metrics.append({
                'MetricName': 'ProductIdeasGenerated',
                'Value': idea_count,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Stage', 'Value': '5'}]
            })
    elif stage == 6:  # Idea Consolidation
        portfolio_size = detail.get('portfolioSize')
        if portfolio_size:
            metrics.append({
                'MetricName': 'PortfolioSize',
                'Value': portfolio_size,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Stage', 'Value': '6'}]
            })
    elif stage == 7:  # GitHub Integration
        issues_created = detail.get('issuesCreated')
        if issues_created:
            metrics.append({
                'MetricName': 'GitHubIssuesCreated',
                'Value': issues_created,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Stage', 'Value': '7'}]
            })
    
    if metrics:
        send_cloudwatch_metrics('MultiStepLLMPipeline/Stages', metrics)

def send_cloudwatch_metrics(namespace: str, metrics: List[Dict[str, Any]]):
    """Send metrics to CloudWatch."""
    try:
        # Add timestamp to all metrics
        timestamp = datetime.now(timezone.utc)
        for metric in metrics:
            metric['Timestamp'] = timestamp
        
        # Send metrics in batches of 20 (CloudWatch limit)
        for i in range(0, len(metrics), 20):
            batch = metrics[i:i+20]
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )
            logger.info(f"Sent {len(batch)} metrics to CloudWatch namespace: {namespace}")
            
    except Exception as e:
        logger.error(f"Error sending CloudWatch metrics: {str(e)}")

def update_job_status(execution_id: str, status: str, metadata: Dict[str, Any]):
    """Update job status in DynamoDB tracking table."""
    if not JOBS_TABLE:
        return
        
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        # Update job record
        response = table.update_item(
            Key={'jobId': execution_id},
            UpdateExpression='SET #status = :status, metadata = :metadata, updatedAt = :updated',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':metadata': metadata,
                ':updated': datetime.now(timezone.utc).isoformat()
            },
            ReturnValues='UPDATED_NEW'
        )
        
        logger.info(f"Updated job status: {execution_id} -> {status}")
        
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")

def generate_performance_report(execution_id: str) -> Dict[str, Any]:
    """Generate a performance report for a completed pipeline execution."""
    try:
        # Retrieve checkpoint data for the execution
        if not CHECKPOINT_TABLE:
            return {'error': 'Checkpoint table not configured'}
        
        table = dynamodb.Table(CHECKPOINT_TABLE)
        
        # Query all checkpoints for this execution
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('executionId').eq(execution_id)
        )
        
        checkpoints = response.get('Items', [])
        
        if not checkpoints:
            return {'error': 'No checkpoints found for execution'}
        
        # Calculate stage durations and analyze performance
        report = {
            'executionId': execution_id,
            'totalStages': len(checkpoints),
            'stagePerformance': [],
            'recommendations': []
        }
        
        # Sort checkpoints by stage
        sorted_checkpoints = sorted(checkpoints, key=lambda x: int(x.get('stage', 0)))
        
        previous_time = None
        for checkpoint in sorted_checkpoints:
            stage = int(checkpoint.get('stage', 0))
            completed_at = checkpoint.get('completedAt')
            
            stage_perf = {
                'stage': stage,
                'completedAt': completed_at
            }
            
            # Calculate duration if we have previous timestamp
            if previous_time and completed_at:
                try:
                    current_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    prev_time = datetime.fromisoformat(previous_time.replace('Z', '+00:00'))
                    duration = (current_time - prev_time).total_seconds()
                    stage_perf['durationSeconds'] = duration
                except Exception as e:
                    logger.warning(f"Error calculating duration: {e}")
            
            report['stagePerformance'].append(stage_perf)
            previous_time = completed_at
        
        # Add performance recommendations
        report['recommendations'] = generate_performance_recommendations(report['stagePerformance'])
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        return {'error': str(e)}

def generate_performance_recommendations(stage_performance: List[Dict[str, Any]]) -> List[str]:
    """Generate performance optimization recommendations based on stage timings."""
    recommendations = []
    
    # Define expected stage durations (in seconds)
    expected_durations = {
        1: 120,  # Research Analysis
        2: 180,  # JTBD Research
        3: 240,  # Clustering
        4: 360,  # Value Curve Mapping
        5: 480,  # Product Idea Generation
        6: 180,  # Idea Consolidation
        7: 120   # GitHub Integration
    }
    
    for stage_perf in stage_performance:
        stage = stage_perf.get('stage')
        duration = stage_perf.get('durationSeconds')
        
        if stage and duration and stage in expected_durations:
            expected = expected_durations[stage]
            
            if duration > expected * 1.5:  # 50% longer than expected
                recommendations.append(
                    f"Stage {stage} took {duration:.0f}s (expected ~{expected}s). Consider optimizing prompts or reducing data volume."
                )
            elif duration < expected * 0.5:  # Much faster than expected
                recommendations.append(
                    f"Stage {stage} completed very quickly ({duration:.0f}s). Verify output quality."
                )
    
    if not recommendations:
        recommendations.append("Pipeline performance is within expected parameters.")
    
    return recommendations