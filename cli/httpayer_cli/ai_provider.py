# httpayer_cli/ai_provider.py
from __future__ import annotations
import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    from openai import OpenAI  # pip install openai>=1.0.0
except Exception:  # keep optional
    OpenAI = None


@dataclass
class AIResponse:
    text: str
    raw: Dict[str, Any]


class LLMProvider:
    """Abstract provider interface."""
    def complete(self, system: str, user: str, model: str, max_tokens: int = 800, temperature: float = 0.0) -> AIResponse:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI chat completions (gpt-4o-mini by default)."""

    def __init__(self, api_key: Optional[str] = None):
        if OpenAI is None:
            raise RuntimeError("openai package not installed. `pip install openai`.")
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY or pass --ai-key.")
        self.client = OpenAI(api_key=key)

    def complete(self, system: str, user: str, model: str, max_tokens: int = 800, temperature: float = 0.0) -> AIResponse:
        res = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
        )
        text = (res.choices[0].message.content or "").strip()
        return AIResponse(text=text, raw=res.to_dict())
