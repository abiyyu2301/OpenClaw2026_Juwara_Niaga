"""Lead CRUD + CSV import."""

from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.models import Campaign, Debate, Lead, LeadAIProfile, OutreachDraft, PaymentEvent, Reply
from db.session import get_db
from schemas import LeadCreate, LeadOut

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(payload.campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/import-csv", response_model=list[LeadOut])
async def import_leads_csv(
    campaign_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """CSV columns expected: company_name, industry, website, buyer_name, buyer_role, email, raw_notes."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    created: list[Lead] = []
    for row in reader:
        lead = Lead(
            campaign_id=campaign_id,
            company_name=row.get("company_name", "").strip(),
            industry=row.get("industry"),
            website=row.get("website"),
            buyer_name=row.get("buyer_name"),
            buyer_role=row.get("buyer_role"),
            email=row.get("email"),
            raw_notes=row.get("raw_notes"),
        )
        db.add(lead)
        created.append(lead)
    db.commit()
    for lead in created:
        db.refresh(lead)
    return created


@router.get("", response_model=list[LeadOut])
def list_leads(
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Lead)
    if campaign_id:
        q = q.filter(Lead.campaign_id == campaign_id)
    if status:
        q = q.filter(Lead.status == status)
    return q.order_by(Lead.id.desc()).limit(500).all()


@router.get("/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    profile = db.query(LeadAIProfile).filter(LeadAIProfile.lead_id == lead_id).first()
    debate = db.query(Debate).filter(Debate.lead_id == lead_id).order_by(Debate.id.desc()).first()
    drafts = (
        db.query(OutreachDraft)
        .filter(OutreachDraft.lead_id == lead_id)
        .order_by(OutreachDraft.created_at.asc())
        .all()
    )
    replies = (
        db.query(Reply)
        .filter(Reply.lead_id == lead_id)
        .order_by(Reply.created_at.asc())
        .all()
    )
    payments = (
        db.query(PaymentEvent)
        .filter(PaymentEvent.lead_id == lead_id)
        .order_by(PaymentEvent.created_at.asc())
        .all()
    )
    return {
        "lead": LeadOut.model_validate(lead).model_dump(),
        "profile": _to_dict(profile),
        "debate": _to_dict(debate),
        "drafts": [_to_dict(d) for d in drafts],
        "replies": [_to_dict(r) for r in replies],
        "payments": [_to_dict(p) for p in payments],
    }


def _to_dict(obj):
    if not obj:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
