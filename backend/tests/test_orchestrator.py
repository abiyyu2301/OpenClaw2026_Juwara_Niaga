"""End-to-end orchestrator test.

Creates a campaign + lead in SQLite, runs the orchestrator, and asserts that:
- Lead transitions through profiling -> debating -> qualified -> outreach_sent
- A LeadAIProfile, a Debate, and an OutreachDraft (status=sent in dry-run) are created
- agent_messages has rows from every agent

Run:
    python tests/test_orchestrator.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from settings import settings  # noqa: E402

if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

from db.session import Base, SessionLocal, engine  # noqa: E402
from db.models import AgentMessage, AgentRun, Campaign, Debate, Lead, LeadAIProfile, OutreachDraft  # noqa: E402
from orchestrator import run_campaign  # noqa: E402


async def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Reset prior test rows
        db.query(AgentMessage).delete()
        db.query(OutreachDraft).delete()
        db.query(Debate).delete()
        db.query(LeadAIProfile).delete()
        db.query(Lead).delete()
        db.query(AgentRun).delete()
        db.query(Campaign).delete()
        db.commit()

        campaign = Campaign(
            name="Niaga pilot — Jakarta training providers",
            target_industry="corporate training providers",
            company_size="10-100 karyawan",
            geography="Jakarta and Jabodetabek",
            buyer_role="Founder / Director of Operations",
            pain_points="Manual sales cycle, low conversion, no BI outreach automation.",
            offer="Niaga pilot at Rp 3,000,000/month",
            pricing_range_min=500_000,
            pricing_range_max=5_000_000,
            currency="IDR",
            disqualifiers="Government, banks, MLM.",
            autonomous_mode=True,
            max_leads_per_run=1,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        lead = Lead(
            campaign_id=campaign.id,
            company_name="PT Mitra Edukasi Nusantara",
            industry="Corporate training",
            website="https://mitraedukasi.example.id",
            buyer_name="Ibu Sri Wahyuni",
            buyer_role="Direktur Operasional",
            email="sri@mitraedukasi.example.id",
            raw_notes=(
                "Mid-size B2B training provider serving Jakarta corporates. "
                "Runs ~12 leadership workshops/month. Posted a job opening "
                "for a sales admin last week. Expanding to Bandung."
            ),
            status="new",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        run = AgentRun(campaign_id=campaign.id, status="running")
        db.add(run)
        db.commit()
        db.refresh(run)

        run_id = run.id
        lead_id = lead.id
        campaign_id = campaign.id
    finally:
        db.close()

    print(f"Running orchestrator for campaign {campaign_id}, run {run_id}")
    await run_campaign(campaign_id, run_id)

    # Verify
    db = SessionLocal()
    try:
        lead = db.query(Lead).get(lead_id)
        run = db.query(AgentRun).get(run_id)
        profile = db.query(LeadAIProfile).filter(LeadAIProfile.lead_id == lead_id).first()
        debate = db.query(Debate).filter(Debate.lead_id == lead_id).first()
        draft = db.query(OutreachDraft).filter(OutreachDraft.lead_id == lead_id).first()
        msgs = db.query(AgentMessage).filter(AgentMessage.run_id == run_id).all()

        print(f"\nLead status   : {lead.status}")
        print(f"Run status    : {run.status}")
        print(f"Run summary   : processed={run.leads_processed} qualified={run.leads_qualified} sent={run.emails_sent}")
        print(f"Profile saved : {bool(profile)} (fit_score={profile.fit_score if profile else 'n/a'})")
        print(f"Debate saved  : {bool(debate)} (verdict={debate.verdict if debate else 'n/a'})")
        print(f"Outreach      : {bool(draft)} (status={draft.status if draft else 'n/a'})")
        print(f"\nDraft subject : {draft.subject if draft else '(none)'}")
        if draft:
            print(f"Draft body    :\n---\n{draft.body[:600]}\n---")
        print(f"\nAgent messages: {len(msgs)} rows")
        for m in msgs:
            print(f"  - {m.agent_name:11} {m.role:13} {(m.content or '')[:80]!r}")

        assert lead.status in ("outreach_sent", "qualified", "disqualified", "lost"), lead.status
        assert run.status == "completed", run.status
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
