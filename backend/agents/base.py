"""BaseAgent — every Niaga agent inherits from this.

Responsibilities:
- Load a prompt template from `prompts/<agent_name>.txt`
- Render it with kwargs (Python format)
- Call Gemini via the shared `gemini_json` wrapper
- Log the call to `agent_messages` (the evidence locker)
- Broadcast over WebSocket to the live agent feed

Subclasses override `name`, `model_setting_key`, and `default_max_output_tokens`,
and provide a `run(...)` method that builds the prompt context dict.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from agents.llm import LLMResult, gemini_json
from db.models import AgentMessage
from settings import settings
from websocket import hub


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class BaseAgent:
    """Subclasses set these class attributes."""

    name: str = "base"
    system_instruction: str = ""
    default_max_output_tokens: int = 1000
    default_temperature: float = 0.4
    # Gemini 2.5 thinking budget. 0 = disabled (fast/cheap, no reasoning).
    # Higher = more reasoning before emitting the final JSON.
    default_thinking_budget: Optional[int] = 0

    def __init__(
        self,
        *,
        db: Session,
        run_id: Optional[int] = None,
        lead_id: Optional[int] = None,
    ):
        self.db = db
        self.run_id = run_id
        self.lead_id = lead_id

    # --- subclass hook ---
    def model_id(self) -> str:
        """Return the configured model for this agent. Default: lookup
        ``MODEL_<NAME>`` in settings."""
        attr = f"model_{self.name}"
        return getattr(settings, attr, settings.model_judge)

    def _load_prompt_template(self) -> str:
        path = PROMPTS_DIR / f"{self.name}.txt"
        return path.read_text(encoding="utf-8")

    def _render_prompt(self, context: Dict[str, Any]) -> str:
        template = self._load_prompt_template()
        # Convert any non-string values to JSON strings for clean embedding.
        rendered_context = {
            k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, indent=2))
            for k, v in context.items()
        }
        try:
            return template.format(**rendered_context)
        except KeyError as e:
            raise RuntimeError(
                f"Prompt for agent '{self.name}' references missing key {e}. "
                f"Provided context keys: {list(rendered_context)}"
            )

    async def _call_llm(
        self,
        *,
        user_prompt: str,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        thinking_budget: Optional[int] = None,
    ) -> LLMResult:
        return await gemini_json(
            model=self.model_id(),
            system_instruction=self.system_instruction,
            user_prompt=user_prompt,
            response_schema=response_schema,
            max_output_tokens=max_output_tokens or self.default_max_output_tokens,
            temperature=temperature if temperature is not None else self.default_temperature,
            thinking_budget=(
                thinking_budget
                if thinking_budget is not None
                else self.default_thinking_budget
            ),
        )

    def _log(
        self,
        *,
        role: str,
        content: str,
        result: Optional[LLMResult] = None,
        tool_calls: Optional[list] = None,
        tool_results: Optional[list] = None,
    ) -> None:
        """Write a row to agent_messages (the evidence locker)."""
        if self.run_id is None:
            return
        msg = AgentMessage(
            run_id=self.run_id,
            lead_id=self.lead_id,
            agent_name=self.name,
            role=role,
            content=content,
            tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
            tool_results_json=json.dumps(tool_results) if tool_results else None,
            prompt_tokens=result.prompt_tokens if result else 0,
            completion_tokens=result.completion_tokens if result else 0,
            model=result.model if result else None,
            latency_ms=result.latency_ms if result else None,
        )
        self.db.add(msg)
        self.db.commit()

    async def _stream(self, role: str, content: str) -> None:
        """Broadcast an event to the live agent feed for this run."""
        if self.run_id is None:
            return
        await hub.broadcast(
            self.run_id,
            {
                "agent": self.name,
                "role": role,
                "content": content,
                "lead_id": self.lead_id,
                "ts": time.time(),
            },
        )

    async def think(self, content: str) -> None:
        """Emit a 'thought' event (for the agent feed) AND log to DB."""
        self._log(role="thought", content=content)
        await self._stream("thought", content)

    async def announce_call(self, model: str) -> None:
        """Emit a 'tool_call' style event saying we're calling the LLM."""
        msg = f"calling {model}…"
        self._log(role="tool_call", content=msg)
        await self._stream("tool_call", msg)

    async def run_llm(self, context: Dict[str, Any], **kwargs) -> LLMResult:
        """Render prompt → call Gemini → log → stream → return result.

        Subclass `run()` methods should call this with a context dict matching
        the placeholders in the prompt template.
        """
        prompt = self._render_prompt(context)
        await self.announce_call(self.model_id())
        try:
            result = await asyncio.wait_for(
                self._call_llm(user_prompt=prompt, **kwargs),
                timeout=settings.agent_call_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._log(role="tool_result", content="(timeout)")
            await self._stream("tool_result", "(timeout)")
            raise
        # Log the result. content = the parsed JSON pretty-printed.
        summary = json.dumps(result.data, ensure_ascii=False)[:800]
        self._log(role="tool_result", content=summary, result=result)
        await self._stream("tool_result", summary)
        return result
