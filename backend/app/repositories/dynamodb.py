"""DynamoDB client factory (AD-1, AD-3, AD-8).

The single place a boto3 client is constructed. Repositories (added by later stories)
build on this. The endpoint override makes local/AWS parity automatic: when
``settings.dynamodb_endpoint`` is set we point at dynamodb-local; when empty, boto3
resolves the real regional endpoint. No environment branching beyond this one check.
"""

from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import get_settings


@lru_cache
def get_dynamodb_client():
    """Return a cached low-level DynamoDB client configured from settings.

    When ``dynamodb_endpoint`` is set (local/emulated) we inject the endpoint and the
    static local credentials. When it is empty (AWS) we pass neither, so boto3's default
    credential chain (ECS task role / instance profile) resolves the real credentials.
    """
    settings = get_settings()
    kwargs = {
        "region_name": settings.aws_region,
        # Fail fast instead of hanging on an unresponsive endpoint.
        "config": Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 2}),
    }
    endpoint = settings.dynamodb_endpoint.strip()
    if endpoint:
        kwargs["endpoint_url"] = endpoint
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("dynamodb", **kwargs)


def list_table_names() -> list[str]:
    """List existing table names — used to prove connectivity in the deep health check."""
    return get_dynamodb_client().list_tables().get("TableNames", [])
