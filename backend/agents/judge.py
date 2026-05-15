"""Judge — read Bull + Bear arguments and render a verdict."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class JudgeAgent(BaseAgent):
    name = "judge"
    system_instruction = (
        "You are the Judge, head of sales. You read adversarial arguments from "
        "a Bull (pursue) and a Bear (skip) and render a calm, decisive verdict. "
        "Return only valid JSON. No prose. No markdown."
    )
    # Visible JSON + thinking budget. Bull/Bear already did the heavy reasoning,
    # so a modest thinking budget is fine. Visible reasoning text needs ~400 tokens.
    default_max_output_tokens = 3000
    default_temperature = 0.2  # decisive, not creative
    default_thinking_budget = 1024

    async def run(
        self,
        *,
        profile: Dict[str, Any],
        bull: Dict[str, Any],
        bear: Dict[str, Any],
        icp: Dict[str, Any],
    ) -> LLMResult:
        await self.think("Reviewing arguments…")
        context = {
            "profile_json": profile,
            "bull_json": bull,
            "bear_json": bear,
            "icp_json": icp,
        }
        return await self.run_llm(context)
