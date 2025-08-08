#!/usr/bin/env python3
"""
Lambda Handler for GitHub Integration Stage
Wraps the github_integration.py module for AWS Lambda execution
"""

import json
import os
import sys
import boto3
import traceback
from datetime import datetime

# Add parent directory to path to import the original modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the original GitHub integration
from github_integration import GitHubIntegration

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

def get_secret(secret_arn):
    """Get secret value from AWS Secrets Manager"""
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except Exception as e:
        print(f"Error getting secret {secret_arn}: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Lambda handler for GitHub integration stage
    """
    try:
        print(f"GitHub Integration Lambda started with event: {json.dumps(event)}")
        
        # Extract parameters from event
        job_id = event.get('jobId')
        s3_bucket = event.get('s3Bucket', os.environ.get('S3_BUCKET'))
        s3_input_key = event.get('s3InputKey', event.get('s3OutputKey'))  # From consolidator
        all_outputs = event.get('allOutputs', {})
        parameters = event.get('parameters', {})
        
        # GitHub specific parameters
        repo_name = parameters.get('github_repo_name', f"innovation-portfolio-{job_id[:8]}")
        private_repo = parameters.get('github_private', False)
        skip_github = parameters.get('skip_github', False)
        
        # Update job status
        table = dynamodb.Table(os.environ.get('JOBS_TABLE'))
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET currentStage = :stage, stageProgress = :progress, updatedAt = :time',
            ExpressionAttributeValues={
                ':stage': 8,
                ':progress': 0,
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        # Skip GitHub if requested
        if skip_github:
            print("Skipping GitHub integration as requested")
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET stageProgress = :progress, #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':progress': 100,
                    ':status': 'COMPLETED'
                }
            )
            return {
                'statusCode': 200,
                'jobId': job_id,
                'stage': 'github',
                'status': 'skipped',
                'message': 'GitHub integration skipped'
            }
        
        # Get GitHub token from Secrets Manager
        github_token = get_secret(os.environ.get('GITHUB_SECRET_ARN'))
        
        # Download consolidated portfolio from S3
        print(f"Downloading portfolio from s3://{s3_bucket}/{s3_input_key}")
        response = s3.get_object(Bucket=s3_bucket, Key=s3_input_key)
        portfolio_data = json.loads(response['Body'].read())
        
        # If we don't have all outputs passed, try to load them from S3
        if not all_outputs:
            all_outputs = {}
            stage_files = {
                'research': 'stage1_research_analysis.json',
                'jtbds': 'stage2_jtbds.json',
                'clusters': 'stage3_clusters.json',
                'zones': 'stage4_opportunity_zones.json',
                'curves': 'stage5_value_curves.json',
                'ideas': 'stage6_product_ideas.json',
                'portfolio': 'stage7_consolidated_portfolio.json'
            }
            
            for stage_name, filename in stage_files.items():
                try:
                    key = f"jobs/{job_id}/output/{filename}"
                    response = s3.get_object(Bucket=s3_bucket, Key=key)
                    all_outputs[stage_name] = json.loads(response['Body'].read())
                except Exception as e:
                    print(f"Could not load {stage_name}: {str(e)}")
                    all_outputs[stage_name] = {}
        
        # Update progress
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET stageProgress = :progress',
            ExpressionAttributeValues={':progress': 20}
        )
        
        # Initialize GitHub integration
        github = GitHubIntegration(github_token)
        
        # Create repository
        print(f"Creating GitHub repository: {repo_name}")
        repo_url = github.create_repository(
            name=repo_name,
            description=f"Innovation portfolio generated from market research analysis",
            private=private_repo
        )
        
        # Update progress
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET stageProgress = :progress',
            ExpressionAttributeValues={':progress': 40}
        )
        
        # Prepare data for README
        readme_data = {
            'research_summary': all_outputs.get('research', {}).get('analysis_results', {}),
            'jtbds': all_outputs.get('jtbds', {}).get('jtbds', []),
            'opportunity_zones': all_outputs.get('zones', {}).get('opportunity_zones', []),
            'product_ideas': portfolio_data.get('consolidated_ideas', []),
            'portfolio': portfolio_data.get('portfolio', {}),
            'themes': portfolio_data.get('themes', {}),
            'synergies': portfolio_data.get('synergies', [])
        }
        
        # Create comprehensive README
        print("Generating README content...")
        readme_content = github.generate_readme(readme_data)
        
        # Update README in repository
        github.update_readme(repo_name, readme_content)
        
        # Update progress
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET stageProgress = :progress',
            ExpressionAttributeValues={':progress': 60}
        )
        
        # Create issues for each product idea
        print(f"Creating issues for {len(readme_data['product_ideas'])} product ideas...")
        issue_urls = []
        
        for i, idea in enumerate(readme_data['product_ideas']):
            try:
                issue_url = github.create_issue_for_idea(repo_name, idea, i + 1)
                issue_urls.append(issue_url)
                
                # Update progress
                progress = 60 + int((i + 1) / len(readme_data['product_ideas']) * 30)
                table.update_item(
                    Key={'jobId': job_id},
                    UpdateExpression='SET stageProgress = :progress',
                    ExpressionAttributeValues={':progress': progress}
                )
            except Exception as e:
                print(f"Error creating issue for idea {i+1}: {str(e)}")
        
        # Format output
        output = {
            'jobId': job_id,
            'timestamp': datetime.utcnow().isoformat(),
            'github_repository': {
                'url': repo_url,
                'name': repo_name,
                'private': private_repo,
                'issues_created': len(issue_urls),
                'issue_urls': issue_urls
            },
            'metadata': {
                'total_ideas': len(readme_data['product_ideas']),
                'issues_created': len(issue_urls),
                'repository_created': True
            }
        }
        
        # Save results to S3
        s3_output_key = f"jobs/{job_id}/output/stage8_github_integration.json"
        print(f"Saving results to s3://{s3_bucket}/{s3_output_key}")
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_output_key,
            Body=json.dumps(output, indent=2),
            ContentType='application/json'
        )
        
        # Update job status to completed
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET stageProgress = :progress, stage8Output = :output, #status = :status, completedAt = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':progress': 100,
                ':status': 'COMPLETED',
                ':time': datetime.utcnow().isoformat(),
                ':output': {
                    's3Key': s3_output_key,
                    'completedAt': datetime.utcnow().isoformat(),
                    'githubUrl': repo_url,
                    'summary': {
                        'repository_created': True,
                        'issues_created': len(issue_urls)
                    }
                }
            }
        )
        
        # Return success
        return {
            'statusCode': 200,
            'jobId': job_id,
            's3Bucket': s3_bucket,
            's3OutputKey': s3_output_key,
            'stage': 'github',
            'status': 'completed',
            'github_repository': repo_url,
            'issues_created': len(issue_urls),
            'message': f'Pipeline completed! GitHub repository created at {repo_url}'
        }
        
    except Exception as e:
        print(f"Error in GitHub integration lambda: {str(e)}")
        print(traceback.format_exc())
        
        # Update job status to failed
        try:
            table = dynamodb.Table(os.environ.get('JOBS_TABLE'))
            table.update_item(
                Key={'jobId': event.get('jobId')},
                UpdateExpression='SET #status = :status, errorMessage = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': f"GitHub integration failed: {str(e)}"
                }
            )
        except:
            pass
        
        raise