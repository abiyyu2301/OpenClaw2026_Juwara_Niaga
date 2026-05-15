"""Pydantic API schemas for Niaga REST endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    sales_target_revenue: Optional[int] = None
    geo_place_name: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    geo_radius_km: Optional[int] = None
    rep_name: Optional[str] = None
    rep_email: Optional[str] = None
    rep_phone: Optional[str] = None
    rep_title: Optional[str] = None
    sales_voice: Optional[str] = None
    sales_voice_samples: Optional[str] = None
    promo_asset_url: Optional[str] = None
    promo_asset_type: Optional[str] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    """Partial update — all fields optional."""

    name: Optional[str] = None
    target_industry: Optional[str] = None
    company_size: Optional[str] = None
    geography: Optional[str] = None
    buyer_role: Optional[str] = None
    pain_points: Optional[str] = None
    offer: Optional[str] = None
    pricing_range_min: Optional[int] = None
    pricing_range_max: Optional[int] = None
    currency: Optional[str] = None
    disqualifiers: Optional[str] = None
    autonomous_mode: Optional[bool] = None
    max_leads_per_run: Optional[int] = None
    sales_target_revenue: Optional[int] = None
    geo_place_name: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    geo_radius_km: Optional[int] = None
    rep_name: Optional[str] = None
    rep_email: Optional[str] = None
    rep_phone: Optional[str] = None
    rep_title: Optional[str] = None
    sales_voice: Optional[str] = None
    sales_voice_samples: Optional[str] = None
    promo_asset_url: Optional[str] = None
    promo_asset_type: Optional[str] = None


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    suggested_max_leads: Optional[int] = None


class CampaignAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    campaign_id: int
    file_name: Optional[str]
    mime_type: Optional[str]
    asset_type: Optional[str]
    storage_url: str
    created_at: datetime


class CampaignSummaryOut(BaseModel):
    """Per-campaign stats for dashboard cards."""

    id: int
    name: str
    target_industry: Optional[str] = None
    geography: Optional[str] = None
    geo_place_name: Optional[str] = None
    offer: Optional[str] = None
    currency: str = "IDR"
    max_leads_per_run: int = 10
    sales_target_revenue: Optional[int] = None
    created_at: datetime
    leads_total: int = 0
    leads_processed: int = 0
    leads_qualified: int = 0
    emails_sent: int = 0
    deals_closed: int = 0
    total_revenue: int = 0
    last_run_status: Optional[str] = None
    last_run_at: Optional[datetime] = None
    active_run_id: Optional[int] = None
    qualify_rate: float = 0.0
    close_rate: float = 0.0


class DashboardStatsOut(BaseModel):
    leads_processed: int = 0
    leads_qualified: int = 0
    emails_sent: int = 0
    deals_closed: int = 0
    total_revenue: int = 0
    qualify_rate: float = 0.0
    outreach_rate: float = 0.0
    close_rate: float = 0.0
    revenue_per_deal: float = 0.0
    campaigns: List[CampaignSummaryOut] = Field(default_factory=list)
    maps_api_configured: bool = False


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


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_role: Optional[str] = None
    email: Optional[str] = None
    raw_notes: Optional[str] = None


class LeadBulkItem(BaseModel):
    company_name: str
    email: Optional[str] = None
    industry: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_role: Optional[str] = None
    raw_notes: Optional[str] = None


class LeadBulkCreate(BaseModel):
    campaign_id: int
    leads: list[LeadBulkItem]


class EmailStatusOut(BaseModel):
    configured: bool
    dry_run: bool
    from_address: Optional[str] = None
    message: str


class TestEmailRequest(BaseModel):
    to_address: str
    campaign_id: Optional[int] = None


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
    tokens_used: int
    created_at: datetime


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
