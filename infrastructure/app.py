#!/usr/bin/env python3
"""
CDK App for Multi-Step LLM Pipeline Batch Infrastructure
"""

import os
import aws_cdk as cdk
from cdk_batch_pipeline import MultiStepLLMBatchStack

app = cdk.App()

# Get environment from context or use default
env_name = app.node.try_get_context("env") or "dev"

# Create the stack
stack = MultiStepLLMBatchStack(
    app, 
    f"MultiStepLLMBatch-{env_name}",
    env={
        "account": os.environ.get("CDK_DEFAULT_ACCOUNT"),
        "region": os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
    },
    description=f"Multi-Step LLM Pipeline Batch Infrastructure ({env_name})"
)

# Add tags
cdk.Tags.of(stack).add("Project", "MultiStepLLM")
cdk.Tags.of(stack).add("Environment", env_name)
cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth()