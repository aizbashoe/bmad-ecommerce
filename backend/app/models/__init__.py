"""Pydantic domain + request/response models (AD-1, AD-5). Populated by later stories.

`CamelModel` is the base for all API request/response models so JSON is camelCase on the
wire (AD-5) while Python code uses snake_case. Populated by later stories.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: snake_case in Python, camelCase in JSON; accepts either on input."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
