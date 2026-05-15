"""DOKUPaymentProvider — sandbox-ready stub for the DOKU Payment Link API.

This adapter is wired to the same PaymentProvider interface as the mock. When
real DOKU sandbox credentials are issued (via https://forms.doku.com/agentic-payments),
fill in DOKU_CLIENT_ID / DOKU_SECRET_KEY in .env and set PAYMENT_PROVIDER=doku.

The implementation here uses the Checkout API (developers.doku.com Checkout)
which is the programmatic equivalent of the no-integration Payment Link product.
Signature verification follows the DOKU HMAC-SHA256 scheme.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx

from settings import settings
from tools.payment.base import PaymentLink, PaymentProvider


class DOKUPaymentProvider(PaymentProvider):
    name = "doku"

    def __init__(self) -> None:
        if not (settings.doku_client_id and settings.doku_secret_key):
            raise RuntimeError(
                "DOKU credentials missing. Set DOKU_CLIENT_ID and DOKU_SECRET_KEY "
                "in .env, or switch PAYMENT_PROVIDER=mock."
            )

    async def create_payment_link(
        self,
        *,
        amount: int,
        currency: str,
        description: str,
        expires_in_hours: int,
        lead_id: int,
        reference: str,
    ) -> PaymentLink:
        invoice_number = f"NIAGA-{lead_id}-{uuid.uuid4().hex[:8]}"
        body: Dict[str, Any] = {
            "order": {
                "amount": amount,
                "invoice_number": invoice_number,
                "currency": currency,
                "callback_url": settings.public_base_url + "/payment-complete" if settings.public_base_url else None,
                "line_items": [{
                    "name": description,
                    "price": amount,
                    "quantity": 1,
                }],
            },
            "payment": {
                "payment_due_date": expires_in_hours * 60,  # minutes
            },
        }
        body_str = json.dumps(body, separators=(",", ":"))
        signature, request_id, timestamp = self._sign("POST", "/checkout/v1/payment", body_str)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.doku_base_url}/checkout/v1/payment",
                headers={
                    "Content-Type": "application/json",
                    "Client-Id": settings.doku_client_id,
                    "Request-Id": request_id,
                    "Request-Timestamp": timestamp,
                    "Signature": signature,
                },
                content=body_str,
            )
            resp.raise_for_status()
            data = resp.json()

        url = data.get("response", {}).get("payment", {}).get("url", "")
        return PaymentLink(
            reference_id=invoice_number,
            url=url,
            amount=amount,
            currency=currency,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
            raw=data,
        )

    async def get_status(self, reference_id: str) -> str:
        # DOKU's status check endpoint. Stub returns created until webhook fires.
        # For demo purposes, we rely on the webhook to update payment_events.payment_status.
        return "created"

    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify DOKU HMAC-SHA256 signature.

        DOKU sends: Client-Id, Request-Id, Request-Timestamp, Signature headers.
        Signature = base64(HMAC-SHA256(secret, client_id|request_id|timestamp|sha256(body)))
        """
        client_id = headers.get("client-id") or headers.get("Client-Id")
        request_id = headers.get("request-id") or headers.get("Request-Id")
        timestamp = headers.get("request-timestamp") or headers.get("Request-Timestamp")
        signature = headers.get("signature") or headers.get("Signature")
        if not (client_id and request_id and timestamp and signature):
            return False
        if client_id != settings.doku_client_id:
            return False
        body_hash = hashlib.sha256(body).hexdigest()
        to_sign = f"{client_id}|{request_id}|{timestamp}|{body_hash}"
        expected = base64.b64encode(
            hmac.new(settings.doku_secret_key.encode(), to_sign.encode(), hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(expected, signature)

    def _sign(self, method: str, path: str, body: str) -> tuple[str, str, str]:
        request_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        to_sign = (
            f"{settings.doku_client_id}|{request_id}|{timestamp}|"
            f"{method}|{path}|{body_hash}"
        )
        sig = base64.b64encode(
            hmac.new(settings.doku_secret_key.encode(), to_sign.encode(), hashlib.sha256).digest()
        ).decode()
        return sig, request_id, timestamp
