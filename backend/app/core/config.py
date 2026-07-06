"""12-factor configuration (AD-8).

Every environment-specific value is read from an environment variable via a single
typed Settings object. The ONLY difference between local and AWS is DYNAMODB_ENDPOINT
(+ credentials): set it to the dynamodb-local URL locally, leave it empty on AWS so
boto3 uses the real regional endpoint. No `if env == ...` branching anywhere in code.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- DynamoDB / AWS ---
    # Empty string => use AWS default endpoint (production). A URL => local/emulated.
    dynamodb_endpoint: str = Field(default="", alias="DYNAMODB_ENDPOINT")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str = Field(default="local", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="local", alias="AWS_SECRET_ACCESS_KEY")

    # --- Table names (AD-3: one table per aggregate). Consumed by later stories. ---
    products_table: str = Field(default="Products", alias="PRODUCTS_TABLE")
    carts_table: str = Field(default="Carts", alias="CARTS_TABLE")
    orders_table: str = Field(default="Orders", alias="ORDERS_TABLE")

    # --- Domain constants ---
    # Flat placeholder for shipping/tax, in integer minor units (cents) per AD-6.
    flat_shipping: int = Field(default=500, alias="FLAT_SHIPPING")

    # --- HTTP ---
    # Comma-separated list of allowed CORS origins.
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("flat_shipping")
    @classmethod
    def _non_negative_shipping(cls, v: int) -> int:
        if v < 0:
            raise ValueError("FLAT_SHIPPING must be >= 0")
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings are parsed once per process (stateless-friendly)."""
    return Settings()
