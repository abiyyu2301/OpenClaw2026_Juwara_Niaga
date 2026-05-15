"""Campaign CRUD + lead discovery + dashboard summaries + asset uploads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from agents.leadfinder import LeadFinderAgent
from campaign_context import format_geography, icp_dict, offer_dict, suggest_max_leads
from db.models import AgentRun, Campaign, CampaignAsset, Lead
from db.session import get_db
from schemas import (
    CampaignAssetOut,
    CampaignCreate,
    CampaignOut,
    CampaignSummaryOut,
    CampaignUpdate,
    DashboardStatsOut,
    LeadOut,
)
from settings import settings
from tools.storage import resolve_local_asset_path, upload_campaign_asset

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


def _campaign_out(campaign: Campaign) -> CampaignOut:
    data = CampaignOut.model_validate(campaign)
    data.suggested_max_leads = suggest_max_leads(campaign)
    return data


def _summarize_campaign(db: Session, campaign: Campaign) -> CampaignSummaryOut:
    lead_counts = dict(
        db.query(Lead.status, func.count(Lead.id))
        .filter(Lead.campaign_id == campaign.id)
        .group_by(Lead.status)
        .all()
    )
    leads_total = sum(lead_counts.values())
    processed = sum(
        lead_counts.get(s, 0)
        for s in (
            "profiled", "debating", "qualified", "disqualified", "outreach_sent",
            "replied", "warm", "closing", "payment_pending", "paid", "lost",
        )
    )
    qualified = lead_counts.get("qualified", 0) + lead_counts.get("outreach_sent", 0) + lead_counts.get("replied", 0) + lead_counts.get("warm", 0) + lead_counts.get("closing", 0) + lead_counts.get("payment_pending", 0) + lead_counts.get("paid", 0)
    paid = lead_counts.get("paid", 0)

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.campaign_id == campaign.id)
        .order_by(AgentRun.id.desc())
        .all()
    )
    agg_processed = sum(r.leads_processed or 0 for r in runs)
    agg_qualified = sum(r.leads_qualified or 0 for r in runs)
    agg_sent = sum(r.emails_sent or 0 for r in runs)
    agg_closed = sum(r.deals_closed or 0 for r in runs)
    agg_revenue = sum(r.total_revenue or 0 for r in runs)

    last_run = runs[0] if runs else None
    active = next((r for r in runs if r.status in ("running", "paused")), None)

    proc = max(agg_processed, processed)
    qual = max(agg_qualified, qualified)

    return CampaignSummaryOut(
        id=campaign.id,
        name=campaign.name,
        target_industry=campaign.target_industry,
        geography=format_geography(campaign) or campaign.geography,
        geo_place_name=campaign.geo_place_name,
        offer=campaign.offer,
        currency=campaign.currency or "IDR",
        max_leads_per_run=campaign.max_leads_per_run or 10,
        sales_target_revenue=campaign.sales_target_revenue,
        created_at=campaign.created_at,
        leads_total=leads_total,
        leads_processed=proc,
        leads_qualified=qual,
        emails_sent=agg_sent,
        deals_closed=max(agg_closed, paid),
        total_revenue=agg_revenue,
        last_run_status=last_run.status if last_run else None,
        last_run_at=last_run.started_at if last_run else None,
        active_run_id=active.id if active else None,
        qualify_rate=(qual / proc) if proc else 0.0,
        close_rate=(max(agg_closed, paid) / proc) if proc else 0.0,
    )


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("max_leads_per_run") and data.get("sales_target_revenue"):
        c_tmp = Campaign(**data)
        data["max_leads_per_run"] = suggest_max_leads(c_tmp)
    campaign = Campaign(**data)
    if campaign.geo_place_name and not campaign.geography:
        campaign.geography = format_geography(campaign)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _campaign_out(campaign)


@router.get("/dashboard", response_model=DashboardStatsOut)
def dashboard_stats(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).order_by(Campaign.id.desc()).all()
    summaries = [_summarize_campaign(db, c) for c in campaigns]

    proc = sum(s.leads_processed for s in summaries)
    qual = sum(s.leads_qualified for s in summaries)
    sent = sum(s.emails_sent for s in summaries)
    closed = sum(s.deals_closed for s in summaries)
    revenue = sum(s.total_revenue for s in summaries)

    return DashboardStatsOut(
        leads_processed=proc,
        leads_qualified=qual,
        emails_sent=sent,
        deals_closed=closed,
        total_revenue=revenue,
        qualify_rate=(qual / proc) if proc else 0.0,
        outreach_rate=(sent / qual) if qual else 0.0,
        close_rate=(closed / proc) if proc else 0.0,
        revenue_per_deal=(revenue / closed) if closed else 0.0,
        campaigns=summaries,
        maps_api_configured=bool(settings.google_maps_api_key),
    )


@router.get("/config/public")
def public_config():
    """Non-secret config for the frontend."""
    return {
        "maps_api_key": settings.google_maps_api_key or None,
        "currencies": ["IDR", "USD", "SGD", "MYR"],
    }


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return [_campaign_out(c) for c in db.query(Campaign).order_by(Campaign.id.desc()).all()]


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return _campaign_out(campaign)


@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    if campaign.geo_place_name:
        campaign.geography = format_geography(campaign)
    db.commit()
    db.refresh(campaign)
    return _campaign_out(campaign)


@router.get("/{campaign_id}/assets", response_model=list[CampaignAssetOut])
def list_assets(campaign_id: int, db: Session = Depends(get_db)):
    if not db.query(Campaign).get(campaign_id):
        raise HTTPException(404, "Campaign not found")
    return (
        db.query(CampaignAsset)
        .filter(CampaignAsset.campaign_id == campaign_id)
        .order_by(CampaignAsset.id.desc())
        .all()
    )


@router.post("/{campaign_id}/assets", response_model=CampaignAssetOut)
async def upload_asset(
    campaign_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    content_type = file.content_type or "application/octet-stream"
    if content_type in _IMAGE_TYPES:
        asset_type = "poster"
    elif content_type in _VIDEO_TYPES:
        asset_type = "video"
    else:
        raise HTTPException(400, "Hanya gambar (JPEG/PNG/WebP) atau video (MP4/WebM) yang didukung")

    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(400, "Ukuran file maksimal 25 MB")

    url = await upload_campaign_asset(
        data,
        campaign_id=campaign_id,
        file_name=file.filename or "asset",
        content_type=content_type,
    )
    asset = CampaignAsset(
        campaign_id=campaign_id,
        file_name=file.filename,
        mime_type=content_type,
        asset_type=asset_type,
        storage_url=url,
    )
    db.add(asset)
    campaign.promo_asset_url = url
    campaign.promo_asset_type = asset_type
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{campaign_id}/assets/file/{file_name}")
def serve_local_asset(campaign_id: int, file_name: str):
    path = resolve_local_asset_path(campaign_id, file_name)
    if not path:
        raise HTTPException(404, "File not found")
    return FileResponse(str(path))


@router.post("/{campaign_id}/find-leads", response_model=list[LeadOut])
async def find_leads(
    campaign_id: int,
    n: int = 3,
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    icp = icp_dict(campaign)
    offer = offer_dict(campaign)
    known = [l.company_name for l in db.query(Lead).filter(Lead.campaign_id == campaign_id).all()]

    agent = LeadFinderAgent(db=db, run_id=None, lead_id=None)
    try:
        result = await agent.run(icp=icp, offer=offer, known_companies=known, n=n)
    except Exception as exc:
        raise HTTPException(502, f"LeadFinder failed: {exc!s}") from exc

    discoveries = result.data.get("leads") or []
    if not isinstance(discoveries, list):
        raise HTTPException(502, f"LeadFinder returned unexpected shape: {type(discoveries).__name__}")

    created: list[Lead] = []
    for item in discoveries:
        if not isinstance(item, dict) or not item.get("company_name"):
            continue
        name = item["company_name"].strip()
        if any(name.lower() in k.lower() or k.lower() in name.lower() for k in known):
            continue
        lead = Lead(
            campaign_id=campaign_id,
            company_name=name,
            industry=item.get("industry") or None,
            website=item.get("website") or None,
            buyer_name=item.get("buyer_name") or None,
            buyer_role=item.get("buyer_role") or None,
            email=item.get("email") or None,
            raw_notes=item.get("raw_notes") or None,
            status="new",
        )
        db.add(lead)
        created.append(lead)
    db.commit()
    for lead in created:
        db.refresh(lead)
    return created
