#!/usr/bin/env python3
"""
Fix the get_secrets function to use the correct key names
"""
import os
import re

def create_correct_get_secrets():
    """Create the correct get_secrets function based on actual AWS Secrets Manager format"""
    
    return '''def get_secrets() -> Dict[str, str]:
    """Load API keys from AWS Secrets Manager"""
    secrets = {}
    
    # Get secret ARNs from environment variables
    anthropic_arn = os.environ.get('ANTHROPIC_SECRET_ARN')
    openai_arn = os.environ.get('OPENAI_SECRET_ARN')
    exa_arn = os.environ.get('EXA_SECRET_ARN')
    cohere_arn = os.environ.get('COHERE_SECRET_ARN')
    github_arn = os.environ.get('GITHUB_SECRET_ARN')
    
    # Load Anthropic API key (JSON format with lowercase key)
    if anthropic_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=anthropic_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['ANTHROPIC_API_KEY'] = secret_data.get('anthropic_key', '')
            except json.JSONDecodeError:
                secrets['ANTHROPIC_API_KEY'] = secret_value
            logger.info("Loaded Anthropic key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Anthropic secret: {e}")
    
    # Load OpenAI API key (JSON format with lowercase key)
    if openai_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=openai_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['OPENAI_API_KEY'] = secret_data.get('openai_key', '')
            except json.JSONDecodeError:
                secrets['OPENAI_API_KEY'] = secret_value
            logger.info("Loaded OpenAI key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load OpenAI secret: {e}")
    
    # Load EXA API key (plain string format)
    if exa_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=exa_arn)
            secret_value = response.get('SecretString', '')
            # EXA key is stored as plain string
            secrets['EXA_API_KEY'] = secret_value
            logger.info("Loaded EXA key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load EXA secret: {e}")
    
    # Load Cohere API key (plain string format)
    if cohere_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=cohere_arn)
            secret_value = response.get('SecretString', '')
            # Cohere key is stored as plain string
            secrets['COHERE_API_KEY'] = secret_value
            logger.info("Loaded Cohere key from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load Cohere secret: {e}")
    
    # Load GitHub token (JSON format with lowercase key)
    if github_arn:
        try:
            response = secrets_client.get_secret_value(SecretId=github_arn)
            secret_value = response.get('SecretString', '{}')
            try:
                secret_data = json.loads(secret_value)
                secrets['GITHUB_TOKEN'] = secret_data.get('github_token', '')
            except json.JSONDecodeError:
                secrets['GITHUB_TOKEN'] = secret_value
            logger.info("Loaded GitHub token from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to load GitHub secret: {e}")
    
    # Fallback to environment variables
    if not secrets.get('ANTHROPIC_API_KEY'):
        secrets['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
    if not secrets.get('OPENAI_API_KEY'):
        secrets['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
    if not secrets.get('EXA_API_KEY'):
        secrets['EXA_API_KEY'] = os.environ.get('EXA_API_KEY', '')
    if not secrets.get('COHERE_API_KEY'):
        secrets['COHERE_API_KEY'] = os.environ.get('COHERE_API_KEY', '')
    if not secrets.get('GITHUB_TOKEN'):
        secrets['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN', '')
    
    return secrets'''

def fix_lambda_file(filepath):
    """Fix get_secrets function in a Lambda file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find the get_secrets function
    pattern = r'def get_secrets\(\)[^:]*:.*?(?=\ndef|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        # Replace with the correct function
        new_function = create_correct_get_secrets()
        content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        
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
    
    print(f"\nFixed {fixed_count} Lambda handler files with correct secret key names")

if __name__ == '__main__':
    main()