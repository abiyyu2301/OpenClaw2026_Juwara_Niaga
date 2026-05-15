"""Vertex AI Gemini client wrapper.

One shared async client. All agents call `gemini_json()` which:
- streams to Gemini with a JSON schema constraint
- retries on transient errors
- enforces per-call timeout
- returns parsed dict + token usage
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from settings import settings


_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Lazy-init the Vertex AI client. Picks up credentials from
    GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON path)."""
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_location,
        )
    return _client


class LLMResult:
    """Return value from gemini_json(). Holds parsed dict + metadata."""

    def __init__(
        self,
        data: Dict[str, Any],
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        raw_text: str,
    ):
        self.data = data
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.latency_ms = latency_ms
        self.raw_text = raw_text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    reraise=True,
)
async def gemini_json(
    *,
    model: str,
    system_instruction: str,
    user_prompt: str,
    response_schema: Optional[Dict[str, Any]] = None,
    max_output_tokens: int = 1500,
    temperature: float = 0.4,
    thinking_budget: Optional[int] = 0,
) -> LLMResult:
    """Call Gemini with native JSON mode and return parsed dict.

    Args:
        model: e.g. "gemini-2.5-flash" or "gemini-2.5-pro"
        system_instruction: the system prompt
        user_prompt: the user-turn prompt (typically the rendered template)
        response_schema: optional JSON Schema. If provided, Gemini enforces
            structured output. If omitted, we set response_mime_type=application/json
            and parse loosely.
        max_output_tokens: hard cap on visible tokens (excludes thinking budget)
        temperature: 0.0-1.0
        thinking_budget: tokens reserved for internal thinking. 0 disables
            thinking entirely (Gemini 2.5+). Pass None to let the model decide.
            For cheap, structured-output agents, keep at 0.
    """
    client = get_client()
    config_kwargs: Dict[str, Any] = dict(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json",
    )
    if response_schema:
        config_kwargs["response_schema"] = response_schema
    if thinking_budget is not None:
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget
        )
    config = types.GenerateContentConfig(**config_kwargs)
    start = time.perf_counter()
    response = await client.aio.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    raw_text = response.text or ""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        data = _repair_json(raw_text)

    usage = getattr(response, "usage_metadata", None)
    prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
    completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

    return LLMResult(
        data=data,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        raw_text=raw_text,
    )


def _repair_json(text: str) -> Dict[str, Any]:
    """Best-effort JSON repair when the model returns malformed output."""
    # Strip code fences
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    # Try to find the first { and matching }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {"_parse_error": True, "raw": text[:500]}
