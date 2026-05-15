"""Abstract PaymentProvider — one interface, multiple backends (Mock, DOKU)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PaymentLink:
    """Return value from create_payment_link()."""
    reference_id: str  # provider-side unique id (DOKU's reference, or mock UUID)
    url: str           # the URL we send to the prospect
    amount: int
    currency: str
    expires_at: datetime
    raw: dict          # provider's full response payload (for debugging)


class PaymentProvider(ABC):
    """All payment providers (Mock, DOKU, ...) implement this surface."""

    @abstractmethod
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
        """Create a hosted payment page and return the URL + reference."""

    @abstractmethod
    async def get_status(self, reference_id: str) -> str:
        """Return one of: created | pending | paid | failed | expired | refunded."""

    @abstractmethod
    async def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify the webhook signature. Return True if authentic."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...
