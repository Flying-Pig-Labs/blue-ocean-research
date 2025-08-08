#!/usr/bin/env python3
"""
CDK Stack for Multi-Step LLM Pipeline with AWS Batch

This stack creates a complete serverless infrastructure for running the
Multi-Step LLM Pipeline in AWS Batch with API Gateway triggers.

Key Components:
1. AWS Batch (Fargate) for containerized pipeline execution
2. API Gateway for REST API endpoints
3. Lambda functions for job submission and monitoring
4. DynamoDB for job tracking and research mapping
5. S3 for input/output storage
6. VPC with private subnets for secure execution

Design Principles:
- Serverless architecture (Fargate, Lambda, DynamoDB)
- Least privilege IAM roles
- Private network isolation for compute
- Automatic cleanup with TTL
- Cost-optimized with on-demand pricing

Author: Multi-Step LLM Pipeline Team
Date: December 2024
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_batch as batch,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_s3 as s3,
    aws_secretsmanager as sm,
)
from constructs import Construct
import json


class MultiStepLLMBatchStack(Stack):
    """
    CDK Stack for Multi-Step LLM Pipeline with Batch Processing.
    
    This stack creates all necessary AWS resources for running the pipeline
    in a scalable, serverless manner using AWS Batch with Fargate.
    
    Attributes:
        output_values (dict): Important resource identifiers for reference
    """
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get account and region
        account = self.account
        region = self.region
        
        # =========================
        # S3 Bucket for Research Files
        # =========================
        # This bucket stores:
        # - Input research documents
        # - Pipeline output files
        # - Intermediate artifacts
        
        # Import existing S3 bucket if it exists
        bucket_name = f"multi-step-llm-research-{account}"
        research_bucket = s3.Bucket.from_bucket_name(
            self, "ResearchBucket",
            bucket_name=bucket_name
        )
        
        # Import the color-code-research-results bucket for reading research reports
        color_code_bucket = s3.Bucket.from_bucket_name(
            self, "ColorCodeBucket",
            bucket_name=f"color-code-research-results-{account}"
        )
        
        # =========================
        # DynamoDB Tables
        # =========================
        # Two tables for tracking:
        # 1. Research documents and their S3 locations
        # 2. Batch job execution status and metadata
        
        # Table for tracking research reports and their S3 keys
        research_table = dynamodb.Table(
            self, "ResearchTable",
            table_name="PipelineResearch",
            partition_key=dynamodb.Attribute(
                name="researchId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl"
        )
        
        # Table for tracking batch job runs
        jobs_table = dynamodb.Table(
            self, "JobsTable",
            table_name="PipelineBatchJobs",
            partition_key=dynamodb.Attribute(
                name="jobId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # GSI for looking up jobs by research ID
        jobs_table.add_global_secondary_index(
            index_name="ResearchIdIndex",
            partition_key=dynamodb.Attribute(
                name="researchId",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # =========================
        # VPC for Batch
        # =========================
        # Private VPC for secure Batch execution
        # NAT Gateway provides outbound internet for API calls
        vpc = ec2.Vpc(
            self, "BatchVPC",
            max_azs=2,
            nat_gateways=1
        )
        
        # =========================
        # ECR Repository
        # =========================
        # Import existing repository (created by 'make docker')
        ecr_repo = ecr.Repository.from_repository_name(
            self, "PipelineRepository",
            repository_name="multi-step-llm-pipeline"
        )
        
        # =========================
        # Batch Compute Environment
        # =========================
        # Fargate-based compute for serverless container execution
        # Auto-scales based on job queue demand
        batch_service_role = iam.Role(
            self, "BatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )
        
        compute_environment = batch.CfnComputeEnvironment(
            self, "ComputeEnvironment",
            type="MANAGED",
            state="ENABLED",
            service_role=batch_service_role.role_arn,
            compute_environment_name="multi-step-llm-compute",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="FARGATE",
                maxv_cpus=256,
                subnets=[subnet.subnet_id for subnet in vpc.private_subnets],
                security_group_ids=[
                    ec2.SecurityGroup(
                        self, "BatchSecurityGroup",
                        vpc=vpc,
                        allow_all_outbound=True
                    ).security_group_id
                ]
            )
        )
        
        # =========================
        # Batch Job Queue
        # =========================
        job_queue = batch.CfnJobQueue(
            self, "JobQueue",
            job_queue_name="multi-step-llm-queue",
            priority=1,
            state="ENABLED",
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref,
                    order=1
                )
            ]
        )
        
        # =========================
        # Task Execution Role
        # =========================
        # Role for ECS/Fargate to pull images and write logs
        # Separate from Task Role for security isolation
        task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )
        
        # Add permissions to access secrets
        task_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{region}:{account}:secret:anthropic_key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:openai_key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:cohere-key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:github_token_blue_ocean-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:perplexity-key-*"
                ]
            )
        )
        
        # =========================
        # Task Role
        # =========================
        # Role for the running container to access AWS resources
        # Has permissions for S3 and DynamoDB operations
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        
        # Grant S3 permissions
        research_bucket.grant_read_write(task_role)
        color_code_bucket.grant_read(task_role)  # Read-only access to color-code research results
        
        # Grant DynamoDB permissions
        research_table.grant_read_write_data(task_role)
        jobs_table.grant_read_write_data(task_role)
        
        # Grant Secrets Manager permissions to task role
        # The task needs to read secrets to get API keys
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{region}:{account}:secret:anthropic_key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:openai_key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:cohere-key-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:github_token_blue_ocean-*",
                    f"arn:aws:secretsmanager:{region}:{account}:secret:perplexity-key-*"
                ]
            )
        )
        
        # =========================
        # Batch Job Definition
        # =========================
        # Defines container specifications for pipeline execution:
        # - 4 vCPUs, 16GB RAM (sufficient for LLM calls)
        # - 50GB ephemeral storage (for temp files)
        # - 2-hour timeout (typical pipeline takes 10-15 min)
        # - 2 retry attempts for resilience
        log_group = logs.LogGroup(
            self, "BatchLogGroup",
            log_group_name="/aws/batch/job/multi-step-llm",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Force job definition update by adding a timestamp comment
        # This ensures IAM policy changes are reflected
        import time
        job_definition = batch.CfnJobDefinition(
            self, "JobDefinition",
            job_definition_name="multi-step-llm-pipeline",
            type="container",
            platform_capabilities=["FARGATE"],
            container_properties={
                "image": ecr_repo.repository_uri + ":latest",
                "resourceRequirements": [
                    {"type": "VCPU", "value": "4"},
                    {"type": "MEMORY", "value": "16384"}
                ],
                "jobRoleArn": task_role.role_arn,
                "executionRoleArn": task_execution_role.role_arn,
                "environment": [
                    {"name": "AWS_DEFAULT_REGION", "value": region},
                    {"name": "RESEARCH_BUCKET", "value": research_bucket.bucket_name},
                    {"name": "RESEARCH_TABLE", "value": research_table.table_name},
                    {"name": "JOBS_TABLE", "value": jobs_table.table_name}
                ],
                # API keys injected from AWS Secrets Manager
                # These must exist in Secrets Manager before deployment
                "secrets": [
                    {"name": "ANTHROPIC_API_KEY", "valueFrom": f"arn:aws:secretsmanager:{region}:{account}:secret:anthropic_key-47iAE6"},
                    {"name": "OPENAI_API_KEY", "valueFrom": f"arn:aws:secretsmanager:{region}:{account}:secret:openai_key-PkoBXY"},
                    {"name": "COHERE_API_KEY", "valueFrom": f"arn:aws:secretsmanager:{region}:{account}:secret:cohere-key-MxBx6j"},
                    {"name": "GITHUB_TOKEN", "valueFrom": f"arn:aws:secretsmanager:{region}:{account}:secret:github_token_blue_ocean-uv7Z1l"},
                    {"name": "PERPLEXITY_KEY", "valueFrom": f"arn:aws:secretsmanager:{region}:{account}:secret:perplexity-key-rrkmhM"}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.log_group_name,
                        "awslogs-region": region,
                        "awslogs-stream-prefix": "pipeline"
                    }
                },
                "fargatePlatformConfiguration": {
                    "platformVersion": "LATEST"
                },
                "ephemeralStorage": {
                    "sizeInGiB": 50
                }
            },
            timeout={
                "attemptDurationSeconds": 7200  # 2 hours
            },
            retry_strategy={
                "attempts": 2
            }
        )
        
        # =========================
        # Lambda Functions
        # =========================
        
        # Lambda for submitting batch jobs
        submit_job_lambda = lambda_.Function(
            self, "SubmitJobLambda",
            function_name="pipeline-submit-job",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "JOB_QUEUE": job_queue.job_queue_name,
                "JOB_DEFINITION": job_definition.job_definition_name,
                "RESEARCH_TABLE": research_table.table_name,
                "JOBS_TABLE": jobs_table.table_name,
                "RESEARCH_BUCKET": research_bucket.bucket_name
            },
            code=lambda_.Code.from_inline("""
