#!/usr/bin/env python3
"""
AWS Secrets Manager integration for API key management
Handles retrieval of API keys from AWS Secrets Manager
"""

import os
import json
import boto3
from typing import Dict, Optional
from functools import lru_cache
from botocore.exceptions import ClientError, NoCredentialsError


# Hardcoded secret ARNs as specified
SECRET_ARNS = {
    "ANTHROPIC_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6",
    "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY",
    "EXA_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:exa-key-N7ylem",
    "COHERE_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:cohere-key-MxBx6j",
    "GITHUB_TOKEN": "arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy",
    "PERPLEXITY_API_KEY": "arn:aws:secretsmanager:us-east-1:984906149037:secret:perplexity-key-rrkmhM",
}


class SecretsManager:
    """Manages retrieval of secrets from AWS Secrets Manager"""

    def __init__(self, profile: str = None, region: str = "us-east-1"):
        """Initialize with AWS profile and region

        Args:
            profile: AWS profile name. If None, uses IAM role credentials (for ECS/Batch)
            region: AWS region
        """
        self.profile = profile
        self.region = region
        self._client = None

    @property
    def client(self):
        """Lazy load boto3 client with profile or IAM role"""
        if self._client is None:
            if self.profile:
                # Use profile if specified (for local development)
                session = boto3.Session(profile_name=self.profile)
                self._client = session.client("secretsmanager", region_name=self.region)
            else:
                # Use IAM role (for ECS/Batch)
                self._client = boto3.client("secretsmanager", region_name=self.region)
        return self._client

    @lru_cache(maxsize=32)
    def get_secret(self, secret_arn: str) -> Optional[str]:
        """Retrieve a secret value from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_arn)

            # Secrets can be stored as either string or binary
            if "SecretString" in response:
                secret = response["SecretString"]
                # Try to parse as JSON in case it's a key-value pair
                try:
                    secret_dict = json.loads(secret)
                    # If it's a dict with a single key, return the value
                    if isinstance(secret_dict, dict) and len(secret_dict) == 1:
                        return list(secret_dict.values())[0]
                    # Otherwise return the first value or the whole string
                    return secret_dict.get("api_key", secret_dict.get("key", secret))
                except json.JSONDecodeError:
                    # If not JSON, return as-is
                    return secret
            else:
                # Binary secrets not supported for API keys
                print(f"Warning: Binary secret not supported for {secret_arn}")
                return None

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                print(f"Secret not found: {secret_arn}")
            elif error_code == "AccessDeniedException":
                print(f"Access denied to secret: {secret_arn}")
            else:
                print(f"Error retrieving secret {secret_arn}: {e}")
            return None
        except NoCredentialsError:
            print(
                "AWS credentials not found. Please configure AWS CLI or set AWS_PROFILE=mvp"
            )
            return None
        except Exception as e:
            print(f"Unexpected error retrieving secret: {e}")
            return None

    def get_all_secrets(self) -> Dict[str, str]:
        """Retrieve all configured secrets"""
        secrets = {}

        print("Loading secrets from AWS Secrets Manager...")
        for key, arn in SECRET_ARNS.items():
            value = self.get_secret(arn)
            if value:
                secrets[key] = value
                print(f"✓ Loaded {key}")
            else:
                print(f"✗ Failed to load {key}")

        return secrets

    def load_secrets_to_env(self) -> None:
        """Load all secrets into environment variables"""
        secrets = self.get_all_secrets()

        for key, value in secrets.items():
            os.environ[key] = value

        if secrets:
            print(f"\nSuccessfully loaded {len(secrets)} secrets to environment")
        else:
            print("\nWarning: No secrets were loaded")


# Singleton instance
_secrets_manager = None


def get_secrets_manager(
    profile: str = None, region: str = "us-east-1"
) -> SecretsManager:
    """Get or create the singleton SecretsManager instance

    Args:
        profile: AWS profile name. If None, uses IAM role credentials (for ECS/Batch)
        region: AWS region
    """
    global _secrets_manager
    if _secrets_manager is None:
        # Check environment for AWS_PROFILE if not specified
        if profile is None:
            profile = os.environ.get("AWS_PROFILE", None)
        _secrets_manager = SecretsManager(profile=profile, region=region)
    return _secrets_manager


def load_aws_secrets(profile: str = None, region: str = "us-east-1") -> None:
    """Convenience function to load all secrets to environment"""
    manager = get_secrets_manager(profile=profile, region=region)
    manager.load_secrets_to_env()


def get_api_key(key_name: str, profile: str = None) -> Optional[str]:
    """Get a specific API key, first checking env then AWS Secrets Manager

    Args:
        key_name: Name of the API key to retrieve
        profile: AWS profile name. If None, uses IAM role credentials (for ECS/Batch)
    """
    # First check if already in environment
    existing = os.getenv(key_name)
    if existing:
        return existing

    # Otherwise try to load from AWS
    if key_name in SECRET_ARNS:
        manager = get_secrets_manager(profile=profile)
        return manager.get_secret(SECRET_ARNS[key_name])

    return None
