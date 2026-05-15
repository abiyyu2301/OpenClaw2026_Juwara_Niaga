"""Niaga orchestrator — the autonomous loop the competition rules mandate.

This is the deterministic state machine that drives the agents. There is no
LLM call in this file; the loop simply decides what to do next given the
current lead state and the agents' verdicts.

Two coroutines run concurrently per active run:
    run_campaign(campaign_id, run_id)
        Walks unprocessed leads through Prospector -> Debate -> Outreach.
    inbox_loop(run_id)
        Polls IMAP for replies, classifies them, and (in autonomous mode)
        invokes the Closer agent + payment provider when intent is hot.

A run ends when:
    - all leads up to max_leads_per_run are processed (status transitions out
      of 'new' / 'profiling' / 'debating'), OR
    - pause_run() is called, OR
    - a hard timeout / cost cap trips.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from agents.bear import BearAgent
from agents.bull import BullAgent
from agents.closer import CloserAgent
from agents.judge import JudgeAgent
from agents.outreach import OutreachAgent
from agents.prospector import ProspectorAgent
from agents.reply import ReplyAgent
from db.models import (
    AgentRun, Campaign, Debate, Lead, LeadAIProfile, OutreachDraft,
    PaymentEvent, Reply,
)
from db.session import SessionLocal
from campaign_context import email_sender, format_geography, icp_dict, offer_dict, outreach_context
from settings import settings
from tools.email import poll_inbox, send_email
from tools.payment import get_payment_provider
from websocket import hub

log = logging.getLogger(__name__)


# ---- run lifecycle -----------------------------------------------------

_paused_runs: set[int] = set()


def pause_run(run_id: int) -> None:
    _paused_runs.add(run_id)


def resume_run(run_id: int) -> None:
    _paused_runs.discard(run_id)


def is_paused(run_id: int) -> bool:
    return run_id in _paused_runs


# ---- helpers -----------------------------------------------------------

def _icp_dict(campaign: Campaign) -> dict:
    return icp_dict(campaign)


def _offer_dict(campaign: Campaign) -> dict:
    return offer_dict(campaign)


def _lead_dict(lead: Lead) -> dict:
    return {
        "company_name": lead.company_name,
        "industry": lead.industry,
        "website": lead.website,
        "linkedin_url": lead.linkedin_url,
        "buyer_name": lead.buyer_name,
        "buyer_role": lead.buyer_role,
        "email": lead.email,
        "raw_notes": lead.raw_notes,
    }


def _set_lead_status(db: Session, lead: Lead, status: str) -> None:
    lead.status = status
    db.commit()


async def _stream_run_event(run_id: int, agent: str, role: str, content: str, lead_id: Optional[int] = None) -> None:
    await hub.broadcast(
        run_id,
        {"agent": agent, "role": role, "content": content, "lead_id": lead_id, "ts": time.time()},
    )


# ---- main loop ---------------------------------------------------------

async def run_campaign(campaign_id: int, run_id: int) -> None:
    """The autonomous loop. One call processes up to max_leads_per_run leads."""
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).get(campaign_id)
        run = db.query(AgentRun).get(run_id)
        if not campaign or not run:
            return

        await _stream_run_event(run_id, "system", "thought", f"Run {run_id} started for campaign '{campaign.name}'")

        leads = (
            db.query(Lead)
            .filter(Lead.campaign_id == campaign_id, Lead.status == "new")
            .order_by(Lead.id)
            .limit(campaign.max_leads_per_run or settings.max_leads_per_run)
            .all()
        )

        for lead in leads:
            if is_paused(run_id):
                run.status = "paused"
                db.commit()
                await _stream_run_event(run_id, "system", "thought", "Paused by operator")
                return

            try:
                await _process_lead(db, campaign, run, lead)
            except Exception as exc:
                log.exception("Lead %s failed: %s", lead.id, exc)
                _set_lead_status(db, lead, "lost")
                await _stream_run_event(run_id, "system", "thought", f"Lead {lead.company_name} errored: {exc!s}", lead_id=lead.id)

            run.leads_processed = (run.leads_processed or 0) + 1
            db.commit()

        run.status = "completed"
        run.ended_at = datetime.now(timezone.utc)
        db.commit()
        await _stream_run_event(run_id, "system", "thought", f"Run {run_id} completed: {run.leads_processed} leads processed, {run.leads_qualified or 0} qualified, {run.emails_sent or 0} emails sent")
    finally:
        db.close()


async def _process_lead(db: Session, campaign: Campaign, run: AgentRun, lead: Lead) -> None:
    """One lead through Prospect -> Debate -> Outreach."""
    icp = _icp_dict(campaign)
    offer = _offer_dict(campaign)
    lead_payload = _lead_dict(lead)

    # 1. Prospect
    _set_lead_status(db, lead, "profiling")
    prospector = ProspectorAgent(db=db, run_id=run.id, lead_id=lead.id)
    prosp_result = await prospector.run(icp=icp, lead=lead_payload)
    profile = prosp_result.data
    if profile.get("_parse_error"):
        log.warning("Prospector parse error for lead %s", lead.id)
    db.add(LeadAIProfile(
        lead_id=lead.id,
        why_relevant=profile.get("why_relevant"),
        detected_trigger=profile.get("detected_trigger"),
        fit_score=profile.get("estimated_fit_score"),
        confidence_level=profile.get("confidence_level"),
        source_evidence_json=json.dumps(profile.get("source_evidence", []), ensure_ascii=False),
        recommended_outreach_angle=profile.get("recommended_outreach_angle"),
        tokens_used=prosp_result.prompt_tokens + prosp_result.completion_tokens,
    ))
    _set_lead_status(db, lead, "profiled")

    # 2. Adversarial debate (parallel)
    _set_lead_status(db, lead, "debating")
    bull = BullAgent(db=db, run_id=run.id, lead_id=lead.id)
    bear = BearAgent(db=db, run_id=run.id, lead_id=lead.id)
    bull_result, bear_result = await asyncio.gather(
        bull.run(profile=profile, offer=offer),
        bear.run(profile=profile, offer=offer),
    )

    # 3. Judge
    judge = JudgeAgent(db=db, run_id=run.id, lead_id=lead.id)
    verdict_result = await judge.run(
        profile=profile, bull=bull_result.data, bear=bear_result.data, icp=icp,
    )
    verdict = verdict_result.data

    db.add(Debate(
        lead_id=lead.id,
        bull_argument_json=json.dumps(bull_result.data, ensure_ascii=False),
        bear_argument_json=json.dumps(bear_result.data, ensure_ascii=False),
        verdict="qualified" if verdict.get("qualified") else "disqualified",
        fit_score=verdict.get("fit_score"),
        confidence=verdict.get("confidence"),
        reasoning=verdict.get("reasoning"),
        recommended_angle=verdict.get("recommended_outreach_angle"),
        tokens_used=(
            bull_result.prompt_tokens + bull_result.completion_tokens
            + bear_result.prompt_tokens + bear_result.completion_tokens
            + verdict_result.prompt_tokens + verdict_result.completion_tokens
        ),
    ))

    if not verdict.get("qualified"):
        _set_lead_status(db, lead, "disqualified")
        await _stream_run_event(
            run.id, "judge", "decision",
            f"DISQUALIFIED — {verdict.get('key_factor', verdict.get('reasoning', 'no fit'))}",
            lead_id=lead.id,
        )
        db.commit()
        return

    run.leads_qualified = (run.leads_qualified or 0) + 1
    _set_lead_status(db, lead, "qualified")
    await _stream_run_event(
        run.id, "judge", "decision",
        f"QUALIFIED — fit {verdict.get('fit_score')} — {verdict.get('key_factor', '')}",
        lead_id=lead.id,
    )

    # 4. Outreach
    outreach = OutreachAgent(db=db, run_id=run.id, lead_id=lead.id)
    email_result = await outreach.run(
        profile=profile,
        angle=verdict.get("recommended_outreach_angle", ""),
        offer=offer,
        outreach_ctx=outreach_context(campaign),
    )
    email = email_result.data
    if email.get("_parse_error"):
        log.warning("Outreach parse error for lead %s", lead.id)
        _set_lead_status(db, lead, "lost")
        return

    draft = OutreachDraft(
        lead_id=lead.id,
        draft_type="first_email",
        language="id",
        subject=email.get("subject", ""),
        body=email.get("body", ""),
        status="drafted",
    )
    db.add(draft)
    db.commit()

    if campaign.autonomous_mode and lead.email:
        await _stream_run_event(run.id, "outreach", "tool_call", f"sending email to {lead.email}", lead_id=lead.id)
        try:
            sender = email_sender(campaign)
            msg_id = await send_email(
                to_address=lead.email,
                subject=draft.subject,
                body=draft.body,
                from_display_name=sender["from_display_name"],
                reply_to=sender["reply_to"],
            )
            draft.smtp_message_id = msg_id
            draft.sent_at = datetime.now(timezone.utc)
            draft.status = "sent"
            run.emails_sent = (run.emails_sent or 0) + 1
            _set_lead_status(db, lead, "outreach_sent")
        except Exception as exc:
            log.exception("Send failed: %s", exc)
            draft.status = "failed"
            _set_lead_status(db, lead, "lost")
        db.commit()


# ---- inbox loop --------------------------------------------------------

async def inbox_loop(run_id: int) -> None:
    """Poll for replies and classify them. Runs alongside run_campaign."""
    while True:
        if is_paused(run_id):
            await asyncio.sleep(settings.imap_poll_interval_seconds)
            continue

        db = SessionLocal()
        try:
            run = db.query(AgentRun).get(run_id)
            if not run or run.status not in ("running", "paused"):
                return

            replies = await poll_inbox()
            for incoming in replies:
                lead = _match_reply_to_lead(db, incoming)
                if not lead:
                    log.info("Unmatched reply from %s", incoming.from_address)
                    continue

                await _handle_reply(db, run, lead, incoming)
        finally:
            db.close()

        await asyncio.sleep(settings.imap_poll_interval_seconds)


def _match_reply_to_lead(db: Session, reply) -> Optional[Lead]:
    """Match an inbound reply to a lead by email address, In-Reply-To, or sender."""
    # 1. Try by In-Reply-To against sent SMTP Message-IDs
    if reply.in_reply_to:
        draft = (
            db.query(OutreachDraft)
            .filter(OutreachDraft.smtp_message_id == reply.in_reply_to)
            .first()
        )
        if draft:
            return db.query(Lead).get(draft.lead_id)
    # 2. Fall back to email-address match
    addr = reply.from_address
    if "<" in addr:
        addr = addr.split("<")[-1].rstrip(">").strip()
    addr = addr.split(",")[0].strip().lower()
    return db.query(Lead).filter(Lead.email == addr).first()


async def _handle_reply(db: Session, run: AgentRun, lead: Lead, incoming) -> None:
    last_draft = (
        db.query(OutreachDraft)
        .filter(OutreachDraft.lead_id == lead.id)
        .order_by(OutreachDraft.sent_at.desc())
        .first()
    )
    last_summary = (
        f"Subject: {last_draft.subject}\n{last_draft.body[:300]}"
        if last_draft
        else "(no prior outreach found)"
    )

    classifier = ReplyAgent(db=db, run_id=run.id, lead_id=lead.id)
    result = await classifier.run(
        lead_summary=f"{lead.company_name} ({lead.industry})",
        last_outreach_summary=last_summary,
        reply_text=incoming.body[:2000],
    )
    data = result.data

    db.add(Reply(
        lead_id=lead.id,
        raw_reply_text=incoming.body,
        classification=data.get("classification"),
        sentiment=data.get("sentiment"),
        confidence=data.get("confidence"),
        recommended_next_action=data.get("recommended_next_action"),
        suggested_response="",
        new_lead_status=data.get("new_lead_status"),
        received_at=incoming.received_at,
    ))
    new_status = data.get("new_lead_status") or "replied"
    _set_lead_status(db, lead, new_status)
    db.commit()

    await _stream_run_event(
        run.id, "reply", "decision",
        f"{lead.company_name}: {data.get('classification')} ({data.get('sentiment')})",
        lead_id=lead.id,
    )

    # Closer handoff: any commercial intent (pricing question, meeting request,
    # explicit ask for a link) wakes the Closer. The Closer makes the final
    # call about whether to actually send a payment link.
    commercial_signals = {
        "send_payment_link", "send_pricing", "schedule_meeting",
    }
    classification = data.get("classification", "")
    if (
        data.get("recommended_next_action") in commercial_signals
        or classification in {"interested", "pricing_question", "meeting_requested"}
    ):
        await _close_with_payment(db, run, lead, data)


async def _close_with_payment(db: Session, run: AgentRun, lead: Lead, reply_analysis: dict) -> None:
    """Closer + payment provider + email handoff. Mock or DOKU per settings."""
    campaign = db.query(Campaign).get(lead.campaign_id)
    pricing = {
        "min": campaign.pricing_range_min,
        "max": campaign.pricing_range_max,
        "currency": campaign.currency,
    }
    closer = CloserAgent(db=db, run_id=run.id, lead_id=lead.id)
    decision_result = await closer.run(
        lead_summary=f"{lead.company_name} ({lead.industry}) — buyer: {lead.buyer_name}",
        reply_analysis=reply_analysis,
        pricing_range_idr=pricing,
    )
    decision = decision_result.data
    if decision.get("_parse_error") or not decision.get("should_send_payment_link"):
        await _stream_run_event(
            run.id, "closer", "decision",
            f"Decided NOT to send link: {decision.get('rationale', '')[:120]}",
            lead_id=lead.id,
        )
        return

    if not campaign.autonomous_mode:
        await _stream_run_event(run.id, "closer", "decision", "Autonomous mode off — link not sent", lead_id=lead.id)
        return

    provider = get_payment_provider()
    amount = int(decision.get("amount_idr") or 0)
    event_type = decision.get("commercial_event_type") or "consultation_deposit"
    expires_in_hours = int(decision.get("expires_in_hours") or 72)

    await _stream_run_event(run.id, "closer", "tool_call", f"creating {provider.name} payment link Rp{amount:,}", lead_id=lead.id)
    link = await provider.create_payment_link(
        amount=amount,
        currency=campaign.currency or "IDR",
        description=event_type,
        expires_in_hours=expires_in_hours,
        lead_id=lead.id,
        reference=f"lead-{lead.id}",
    )

    db.add(PaymentEvent(
        lead_id=lead.id,
        commercial_event_type=event_type,
        amount=amount,
        currency=campaign.currency or "IDR",
        payment_link=link.url,
        payment_status="created",
        doku_reference_id=link.reference_id,
        expires_at=link.expires_at,
    ))
    _set_lead_status(db, lead, "payment_pending")
    db.commit()

    # Send the follow-up email with the link.
    subject = decision.get("follow_up_subject_bahasa") or f"Link Pembayaran — {event_type}"
    body = decision.get("follow_up_message_bahasa") or ""
    body_with_link = f"{body}\n\nLink pembayaran: {link.url}\nBerlaku selama {expires_in_hours} jam.\n\nSalam hangat,\nTim Niaga"

    if lead.email:
        try:
            sender = email_sender(campaign)
            await send_email(
                to_address=lead.email,
                subject=subject,
                body=body_with_link,
                from_display_name=sender["from_display_name"],
                reply_to=sender["reply_to"],
            )
            run.emails_sent = (run.emails_sent or 0) + 1
            db.commit()
            await _stream_run_event(
                run.id, "closer", "message_out",
                f"Sent payment link Rp{amount:,} to {lead.email}",
                lead_id=lead.id,
            )
        except Exception as exc:
            log.exception("Closer email send failed: %s", exc)
