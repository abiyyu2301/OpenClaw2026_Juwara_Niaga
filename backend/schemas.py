"""Pydantic API schemas for Niaga REST endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CampaignBase(BaseModel):
    name: str
    target_industry: Optional[str] = None
    company_size: Optional[str] = None
    geography: Optional[str] = None
    buyer_role: Optional[str] = None
    pain_points: Optional[str] = None
    offer: Optional[str] = None
    pricing_range_min: Optional[int] = None
    pricing_range_max: Optional[int] = None
    currency: str = "IDR"
    disqualifiers: Optional[str] = None
    autonomous_mode: bool = True
    max_leads_per_run: int = 10


class CampaignCreate(CampaignBase):
    pass


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class LeadBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_role: Optional[str] = None
    email: Optional[str] = None
    raw_notes: Optional[str] = None


class LeadCreate(LeadBase):
    campaign_id: int


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    status: str
    created_at: datetime


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    leads_processed: int
    leads_qualified: int
    emails_sent: int
    deals_closed: int
    total_revenue: int
    total_tokens: int
    status: str
    error_message: Optional[str]


class DebateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lead_id: int
    bull_argument_json: Optional[str]
    bear_argument_json: Optional[str]
    verdict: Optional[str]
    fit_score: Optional[int]
    confidence: Optional[str]
    reasoning: Optional[str]
    recommended_angle: Optional[str]


class AgentMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    lead_id: Optional[int]
    agent_name: str
    role: str
    content: Optional[str]
    model: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    latency_ms: Optional[int]
    created_at: datetime