import json
import boto3
import uuid
import os
from datetime import datetime, timedelta

batch_client = boto3.client('batch')
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

def handler(event, context):
    '''
    Submit a batch job for the pipeline
    Expects 'researchId' in the request body
    '''
    
    # Always return CORS headers, even on errors
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        research_id = body.get('researchId')
        team = body.get('team', 'red')  # Default to 'red' if not specified
        
        if not research_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'researchId is required'})
            }
        
        # The research markdown files are stored in color-code-research-results bucket
        # Path format: users/fprior/research/{team}/{reportId}/report.md
        source_bucket = 'color-code-research-results-984906149037'
        source_key = f"users/fprior/research/{team}/{research_id}/report.md"
        
        # SIMPLIFIED: Just pass the S3 location directly - no copying!
        s3_key = f"{source_bucket}/{source_key}"
        
        # Verify the file exists
        try:
            s3_client.head_object(Bucket=source_bucket, Key=source_key)
            print(f"Verified research report exists at s3://{source_bucket}/{source_key}")
            
        except s3_client.exceptions.NoSuchKey:
            print(f"Research report not found at s3://{source_bucket}/{source_key}")
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Research report not found at expected location: s3://{source_bucket}/{source_key}'})
            }
            
        except Exception as e:
            print(f"Error accessing research report: {str(e)}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to access research report: {str(e)}'})
            }
        
        # Generate job ID and name
        job_id = str(uuid.uuid4())
        job_name = f"pipeline-{research_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Submit batch job
        batch_response = batch_client.submit_job(
            jobName=job_name,
            jobQueue=os.environ['JOB_QUEUE'],
            jobDefinition=os.environ['JOB_DEFINITION'],
            containerOverrides={
                'environment': [
                    {'name': 'S3_INPUT_KEY', 'value': s3_key},
                    {'name': 'RESEARCH_ID', 'value': research_id},
                    {'name': 'JOB_ID', 'value': job_id}
                ],
                'command': ['--s3-input', f"s3://{s3_key}"]  # s3_key already contains bucket/key
            }
        )
        
        # Store job info in DynamoDB
        jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
        jobs_table.put_item(
            Item={
                'jobId': batch_response['jobId'],
                'researchId': research_id,
                'jobName': batch_response['jobName'],
                'status': 'SUBMITTED',
                'createdAt': datetime.now().isoformat(),
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp()),
                'batchJobId': batch_response['jobId'],
                'logStreamName': f"pipeline/default/{batch_response['jobId']}"
            }
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'jobId': batch_response['jobId'],
                'jobName': batch_response['jobName'],
                'status': 'SUBMITTED',
                'message': 'Pipeline job submitted successfully'
            })
        }
    except Exception as e:
        print(f"Error in handler: {str(e)}")
        # Always return CORS headers even on unexpected errors
        return {
            'statusCode': 502,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }
