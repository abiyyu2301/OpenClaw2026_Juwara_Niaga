"""Outreach — draft a Bahasa Indonesia first-touch email."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class OutreachAgent(BaseAgent):
    name = "outreach"
    system_instruction = (
        "You write warm, formal-but-friendly Bahasa Indonesia B2B outreach "
        "emails. Return only valid JSON. No prose. No markdown."
    )
    # Pro model + thinking for nuanced Bahasa Indonesia prose.
    default_max_output_tokens = 2500
    default_temperature = 0.6
    default_thinking_budget = 768

    async def run(
        self,
        *,
        profile: Dict[str, Any],
        angle: str,
        offer: Dict[str, Any],
    ) -> LLMResult:
        await self.think("Drafting Bahasa Indonesia email…")
        context = {"profile_json": profile, "angle": angle, "offer_json": offer}
        return await self.run_llm(context)
