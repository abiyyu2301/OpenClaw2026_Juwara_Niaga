"""Bear — argue strongly that pursuing the lead is a WASTE of time."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class BearAgent(BaseAgent):
    name = "bear"
    system_instruction = (
        "You are a Bear, a skeptical sales-ops manager who pokes holes in leads. "
        "Return only valid JSON. No prose. No markdown."
    )
    default_max_output_tokens = 800
    default_temperature = 0.6

    async def run(
        self,
        *,
        profile: Dict[str, Any],
        offer: Dict[str, Any],
    ) -> LLMResult:
        await self.think("Building case AGAINST…")
        context = {"profile_json": profile, "offer_json": offer}
        return await self.run_llm(context)
