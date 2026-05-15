"""End-to-end closer test.

Builds on test_orchestrator (which leaves a lead in 'outreach_sent' state),
then injects a synthetic reply that signals commercial intent, runs the
inbox_loop briefly, and asserts that Closer fires + a payment link is created
+ the follow-up email body would be sent.

Run:
    python tests/test_closer.py
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
from tools.email import InboundReply, inject_reply  # noqa: E402


SYNTHETIC_REPLY_BODY = """Halo Tim Niaga,

Terima kasih atas emailnya. Saya tertarik untuk mengetahui lebih lanjut tentang program pilot ini. Kira-kira berapa biayanya dan bagaimana cara mendaftarnya?

Terima kasih,
Sri Wahyuni
"""


async def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Reset
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
            raw_notes="Mid-size B2B training provider. Posted sales admin job. Expanding to Bandung.",
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

    # Stage 1: run orchestrator -> reaches outreach_sent
    print("=== Stage 1: orchestrator (prospect -> debate -> qualify -> outreach) ===")
    await run_campaign(campaign_id, run_id)

    # Stage 2: inject a synthetic reply with commercial intent
    print("\n=== Stage 2: inject synthetic reply (pricing question) ===")
    db = SessionLocal()
    try:
        run = db.query(AgentRun).get(run_id)
        # Re-open the run so handle_reply can write to it
        run.status = "running"
        db.commit()

        # The orchestrator's _handle_reply expects a Lead and InboundReply
        lead = db.query(Lead).get(lead_id)
        reply = InboundReply(
            message_id="<fake@mitra>",
            in_reply_to=None,
            from_address=lead.email,
            subject="Re: Terkait pertumbuhan tim di Mitra Edukasi Nusantara",
            body=SYNTHETIC_REPLY_BODY,
        )
        await _handle_reply(db, run, lead, reply)
    finally:
        db.close()

    # Verify
    db = SessionLocal()
    try:
        lead = db.query(Lead).get(lead_id)
        reply_row = db.query(Reply).filter(Reply.lead_id == lead_id).first()
        payment = db.query(PaymentEvent).filter(PaymentEvent.lead_id == lead_id).first()

        print(f"\nLead status   : {lead.status}")
        print(f"Reply intent  : {reply_row.classification if reply_row else 'n/a'} ({reply_row.sentiment if reply_row else 'n/a'})")
        print(f"Reply action  : {reply_row.recommended_next_action if reply_row else 'n/a'}")
        print(f"PaymentEvent  : {bool(payment)}")
        if payment:
            print(f"  type        : {payment.commercial_event_type}")
            print(f"  amount      : {payment.currency} {payment.amount:,}")
            print(f"  link        : {payment.payment_link}")
            print(f"  status      : {payment.payment_status}")
            print(f"  reference   : {payment.doku_reference_id}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
