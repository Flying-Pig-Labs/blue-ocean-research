# GitHub Actions CI/CD Pipeline

This repository is configured with automated CI/CD using GitHub Actions. The pipeline automatically builds, tests, and deploys the Multi-Step LLM Pipeline to AWS whenever code is merged to the main branch.

## 🚀 Features

- **Automated Testing**: Runs pytest on all pull requests
- **Docker Build & Push**: Builds and pushes Docker images to Amazon ECR
- **CDK Deployment**: Automatically deploys infrastructure changes using AWS CDK
- **Environment Support**: Supports dev, staging, and production environments
- **Manual Trigger**: Can be manually triggered with environment selection
- **Caching**: Optimized with caching for pip packages and CDK assets
- **Notifications**: Creates commit statuses for deployment tracking

## 📋 Prerequisites

### AWS OIDC Configuration ✅

This repository uses AWS OIDC (OpenID Connect) for secure, keyless authentication. The following has been configured:

- **OIDC Provider**: `token.actions.githubusercontent.com` 
- **IAM Role**: `github-actions-flying-pig-labs`
- **Authorized Repos**: Only Flying-Pig-Labs repos (main branch)
- **Secrets**: Stored in AWS Secrets Manager (`ColorCodeResearchHubSecrets`)

The workflow automatically:
- Assumes the IAM role using OIDC (no AWS credentials in GitHub)
- Fetches API keys from AWS Secrets Manager at runtime
- Runs tests and deployments with proper credentials

### IAM Permissions Required

The IAM role (or user) needs the following permissions:
- ECR: Full access to push Docker images
- CloudFormation: Full access to deploy CDK stacks
- Batch: Full access to update job definitions
- Lambda: Full access to deploy functions
- API Gateway: Full access to deploy APIs
- DynamoDB: Full access to create tables
- S3: Full access to manage buckets
- IAM: Limited access to create service roles

## 🔄 Workflow Triggers

The workflow runs on:

1. **Push to main**: Automatically deploys to dev environment
2. **Pull Requests**: Runs tests only (no deployment)
3. **Manual Dispatch**: Can be triggered manually with environment selection

## 📊 Workflow Jobs

### 1. Test Job (PR only)
- Runs on pull requests
- Sets up Python 3.11
- Installs dependencies
- Runs pytest with coverage
- Uploads coverage reports to Codecov

### 2. Build and Push Job (main branch only)
- Builds Docker image for linux/amd64
- Tags with multiple strategies (latest, SHA, timestamp)
- Pushes to Amazon ECR
- Uses GitHub Actions cache for faster builds

### 3. Deploy CDK Job (main branch only)
- Installs AWS CDK CLI
- Runs CDK bootstrap if needed
- Shows CDK diff before deployment
- Deploys stack with no approval required
- Saves outputs as artifacts

### 4. Update Batch Job Definition
- Updates AWS Batch job definition with new image
- Ensures Batch uses the latest Docker image

### 5. Notification Job
- Sends deployment status
- Creates GitHub commit status
- Always runs to report success or failure

## 🎯 Manual Deployment

To manually trigger a deployment:

1. Go to **Actions** tab
2. Select **Deploy Multi-Step LLM Pipeline**
3. Click **Run workflow**
4. Choose the branch and environment
5. Click **Run workflow**

## 🏷️ Docker Image Tagging

Images are tagged with:
- `latest` - Always points to the latest main branch build
- `main-<SHA>` - Git commit SHA
- `YYYYMMDD-HHmmss` - Timestamp of build
- Branch name for feature branches

## 🔍 Monitoring Deployments

### Check Deployment Status
1. Go to the **Actions** tab to see running workflows
2. Click on a workflow run to see detailed logs
3. Check commit status on the main branch

### View CDK Outputs
After deployment, CDK outputs are saved as artifacts:
1. Go to the workflow run
2. Scroll to **Artifacts** section
3. Download `cdk-outputs` to see API endpoints and resource ARNs

## 🛠️ Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   - Verify AWS secrets are set correctly
   - Check IAM user has required permissions

2. **Docker Build Fails**
   - Check Dockerfile syntax
   - Verify all required files are present

3. **CDK Deploy Fails**
   - Run `cdk diff` locally to check changes
   - Verify CDK bootstrap has been run
   - Check CloudFormation stack for errors

4. **Tests Fail**
   - Run tests locally: `python -m pytest tests/ -v`
   - Check test logs in GitHub Actions

## 📝 Updating the Workflow

To modify the workflow:

1. Edit `.github/workflows/deploy.yml`
2. Test changes in a feature branch
3. Create a pull request
4. Merge to main after review

## 🔐 Security Notes

### OIDC Authentication (Recommended)
This repository uses AWS OIDC for GitHub Actions, which provides:
- **No long-lived credentials**: No AWS keys stored in GitHub
- **Short-lived tokens**: Credentials expire after each workflow run
- **Granular permissions**: Role can only be assumed by this specific repository
- **Audit trail**: All actions are logged with the workflow run ID
- **Automatic rotation**: No manual key rotation needed

### General Security Best Practices
- Never commit AWS credentials or API keys
- Use GitHub Secrets for API keys (Anthropic, OpenAI, GitHub)
- Review IAM role permissions periodically
- Use least-privilege principle for IAM roles
- Enable AWS CloudTrail for audit logging

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [AWS Actions for GitHub](https://github.com/aws-actions)