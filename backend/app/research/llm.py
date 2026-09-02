"""Thin LLM layer.

Rule from the architecture: deterministic maths stays deterministic. The model
only writes interpretation and narrative on top of numbers other modules already
computed. If no key is present, every call falls back to a template built from
the same inputs, so the pipeline never fabricates and never hard-fails.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

from . import config

_ENDPOINT = "https://api.anthropic.com/v1/messages"


class LLM:
    def __init__(self) -> None:
        self.enabled = config.LLM_ENABLED
        self.calls = 0
        self.failures = 0

    def write(self, prompt: str, fallback: Callable[[], str], system: str = "",
              max_tokens: int = 700) -> tuple[str, bool]:
        """Returns (text, used_llm)."""
        if not self.enabled:
            return fallback(), False
        body = {
            "model": config.LLM_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        req = urllib.request.Request(
            _ENDPOINT,
            data=json.dumps(body).encode(),
            headers={
                "content-type": "application/json",
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            self.calls += 1
            with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT) as resp:
                data = json.loads(resp.read())
            text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
            return (text.strip() or fallback()), bool(text.strip())
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            self.failures += 1
            return fallback(), False


llm = LLM()
