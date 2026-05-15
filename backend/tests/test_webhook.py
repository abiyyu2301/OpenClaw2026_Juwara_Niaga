"""Tests the mock-pay webhook path end-to-end:

1. Run orchestrator (creates outreach_sent lead)
2. Inject pricing-question reply (Closer creates payment_pending event)
3. Hit /webhooks/mock-pay/{ref}?status=paid (simulates user paying)
4. Verify AfterCare email is drafted (dry-run send), payment_status=paid,
   lead.status=paid, run.deals_closed += 1

Run:
    python tests/test_webhook.py
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
from db.models import AgentMessage, AgentRun, Campaign, Debate, Lead, LeadAIProfile, OutreachDraft, PaymentEvent, Reply  # noqa: E402
from orchestrator import _handle_reply, run_campaign  # noqa: E402
from routes.webhooks import _handle_payment_status  # noqa: E402
from tools.email import InboundReply  # noqa: E402
from tools.payment.mock import MockPaymentProvider  # noqa: E402


async def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for cls in (AgentMessage, PaymentEvent, Reply, OutreachDraft, Debate, LeadAIProfile, Lead, AgentRun, Campaign):
            db.query(cls).delete()
        db.commit()

        campaign = Campaign(
            name="Niaga pilot",
            target_industry="corporate training providers",
            company_size="10-100",
            geography="Jakarta",
            buyer_role="Director of Operations",
            pain_points="Manual sales cycle.",
            offer="Niaga pilot at Rp 3,000,000/month",
            pricing_range_min=500_000,
            pricing_range_max=2_000_000,
            currency="IDR",
            disqualifiers="Government, banks.",
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
            buyer_name="Ibu Sri Wahyuni",
            buyer_role="Direktur Operasional",
            email="sri@mitraedukasi.example.id",
            raw_notes="Mid-size B2B training provider. Posted sales admin job.",
            status="new",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        run = AgentRun(campaign_id=campaign.id, status="running")
        db.add(run)
        db.commit()
        db.refresh(run)
        campaign_id, lead_id, run_id = campaign.id, lead.id, run.id
    finally:
        db.close()

    # Stage 1 + 2: orchestrator + reply -> closer creates a payment event
    print("=== Stage 1: orchestrator run ===")
    await run_campaign(campaign_id, run_id)

    print("=== Stage 2: pricing-question reply ===")
    db = SessionLocal()
    try:
        run = db.query(AgentRun).get(run_id)
        run.status = "running"
        db.commit()
        lead = db.query(Lead).get(lead_id)
        reply = InboundReply(
            message_id="<x>", in_reply_to=None,
            from_address=lead.email, subject="Re:",
            body="Halo Tim Niaga, terima kasih. Berapa harganya? — Sri",
        )
        await _handle_reply(db, run, lead, reply)
    finally:
        db.close()

    # Stage 3: simulate paid webhook
    print("\n=== Stage 3: webhook (status=paid) ===")
    db = SessionLocal()
    try:
        payment = db.query(PaymentEvent).filter(PaymentEvent.lead_id == lead_id).first()
        if not payment:
            print("FAIL: no payment event created")
            return
        ref = payment.doku_reference_id
    finally:
        db.close()

    MockPaymentProvider.set_status(ref, "paid")
    await _handle_payment_status(ref, "paid")

    # Verify
    db = SessionLocal()
    try:
        lead = db.query(Lead).get(lead_id)
        run = db.query(AgentRun).get(run_id)
        payment = db.query(PaymentEvent).filter(PaymentEvent.lead_id == lead_id).first()
        aftercare_msgs = (
            db.query(AgentMessage)
            .filter(AgentMessage.agent_name == "aftercare")
            .all()
        )
        print(f"\nLead status      : {lead.status}")
        print(f"Payment status   : {payment.payment_status}")
        print(f"Payment paid_at  : {payment.paid_at}")
        print(f"Run deals_closed : {run.deals_closed}")
        print(f"Run revenue      : Rp {run.total_revenue:,}")
        print(f"AfterCare msgs   : {len(aftercare_msgs)} rows")
        for m in aftercare_msgs[-2:]:
            print(f"   {m.role:13} {(m.content or '')[:100]!r}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