""")
        )
        
        # Grant permissions to submit jobs
        # Use wildcard for all Batch resources to avoid permission issues
        submit_job_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["batch:SubmitJob", "batch:DescribeJobDefinitions"],
                resources=["*"]  # Temporary broad permission to diagnose issue
            )
        )
        
        # Grant S3 permissions to upload input data to pipeline bucket
        research_bucket.grant_read_write(submit_job_lambda)
        
        # Grant S3 permissions to read from the color-code-research-results bucket
        color_code_bucket.grant_read(submit_job_lambda)
        
        # Grant DynamoDB permissions
        # The Lambda needs to read from ResearchReports table (not PipelineResearch)
        submit_job_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem"],
                resources=[f"arn:aws:dynamodb:{region}:{account}:table/ResearchReports"]
            )
        )
        jobs_table.grant_write_data(submit_job_lambda)
        
        # Lambda for monitoring job logs
        monitor_logs_lambda = lambda_.Function(
            self, "MonitorLogsLambda",
            function_name="pipeline-monitor-logs",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "JOBS_TABLE": jobs_table.table_name,
                "LOG_GROUP": log_group.log_group_name
            },
            code=lambda_.Code.from_inline("""
import json
import boto3
import os
from datetime import datetime

logs_client = boto3.client('logs')
dynamodb = boto3.resource('dynamodb')
batch_client = boto3.client('batch')

