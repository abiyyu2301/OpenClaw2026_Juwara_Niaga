"""Lead CRUD + CSV import + bulk paste + email test."""

from __future__ import annotations

import csv
import io
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.models import Campaign, Debate, Lead, LeadAIProfile, OutreachDraft, PaymentEvent, Reply
from db.session import get_db
from schemas import (
    EmailStatusOut,
    LeadBulkCreate,
    LeadCreate,
    LeadOut,
    LeadUpdate,
    TestEmailRequest,
)
from settings import settings
from tools.email import send_email

router = APIRouter(prefix="/leads", tags=["leads"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("/email-status", response_model=EmailStatusOut)
def email_status():
    configured = bool(settings.gmail_address and settings.gmail_app_password)
    dry_run = not configured
    if configured:
        msg = f"Email aktif — pengirim: {settings.gmail_address}"
    else:
        msg = (
            "Mode simulasi (dry-run): set GMAIL_ADDRESS dan GMAIL_APP_PASSWORD "
            "di Cloud Run / .env agar email benar-benar terkirim."
        )
    return EmailStatusOut(
        configured=configured,
        dry_run=dry_run,
        from_address=settings.gmail_address or None,
        message=msg,
    )


@router.post("/test-send")
async def test_send_email(payload: TestEmailRequest):
    if not _EMAIL_RE.match(payload.to_address.strip()):
        raise HTTPException(400, "Format email tidak valid")
    subject = "Tes Niaga — email berfungsi"
    body = (
        "Halo,\n\n"
        "Ini email percobaan dari Niaga. Jika Anda menerima pesan ini, "
        "konfigurasi SMTP Gmail sudah benar.\n\n"
        "— Tim Niaga"
    )
    msg_id = await send_email(
        to_address=payload.to_address.strip(),
        subject=subject,
        body=body,
    )
    return {
        "ok": True,
        "message_id": msg_id,
        "dry_run": not (settings.gmail_address and settings.gmail_app_password),
    }


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(payload.campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if payload.email and not _EMAIL_RE.match(payload.email.strip()):
        raise HTTPException(400, "Format email tidak valid")
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/bulk", response_model=list[LeadOut])
def create_leads_bulk(payload: LeadBulkCreate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(payload.campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if not payload.leads:
        raise HTTPException(400, "Daftar lead kosong")
    created: list[Lead] = []
    for item in payload.leads:
        if not item.company_name.strip():
            continue
        email = item.email.strip().lower() if item.email else None
        if email and not _EMAIL_RE.match(email):
            raise HTTPException(400, f"Email tidak valid: {item.email}")
        lead = Lead(
            campaign_id=payload.campaign_id,
            company_name=item.company_name.strip(),
            industry=item.industry,
            buyer_name=item.buyer_name,
            buyer_role=item.buyer_role,
            email=email,
            raw_notes=item.raw_notes or "Diimpor manual untuk uji email outreach.",
            status="new",
        )
        db.add(lead)
        created.append(lead)
    db.commit()
    for lead in created:
        db.refresh(lead)
    return created


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        if not _EMAIL_RE.match(data["email"].strip()):
            raise HTTPException(400, "Format email tidak valid")
        data["email"] = data["email"].strip().lower()
    for key, value in data.items():
        setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/import-csv", response_model=list[LeadOut])
async def import_leads_csv(
    campaign_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """CSV columns: company_name, email, industry, website, buyer_name, buyer_role, raw_notes."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    created: list[Lead] = []
    for row in reader:
        name = (row.get("company_name") or "").strip()
        if not name:
            continue
        lead = Lead(
            campaign_id=campaign_id,
            company_name=name,
            industry=row.get("industry"),
            website=row.get("website"),
            buyer_name=row.get("buyer_name"),
            buyer_role=row.get("buyer_role"),
            email=(row.get("email") or "").strip().lower() or None,
            raw_notes=row.get("raw_notes"),
            status="new",
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
