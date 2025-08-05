#!/usr/bin/env python3
"""Wrapper script to load AWS secrets before running other scripts"""
import sys
import subprocess
from src.utils.secrets_manager import load_aws_secrets

if __name__ == "__main__":
    # Load secrets from AWS
    print("Loading AWS secrets...")
    load_aws_secrets(profile="mvp")
    
    # Run the provided command
    if len(sys.argv) > 1:
        script = sys.argv[1]
        args = sys.argv[2:]
        print(f"\nRunning: python {script} {' '.join(args)}")
        subprocess.run(["python", script] + args)
    else:
        print("Usage: python run_with_secrets.py <script> [args...]")