"""Payment webhook receivers.

POST /webhooks/doku           — real DOKU webhook receiver (HMAC-verified)
POST /webhooks/mock-pay       — simulated event from the UI's Mark Paid / Mark Failed
                                / Mark Expired buttons (mock provider only)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from agents.aftercare import AfterCareAgent
from db.models import AgentRun, Lead, PaymentEvent
from db.session import SessionLocal, get_db
from tools.email import send_email
from tools.payment import get_payment_provider
from tools.payment.mock import MockPaymentProvider

log = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _handle_payment_status(reference_id: str, new_status: str) -> None:
    """Update payment_events + trigger AfterCare for a status change.

    Runs as a background task so the webhook responds 200 immediately.
    """
    db: Session = SessionLocal()
    try:
        event = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.doku_reference_id == reference_id)
            .first()
        )
        if not event:
            log.warning("Unknown payment reference: %s", reference_id)
            return

        old = event.payment_status
        event.payment_status = new_status
        if new_status == "paid":
            event.paid_at = datetime.now(timezone.utc)
        db.commit()

        if old == new_status:
            return

        lead = db.query(Lead).get(event.lead_id)
        if not lead:
            return

        new_lead_status = {
            "paid": "paid",
            "failed": "lost",
            "expired": "lost",
            "refunded": "lost",
        }.get(new_status, lead.status)
        lead.status = new_lead_status
        db.commit()

        # Find the active run for this lead's campaign so AfterCare is logged correctly.
        run = (
            db.query(AgentRun)
            .filter(AgentRun.campaign_id == lead.campaign_id)
            .order_by(AgentRun.id.desc())
            .first()
        )
        run_id = run.id if run else None

        # Bump run-level metrics on paid
        if new_status == "paid" and run:
            run.deals_closed = (run.deals_closed or 0) + 1
            run.total_revenue = (run.total_revenue or 0) + event.amount
            db.commit()

        aftercare = AfterCareAgent(db=db, run_id=run_id, lead_id=lead.id)
        result = await aftercare.run(
            lead_summary=f"{lead.company_name} ({lead.industry}) — buyer: {lead.buyer_name}",
            event={
                "type": event.commercial_event_type,
                "amount": event.amount,
                "currency": event.currency,
                "reference_id": event.doku_reference_id,
            },
            status=new_status,
        )
        data = result.data
        if data.get("should_send") and lead.email:
            try:
                await send_email(
                    to_address=lead.email,
                    subject=data.get("subject", "Update Niaga"),
                    body=data.get("body", ""),
                )
            except Exception as exc:
                log.exception("AfterCare send failed: %s", exc)
    finally:
        db.close()


@router.post("/doku")
async def doku_webhook(
    request: Request,
    background: BackgroundTasks,
):
    body = await request.body()
    provider = get_payment_provider()
    if not await provider.verify_webhook(dict(request.headers), body):
        raise HTTPException(401, "Invalid signature")

    payload = json.loads(body or b"{}")
    # DOKU sends `order.invoice_number` + `transaction.status`. Normalize.
    invoice_number = (
        payload.get("order", {}).get("invoice_number")
        or payload.get("invoice_number")
        or payload.get("reference_id")
    )
    raw_status = (
        payload.get("transaction", {}).get("status")
        or payload.get("payment_status")
        or payload.get("status", "")
    ).lower()
    # Map DOKU status vocabulary to ours.
    status = {
        "success": "paid",
        "completed": "paid",
        "paid": "paid",
        "failed": "failed",
        "expired": "expired",
        "refunded": "refunded",
        "pending": "pending",
    }.get(raw_status, raw_status or "pending")
    if not invoice_number:
        raise HTTPException(400, "Missing reference")
    background.add_task(_handle_payment_status, invoice_number, status)
    return {"ok": True}


@router.post("/mock-pay/{reference_id}")
async def simulate_payment(
    reference_id: str,
    status: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Driven by the UI buttons in mock-payment mode."""
    if status not in ("paid", "failed", "expired"):
        raise HTTPException(400, "status must be paid|failed|expired")
    MockPaymentProvider.set_status(reference_id, status)
    background.add_task(_handle_payment_status, reference_id, status)
    return {"ok": True, "reference_id": reference_id, "status": status}
