"""LeadFinder — uses Gemini with Google Search grounding to discover real
Indonesian organizations matching the ICP. Saves them as Lead rows so the
orchestrator can then process them through the normal Prospect -> Debate
-> Outreach pipeline.

This is the "tool use" piece judges care about: a real external API call
(Google Search via Vertex AI grounding) feeding the agent loop.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agents.base import BaseAgent
from agents.llm import LLMResult


class LeadFinderAgent(BaseAgent):
    name = "leadfinder"
    system_instruction = (
        "You are an Indonesian B2B market researcher. You discover real "
        "Indonesian companies that match a sales ICP using Google Search. "
        "Return only valid JSON. No prose. No markdown. No commentary about "
        "search queries."
    )
    # Pro + thinking + grounding. This is the most cognitively demanding agent.
    default_max_output_tokens = 4000
    default_temperature = 0.4
    default_thinking_budget = 2048
    default_enable_google_search = True

    def model_id(self) -> str:
        # Override default model_<name> lookup — leadfinder needs Pro for
        # grounding quality.
        from settings import settings
        return settings.model_judge  # gemini-2.5-pro

    async def run(
        self,
        *,
        icp: Dict[str, Any],
        offer: Dict[str, Any],
        known_companies: List[str],
        n: int = 3,
    ) -> LLMResult:
        await self.think(f"Searching the web for {n} {icp.get('target_industry', 'leads')} in {icp.get('geography', 'Indonesia')}…")
        context = {
            "icp_json": icp,
            "offer_json": offer,
            "known_companies": known_companies or ["(none yet)"],
            "geography": icp.get("geography", "Indonesia"),
            "target_industry": icp.get("target_industry", "any"),
            "n": str(n),
        }
        return await self.run_llm(context)
