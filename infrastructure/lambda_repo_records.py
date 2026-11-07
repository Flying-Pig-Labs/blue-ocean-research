#!/usr/bin/env python3
"""
Lambda function for retrieving stored GitHub repository and issue data
from the PipelineRepos DynamoDB table.
"""

import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("REPOS_TABLE", "PipelineRepos"))


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    repo_name = event.get("pathParameters", {}).get("repoName")
    if not repo_name:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "repoName path parameter is required"}),
        }

    try:
        response = table.query(KeyConditionExpression=Key("repoName").eq(repo_name))
        items = response.get("Items", [])
        repo_item = next((i for i in items if i.get("itemType") == "REPO"), None)
        issues = [i for i in items if i.get("itemType", "").startswith("ISSUE#")]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"repo": repo_item, "issues": issues}, default=decimal_default),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e)}),
        }