def handler(event, context):
    '''
    Get logs/status for a pipeline job
    Expects either 'researchId' or 'jobId' in the path parameters
    '''
    
    # Get research ID or job ID from path
    path_params = event.get('pathParameters', {})
    research_id = path_params.get('researchId')
    job_id = path_params.get('jobId')
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': ''
        }
    
    if not research_id and not job_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({'error': 'researchId or jobId is required'})
        }
    
    # Look up job in DynamoDB
    jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
    
    # If jobId is provided, look up directly
    if job_id:
        response = jobs_table.get_item(Key={'jobId': job_id})
        items = [response['Item']] if 'Item' in response else []
    else:
        # Otherwise, query by researchId
        response = jobs_table.query(
            IndexName='ResearchIdIndex',
            KeyConditionExpression='researchId = :rid',
            ExpressionAttributeValues={':rid': research_id},
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get('Items', [])
    
    if not items:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({'error': 'No job found'})
        }
    
    job = items[0]
    batch_job_id = job['batchJobId']
    
    # Get current job status from Batch
    batch_response = batch_client.describe_jobs(jobs=[batch_job_id])
    if batch_response['jobs']:
        current_status = batch_response['jobs'][0]['status']
        job['status'] = current_status
        
        # Update status in DynamoDB if changed
        if current_status != job.get('status'):
            jobs_table.update_item(
                Key={'jobId': job['jobId']},
                UpdateExpression='SET #s = :status',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':status': current_status}
            )
    
    # Get logs if job is running or completed
    logs = []
    if job['status'] in ['RUNNING', 'SUCCEEDED', 'FAILED']:
        log_stream_name = job.get('logStreamName')
        
        if log_stream_name:
            try:
                # Get log events
                log_response = logs_client.get_log_events(
                    logGroupName=os.environ['LOG_GROUP'],
                    logStreamName=log_stream_name,
                    startFromHead=True,
                    limit=1000
                )
                
                logs = [
                    {
                        'timestamp': event['timestamp'],
                        'message': event['message']
                    }
                    for event in log_response['events']
                ]
            except Exception as e:
                print(f"Error fetching logs: {str(e)}")
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({
            'jobId': job['jobId'],
            'researchId': job.get('researchId', research_id),
            'status': job['status'],
            'createdAt': job.get('createdAt'),
            'currentStage': job.get('currentStage', 'unknown'),
            'progress_percentage': job.get('progress_percentage', 0),
            'logs': logs,
            'logStreamUrl': f"https://console.aws.amazon.com/cloudwatch/home?region={os.environ['AWS_REGION']}#logsV2:log-groups/log-group/{os.environ['LOG_GROUP']}/log-events/{job.get('logStreamName', '')}"
        })
    }
""")
        )
        
        # Grant permissions to read logs
        monitor_logs_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:GetLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=[log_group.log_group_arn]
            )
        )
        
        # Grant permissions to describe batch jobs
        monitor_logs_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["batch:DescribeJobs"],
                resources=["*"]
            )
        )
        
        # Grant DynamoDB permissions
        jobs_table.grant_read_write_data(monitor_logs_lambda)
        
        # =========================
        # API Gateway
        # =========================
        api = apigw.RestApi(
            self, "PipelineAPI",
            rest_api_name="multi-step-llm-pipeline-api",
            description="API for Multi-Step LLM Pipeline",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # /submit endpoint
        submit_resource = api.root.add_resource("submit")
        submit_resource.add_method(
            "POST",
            apigw.LambdaIntegration(submit_job_lambda)
        )
        
        # /logs/{researchId} endpoint
        logs_resource = api.root.add_resource("logs")
        logs_id_resource = logs_resource.add_resource("{researchId}")
        logs_id_resource.add_method(
            "GET",
            apigw.LambdaIntegration(monitor_logs_lambda)
        )
        
        # /status/{jobId} endpoint - for frontend compatibility
        status_resource = api.root.add_resource("status")
        status_id_resource = status_resource.add_resource("{jobId}")
        status_id_resource.add_method(
            "GET",
            apigw.LambdaIntegration(monitor_logs_lambda)  # Reuse the same Lambda for now
        )
        
        # Output important values
        self.output_values = {
            "api_url": api.url,
            "ecr_repo_uri": ecr_repo.repository_uri,
            "job_queue": job_queue.job_queue_name,
            "job_definition": job_definition.job_definition_name,
            "research_bucket": research_bucket.bucket_name,
            "research_table": research_table.table_name,
            "jobs_table": jobs_table.table_name
        }