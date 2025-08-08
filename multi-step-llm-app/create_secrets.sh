#!/bin/bash
# Create secrets in AWS Secrets Manager

echo "Creating secrets in AWS Secrets Manager..."

# Anthropic API Key
aws secretsmanager create-secret \
    --name anthropic_key \
    --description "Anthropic API Key" \
    --secret-string "$ANTHROPIC_API_KEY" \
    --region us-east-1 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id anthropic_key \
    --secret-string "$ANTHROPIC_API_KEY" \
    --region us-east-1

# OpenAI API Key  
aws secretsmanager create-secret \
    --name openai_key \
    --description "OpenAI API Key" \
    --secret-string "$OPENAI_API_KEY" \
    --region us-east-1 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id openai_key \
    --secret-string "$OPENAI_API_KEY" \
    --region us-east-1

# EXA API Key
aws secretsmanager create-secret \
    --name exa-key \
    --description "EXA API Key" \
    --secret-string "$EXA_API_KEY" \
    --region us-east-1 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id exa-key \
    --secret-string "$EXA_API_KEY" \
    --region us-east-1

# Cohere API Key
aws secretsmanager create-secret \
    --name cohere-key \
    --description "Cohere API Key" \
    --secret-string "$COHERE_API_KEY" \
    --region us-east-1 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id cohere-key \
    --secret-string "$COHERE_API_KEY" \
    --region us-east-1

# GitHub Token
aws secretsmanager create-secret \
    --name github_token \
    --description "GitHub Personal Access Token" \
    --secret-string "$GITHUB_TOKEN" \
    --region us-east-1 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id github_token \
    --secret-string "$GITHUB_TOKEN" \
    --region us-east-1

echo "Secrets created/updated successfully!"
echo ""
echo "Secret ARNs:"
aws secretsmanager describe-secret --secret-id anthropic_key --region us-east-1 --query ARN --output text
aws secretsmanager describe-secret --secret-id openai_key --region us-east-1 --query ARN --output text
aws secretsmanager describe-secret --secret-id exa-key --region us-east-1 --query ARN --output text
aws secretsmanager describe-secret --secret-id cohere-key --region us-east-1 --query ARN --output text
aws secretsmanager describe-secret --secret-id github_token --region us-east-1 --query ARN --output text