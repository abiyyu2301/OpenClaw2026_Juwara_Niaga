"""Phase 1 end-to-end pipeline test.

Runs Prospector -> (Bull || Bear) -> Judge on a single in-memory demo lead.
No DB writes (run_id=None). Useful for sanity-checking the agents before
wiring them to the orchestrator.

Usage:
    python tests/test_pipeline.py
    python tests/test_pipeline.py --lead "PT Mitra Edukasi"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from settings import settings  # noqa: E402

if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

from agents.bear import BearAgent  # noqa: E402
from agents.bull import BullAgent  # noqa: E402
from agents.judge import JudgeAgent  # noqa: E402
from agents.prospector import ProspectorAgent  # noqa: E402


DEMO_ICP = {
    "target_industry": "corporate training providers",
    "company_size": "10-100 karyawan",
    "geography": "Jakarta and Jabodetabek",
    "buyer_role": "Founder / Director of Operations",
    "pain_points": "Manual sales cycle, low conversion, no Indonesian-language outreach automation.",
    "disqualifiers": "Government, banks, MLM/network marketing.",
}

DEMO_OFFER = {
    "name": "Niaga pilot",
    "pricing_idr": "3,000,000 per month",
    "outcome": "An autonomous AI sales team that prospects, qualifies, emails (Bahasa Indonesia), and closes via DOKU.",
    "trial": "Workshop booking deposit Rp 500.000, refunded if pilot doesn't sign.",
}

DEMO_LEAD = {
    "company_name": "PT Mitra Edukasi Nusantara",
    "industry": "Corporate training",
    "website": "https://mitraedukasi.example.id",
    "buyer_name": "Ibu Sri Wahyuni",
    "buyer_role": "Direktur Operasional",
    "email": "sri@mitraedukasi.example.id",
    "raw_notes": (
        "Mid-size B2B training provider serving Jakarta corporates. Runs ~12 "
        "leadership workshops/month. Mentioned on Instagram that they're "
        "expanding to Bandung. Currently relies on referrals and Instagram DMs. "
        "Owner posted a job opening for a sales admin last week."
    ),
}


def pretty(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


async def main(lead_name: str) -> None:
    lead = dict(DEMO_LEAD)
    if lead_name and lead_name != DEMO_LEAD["company_name"]:
        lead["company_name"] = lead_name
        lead["raw_notes"] = f"(no notes — testing pipeline against {lead_name})"

    print("=" * 70)
    print(f"PIPELINE TEST · lead = {lead['company_name']}")
    print("=" * 70)

    # 1. Prospector
    prospector = ProspectorAgent(db=None, run_id=None, lead_id=None)
    print("\n[1/4] PROSPECTOR")
    prosp_result = await prospector.run(icp=DEMO_ICP, lead=lead)
    print(f"      {prosp_result.latency_ms}ms · "
          f"{prosp_result.prompt_tokens} in / {prosp_result.completion_tokens} out")
    print(pretty(prosp_result.data))
    profile = prosp_result.data

    # 2. Bull + Bear in parallel
    bull = BullAgent(db=None, run_id=None, lead_id=None)
    bear = BearAgent(db=None, run_id=None, lead_id=None)
    print("\n[2/4] BULL  vs  [3/4] BEAR  (parallel)")
    bull_result, bear_result = await asyncio.gather(
        bull.run(profile=profile, offer=DEMO_OFFER),
        bear.run(profile=profile, offer=DEMO_OFFER),
    )
    print(f"      BULL : {bull_result.latency_ms}ms · "
          f"{bull_result.prompt_tokens} in / {bull_result.completion_tokens} out")
    print(pretty(bull_result.data))
    print(f"      BEAR : {bear_result.latency_ms}ms · "
          f"{bear_result.prompt_tokens} in / {bear_result.completion_tokens} out")
    print(pretty(bear_result.data))

    # 3. Judge
    judge = JudgeAgent(db=None, run_id=None, lead_id=None)
    print("\n[4/4] JUDGE")
    verdict_result = await judge.run(
        profile=profile,
        bull=bull_result.data,
        bear=bear_result.data,
        icp=DEMO_ICP,
    )
    print(f"      {verdict_result.latency_ms}ms · "
          f"{verdict_result.prompt_tokens} in / {verdict_result.completion_tokens} out")
    print(pretty(verdict_result.data))

    print("\n" + "=" * 70)
    qualified = verdict_result.data.get("qualified")
    print(f"VERDICT: {'QUALIFIED' if qualified else 'DISQUALIFIED'}")
    total_in = (prosp_result.prompt_tokens + bull_result.prompt_tokens
                + bear_result.prompt_tokens + verdict_result.prompt_tokens)
    total_out = (prosp_result.completion_tokens + bull_result.completion_tokens
                 + bear_result.completion_tokens + verdict_result.completion_tokens)
    print(f"TOTAL TOKENS: {total_in} in / {total_out} out across 4 agents")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lead", default=DEMO_LEAD["company_name"])
    args = parser.parse_args()
    asyncio.run(main(args.lead))
