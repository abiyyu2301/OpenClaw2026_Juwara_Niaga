"""Prospector — enrich a raw lead with web data and produce a structured profile."""

from __future__ import annotations

from typing import Any, Dict

from agents.base import BaseAgent
from agents.llm import LLMResult


class ProspectorAgent(BaseAgent):
    name = "prospector"
    system_instruction = (
        "You are a B2B sales analyst. Return only valid JSON. "
        "No prose before or after the JSON. No markdown code fences."
    )
    default_max_output_tokens = 1200
    default_temperature = 0.3

    async def run(
        self,
        *,
        icp: Dict[str, Any],
        lead: Dict[str, Any],
        web_context: str = "",
    ) -> LLMResult:
        await self.think(f"Researching {lead.get('company_name', 'lead')}…")
        context = {
            "icp_json": icp,
            "lead_json": lead,
            "web_context": web_context or "(no web context available)",
        }
        return await self.run_llm(context)
