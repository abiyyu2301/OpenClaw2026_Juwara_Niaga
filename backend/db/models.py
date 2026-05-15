"""SQLAlchemy models — 9 tables matching docs/BUILD_PLAN.md §6.

`agent_messages` is the evidence locker for the autonomy claim: every LLM
call and every tool call writes a row.
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from db.session import Base


def _now():
    return datetime.utcnow()


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    target_industry = Column(String(200))
    company_size = Column(String(100))
    geography = Column(String(200))
    buyer_role = Column(String(200))
    pain_points = Column(Text)
    offer = Column(Text)
    pricing_range_min = Column(Integer)
    pricing_range_max = Column(Integer)
    currency = Column(String(10), default="IDR")
    disqualifiers = Column(Text)
    autonomous_mode = Column(Boolean, default=True)
    max_leads_per_run = Column(Integer, default=10)
    created_at = Column(DateTime, default=_now)

    leads = relationship("Lead", back_populates="campaign", cascade="all, delete-orphan")
    runs = relationship("AgentRun", back_populates="campaign", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    company_name = Column(String(300), nullable=False)
    industry = Column(String(200))
    website = Column(String(500))
    linkedin_url = Column(String(500))
    buyer_name = Column(String(200))
    buyer_role = Column(String(200))
    email = Column(String(300))
    raw_notes = Column(Text)
    # status: new, profiling, profiled, debating, qualified, disqualified,
    #         outreach_sent, replied, warm, closing, payment_pending,
    #         paid, lost, do_not_contact
    status = Column(String(50), default="new", index=True)
    created_at = Column(DateTime, default=_now)

    campaign = relationship("Campaign", back_populates="leads")
    profile = relationship("LeadAIProfile", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    debates = relationship("Debate", back_populates="lead", cascade="all, delete-orphan")
    drafts = relationship("OutreachDraft", back_populates="lead", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="lead", cascade="all, delete-orphan")
    payment_events = relationship("PaymentEvent", back_populates="lead", cascade="all, delete-orphan")


class LeadAIProfile(Base):
    __tablename__ = "lead_ai_profiles"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    why_relevant = Column(Text)
    detected_trigger = Column(Text)
    fit_score = Column(Integer)
    confidence_level = Column(String(20))
    source_evidence_json = Column(Text)
    recommended_outreach_angle = Column(Text)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)

    lead = relationship("Lead", back_populates="profile")


class Debate(Base):
    """Bull/Bear/Judge debate — the demo differentiator."""

    __tablename__ = "debates"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    bull_argument_json = Column(Text)
    bear_argument_json = Column(Text)
    verdict = Column(String(20))  # qualified | disqualified
    fit_score = Column(Integer)
    confidence = Column(String(20))
    reasoning = Column(Text)
    recommended_angle = Column(Text)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)

    lead = relationship("Lead", back_populates="debates")


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    # draft_type: first_email | follow_up_1 | follow_up_2 | objection_reply | meeting_request
    draft_type = Column(String(50), default="first_email")
    language = Column(String(10), default="id")
    subject = Column(String(300))
    body = Column(Text)
    sent_at = Column(DateTime)
    smtp_message_id = Column(String(300))
    # status: drafted | approved | sent | failed
    status = Column(String(20), default="drafted")
    created_at = Column(DateTime, default=_now)

    lead = relationship("Lead", back_populates="drafts")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    raw_reply_text = Column(Text)
    # classification: interested | not_now | not_relevant | wrong_person |
    #   request_for_info | pricing_question | meeting_requested |
    #   unsubscribe_do_not_contact | negative_response
    classification = Column(String(50))
    sentiment = Column(String(20))
    confidence = Column(String(20))
    recommended_next_action = Column(String(50))
    suggested_response = Column(Text)
    new_lead_status = Column(String(50))
    received_at = Column(DateTime, default=_now)
    created_at = Column(DateTime, default=_now)

    lead = relationship("Lead", back_populates="replies")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    # commercial_event_type: paid_trial | pilot_fee | consultation_deposit |
    #   onboarding_fee | subscription_first | workshop_booking | renewal
    commercial_event_type = Column(String(50))
    amount = Column(Integer)
    currency = Column(String(10), default="IDR")
    payment_link = Column(String(500))
    # payment_status: created | pending | paid | failed | expired | refunded
    payment_status = Column(String(20), default="created")
    doku_reference_id = Column(String(200))
    expires_at = Column(DateTime)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    lead = relationship("Lead", back_populates="payment_events")


class AgentRun(Base):
    """One row per orchestrator run session."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    started_at = Column(DateTime, default=_now)
    ended_at = Column(DateTime)
    leads_processed = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    deals_closed = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    # status: running | completed | paused | failed
    status = Column(String(20), default="running")
    error_message = Column(Text)

    campaign = relationship("Campaign", back_populates="runs")
    messages = relationship("AgentMessage", back_populates="run", cascade="all, delete-orphan")


class AgentMessage(Base):
    """Evidence locker for the 'Autonomy & Agent Behaviour' judging.

    One row per agent action — thought, tool_call, tool_result, decision,
    message_out. The Live Agent Feed reads from this table over WebSocket.
    """

    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    agent_name = Column(String(50), index=True)
    # role: thought | tool_call | tool_result | decision | message_out
    role = Column(String(20))
    content = Column(Text)
    tool_calls_json = Column(Text)
    tool_results_json = Column(Text)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    model = Column(String(100))
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=_now, index=True)

    run = relationship("AgentRun", back_populates="messages")
