"""Bull — argue strongly that the lead is WORTH pursuing."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class BullAgent(BaseAgent):
    name = "bull"
    system_instruction = (
        "You are a Bull, an aggressive SDR who advocates for the lead. "
        "Return only valid JSON. No prose. No markdown."
    )
    default_max_output_tokens = 800
    default_temperature = 0.6  # slightly higher → more vivid arguments

    async def run(
        self,
        *,
        profile: Dict[str, Any],
        offer: Dict[str, Any],
    ) -> LLMResult:
        await self.think("Building case FOR…")
        context = {"profile_json": profile, "offer_json": offer}
        return await self.run_llm(context)
