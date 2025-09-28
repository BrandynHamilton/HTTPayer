# httpayer_cli/schemas.py
from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class DraftCall(BaseModel):
    method: str = Field(description="HTTP method, e.g., GET/POST")
    api_url: HttpUrl = Field(description="Full URL to call")
    headers: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    data: Optional[Any] = Field(default=None)

    @field_validator("method")
    @classmethod
    def upper_http_method(cls, v: str) -> str:
        return v.upper()
