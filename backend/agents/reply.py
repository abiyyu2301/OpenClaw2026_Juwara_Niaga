"""Reply — classify an inbound email reply by intent."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.llm import LLMResult


class ReplyAgent(BaseAgent):
    name = "reply"
    system_instruction = (
        "You are a CRM reply classifier. Return only valid JSON. "
        "No prose. No markdown."
    )
    default_max_output_tokens = 1000
    default_temperature = 0.1  # classification — low temp for consistency
    default_thinking_budget = 0  # classification doesn't need thinking

    async def run(
        self,
        *,
        lead_summary: str,
        last_outreach_summary: str,
        reply_text: str,
    ) -> LLMResult:
        await self.think("Classifying reply…")
        context = {
            "lead_summary": lead_summary,
            "last_outreach_summary": last_outreach_summary,
            "reply_text": reply_text,
        }
        return await self.run_llm(context)
