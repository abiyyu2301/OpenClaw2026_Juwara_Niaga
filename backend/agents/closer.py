"""Closer — decide whether to send a DOKU payment link, and which type/amount."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class CloserAgent(BaseAgent):
    name = "closer"
    system_instruction = (
        "You are a senior B2B sales closer. You decide whether to send a "
        "DOKU payment link based on the prospect's reply intent and the "
        "ICP pricing range. Return only valid JSON. No prose. No markdown."
    )
    # Pro + thinking — this is a commercial decision worth reasoning about.
    default_max_output_tokens = 3000
    default_temperature = 0.3
    default_thinking_budget = 1024

    async def run(
        self,
        *,
        lead_summary: str,
        reply_analysis: Dict[str, Any],
        pricing_range_idr: Dict[str, Any],
    ) -> LLMResult:
        await self.think("Deciding payment link…")
        context = {
            "lead_summary": lead_summary,
            "reply_analysis": reply_analysis,
            "pricing_range_idr": pricing_range_idr,
        }
        return await self.run_llm(context)
