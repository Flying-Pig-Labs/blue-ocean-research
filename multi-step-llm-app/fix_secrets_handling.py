#!/usr/bin/env python3
"""
Fix secrets handling in all Lambda functions
"""
import os
import re

def fix_get_secrets_function(content):
    """Replace the get_secrets function with ARN-based version"""
    
    # New get_secrets function that uses ARN environment variables
    new_get_secrets = '''def get_secrets() -> Dict[str, str]:
    """Load API keys from AWS Secrets Manager"""
    secrets = {}
    
    # Get secret ARNs from environment variables
    anthropic_arn = os.environ.get('ANTHROPIC_SECRET_ARN')
    openai_arn = os.environ.get('OPENAI_SECRET_ARN')
    exa_arn = os.environ.get('EXA_SECRET_ARN')
    cohere_arn = os.environ.get('COHERE_SECRET_ARN')
    github_arn = os.environ.get('GITHUB_SECRET_ARN')
    
    # Load Anthropic API key
    if anthropic_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=anthropic_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['ANTHROPIC_API_KEY'] = secret_data.get('ANTHROPIC_API_KEY', secret_data.get('api_key', secret_value))
            except json.JSONDecodeError:
                secrets['ANTHROPIC_API_KEY'] = secret_value
            logger.info("Loaded Anthropic key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Anthropic secret: {e}")
    
    # Load OpenAI API key
    if openai_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=openai_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['OPENAI_API_KEY'] = secret_data.get('OPENAI_API_KEY', secret_data.get('api_key', secret_value))
            except json.JSONDecodeError:
                secrets['OPENAI_API_KEY'] = secret_value
            logger.info("Loaded OpenAI key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load OpenAI secret: {e}")
    
    # Load EXA API key
    if exa_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=exa_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['EXA_API_KEY'] = secret_data.get('EXA_API_KEY', secret_data.get('api_key', secret_value))
            except json.JSONDecodeError:
                secrets['EXA_API_KEY'] = secret_value
            logger.info("Loaded EXA key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load EXA secret: {e}")
    
    # Load Cohere API key
    if cohere_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=cohere_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['COHERE_API_KEY'] = secret_data.get('COHERE_API_KEY', secret_data.get('api_key', secret_value))
            except json.JSONDecodeError:
                secrets['COHERE_API_KEY'] = secret_value
            logger.info("Loaded Cohere key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Cohere secret: {e}")
    
    # Load GitHub token
    if github_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=github_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['GITHUB_TOKEN'] = secret_data.get('GITHUB_TOKEN', secret_data.get('token', secret_value))
            except json.JSONDecodeError:
                secrets['GITHUB_TOKEN'] = secret_value
            logger.info("Loaded GitHub token from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load GitHub secret: {e}")
    
    # Fallback to environment variables
    if not secrets.get('ANTHROPIC_API_KEY'):
        secrets['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY')
    if not secrets.get('OPENAI_API_KEY'):
        secrets['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    if not secrets.get('EXA_API_KEY'):
        secrets['EXA_API_KEY'] = os.environ.get('EXA_API_KEY')
    if not secrets.get('COHERE_API_KEY'):
        secrets['COHERE_API_KEY'] = os.environ.get('COHERE_API_KEY')
    if not secrets.get('GITHUB_TOKEN'):
        secrets['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN')
    
    return secrets'''
    
    # Pattern to find the get_secrets function
    pattern = r'def get_secrets\(\)[^:]*:.*?(?=\ndef|\Z)'
    
    # Replace the function
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_get_secrets, content, flags=re.DOTALL)
        return content, True
    return content, False

def fix_lambda_file(filepath):
    """Fix secrets handling in a Lambda handler file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Only fix files that have get_secrets function
    if 'def get_secrets' in content:
        content, fixed = fix_get_secrets_function(content)
        
        if fixed:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
    return False

def main():
    src_dir = 'src'
    fixed_count = 0
    
    # Lambda files that need fixing
    lambda_files = [
        'lambda_research_analyzer.py',
        'lambda_jobs_researcher.py',
        'lambda_cluster_jtbd.py',
        'lambda_opportunity_zones.py',
        'lambda_value_curves.py',
        'lambda_product_ideas.py',
        'lambda_github.py'
    ]
    
    for filename in lambda_files:
        filepath = os.path.join(src_dir, filename)
        if os.path.exists(filepath):
            if fix_lambda_file(filepath):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} Lambda handler files")

if __name__ == '__main__':
    main()