#!/usr/bin/env python3
"""
Fix parameter handling in all Lambda functions to work with Step Functions
"""
import os
import re

def fix_lambda_file(filepath):
    """Fix parameter handling in a Lambda handler file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern replacements for parameter extraction
    replacements = [
        # Fix bucket parameter
        (r"bucket = event\.get\('bucket'\)",
         "bucket = event.get('s3Bucket') or event.get('bucket')"),
        
        # Fix input_key parameter
        (r"input_key = event\.get\('input_key'\)",
         "input_key = event.get('s3InputKey') or event.get('input_key')"),
        
        # Fix output_key parameter
        (r"output_key = event\.get\('output_key'",
         "output_key = event.get('s3OutputKey') or event.get('output_key'"),
         
        # Fix job_id parameter
        (r"job_id = event\.get\('job_id'",
         "job_id = event.get('jobId') or event.get('job_id'"),
         
        # Fix input_keys parameter
        (r"input_keys = event\.get\('input_keys'",
         "input_keys = event.get('s3InputKeys') or event.get('input_keys'"),
         
        # Fix output_keys parameter
        (r"output_keys = event\.get\('output_keys'",
         "output_keys = event.get('s3OutputKeys') or event.get('output_keys'"),
    ]
    
    # Apply replacements
    modified = False
    for pattern, replacement in replacements:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    # Also fix response format to include Step Functions compatible keys
    if "'job_id': job_id" in content:
        content = content.replace("'job_id': job_id", "'jobId': job_id")
        modified = True
    
    # Add s3Bucket and s3OutputKey to responses
    response_pattern = r"response = \{[^}]*'statusCode': 200"
    if re.search(response_pattern, content):
        # Find all response definitions
        def add_step_function_keys(match):
            response = match.group(0)
            if "'s3Bucket':" not in response:
                # Add after statusCode
                response = response.replace(
                    "'statusCode': 200,",
                    "'statusCode': 200,\n            'jobId': job_id,\n            's3Bucket': bucket,"
                )
            return response
        
        content = re.sub(response_pattern, add_step_function_keys, content, flags=re.MULTILINE)
        modified = True
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    src_dir = 'src'
    fixed_count = 0
    
    for filename in os.listdir(src_dir):
        if filename.startswith('lambda_') and filename.endswith('.py'):
            filepath = os.path.join(src_dir, filename)
            if fix_lambda_file(filepath):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} Lambda handler files")

if __name__ == '__main__':
    main()