"""MockPaymentProvider — always-works fallback for demos and dev.

The real DOKU adapter requires sandbox credentials and a 15-30 min consultation
call. The mock provider mirrors DOKU's interface so the orchestrator and UI
behave identically when the real credentials are not yet available.

The /webhooks/doku endpoint accepts a "simulated" event from the UI's
"Mark Paid / Mark Failed / Mark Expired" buttons, which goes through the
same code path as a real DOKU webhook.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from settings import settings
from tools.payment.base import PaymentLink, PaymentProvider


# In-memory store of reference -> status. Simple, in-process. Resets on restart.
_payment_state: Dict[str, str] = {}


class MockPaymentProvider(PaymentProvider):
    name = "mock"

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
        ref = f"mock_{uuid.uuid4().hex[:12]}"
        _payment_state[ref] = "created"
        # The "URL" points back to our own UI which renders the mock checkout
        # page with the simulate buttons.
        public = settings.public_base_url or "http://localhost:5173"
        url = f"{public}/mock-pay/{ref}?amount={amount}&desc={description}&lead={lead_id}"
        return PaymentLink(
            reference_id=ref,
            url=url,
            amount=amount,
            currency=currency,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
            raw={"mock": True, "ref": ref, "lead_id": lead_id, "reference": reference},
        )

    async def get_status(self, reference_id: str) -> str:
        return _payment_state.get(reference_id, "created")

    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        # Mock always accepts. Real DOKU adapter validates HMAC.
        return True

    # Helper used by the simulate endpoint to set status.
    @staticmethod
    def set_status(reference_id: str, status: str) -> None:
        _payment_state[reference_id] = status
