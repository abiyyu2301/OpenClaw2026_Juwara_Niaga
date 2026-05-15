"""Campaign CRUD + lead discovery (LeadFinder agent)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.leadfinder import LeadFinderAgent
from db.models import Campaign, Lead
from db.session import get_db
from schemas import CampaignCreate, CampaignOut, LeadOut

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).order_by(Campaign.id.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign


@router.post("/{campaign_id}/find-leads", response_model=list[LeadOut])
async def find_leads(
    campaign_id: int,
    n: int = 3,
    db: Session = Depends(get_db),
):
    """Use Gemini + Google Search grounding to discover Indonesian SMEs
    matching this campaign's ICP. Saves the discoveries as Lead rows in
    status='new' so the orchestrator picks them up on the next run."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    icp = {
        "target_industry": campaign.target_industry,
        "company_size": campaign.company_size,
        "geography": campaign.geography,
        "buyer_role": campaign.buyer_role,
        "pain_points": campaign.pain_points,
        "disqualifiers": campaign.disqualifiers,
    }
    offer = {
        "offer": campaign.offer,
        "pricing_range_min": campaign.pricing_range_min,
        "pricing_range_max": campaign.pricing_range_max,
        "currency": campaign.currency,
    }
    known = [l.company_name for l in db.query(Lead).filter(Lead.campaign_id == campaign_id).all()]

    agent = LeadFinderAgent(db=db, run_id=None, lead_id=None)
    try:
        result = await agent.run(icp=icp, offer=offer, known_companies=known, n=n)
    except Exception as exc:
        raise HTTPException(502, f"LeadFinder failed: {exc!s}")

    discoveries = result.data.get("leads") or []
    if not isinstance(discoveries, list):
        raise HTTPException(502, f"LeadFinder returned unexpected shape: {type(discoveries).__name__}")

    created: list[Lead] = []
    for item in discoveries:
        if not isinstance(item, dict) or not item.get("company_name"):
            continue
        # Skip duplicates against already-known names (case-insensitive substring)
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
