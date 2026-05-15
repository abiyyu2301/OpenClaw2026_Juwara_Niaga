"""Payment provider factory — choose Mock or DOKU based on settings."""

from settings import settings
from tools.payment.base import PaymentProvider
from tools.payment.mock import MockPaymentProvider


def get_payment_provider() -> PaymentProvider:
    if settings.payment_provider == "doku":
        # Lazy import so the optional DOKU adapter doesn't break dev runs.
        from tools.payment.doku import DOKUPaymentProvider
        return DOKUPaymentProvider()
    return MockPaymentProvider()


__all__ = ["PaymentProvider", "MockPaymentProvider", "get_payment_provider"]
