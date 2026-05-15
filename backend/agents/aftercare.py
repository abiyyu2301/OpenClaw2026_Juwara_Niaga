"""AfterCare — Bahasa Indonesia follow-up after a payment event."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class AfterCareAgent(BaseAgent):
    name = "aftercare"
    system_instruction = (
        "You are a warm customer-success specialist writing in Bahasa "
        "Indonesia. Return only valid JSON. No prose. No markdown."
    )
    default_max_output_tokens = 2000
    default_temperature = 0.5
    default_thinking_budget = 0  # short, formulaic follow-up; no thinking

    async def run(
        self,
        *,
        lead_summary: str,
        event: Dict[str, Any],
        status: str,
    ) -> LLMResult:
        await self.think(f"Composing post-payment email ({status})…")
        context = {"lead_summary": lead_summary, "event_json": event, "status": status}
        return await self.run_llm(context)
